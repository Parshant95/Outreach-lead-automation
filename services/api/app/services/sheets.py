"""Google Sheets is the sole persistence layer for the lightweight edition."""
from pathlib import Path
from threading import Lock
from uuid import uuid4
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.core.config import settings

SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
TAB = "Leads"
HEADERS = ["ID", "Business Name", "Category", "City", "Country", "Address", "Phone", "Email", "Website", "Rating", "Reviews", "Lead Score", "Priority", "Issues", "Status", "Google Maps URL", "Created At"]
_tab_lock = Lock()

def _service():
    if not settings.google_sheets_spreadsheet_id or not settings.google_service_account_file:
        raise ValueError("Set GOOGLE_SHEETS_SPREADSHEET_ID and GOOGLE_SERVICE_ACCOUNT_FILE in .env")
    path = Path(settings.google_service_account_file)
    if not path.exists(): raise ValueError("Google service-account JSON was not found at GOOGLE_SERVICE_ACCOUNT_FILE")
    credentials = Credentials.from_service_account_file(path, scopes=SCOPE)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)

def _values():
    return _service().spreadsheets().values()

def _ensure_tab():
    with _tab_lock:
        service = _service()
        spreadsheet_id = settings.google_sheets_spreadsheet_id
        metadata = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets.properties.title",
        ).execute()
        tabs = {sheet["properties"]["title"] for sheet in metadata.get("sheets", [])}
        if TAB not in tabs:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
            ).execute()

def _ensure_headers():
    _ensure_tab()
    values = _values()
    existing = values.get(spreadsheetId=settings.google_sheets_spreadsheet_id, range=f"{TAB}!1:1").execute().get("values", [])
    if not existing:
        values.update(spreadsheetId=settings.google_sheets_spreadsheet_id, range=f"{TAB}!A1", valueInputOption="RAW", body={"values":[HEADERS]}).execute()

def _row_to_lead(row:list[str], index:int) -> dict:
    row = row + [""] * (len(HEADERS) - len(row)); item = dict(zip(HEADERS,row))
    issues = [i.strip() for i in item["Issues"].split(";") if i.strip()]
    audit = None if not item["Lead Score"] else {"score":int(float(item["Lead Score"])),"priority":item["Priority"],"issues":issues}
    return {"id":item["ID"] or str(index),"name":item["Business Name"],"category":item["Category"] or None,"city":item["City"] or None,"country":item["Country"] or None,"address":item["Address"] or None,"phone":item["Phone"] or None,"email":item["Email"] or None,"website":item["Website"] or None,"rating":float(item["Rating"]) if item["Rating"] else None,"review_count":int(float(item["Reviews"])) if item["Reviews"] else 0,"status":item["Status"] or "New","maps_url":item["Google Maps URL"] or None,"audit":audit,"_row":index}

def list_leads() -> list[dict]:
    _ensure_headers()
    rows = _values().get(spreadsheetId=settings.google_sheets_spreadsheet_id, range=f"{TAB}!A2:Q").execute().get("values", [])
    return [_row_to_lead(row, idx + 2) for idx,row in enumerate(rows) if row and any(row)]

def append_lead(data:dict) -> dict:
    _ensure_headers(); item={**data,"id":str(uuid4()),"status":data.get("status","New")}
    row=[item["id"],item.get("name",""),item.get("category","") or "",item.get("city","") or "",item.get("country","") or "",item.get("address","") or "",item.get("phone","") or "",item.get("email","") or "",item.get("website","") or "",item.get("rating","") or "",item.get("review_count",0),"","","",item["status"],item.get("maps_url","") or "",item.get("created_at","")]
    _values().append(spreadsheetId=settings.google_sheets_spreadsheet_id, range=f"{TAB}!A1", valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body={"values":[row]}).execute()
    return {**item,"audit":None}

def update_audit(lead_id:str, result:dict) -> dict:
    lead=next((x for x in list_leads() if x["id"]==lead_id),None)
    if not lead: raise LookupError("Business not found")
    r=lead["_row"]
    _values().update(spreadsheetId=settings.google_sheets_spreadsheet_id, range=f"{TAB}!L{r}:N{r}", valueInputOption="USER_ENTERED", body={"values":[[result["score"],result["priority"],"; ".join(result["issues"])]]}).execute()
    lead["audit"]={"score":result["score"],"priority":result["priority"],"issues":result["issues"]}; return lead
