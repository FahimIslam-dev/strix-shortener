# 🚀 StrixShort - প্রিমিয়াম লিঙ্ক শর্টনার, QR স্টুডিও ও অ্যানালিটিক্স ইঞ্জিন
**ডেভেলপমেন্ট ও পাবলিশার:** [StrixDevs](https://strixdevs.com)

**StrixShort** হলো একটি আধুনিক, এন্টারপ্রাইজ গ্রেডের ইউআরএল শর্টনার ও লিঙ্ক ইন্টেলিজেন্স প্ল্যাটফর্ম। এটি বিশেষভাবে তৈরি করা হয়েছে **StrixDevs** ব্র্যান্ডিং এবং **Google AdSense** থেকে বৈধ উপায়ে সর্বোচ্চ আয় (Monetization) নিশ্চিত করার লক্ষ্যে।

---

## 💎 কী কী স্পেশাল ফিচার যুক্ত করা হয়েছে?

### ১. ⚡ আল্ট্রা-ফাস্ট Base62 লিঙ্ক শর্টনিং
- যেকোনো বড় URL নিমেষে ছোট কোডে রূপান্তর।
- **কাস্টম অ্যালিয়াস (Custom Slug):** নিজের পছন্দের নাম দেওয়া (যেমন: `strix/my-campaign`)।
- **পাসওয়ার্ড প্রোটেকশন:** গোপনীয় লিঙ্কে পাসওয়ার্ড দিয়ে লক করার সুবিধা।
- **মেয়াদ নির্ধারণ (Expiration Date):** নির্দিষ্ট তারিখের পর লিঙ্ক স্বয়ংক্রিয়ভাবে বন্ধ হওয়ার সুবিধা।

### ২. 💰 Google AdSense মনেটাইজেশন (Safe Transit Interstitial Mode)
- সাধারণ স্ক্যামি অ্যাডফ্লাই (Adf.ly) ধরণের সাইট Google AdSense অবিলম্বে ব্যান করে দেয়। তাই আমরা যুক্ত করেছি **Google Policy-Compliant Safe Transit Page** (`/safe/{code}`)।
- এতে ৪ সেকেন্ডের সিকিউরিটি ভেরিফিকেশন টাইমার ও গন্তব্য ওয়েবসাইটের তথ্য প্রদর্শিত হয়।
- এই পেজে উপরে ও নিচে হাই-সিপিআর (High-CTR) গুগল অ্যাডসেন্স ব্যানার স্লট বসানো আছে।
- ব্যবহারকারীরা তাদের লিঙ্কের জন্য **Direct 302 Redirect** অথবা **Safe Transit (Monetized)** মোড বেছে নিতে পারেন।

### ৩. 🎨 প্রিমিয়াম ভেক্টর QR কোড স্টুডিও
- শর্ট লিঙ্ক তৈরির সাথে সাথে স্বয়ংক্রিয়ভাবে হাই-রেজোলিউশন PNG এবং SVG QR কোড জেনারেট হয়।
- ডেডিকেটেড `/qr-generator` পেজ থেকে ব্যাকগ্রাউন্ড ও ফোরগ্রাউন্ড কালার পরিবর্তন করে প্রিন্ট-রেডি QR কোড ডাউনলোড করা যায়।

### ৪. 📊 রিয়েল-টাইম ক্লিক অ্যানালিটিক্স ড্যাশবোর্ড (`/analytics/{code}`)
- মোট ক্লিক সংখ্যা এবং লাইভ ট্র্যাকিং।
- ভিজিটরের ডিভাইস (মোবাইল, ডেস্কটপ, ট্যাবলেট)।
- ব্রাউজার ও অপারেটিং সিস্টেমের ভাগ (Chrome, Safari, Windows, iOS, ইত্যাদি)।
- ট্রাফিক সোর্স বা রেফারার চ্যানেল (Google, Twitter/X, Facebook, Direct)।
- ড্যাশবোর্ডেও গুগল অ্যাডসেন্স স্লট যুক্ত করা হয়েছে।

### ৫. 🏷️ ক্যাম্পেইন UTM বিল্ডার (`/utm-builder`)
- ডিজিটাল মার্কেটার ও এফিলিয়েটদের জন্য গুগল অ্যানালিটিক্স ক্যাম্পেইন প্যারামিটার (utm_source, utm_medium, utm_campaign) তৈরির পূর্ণাঙ্গ টুল।

### ৬. 🛡️ লিঙ্ক সেফটি ইন্সপেক্টর ও এক্সপ্যান্ডার (`/inspector`)
- অজানা কোনো শর্ট লিঙ্ক কোথায় রিডাইরেক্ট করে তা নিরাপদে দেখার টুল (Anti-Phishing Shield)।

### ৭. 🤖 এসইও (SEO) ও LLM-ফ্রেন্ডলি আর্কিটেকচার
- **JSON-LD Schema Markup:** Organization (StrixDevs), WebSite, SoftwareApplication এবং Rich Snippets-এর জন্য FAQPage স্কিমা যুক্ত।
- **AI ক্রলারের জন্য `llms.txt`:** ChatGPT, Claude, Perplexity যেন StrixShort-কে লিঙ্ক শর্টনার হিসেবে রেফার করে।
- **স্বয়ংক্রিয় `sitemap.xml` ও `robots.txt`**।

---

## 🛠️ প্রযুক্তিগত কাঠামো (Tech Stack)

- **ব্যাকএন্ড ও এপিআই:** Python FastAPI + Uvicorn (Asynchronous, High Concurrency)
- **ডেটাবেস:** SQLite 3 (WAL - Write-Ahead Logging মোড সক্রিয় করা, যা উচ্চ ট্রাফিকেও স্মুথ চলে)
- **ফ্রন্টএন্ড:** HTML5, আধুনিক Tailwind CSS (Glassmorphism + Dark Mode), FontAwesome 6, Lucide SVGs
- **QR ইঞ্জিন:** Pillow + python-qrcode

---

## 🏃‍♂️ কীভাবে রান করবেন (How to Run)

১. প্রজেক্ট ডিরেক্টরিতে যান:
```bash
cd /home/fahim/.gemini/antigravity/scratch/strix-shortener
```

২. ভার্চুয়াল এনভায়রনমেন্ট অ্যাক্টিভ করে সার্ভার চালু করুন:
```bash
./run.sh
```
অথবা:
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

৩. ব্রাউজারে ওপেন করুন: `http://localhost:8000`

---

## 💸 Google AdSense সেটআপ করার নিয়ম

১. `app/config.py` ফাইলে যান অথবা এনভায়রনমেন্ট ভেরিয়েবল সেট করুন:
```python
ADSENSE_CLIENT_ID = "ca-pub-আপনার-পাবলিশার-আইডি"
ADSENSE_ENABLED = True
```
২. আপনার AdSense আইডি বসিয়ে দিলে সমস্ত প্লেসহোল্ডার স্বয়ংক্রিয়ভাবে লাইভ গুগল অ্যাডে পরিণত হবে।

---

© 2026 **StrixDevs** (https://strixdevs.com). সর্বস্বত্ব সংরক্ষিত।
