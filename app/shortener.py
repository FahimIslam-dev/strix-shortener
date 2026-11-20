import string
import secrets
import hashlib
import re
import io
import base64
import ipaddress
from urllib.parse import urlparse
from typing import Optional, Tuple
import qrcode

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
RESERVED_SLUGS = {
    "api", "static", "admin", "dashboard", "analytics", "preview", "safe", 
    "privacy", "terms", "about", "dmca", "contact", "utm-builder", "qr-generator",
    "inspector", "plans", "pricing", "sitemap.xml", "robots.txt", "llms.txt", 
    "favicon.ico", "docs", "help", "login", "register", "logout"
}

def generate_random_code(length: int = 6) -> str:
    """Generate cryptographically secure random base62 string."""
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))

def is_valid_url(url: str) -> bool:
    """
    Validate that the URL is a valid web URL and not internal, private loopback, 
    or cloud metadata service (protects against SSRF attacks).
    """
    if not url or len(url) > 2048:
        return False
    
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    
    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return False
        
    # Block localhost & standard loopback names
    if hostname in ("localhost", "0.0.0.0", "::1", "127.0.0.1"):
        return False
        
    if hostname.endswith((".local", ".internal", ".localhost", ".lan")):
        return False

    # Check IP addresses (private, loopback, link-local, cloud metadata 169.254.x.x)
    try:
        ip = ipaddress.ip_address(hostname)
        if (ip.is_private or ip.is_loopback or ip.is_link_local or 
            ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    except ValueError:
        # Hostname is a domain name (not raw IP)
        pass
        
    return True

def validate_custom_slug(slug: str) -> Tuple[bool, str]:
    """Validate custom slug format and check against reserved routes."""
    slug = slug.strip().lower()
    if len(slug) < 3 or len(slug) > 32:
        return False, "Custom alias must be between 3 and 32 characters long."
    
    if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
        return False, "Custom alias can only contain letters, numbers, hyphens (-), and underscores (_)."
        
    if slug in RESERVED_SLUGS:
        return False, f"'{slug}' is a reserved system path and cannot be used."
        
    return True, ""

def hash_password(password: str) -> str:
    """Hash link password with SHA256 and salt."""
    salt = "strix_salt_protect_2026_"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify link password against hash."""
    return hash_password(plain_password) == hashed_password

def generate_qr_base64(url: str, fill_color: str = "#0f172a", back_color: str = "#ffffff") -> str:
    """Generate high-quality QR code image as Base64 Data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
