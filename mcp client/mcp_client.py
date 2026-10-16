"""
Data Standardization & Preprocessing — Independent MCP Client
Connects to the running MCP Server over Streamable HTTP transport.
Does NOT import sqlite3 or database code. Exclusively uses MCP protocol messages.
"""
import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
for p in [_curr_dir, _parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import json
import asyncio
import re
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
import httpx

load_dotenv()
load_dotenv(os.path.join(_parent_dir, ".env"))

DEFAULT_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")

COMMON_CITY_MAP = {
    "hyd": "Hyderabad",
    "hyderabad": "Hyderabad",
    "secunderabad": "Hyderabad",
    "cyberabad": "Hyderabad",
    "blr": "Bengaluru",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bom": "Mumbai",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "del": "Delhi",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "ncr": "Delhi",
    "maa": "Chennai",
    "madras": "Chennai",
    "chennai": "Chennai",
    "ccu": "Kolkata",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad",
    "amd": "Ahmedabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "nyc": "New York",
    "new york": "New York",
    "la": "Los Angeles",
    "los angeles": "Los Angeles",
    "sf": "San Francisco",
    "san francisco": "San Francisco",
    "chicago": "Chicago",
    "london": "London",
}


def clean_record_locally(record: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback deterministic standardizer if offline or without LLM API key."""
    cleaned = dict(record)

    # 1. Customer Name: strip honorifics and title-case
    if "customer_name" in cleaned and cleaned["customer_name"] is not None:
        name = str(cleaned["customer_name"]).strip()
        name = re.sub(r'^(mr\.|ms\.|mrs\.|dr\.|prof\.)\s*', '', name, flags=re.IGNORECASE)
        cleaned["customer_name"] = name.strip().title()

    # 2. City: lookup abbreviation map
    if "city" in cleaned and cleaned["city"] is not None:
        city_raw = str(cleaned["city"]).strip().lower()
        cleaned["city"] = COMMON_CITY_MAP.get(city_raw, str(cleaned["city"]).strip().title())

    # 3. Phone: strip non-digits
    if "phone_number" in cleaned and cleaned["phone_number"] is not None:
        digits = re.sub(r'\D', '', str(cleaned["phone_number"]))
        cleaned["phone_number"] = digits if digits else None

    # 4. Email: trim and lowercase
    if "email" in cleaned and cleaned["email"] is not None:
        cleaned["email"] = str(cleaned["email"]).strip().lower()

    # 5. Date: standard YYYY-MM-DD
    if "signup_date" in cleaned and cleaned["signup_date"] is not None:
        val = str(cleaned["signup_date"]).strip()
        m = re.search(r'(\d{4})[\-\/\.](\d{1,2})[\-\/\.](\d{1,2})', val)
        if m:
            cleaned["signup_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        else:
            m2 = re.search(r'(\d{1,2})[\-\/\.](\d{1,2})[\-\/\.](\d{4})', val)
            if m2:
                cleaned["signup_date"] = f"{m2.group(3)}-{int(m2.group(2)):02d}-{int(m2.group(1)):02d}"

    return cleaned


async def standardize_record_with_llm(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize a single record's values using OpenRouter LLM (Gemini 2.5).
    Cleans city abbreviations, names, phone numbers, and dates.
    Falls back gracefully to local deterministic cleaning.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return clean_record_locally(record)

    prompt = f"""You are an expert data standardization engine.
Given the following customer record, standardize the values strictly according to canonical rules:
1. 'customer_name': Title Case. Remove prefixes (Mr., Ms., Dr., Prof.) and suffixes.
2. 'city': Standard full canonical city name (e.g. 'HYD' -> 'Hyderabad', 'BLR'/'Bangalore' -> 'Bengaluru', 'Bombay' -> 'Mumbai', 'Calcutta' -> 'Kolkata', 'Madras' -> 'Chennai', 'NCR' -> 'Delhi', 'NYC' -> 'New York').
3. 'phone_number': Extract digits only (7 to 15 digits).
4. 'signup_date': Strict ISO-8601 YYYY-MM-DD format. If missing/invalid, return null.
5. 'email': Lowercase, stripped.

Input Record:
{json.dumps(record, indent=2)}

Respond ONLY in valid JSON matching the input keys:
{{
  "customer_name": "...",
  "email": "...",
  "phone_number": "...",
  "city": "...",
  "signup_date": "..."
}}
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "MCP Client Data Standardizer"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                parsed = json.loads(content)
                merged = dict(record)
                for k, v in parsed.items():
                    if v is not None:
                        merged[k] = v
                return merged
    except Exception:
        pass

async def classify_column_with_llm(
    input_col: str,
    sample_values: list = None,
    standard_columns: list = None
) -> Dict[str, Any]:
    """
    Client-side LLM Column Mapper:
    Maps an arbitrary input column header to the canonical database schema using OpenRouter LLM (Gemini 2.5).
    """
    if sample_values is None:
        sample_values = []
    if standard_columns is None:
        standard_columns = []

    # Rule 1: First check fast client-side exact/alias match
    norm_input = re.sub(r'[_\-\.\/]+', ' ', input_col.lower().strip())
    norm_input = re.sub(r'[^a-z0-9\s]', '', norm_input).strip()
    col_input = re.sub(r'[^a-z0-9]', '', input_col.lower())

    for col in standard_columns:
        cname = col.get("column_name", "")
        cname_norm = re.sub(r'[_\-\.\/]+', ' ', cname.lower().strip())
        cname_col = re.sub(r'[^a-z0-9]', '', cname.lower())
        if norm_input == cname_norm or col_input == cname_col:
            return {
                "input_column": input_col,
                "standardized_column": cname,
                "confidence": 1.0,
                "method": "client_exact_match",
                "reasoning": f"Exact match with canonical column '{cname}'",
                "auto_accepted": True
            }
        for alias in col.get("aliases", []):
            alias_norm = re.sub(r'[_\-\.\/]+', ' ', alias.lower().strip())
            alias_col = re.sub(r'[^a-z0-9]', '', alias.lower())
            if norm_input == alias_norm or col_input == alias_col:
                return {
                    "input_column": input_col,
                    "standardized_column": cname,
                    "confidence": 0.96,
                    "method": "client_alias_match",
                    "reasoning": f"Matched standard alias '{alias}' for '{cname}'",
                    "auto_accepted": True
                }

    # Rule 2: LLM Classification with Gemini 2.5 on Client Side
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return {
            "input_column": input_col,
            "standardized_column": "none",
            "confidence": 0.0,
            "method": "offline_fallback",
            "reasoning": "Offline mode (No OpenRouter API key found)",
            "auto_accepted": False
        }

    schema_info = []
    for col in standard_columns:
        cname = col.get("column_name", "")
        desc = col.get("description", "")
        aliases = col.get("aliases", [])
        dtype = col.get("data_type", "TEXT")
        schema_info.append(f"- '{cname}' ({dtype}): {desc}. Known aliases: {aliases[:8]}")
    schema_text = "\n".join(schema_info)

    clean_samples = [str(s) for s in sample_values if s is not None and str(s).strip() != ""][:5]

    prompt = f"""You are a database data standardization expert.
We have a target canonical database schema with these columns:
{schema_text}

An uploaded dataset contains an input column named: '{input_col}'
Sample row values in this column: {clean_samples}

Task:
Determine which target canonical database column this input column maps to, or 'none' if it does not fit any.
Calculate your confidence score between 0.00 and 1.00 (e.g. 0.95 for confident match, 0.60 for ambiguous match).

Respond strictly in valid JSON format:
{{
  "matched_column": "target_column_name_or_none",
  "confidence": 0.95,
  "reasoning": "brief explanation"
}}
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "MCP Client Column Mapper"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 400
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                parsed = json.loads(content)
                matched = parsed.get("matched_column", "none")
                conf = float(parsed.get("confidence", 0.0))
                reasoning = parsed.get("reasoning", "Client LLM classification")

                valid_cols = [c.get("column_name") for c in standard_columns] + ["none"]
                if matched not in valid_cols:
                    matched = "none"

                return {
                    "input_column": input_col,
                    "standardized_column": matched,
                    "confidence": conf,
                    "method": "client_llm_classification",
                    "reasoning": reasoning,
                    "auto_accepted": conf >= 0.90
                }
    except Exception:
        pass

    return {
        "input_column": input_col,
        "standardized_column": "none",
        "confidence": 0.20,
        "method": "unmatched",
        "reasoning": "No confident match found",
        "auto_accepted": False
    }


class MCPClient:
    """
    Independent MCP Client connecting to the Data Standardization MCP Server
    via Streamable HTTP transport.
    Exclusively communicates via MCP protocol messages; no direct database access.
    """

    def __init__(self, server_url: str = DEFAULT_SERVER_URL):
        self.server_url = server_url

    @asynccontextmanager
    async def get_session(self):
        """Establish a Streamable HTTP MCP session with the server."""
        try:
            timeout = httpx.Timeout(60.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as http_client:
                async with streamable_http_client(self.server_url, http_client=http_client) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        yield session
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to MCP Server at {self.server_url}.\n"
                f"Please ensure the server is running in another terminal:\n"
                f"  venv\\Scripts\\python.exe server/mcp_server.py\n"
                f"Details: {str(e)}"
            )

    async def list_tools(self) -> List[Any]:
        """Discover all available tools dynamically through the MCP server."""
        async with self.get_session() as session:
            tools_resp = await session.list_tools()
            return tools_resp.tools

    async def call_tool(self, name: str, arguments: dict = None) -> str:
        """Call any tool by name with arguments over Streamable HTTP."""
        if arguments is None:
            arguments = {}
        async with self.get_session() as session:
            result = await session.call_tool(name, arguments)
            if result.content:
                return result.content[0].text
            return "{}"

    # -------------------------------------------------------------
    # Typed Tool Methods
    # -------------------------------------------------------------

    async def get_column(self) -> dict:
        """MCP Tool: get_column"""
        raw = await self.call_tool("get_column", {})
        return json.loads(raw)

    async def check_data(self, table_name: str = "customers") -> dict:
        """MCP Tool: check_data"""
        raw = await self.call_tool("check_data", {"table_name": table_name})
        return json.loads(raw)

    async def extract_data(self, search: str = "", limit: int = 1000, offset: int = 0) -> dict:
        """MCP Tool: extract_data"""
        raw = await self.call_tool("extract_data", {"search": search, "limit": limit, "offset": offset})
        return json.loads(raw)

    async def validate_data(self, records: list) -> dict:
        """MCP Tool: validate_data"""
        raw = await self.call_tool("validate_data", {"records_json": json.dumps(records)})
        return json.loads(raw)

    async def classify_columns(self, input_columns: List[str], sample_data: Dict[str, list] = None) -> List[Dict[str, Any]]:
        """
        Client-Side Column Mapper:
        Queries canonical schema from the MCP Server, then uses the Client LLM to classify columns.
        """
        if sample_data is None:
            sample_data = {}

        schema_resp = await self.get_column()
        standard_columns = schema_resp.get("columns", [])

        tasks = [
            classify_column_with_llm(col, sample_data.get(col, []), standard_columns)
            for col in input_columns
        ]
        return await asyncio.gather(*tasks)

    async def standardize_record(self, record: dict, use_llm: bool = True) -> dict:
        """Standardize a single record's values using Client-side LLM (or fallback rules)."""
        if use_llm:
            return await standardize_record_with_llm(record)
        return clean_record_locally(record)

    async def standardize_batch(self, records: list, use_llm: bool = True) -> list:
        """Standardize a list of records concurrently using Client-side LLM."""
        if not records:
            return []
        tasks = [self.standardize_record(r, use_llm=use_llm) for r in records]
        return await asyncio.gather(*tasks)

    async def add_row(self, row: dict, confirm_mappings: dict = None, standardize_values: bool = True) -> dict:
        """MCP Tool: add_row with Client-side LLM value standardization."""
        if standardize_values and isinstance(row, dict):
            row = await self.standardize_record(row)
        raw = await self.call_tool("add_row", {
            "row_json": json.dumps(row),
            "confirm_mappings": json.dumps(confirm_mappings or {})
        })
        return json.loads(raw)

    async def delete_row(self, row_id: int, confirm: bool = False) -> dict:
        """MCP Tool: delete_row"""
        raw = await self.call_tool("delete_row", {"row_id": int(row_id), "confirm": confirm})
        return json.loads(raw)

    async def delete_column(self, column_name: str, confirm: bool = False) -> dict:
        """MCP Tool: delete_column"""
        raw = await self.call_tool("delete_column", {"column_name": column_name, "confirm": confirm})
        return json.loads(raw)

    async def delete_duplicates(self, table_name: str = "customers", confirm: bool = False) -> dict:
        """MCP Tool: delete_duplicates"""
        raw = await self.call_tool("delete_duplicates", {"table_name": table_name, "confirm": confirm})
        return json.loads(raw)

    async def edit_data(self, row_id: int = None, customer_name: str = None, updates: dict = None, confirm: bool = False, standardize_values: bool = True) -> dict:
        """MCP Tool: edit_data with Client-side LLM value standardization."""
        args = {"confirm": confirm}
        if row_id is not None:
            args["row_id"] = int(row_id)
        if customer_name is not None:
            args["customer_name"] = str(customer_name)
        if updates is not None:
            if isinstance(updates, dict) and standardize_values:
                updates = await self.standardize_record(updates)
            args["updates_json"] = json.dumps(updates) if isinstance(updates, dict) else str(updates)
        raw = await self.call_tool("edit_data", args)
        return json.loads(raw)

    async def search_customers(self, customer_name: str) -> dict:
        """Search database based on customer name using edit_data tool."""
        return await self.edit_data(customer_name=customer_name)

    async def get_row(self, row_id: int) -> dict:
        """Fetch row by ID using get_row tool."""
        raw = await self.call_tool("get_row", {"row_id": int(row_id)})
        return json.loads(raw)

    async def batch_insert(self, records: list, standardize_values: bool = True) -> dict:
        """MCP Tool: batch_insert with Client-side LLM value standardization."""
        if standardize_values and isinstance(records, list):
            records = await self.standardize_batch(records)
        raw = await self.call_tool("batch_insert", {"records_json": json.dumps(records)})
        return json.loads(raw)

    async def upload_classify_standardize(
        self,
        filename: str,
        file_content_base64: str = "",
        file_content_text: str = "",
        confirmed_mappings: dict = None,
        proceed_with_insert: bool = False
    ) -> dict:
        """
        MCP Tool: upload_classify_standardize
        Executes end-to-end upload, classification, validation, and storage on the MCP server.
        """
        args = {
            "filename": filename,
            "file_content_base64": file_content_base64,
            "file_content_text": file_content_text,
            "confirmed_mappings_json": json.dumps(confirmed_mappings or {}),
            "proceed_with_insert": proceed_with_insert
        }
        raw = await self.call_tool("upload_classify_standardize", args)
        return json.loads(raw)


mcp_client = MCPClient()


if __name__ == "__main__":
    try:
        from client.cli_main import run_interactive_client
    except ImportError:
        from cli_main import run_interactive_client

    server_url = DEFAULT_SERVER_URL
    for arg in sys.argv[1:]:
        if arg.startswith("http"):
            server_url = arg
    asyncio.run(run_interactive_client(server_url=server_url))
