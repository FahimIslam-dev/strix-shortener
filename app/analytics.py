import re
from typing import Tuple, Dict

def parse_user_agent(ua_string: str) -> Dict[str, str]:
    """Parse User-Agent string to extract device, browser, and operating system."""
    ua = (ua_string or "").lower()
    
    # Device detection
    if "tablet" in ua or "ipad" in ua:
        device = "Tablet"
    elif "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "Mobile"
    else:
        device = "Desktop"
        
    # Browser detection
    if "edg" in ua:
        browser = "Microsoft Edge"
    elif "chrome" in ua and "safari" in ua and "edg" not in ua and "opr" not in ua:
        browser = "Google Chrome"
    elif "firefox" in ua:
        browser = "Mozilla Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Apple Safari"
    elif "opr" in ua or "opera" in ua:
        browser = "Opera"
    else:
        browser = "Other / Bot"
        
    # Operating System detection
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        os_name = "iOS"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Other"
        
    return {
        "device": device,
        "browser": browser,
        "os": os_name
    }

def clean_referrer(referrer: str) -> str:
    """Format and clean referrer domain."""
    if not referrer:
        return "Direct / Unknown"
    ref = referrer.lower()
    if "google." in ref:
        return "Google Search"
    elif "t.co" in ref or "twitter.com" in ref or "x.com" in ref:
        return "Twitter / X"
    elif "facebook.com" in ref or "fb.com" in ref:
        return "Facebook"
    elif "linkedin.com" in ref:
        return "LinkedIn"
    elif "instagram.com" in ref:
        return "Instagram"
    elif "youtube.com" in ref:
        return "YouTube"
    elif "reddit.com" in ref:
        return "Reddit"
    
    # Extract domain
    m = re.search(r"https?://([^/]+)", referrer)
    if m:
        return m.group(1)
    return referrer[:30]
