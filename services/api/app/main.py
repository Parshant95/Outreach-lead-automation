from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import BusinessCreate, DiscoveryRequest, OutreachRequest
from app.services.analyzer import analyze_website
from app.services.discovery import DiscoveryError, discover_google_places
from app.services.sheets import append_lead, list_leads, update_audit

app=FastAPI(title="LeadForge AI — Sheets Edition", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def sheet_error(exc:Exception):
    if isinstance(exc, (ValueError, PermissionError)): raise HTTPException(503, str(exc))
    raise exc
@app.get("/health")
def health(): return {"status":"ok","storage":"google-sheets"}
@app.get("/api/v1/businesses")
def businesses(city:str|None=None,category:str|None=None,no_website:bool=False,min_score:int|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100)):
    try: rows=list_leads()
    except Exception as exc: sheet_error(exc)
    if city: rows=[x for x in rows if city.lower() in (x["city"] or "").lower()]
    if category: rows=[x for x in rows if category.lower() in (x["category"] or "").lower()]
    if no_website: rows=[x for x in rows if not x["website"]]
    if min_score is not None: rows=[x for x in rows if x["audit"] and x["audit"]["score"]>=min_score]
    total=len(rows); rows=rows[(page-1)*page_size:page*page_size]
    for x in rows: x.pop("_row",None)
    return {"items":rows,"total":total,"page":page,"page_size":page_size}
@app.post("/api/v1/businesses",status_code=201)
def create_business(data:BusinessCreate):
    try: return append_lead({**data.model_dump(),"created_at":datetime.now(timezone.utc).isoformat()})
    except Exception as exc: sheet_error(exc)
@app.post("/api/v1/discovery",status_code=201)
async def discovery(request:DiscoveryRequest):
    try:
        results=await discover_google_places(request); output=[]
        for item in results: output.append(append_lead({**item.model_dump(),"created_at":datetime.now(timezone.utc).isoformat()}))
        return output
    except DiscoveryError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc: sheet_error(exc)
@app.post("/api/v1/businesses/{business_id}/analyze")
async def analyze(business_id:str):
    try: lead=next((x for x in list_leads() if x["id"]==business_id),None)
    except Exception as exc: sheet_error(exc)
    if not lead: raise HTTPException(404,"Business not found")
    result=await analyze_website(lead["website"])
    try: return update_audit(business_id,result)
    except Exception as exc: sheet_error(exc)
@app.get("/api/v1/dashboard")
def dashboard():
    try: rows=list_leads()
    except Exception as exc: sheet_error(exc)
    audits=[x["audit"] for x in rows if x["audit"]]
    return {"total_leads":len(rows),"no_website":sum(not x["website"] for x in rows),"high_priority":sum(x["score"]>=70 for x in audits),"seo_problems":0,"average_score":round(sum(x["score"] for x in audits)/len(audits),1) if audits else 0,"cities":len({x["city"] for x in rows if x["city"]}),"categories":len({x["category"] for x in rows if x["category"]}),"conversion_rate":0}
@app.post("/api/v1/businesses/{business_id}/outreach")
def outreach(business_id:str,request:OutreachRequest):
    try: lead=next((x for x in list_leads() if x["id"]==business_id),None)
    except Exception as exc: sheet_error(exc)
    if not lead: raise HTTPException(404,"Business not found")
    issues=(lead["audit"] or {}).get("issues",["your public digital presence"]); text=", ".join(issues[:3]).replace("Missing ","")
    return {"channel":request.channel,"message":f"Hi {lead['name']} team! While reviewing your online presence, we noticed {text}. We can share a short complimentary audit with practical improvements for more enquiries. Would you like that?","based_on":issues}
