# StrixShort - Enterprise Link Intelligence, Branded URLs & QR Studio

StrixShort is a high-performance URL shortener, branded link management utility, and link intelligence platform built with **Python FastAPI**, **SQLite (WAL Mode)**, and modern **Tailwind CSS**.

---

## 🚀 Key Features

### 1. Ultra-Fast Base62 Link Shortening
- Instant redirection with sub-35ms response time.
- **Custom Slugs:** Create branded aliases (e.g., `strixshort.com/my-campaign`).
- **Passcode Protection:** Secure sensitive destination links with a password.
- **Auto-Expiration:** Set links to automatically expire on a specific date and time.

### 2. Google AdSense Monetization (Safe Transit Mode)
- Policy-compliant interstitial security check page (`/safe/{code}`) with customizable countdown.
- Top and bottom high-CTR AdSense banner slots.
- Users can choose between **Direct 302 Redirection** or **Safe Transit (Monetized)**.

### 3. Vector QR Code Studio (`/qr-generator`)
- Generates high-resolution PNG & SVG vector QR codes.
- Custom foreground and background color palettes.
- Print-ready and instant download.

### 4. Click Intelligence & Audience Analytics (`/analytics/{code}`)
- Real-time click counting and geographic distribution.
- Device breakdown (Mobile, Desktop, Tablet).
- Browser and Operating System tracking.
- Traffic referrers and campaign performance metrics.

### 5. Campaign UTM Builder (`/utm-builder`)
- Built-in Google Analytics campaign parameter generator (`utm_source`, `utm_medium`, `utm_campaign`, etc.).
- Shorten UTM-tagged campaign links in a single click.

### 6. Anti-Phishing Link Inspector (`/inspector`)
- Expand and verify destination URLs before opening.
- SSL protocol validation and destination metadata inspection.

### 7. Authentication & Dashboards
- User registration and login with secure HMAC-SHA256 session cookies.
- **User Dashboard (`/dashboard`):** Manage personal links, view analytics, pause/activate, or delete links.
- **Admin Portal (`/admin`):** System-wide analytics, user management, and global link moderation.

---

## 🛠️ Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn (Asynchronous, High Concurrency)
- **Database:** SQLite 3 (WAL - Write-Ahead Logging mode enabled)
- **Frontend:** HTML5, Tailwind CSS (Liquid Glass UI), FontAwesome 6
- **QR Engine:** python-qrcode, Pillow

---

## 🏃 Running the Application

### 1. Start with the startup script:
```bash
./run.sh
```

### 2. Or start directly using uvicorn:
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open in your browser:
```text
http://localhost:8000
```

---

## ⚙️ Configuration & AdSense Setup

Configure environment variables in `.env` (or rename `.env.example` to `.env`):

```bash
# Public Domain
BASE_URL=https://your-domain.com

# Google AdSense
ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
ADSENSE_ENABLED=true

# Security
SECRET_KEY=your_super_secret_key_here
```

---

## 📁 Project Structure

```text
strix-shortener/
├── app/
│   ├── main.py              # Application routes, APIs, and redirection logic
│   ├── database.py          # SQLite schema, queries, and analytics storage
│   ├── auth.py              # Authentication, password hashing, and signed cookies
│   ├── shortener.py         # Base62 generator, SSRF protection, QR utilities
│   ├── analytics.py         # User-agent, device, and referrer parsing
│   ├── config.py            # Settings and environment configuration
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Global layout, header, footer, and navigation
│   │   ├── index.html       # Landing page and shortener console
│   │   ├── dashboard.html   # User dashboard
│   │   ├── admin.html       # Admin portal
│   │   ├── login.html       # Login page
│   │   ├── register.html    # Registration page
│   │   ├── preview.html     # Monetized interstitial safe transit page
│   │   ├── analytics.html   # Detailed click analytics report
│   │   ├── inspector.html   # Link safety inspector
│   │   ├── qr_generator.html# QR Code studio
│   │   └── utm_builder.html # Campaign UTM builder
│   └── static/              # CSS, images, and public assets
├── requirements.txt         # Python dependencies
├── Procfile                 # Cloud deployment startup definition
├── .env.example             # Example environment configuration
└── run.sh                   # Local execution script
```

---

© 2026 **StrixDevs** (https://strixdevs.com). All rights reserved.
