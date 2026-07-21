import re
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from app.services.scoring import score_audit

async def analyze_website(url:str|None):
    if not url: return {"score":100,"priority":"High","lead_type":"No Website","website_score":0,"seo_score":0,"performance_score":0,"issues":["No website found"],"findings":{}}
    if not url.startswith("http"): url="https://"+url
    findings={"https":url.startswith("https://")}; issues=[]
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            res=await client.get(url, headers={"User-Agent":"LeadForgeAI/1.0 contact@example.com"}); html=res.text
            soup=BeautifulSoup(html,"lxml")
            text=html.lower(); title=soup.title.string.strip() if soup.title and soup.title.string else ""
            findings.update({"title":bool(title),"meta_description":bool(soup.select_one('meta[name="description"]')),"canonical":bool(soup.select_one('link[rel="canonical"]')),"structured_data":bool(soup.select_one('script[type="application/ld+json"]')),"open_graph":bool(soup.select_one('meta[property^="og:"]')),"favicon":bool(soup.select_one('link[rel*="icon"]')),"contact_form":bool(soup.select_one("form")),"whatsapp":"wa.me" in text or "whatsapp" in text,"booking":any(x in text for x in ["book now","appointment","reservation"]),"privacy":"privacy" in text,"mobile":bool(soup.select_one('meta[name="viewport"]')),"sitemap":False})
            alt_missing=sum(1 for i in soup.select("img") if not i.get("alt")); findings["alt_missing"]=alt_missing
            h1=len(soup.select("h1")); findings["h1_count"]=h1
            for k,label in [("https","HTTPS/SSL"),("mobile","mobile viewport"),("meta_description","meta description"),("contact_form","contact form"),("whatsapp","WhatsApp CTA"),("privacy","privacy policy"),("structured_data","structured data")]:
                if not findings.get(k): issues.append(f"Missing {label}")
            if alt_missing: issues.append(f"{alt_missing} image(s) missing alt text")
            if h1 != 1: issues.append("Heading structure should have exactly one H1")
            findings["seo"]=max(0,100-len(issues)*9); findings["performance"]=60
    except Exception as exc: issues.append("Website could not be reached reliably"); findings.update({"mobile":False,"seo":20,"performance":20})
    score,priority,lead_type=score_audit(url,findings,issues)
    return {"score":score,"priority":priority,"lead_type":lead_type,"website_score":max(0,100-len(issues)*8),"seo_score":findings.get("seo",0),"performance_score":findings.get("performance",0),"issues":issues,"findings":findings}
