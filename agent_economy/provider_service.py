"""Stateless CSV/JSON quality-check HTTP service for AgenC MVP; no chain writes."""
from __future__ import annotations
import csv, hashlib, io, json, os, time
from collections import defaultdict, deque
from typing import Any
from wsgiref.simple_server import make_server

MAX_BODY_BYTES = 256 * 1024
MAX_CONTENT_BYTES = 192 * 1024
MAX_REQUESTS_PER_MINUTE = 30
_requests: dict[str, deque[float]] = defaultdict(deque)

def _response(start_response, status: str, payload: dict[str, Any]):
    body = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")])
    return [body]

def _limited(client: str, now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    q = _requests[client]
    while q and now - q[0] >= 60: q.popleft()
    if len(q) >= MAX_REQUESTS_PER_MINUTE: return True
    q.append(now)
    return False

def _csv(text: str) -> dict[str, Any]:
    try: rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error as exc: return {"valid": False, "format": "csv", "findings": [{"code":"CSV_PARSE_ERROR","message":str(exc)}]}
    findings = []
    if not rows or not rows[0] or not any(c.strip() for c in rows[0]):
        return {"valid":False,"format":"csv","findings":[{"code":"MISSING_HEADER","message":"CSV needs a non-empty header row."}]}
    header=rows[0]
    if any(not name.strip() for name in header): findings.append({"code":"EMPTY_COLUMN_NAME","message":"One or more column names are empty."})
    norm=[name.strip().casefold() for name in header]
    if len(set(norm)) != len(norm): findings.append({"code":"DUPLICATE_COLUMN","message":"Column names are duplicated (case-insensitive)."})
    bad=[i+1 for i,row in enumerate(rows[1:],start=1) if len(row)!=len(header)]
    if bad: findings.append({"code":"ROW_WIDTH_MISMATCH","message":"Some data rows have a different number of fields.","row_numbers":bad[:100],"count":len(bad)})
    if len(rows)==1: findings.append({"code":"NO_DATA_ROWS","message":"CSV has a header but no data rows.","severity":"warning"})
    return {"valid":not any(f.get("severity")!="warning" for f in findings),"format":"csv","columns":len(header),"data_rows":max(0,len(rows)-1),"findings":findings}

def validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload,dict): raise ValueError("Request JSON must be an object.")
    filename=payload.get("filename","upload"); fmt=str(payload.get("format","")).lower().strip(); content=payload.get("content")
    if not isinstance(filename,str) or not filename or len(filename)>160 or "/" in filename or chr(92) in filename: raise ValueError("filename must be a simple filename, not a path.")
    if fmt not in {"csv","json"}: raise ValueError("format must be 'csv' or 'json'.")
    if not isinstance(content,str): raise ValueError("content must be a UTF-8 text string.")
    raw=content.encode("utf-8")
    if len(raw)>MAX_CONTENT_BYTES: raise OverflowError("content exceeds the 192 KiB limit.")
    result: dict[str,Any]
    if fmt=="json":
        try:
            parsed=json.loads(content); result={"valid":True,"format":"json","root_type":type(parsed).__name__,"findings":[]}
        except json.JSONDecodeError as exc: result={"valid":False,"format":"json","findings":[{"code":"JSON_PARSE_ERROR","message":exc.msg,"line":exc.lineno,"column":exc.colno}]}
    else: result=_csv(content)
    return {"service":"CSV/JSON Data Quality Check","version":"0.1.0","filename":filename,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"stored":False,"settlement_verified":False,**result}

def app(environ, start_response):
    method,path=environ.get("REQUEST_METHOD","GET"),environ.get("PATH_INFO","/")
    if method=="GET" and path in {"/","/health","/healthz"}:
        return _response(start_response,"200 OK",{"ok":True,"service":"csv-json-quality-check","version":"0.1.0","max_content_bytes":MAX_CONTENT_BYTES,"stores_uploads":False,"performs_payments":False})
    if method!="POST" or path!="/v1/validate": return _response(start_response,"404 Not Found",{"error":"not_found"})
    client=(environ.get("HTTP_X_FORWARDED_FOR","").split(",")[0].strip() or environ.get("REMOTE_ADDR","unknown"))
    if _limited(client): return _response(start_response,"429 Too Many Requests",{"error":"rate_limited"})
    try: length=int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError: return _response(start_response,"400 Bad Request",{"error":"invalid_content_length"})
    if length<1 or length>MAX_BODY_BYTES: return _response(start_response,"413 Payload Too Large" if length>MAX_BODY_BYTES else "400 Bad Request",{"error":"body_size_out_of_range","max_body_bytes":MAX_BODY_BYTES})
    if "application/json" not in environ.get("CONTENT_TYPE","").lower(): return _response(start_response,"415 Unsupported Media Type",{"error":"content_type_must_be_application_json"})
    try: result=validate_payload(json.loads(environ["wsgi.input"].read(length).decode("utf-8")))
    except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as exc: return _response(start_response,"400 Bad Request",{"error":"invalid_request","message":str(exc)})
    except OverflowError as exc: return _response(start_response,"413 Payload Too Large",{"error":"content_too_large","message":str(exc)})
    return _response(start_response,"200 OK",result)

if __name__=="__main__":
    port=int(os.getenv("PORT","8080"))
    with make_server("0.0.0.0",port,app) as server:
        print(f"Development server listening on port {port}")
        server.serve_forever()
