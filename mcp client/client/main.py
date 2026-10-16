"""
Data Standardization & Preprocessing System — Web Application
Connects exclusively through the MCP Client to the independent MCP Server.
Does NOT import server implementation modules, connect to SQLite, or run database operations.
"""
import os
import sys
import base64
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
for p in [_curr_dir, _parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from client.mcp_client import mcp_client
    from client.ai_assistant import process_assistant_message
except ImportError:
    from mcp_client import mcp_client
    from ai_assistant import process_assistant_message

load_dotenv()
load_dotenv(os.path.join(_parent_dir, ".env"))

app = FastAPI(title="MCP Data Standardization System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_for_json(data):
    """Recursively sanitize data structures for clean JSON serialization."""
    import math
    if data is None:
        return None
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_json(item) for item in data]
    return data


# ---------------------------------------------------------
# Global Offline Error Handler for MCP Protocol Calls
# ---------------------------------------------------------
@app.exception_handler(ConnectionError)
async def mcp_connection_error_handler(request: Request, exc: ConnectionError):
    """
    If the MCP server is not running, prevent tool execution and notify user.
    """
    return JSONResponse(
        status_code=503,
        content={
            "status": "error",
            "error_type": "SERVER_OFFLINE",
            "message": "MCP Server is offline (http://127.0.0.1:8001/mcp). Tools cannot be executed.",
            "detail": str(exc),
            "instructions": "Please start the MCP server separately in another terminal: venv\\Scripts\\python.exe backend/server/mcp_server.py"
        }
    )


# ---------------------------------------------------------
# MODULE 1: File Upload & Data Import via MCP Tool
# ---------------------------------------------------------

# In-memory session cache for uploaded files (between upload preview & user ingestion confirmation)
_file_session_cache: Dict[int, Dict[str, Any]] = {}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts CSV or Excel upload, encodes content, and transfers to MCP Server
    via MCP tool 'upload_classify_standardize' for classification & preview (dry run).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a CSV or Excel (.xlsx/.xls) file."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    b64_content = base64.b64encode(content).decode("utf-8")

    # Initiate classification on MCP server via MCP Client tool call
    res = await mcp_client.upload_classify_standardize(
        filename=file.filename,
        file_content_base64=b64_content,
        proceed_with_insert=False
    )

    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "File inspection failed on MCP server."))

    file_id = res.get("file_id") or (abs(hash(file.filename + str(len(content)))) % 10000000)

    # Store file context in memory for subsequent user confirmation
    _file_session_cache[file_id] = {
        "filename": file.filename,
        "base64": b64_content,
        "classification": res.get("classification") or res.get("mapping_decisions", []),
        "preview_rows": res.get("preview_rows", []),
        "columns": res.get("columns", []),
        "total_rows": res.get("total_rows", 0),
        "format": res.get("format", ext.lstrip(".")),
        "target_columns": res.get("target_columns", []),
        "requires_user_action": res.get("requires_user_action", False)
    }

    return sanitize_for_json({
        "status": "success",
        "file_id": file_id,
        "filename": file.filename,
        "format": res.get("format", ext.lstrip(".")),
        "filepath": "",
        "columns": res.get("columns", []),
        "total_rows": res.get("total_rows", 0),
        "preview_rows": res.get("preview_rows", [])
    })


class ClassifyRequest(BaseModel):
    file_id: int
    filepath: Optional[str] = ""
    format: Optional[str] = ""


@app.post("/api/classify_columns")
async def classify_columns(req: ClassifyRequest):
    """
    Returns column classification results.
    Uses Client-side LLM column mapping if classification is not yet computed.
    """
    cached = _file_session_cache.get(req.file_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="File upload session expired or not found. Please upload your file again."
        )

    classification = cached.get("classification", [])
    if not classification and cached.get("columns"):
        preview_rows = cached.get("preview_rows", [])
        sample_dict = {}
        for col in cached.get("columns", []):
            sample_dict[col] = [row.get(col) for row in preview_rows if col in row]
        classification = await mcp_client.classify_columns(cached.get("columns", []), sample_data=sample_dict)
        cached["classification"] = classification

    return sanitize_for_json({
        "status": "success",
        "file_id": req.file_id,
        "classification": classification,
        "requires_user_action": cached.get("requires_user_action", False) or any(c.get("confidence", 1.0) < 0.90 for c in classification),
        "target_columns": cached.get("target_columns", [])
    })


class ColumnClassifyRequest(BaseModel):
    columns: List[str]
    sample_data: Optional[Dict[str, List[Any]]] = {}


@app.post("/api/mcp/classify_columns")
async def api_mcp_classify_columns(req: ColumnClassifyRequest):
    """Client-side LLM Column Mapper: maps input columns to canonical schema via Client LLM."""
    mappings = await mcp_client.classify_columns(req.columns, sample_data=req.sample_data or {})
    return {"status": "success", "mappings": mappings}


class ColumnMappingItem(BaseModel):
    input_column: str
    standardized_column: str
    confidence: Optional[float] = 1.0
    method: Optional[str] = ""


class StoreRequest(BaseModel):
    file_id: int
    filepath: Optional[str] = ""
    format: Optional[str] = ""
    mappings: List[ColumnMappingItem]


@app.post("/api/standardize_and_store")
async def standardize_and_store(req: StoreRequest):
    """
    Standardize and store records:
    Sends confirmed user column mappings and base64 content to the MCP server tool
    'upload_classify_standardize' with proceed_with_insert=True.
    The server standardizes data, validates records, and ingests them into SQLite.
    """
    cached = _file_session_cache.get(req.file_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="File upload session expired or not found. Please upload your file again."
        )

    # Build confirmed mappings dictionary
    confirmed_mappings = {m.input_column: m.standardized_column for m in req.mappings}

    # Call MCP Server tool via MCP Client to ingest into SQLite
    res = await mcp_client.upload_classify_standardize(
        filename=cached["filename"],
        file_content_base64=cached["base64"],
        confirmed_mappings=confirmed_mappings,
        proceed_with_insert=True
    )

    if res.get("status") == "error":
        raise HTTPException(
            status_code=400,
            detail=res.get("message", "Standardization and storage failed on MCP server.")
        )

    inserted_count = res.get("inserted_count", 0)
    return sanitize_for_json({
        "status": "success",
        "message": res.get("message", f"Successfully standardized and stored {inserted_count} records into the SQLite database."),
        "inserted_count": inserted_count,
        "validation_report": res.get("validation_report") or res.get("validation_summary", {})
    })


# ---------------------------------------------------------
# MODULE 2: Direct Database Tools Panel (FastAPI -> MCP Client -> MCP Server)
# Directly invoked without LLM.
# ---------------------------------------------------------

@app.get("/api/mcp/get_columns")
async def api_mcp_get_columns():
    """MCP Tool: get_column — directly called without LLM."""
    res = await mcp_client.get_column()
    return res


@app.get("/api/mcp/check_data")
async def api_mcp_check_data(table: str = "customers"):
    """MCP Tool: check_data — directly called without LLM."""
    res = await mcp_client.check_data(table_name=table)
    return res


@app.get("/api/mcp/extract_data")
async def api_mcp_extract_data(search: str = "", limit: int = 1000, offset: int = 0):
    """MCP Tool: extract_data — directly called without LLM."""
    res = await mcp_client.extract_data(search=search, limit=limit, offset=offset)
    return sanitize_for_json(res)


class ValidateRequest(BaseModel):
    records: List[Dict[str, Any]]


@app.post("/api/mcp/validate_data")
async def api_mcp_validate_data(req: ValidateRequest):
    """MCP Tool: validate_data — directly called without LLM."""
    res = await mcp_client.validate_data(req.records)
    return res


class StandardizeValuesRequest(BaseModel):
    record: Optional[Dict[str, Any]] = None
    records: Optional[List[Dict[str, Any]]] = None
    use_llm: bool = True


@app.post("/api/mcp/standardize_values")
async def api_mcp_standardize_values(req: StandardizeValuesRequest):
    """Client-side AI value standardization endpoint (cleans cities, names, dates, phones)."""
    if req.record:
        cleaned = await mcp_client.standardize_record(req.record, use_llm=req.use_llm)
        return {"status": "success", "standardized_record": cleaned, "original_record": req.record}
    elif req.records:
        cleaned_list = await mcp_client.standardize_batch(req.records, use_llm=req.use_llm)
        return {"status": "success", "standardized_records": cleaned_list, "count": len(cleaned_list)}
    else:
        raise HTTPException(status_code=400, detail="Must provide either 'record' or 'records'")


class AddRowRequest(BaseModel):
    row: Dict[str, Any]
    confirm_mappings: Optional[Dict[str, str]] = {}


@app.post("/api/mcp/add_row")
async def api_mcp_add_row(req: AddRowRequest):
    """MCP Tool: add_row — directly called without LLM."""
    res = await mcp_client.add_row(req.row, req.confirm_mappings)
    return res


class DeleteRowRequest(BaseModel):
    row_id: int
    confirm: bool = False


@app.post("/api/mcp/delete_row")
async def api_mcp_delete_row(req: DeleteRowRequest):
    """MCP Tool: delete_row — directly called without LLM."""
    res = await mcp_client.delete_row(req.row_id, req.confirm)
    return res


class DeleteColumnRequest(BaseModel):
    column_name: str
    confirm: bool = False


@app.post("/api/mcp/delete_column")
async def api_mcp_delete_column(req: DeleteColumnRequest):
    """MCP Tool: delete_column — directly called without LLM."""
    res = await mcp_client.delete_column(req.column_name, req.confirm)
    return res


class DeleteDuplicatesRequest(BaseModel):
    table: str = "customers"
    confirm: bool = False


@app.post("/api/mcp/delete_duplicates")
async def api_mcp_delete_duplicates(req: DeleteDuplicatesRequest):
    """MCP Tool: delete_duplicates — directly called without LLM."""
    res = await mcp_client.delete_duplicates(table_name=req.table, confirm=req.confirm)
    return res


class EditDataRequest(BaseModel):
    row_id: Optional[int] = None
    customer_name: Optional[str] = None
    updates: Optional[Dict[str, Any]] = None
    confirm: bool = False


@app.post("/api/mcp/edit_data")
async def api_mcp_edit_data(req: EditDataRequest):
    """MCP Tool: edit_data — directly called without LLM."""
    res = await mcp_client.edit_data(
        row_id=req.row_id,
        customer_name=req.customer_name,
        updates=req.updates,
        confirm=req.confirm
    )
    return res


@app.get("/api/mcp/search_customers")
async def api_mcp_search_customers(name: str = Query(...)):
    """Search database based on customer name using edit_data tool — directly called without LLM."""
    res = await mcp_client.search_customers(customer_name=name)
    return res


@app.get("/api/mcp/get_row")
async def api_mcp_get_row(row_id: int = Query(...)):
    """Fetch row by ID via MCP tool get_row — directly called without LLM."""
    res = await mcp_client.get_row(row_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message", f"Row with ID {row_id} does not exist."))
    return res


class MCPUploadRequest(BaseModel):
    filename: str
    file_content_base64: str = ""
    file_content_text: str = ""
    confirmed_mappings: Optional[Dict[str, str]] = {}
    proceed_with_insert: bool = False


@app.post("/api/mcp/upload_classify_standardize")
async def api_mcp_upload_classify_standardize(req: MCPUploadRequest):
    """MCP Tool: upload_classify_standardize — directly called without LLM."""
    res = await mcp_client.upload_classify_standardize(
        filename=req.filename,
        file_content_base64=req.file_content_base64,
        file_content_text=req.file_content_text,
        confirmed_mappings=req.confirmed_mappings,
        proceed_with_insert=req.proceed_with_insert
    )
    return res


# ---------------------------------------------------------
# MODULE 3: Database View Endpoint (MCP Client -> MCP Server)
# ---------------------------------------------------------

@app.get("/api/database/view")
async def view_database(search: str = "", limit: int = 1000, offset: int = 0):
    """Retrieve full standardized database records with schema via MCP tools."""
    res = await mcp_client.extract_data(search=search, limit=limit, offset=offset)
    col_res = await mcp_client.get_column()
    return sanitize_for_json({
        "status": "success",
        "data": res,
        "schema": col_res
    })


# ---------------------------------------------------------
# MODULE 4: AI Assistant Query Endpoint (UI -> Client -> Server)
# ---------------------------------------------------------

class AIChatRequest(BaseModel):
    message: Optional[str] = ""
    conversation_history: Optional[List[Dict[str, Any]]] = []
    confirmed_action: Optional[Dict[str, Any]] = None


@app.post("/api/ai/chat")
async def api_ai_chat(req: AIChatRequest):
    """
    AI Assistant Endpoint:
    UI asks the client, and the client generates the response by contacting the MCP Server.
    The LLM selects the MCP tool, and the client executes it via the MCP protocol.
    """
    if not req.message and not req.confirmed_action:
        raise HTTPException(status_code=400, detail="Message or confirmed_action is required")

    res = await process_assistant_message(
        user_message=req.message or "",
        conversation_history=req.conversation_history or [],
        confirmed_action=req.confirmed_action
    )
    return res


# Mount frontend static files at root
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if not os.path.exists(_frontend_dir):
    _frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if not os.path.exists(_frontend_dir):
    _frontend_dir = "frontend"

app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    if "--web" in sys.argv:
        import uvicorn
        print("\n=======================================================")
        print("  MCP Client Web Application & API")
        print("  Connects to MCP Server at: http://127.0.0.1:8001/mcp")
        print("  Open in browser: http://127.0.0.1:8000")
        print("=======================================================\n")
        uvicorn.run("client.main:app" if os.path.exists("client") else "main:app", host="127.0.0.1", port=8000, reload=False)
    else:
        import asyncio
        try:
            from client.cli_main import run_interactive_client, DEFAULT_SERVER_URL
        except ImportError:
            from cli_main import run_interactive_client, DEFAULT_SERVER_URL

        server_url = DEFAULT_SERVER_URL
        for arg in sys.argv[1:]:
            if arg.startswith("http"):
                server_url = arg
        asyncio.run(run_interactive_client(server_url=server_url))
