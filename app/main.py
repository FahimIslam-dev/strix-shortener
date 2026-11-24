import os
import io
import time
from collections import defaultdict
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Form, Depends, BackgroundTasks, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .config import settings
from .database import (
    init_db, create_url, get_url_by_code, record_click, 
    get_url_analytics, get_platform_stats,
    create_user, get_user_by_email, get_user_by_id,
    get_user_urls, get_all_users, get_all_urls,
    delete_url, toggle_url_status, get_admin_stats
)
from .shortener import (
    generate_random_code, is_valid_url, validate_custom_slug, 
    hash_password as hash_link_password, verify_password as verify_link_password,
    generate_qr_base64
)
from .auth import (
    SESSION_COOKIE_NAME, sign_session_data, verify_session_token,
    get_current_user_optional, get_current_user, get_current_admin,
    hash_password, verify_password
)
from .analytics import parse_user_agent, clean_referrer
import qrcode

# In-memory sliding window rate limiter
_ip_rate_limits = defaultdict(list)

def check_rate_limit(client_ip: str, max_requests: int = 40, window_seconds: int = 60) -> bool:
    """Sliding-window IP rate limiter to protect against bot floods & DoS."""
    now = time.time()
    timestamps = _ip_rate_limits[client_ip]
    _ip_rate_limits[client_ip] = [t for t in timestamps if now - t < window_seconds]
    if len(_ip_rate_limits[client_ip]) >= max_requests:
        return False
    _ip_rate_limits[client_ip].append(now)
    return True

# Safe redirect handler to prevent SSRF via 30x HTTP redirects
class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_valid_url(newurl):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)

safe_urllib_opener = urllib.request.build_opener(SafeRedirectHandler())

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise link management, URL shortening, QR studio & analytics engine by StrixDevs.",
    version="2.1.0"
)

# Static and Templates
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_base_url(request: Request) -> str:
    """Resolve the active base URL from BASE_URL env var or incoming request headers."""
    env_base = os.getenv("BASE_URL", "").strip().rstrip("/")
    if env_base:
        return env_base
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc)).split(",")[0].strip()
    return f"{proto}://{host}".rstrip("/")

# Context processor for templates
def template_context(request: Request, extra: dict = None) -> dict:
    current_user = get_current_user_optional(request)
    req_settings = settings.model_copy(update={"BASE_URL": get_base_url(request)})
    ctx = {
        "request": request,
        "settings": req_settings,
        "now_year": datetime.now().year,
        "user": current_user
    }
    if extra:
        ctx.update(extra)
    return ctx

def render_template(request: Request, name: str, extra: dict = None, status_code: int = 200) -> HTMLResponse:
    ctx = template_context(request, extra)
    return templates.TemplateResponse(request=request, name=name, context=ctx, status_code=status_code)

@app.on_event("startup")
def on_startup():
    init_db()

# Request Models
class ShortenRequest(BaseModel):
    url: str
    custom_slug: Optional[str] = None
    transit_mode: Optional[str] = "direct"
    password: Optional[str] = None
    expires_at: Optional[str] = None

# Background task for click tracking
def log_click_task(url_id: int, client_ip: str, referrer: str, user_agent: str, country: str):
    ua_data = parse_user_agent(user_agent)
    ref = clean_referrer(referrer)
    record_click(
        url_id=url_id,
        ip=client_ip,
        referrer=ref,
        user_agent=user_agent,
        device=ua_data["device"],
        browser=ua_data["browser"],
        os_name=ua_data["os"],
        country=country
    )

# ----------------- Frontend Web Pages -----------------

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    stats = get_platform_stats()
    return render_template(request, "index.html", {"stats": stats})

@app.get("/plans", response_class=HTMLResponse)
async def plans_page(request: Request):
    return render_template(request, "plans.html")

@app.get("/qr-generator", response_class=HTMLResponse)
async def qr_page(request: Request):
    return render_template(request, "qr_generator.html")

@app.get("/utm-builder", response_class=HTMLResponse)
async def utm_page(request: Request):
    return render_template(request, "utm_builder.html")

@app.get("/inspector", response_class=HTMLResponse)
async def inspector_page(request: Request):
    return render_template(request, "inspector.html")

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return render_template(request, "about.html")

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return render_template(request, "privacy.html")

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return render_template(request, "terms.html")

@app.get("/dmca", response_class=HTMLResponse)
async def dmca_page(request: Request):
    return render_template(request, "dmca.html")

# ----------------- Authentication Routes -----------------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        if user.get("is_admin"):
            return RedirectResponse(url="/admin", status_code=302)
        return RedirectResponse(url="/dashboard", status_code=302)
    return render_template(request, "login.html")

@app.post("/login")
async def handle_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return render_template(request, "login.html", {
            "error": "Invalid email or password. Please try again."
        }, status_code=400)
    
    session_token = sign_session_data({"user_id": user["id"], "email": user["email"]})
    redirect_target = "/admin" if user.get("is_admin") else "/dashboard"
    response = RedirectResponse(url=redirect_target, status_code=302)
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=is_secure,
        max_age=60 * 60 * 24 * 30, # 30 days
        samesite="lax"
    )
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return render_template(request, "register.html")

@app.post("/register")
async def handle_register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return render_template(request, "register.html", {"error": "Please enter a valid email address."}, status_code=400)
    
    if len(password) < 6:
        return render_template(request, "register.html", {"error": "Password must be at least 6 characters long."}, status_code=400)
        
    existing = get_user_by_email(clean_email)
    if existing:
        return render_template(request, "register.html", {"error": "An account with this email already exists."}, status_code=400)
    
    pwd_hash = hash_password(password)
    user = create_user(email=clean_email, password_hash=pwd_hash, full_name=full_name)
    if not user:
        return render_template(request, "register.html", {"error": "Could not register account. Please try again."}, status_code=500)
        
    session_token = sign_session_data({"user_id": user["id"], "email": user["email"]})
    response = RedirectResponse(url="/dashboard", status_code=302)
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=is_secure,
        max_age=60 * 60 * 24 * 30,
        samesite="lax"
    )
    return response

@app.get("/logout")
async def handle_logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response

# ----------------- User Dashboard & Admin -----------------

@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    user_urls = get_user_urls(user["id"])
    total_clicks = sum(u["clicks_count"] for u in user_urls)
    active_links = sum(1 for u in user_urls if u["is_active"] == 1)
    
    return render_template(request, "dashboard.html", {
        "user": user,
        "urls": user_urls,
        "total_links": len(user_urls),
        "total_clicks": total_clicks,
        "active_links": active_links
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_portal(request: Request):
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Administrator access required.")
    
    stats = get_admin_stats()
    all_urls = get_all_urls(limit=200)
    all_users = get_all_users()
    
    return render_template(request, "admin.html", {
        "user": user,
        "stats": stats,
        "all_urls": all_urls,
        "all_users": all_users
    })

# ----------------- Analytics & Preview -----------------

@app.get("/analytics/{short_code}", response_class=HTMLResponse)
async def analytics_page(request: Request, short_code: str):
    url_data = get_url_by_code(short_code)
    if not url_data:
        raise HTTPException(status_code=404, detail="Short link not found.")
    
    analytics_data = get_url_analytics(url_data["id"])
    return render_template(request, "analytics.html", analytics_data)

@app.get("/safe/{short_code}", response_class=HTMLResponse)
async def safe_preview_page(request: Request, short_code: str, background_tasks: BackgroundTasks):
    url_data = get_url_by_code(short_code)
    if not url_data:
        raise HTTPException(status_code=404, detail="Short link not found.")
    
    # Log click
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    referrer = request.headers.get("referer", "")
    user_agent = request.headers.get("user-agent", "")
    country = request.headers.get("cf-ipcountry", "Global")
    
    background_tasks.add_task(log_click_task, url_data["id"], client_ip, referrer, user_agent, country)

    return render_template(request, "preview.html", {
        "url": url_data,
        "target_url": url_data["long_url"],
        "delay": settings.DEFAULT_TRANSIT_DELAY
    })

# ----------------- APIs -----------------

@app.post("/api/shorten")
async def api_shorten(request: Request, req: ShortenRequest):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1").split(",")[0].strip()
    if not check_rate_limit(client_ip, max_requests=40, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment before creating more links.")
        
    clean_url = req.url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url
        
    if not is_valid_url(clean_url):
        raise HTTPException(status_code=400, detail="Invalid destination URL. Internal, loopback, or malformed URLs are rejected.")
    
    # Check custom alias
    short_code = ""
    is_custom = False
    if req.custom_slug:
        valid_slug, err_msg = validate_custom_slug(req.custom_slug)
        if not valid_slug:
            raise HTTPException(status_code=400, detail=err_msg)
        existing = get_url_by_code(req.custom_slug.strip().lower())
        if existing:
            raise HTTPException(status_code=400, detail=f"Alias '{req.custom_slug}' is already taken. Please choose another.")
        short_code = req.custom_slug.strip().lower()
        is_custom = True
    else:
        # Generate random unique code
        for _ in range(5):
            code_candidate = generate_random_code(6)
            if not get_url_by_code(code_candidate):
                short_code = code_candidate
                break
        if not short_code:
            short_code = generate_random_code(8)
            
    # Hash password if provided
    pwd_hash = hash_link_password(req.password) if req.password and req.password.strip() else None
    
    # Transit mode
    mode = req.transit_mode if req.transit_mode in ("direct", "safe_transit") else "direct"
    
    # Check logged-in user
    current_user = get_current_user_optional(request)
    user_id = current_user["id"] if current_user else None
    
    created = create_url(
        short_code=short_code,
        long_url=clean_url,
        custom_alias=is_custom,
        password_hash=pwd_hash,
        expires_at=req.expires_at if req.expires_at else None,
        transit_mode=mode,
        user_id=user_id
    )
    
    short_url = f"{get_base_url(request)}/{short_code}"
    qr_b64 = generate_qr_base64(short_url)
    
    return {
        "success": True,
        "short_code": short_code,
        "short_url": short_url,
        "long_url": clean_url,
        "transit_mode": mode,
        "qr_code_base64": qr_b64,
        "created_at": created["created_at"],
        "user_id": user_id
    }

@app.post("/api/urls/{url_id}/toggle")
async def api_toggle_url(request: Request, url_id: int):
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    
    is_admin = bool(user.get("is_admin"))
    new_status = toggle_url_status(url_id=url_id, user_id=user["id"], is_admin=is_admin)
    if new_status is None:
        raise HTTPException(status_code=404, detail="URL not found or unauthorized.")
        
    return {"success": True, "url_id": url_id, "is_active": new_status}

@app.delete("/api/urls/{url_id}")
async def api_delete_url(request: Request, url_id: int):
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    is_admin = bool(user.get("is_admin"))
    deleted = delete_url(url_id=url_id, user_id=user["id"], is_admin=is_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="URL not found or unauthorized.")
        
    return {"success": True, "url_id": url_id}

@app.get("/api/qr")
async def api_qr(text: str = "https://strixdevs.com", fg: str = "#0f172a", bg: str = "#ffffff"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/api/inspect")
async def api_inspect(request: Request, url: str):
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url
        
    if not is_valid_url(clean_url):
        raise HTTPException(status_code=400, detail="Invalid target URL.")

    # Check if this is an internal short URL
    parsed_base = get_base_url(request).replace("http://", "").replace("https://", "")
    if parsed_base in clean_url:
        code = clean_url.rstrip("/").split("/")[-1]
        local = get_url_by_code(code)
        if local:
            return {
                "input_url": url,
                "final_url": local["long_url"],
                "status_code": 200,
                "title": "StrixShort Verified Target",
                "is_secure": local["long_url"].startswith("https://")
            }

    try:
        req = urllib.request.Request(clean_url, headers={"User-Agent": "Mozilla/5.0 (compatible; StrixShort-Inspector/2.0; +https://strixdevs.com)"})
        with safe_urllib_opener.open(req, timeout=5) as response:
            final_url = response.geturl()
            status_code = response.getcode()
            content = response.read(2048).decode("utf-8", errors="ignore")
            title = ""
            if "<title>" in content:
                start = content.find("<title>") + 7
                end = content.find("</title>", start)
                if end != -1:
                    title = content[start:end].strip()
            return {
                "input_url": url,
                "final_url": final_url,
                "status_code": status_code,
                "title": title[:100] if title else "Web Resource",
                "is_secure": final_url.startswith("https://")
            }
    except Exception:
        return {
            "input_url": url,
            "final_url": clean_url,
            "status_code": 200,
            "title": "Verified Destination",
            "is_secure": clean_url.startswith("https://")
        }

# ----------------- SEO & LLM Specifications -----------------

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(request: Request):
    base_url = get_base_url(request)
    return f"""User-agent: *
Allow: /
Allow: /qr-generator
Allow: /utm-builder
Allow: /inspector
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /dmca
Disallow: /api/
Disallow: /analytics/
Disallow: /admin
Disallow: /dashboard

User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {base_url}/sitemap.xml
"""

@app.get("/llms.txt", response_class=PlainTextResponse)
async def llms_txt():
    path = os.path.join(STATIC_DIR, "llms.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "StrixShort - Link Intelligence by StrixDevs"

@app.get("/ads.txt", response_class=PlainTextResponse)
async def ads_txt():
    pub_id = settings.ADSENSE_CLIENT_ID.replace("ca-", "")
    return f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"

@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml(request: Request):
    base_url = get_base_url(request)
    today = datetime.now().strftime("%Y-%m-%d")
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/qr-generator</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/utm-builder</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/inspector</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/about</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>{base_url}/privacy</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base_url}/terms</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{base_url}/dmca</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return Response(content=xml_content, media_type="application/xml")

# ----------------- Dynamic Shortcode Redirection -----------------

@app.get("/{short_code}")
async def handle_redirect(request: Request, short_code: str, background_tasks: BackgroundTasks):
    url_data = get_url_by_code(short_code)
    if not url_data:
        raise HTTPException(status_code=404, detail="Short URL not found or has been disabled.")
    
    if url_data.get("is_active") == 0:
        return HTMLResponse(content="<div style='text-align:center;padding:50px;font-family:sans-serif;'><h2>This link has been disabled by the administrator or owner.</h2></div>", status_code=403)
    
    # Check expiration
    if url_data["expires_at"]:
        try:
            exp_date = datetime.fromisoformat(url_data["expires_at"])
            if datetime.now() > exp_date:
                return HTMLResponse(content="<h2 style='text-align:center;margin-top:50px;font-family:sans-serif;'>This link has expired.</h2>", status_code=410)
        except Exception:
            pass

    # Check password protection
    if url_data["password_hash"]:
        return render_template(request, "password_prompt.html", {
            "short_code": short_code,
            "error": None
        })

    # Log analytics
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    referrer = request.headers.get("referer", "")
    user_agent = request.headers.get("user-agent", "")
    country = request.headers.get("cf-ipcountry", "Global")
    
    background_tasks.add_task(log_click_task, url_data["id"], client_ip, referrer, user_agent, country)

    # Monetized / Safe transit mode
    if url_data["transit_mode"] == "safe_transit":
        return render_template(request, "preview.html", {
            "url": url_data,
            "target_url": url_data["long_url"],
            "delay": settings.DEFAULT_TRANSIT_DELAY
        })

    # Direct 302 Redirection
    return RedirectResponse(url=url_data["long_url"], status_code=302)

@app.post("/{short_code}")
async def verify_link_password(
    request: Request, 
    short_code: str, 
    password: str = Form(...), 
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    url_data = get_url_by_code(short_code)
    if not url_data:
        raise HTTPException(status_code=404, detail="Short URL not found.")
        
    if url_data.get("is_active") == 0:
        return HTMLResponse(content="<div style='text-align:center;padding:50px;font-family:sans-serif;'><h2>This link has been disabled.</h2></div>", status_code=403)
        
    if not url_data["password_hash"] or verify_link_password(password, url_data["password_hash"]):
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
        referrer = request.headers.get("referer", "")
        user_agent = request.headers.get("user-agent", "")
        country = request.headers.get("cf-ipcountry", "Global")
        background_tasks.add_task(log_click_task, url_data["id"], client_ip, referrer, user_agent, country)

        if url_data["transit_mode"] == "safe_transit":
            return render_template(request, "preview.html", {
                "url": url_data,
                "target_url": url_data["long_url"],
                "delay": settings.DEFAULT_TRANSIT_DELAY
            })
        return RedirectResponse(url=url_data["long_url"], status_code=302)
    else:
        return render_template(request, "password_prompt.html", {
            "short_code": short_code,
            "error": "Incorrect password. Please try again."
        })
