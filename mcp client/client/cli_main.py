"""
Data Standardization & Preprocessing — Independent MCP Client Runner
Connects to the running MCP Server over Streamable HTTP transport.
Accepts natural-language commands interactively, discovers tools dynamically,
and displays human-readable results without calling tools unnecessarily.
"""
import sys
import os
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
for p in [_curr_dir, _parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from client.mcp_client import MCPClient, DEFAULT_SERVER_URL
except ImportError:
    from mcp_client import MCPClient, DEFAULT_SERVER_URL

import httpx

load_dotenv()
load_dotenv(os.path.join(_parent_dir, ".env"))


def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data as a clean, readable ASCII table."""
    if not rows:
        return "(No rows returned)"
    
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            str_val = str(val if val is not None else "")
            if len(str_val) > col_widths[idx]:
                col_widths[idx] = min(len(str_val), 40)

    # Format header
    sep = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    header_str = "| " + " | ".join([f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers))]) + " |"
    
    body_lines = []
    for row in rows:
        formatted_cells = []
        for i, val in enumerate(row):
            str_val = str(val if val is not None else "")
            if len(str_val) > 40:
                str_val = str_val[:37] + "..."
            formatted_cells.append(f"{str_val:<{col_widths[i]}}")
        body_lines.append("| " + " | ".join(formatted_cells) + " |")

    return "\n".join([sep, header_str, sep] + body_lines + [sep])


def display_tool_result(tool_name: str, result_data: Any):
    """Render tool results as human-readable tables or formatted summaries."""
    if isinstance(result_data, str):
        try:
            result_data = json.loads(result_data)
        except Exception:
            print(result_data)
            return

    if tool_name == "extract_data":
        records = result_data.get("records", [])
        total = result_data.get("total_count", len(records))
        query = result_data.get("query", "")
        print(f"\n[Result] Found {len(records)} record(s) (Total in query: {total}):")
        if query:
            print(f"Filter search: '{query}'")
        if records:
            headers = ["ID", "Customer Name", "Email", "Phone", "City", "Signup Date"]
            rows = [
                [r.get("id"), r.get("customer_name"), r.get("email"), r.get("phone_number"), r.get("city"), r.get("signup_date")]
                for r in records
            ]
            print(format_table(headers, rows))
        else:
            print("No matching customer records found.")

    elif tool_name == "check_data":
        print("\n" + "=" * 55)
        print("          DATABASE DATA QUALITY REPORT")
        print("=" * 55)
        score = result_data.get("data_quality_score", 100)
        print(f"  • Overall Quality Score : {score}%")
        print(f"  • Total Rows Inspected  : {result_data.get('total_records', 0)}")
        print(f"  • Duplicate Records     : {result_data.get('duplicate_records', 0)}")
        print(f"  • Invalid Emails        : {result_data.get('invalid_emails', 0)}")
        print(f"  • Invalid Phone Numbers : {result_data.get('invalid_phones', 0)}")
        print(f"  • Invalid Dates         : {result_data.get('invalid_dates', 0)}")
        print(f"  • Summary               : {result_data.get('summary', 'Audit complete')}")
        missing = result_data.get("missing_values", {})
        if missing:
            print("  • Missing Values Count  :")
            for col, cnt in missing.items():
                print(f"      - {col}: {cnt}")
        print("=" * 55)

    elif tool_name == "get_column":
        columns = result_data.get("columns", [])
        print(f"\n[Database Schema] Active Database Columns ({len(columns)}):")
        headers = ["Column Name", "Type", "Known Aliases", "Description"]
        rows = []
        for c in columns:
            aliases_str = ", ".join(c.get("aliases", [])[:4])
            if len(c.get("aliases", [])) > 4:
                aliases_str += "..."
            rows.append([c.get("column_name"), c.get("data_type"), aliases_str, c.get("description", "")])
        print(format_table(headers, rows))

    elif tool_name == "edit_data":
        status = result_data.get("status")
        if status == "needs_confirmation":
            print("\n" + result_data.get("readable_preview", "Confirm changes?"))
        elif status == "success":
            print("\n" + result_data.get("readable_output", result_data.get("message", "Updated successfully.")))
        else:
            print(f"\n[{status.upper()}] {result_data.get('message', 'No changes made.')}")

    elif tool_name == "add_row":
        status = result_data.get("status")
        msg = result_data.get("message", "")
        row = result_data.get("row", {})
        print(f"\n[{status.upper()}] {msg}")
        if row:
            print(f"  Added Row ID: {row.get('id')}")
            print(f"  Customer    : {row.get('customer_name')}")
            print(f"  Email       : {row.get('email')}")
            print(f"  Phone       : {row.get('phone_number')}")
            print(f"  City        : {row.get('city')}")
            print(f"  Signup Date : {row.get('signup_date')}")

    elif tool_name in ["delete_row", "delete_column", "delete_duplicates"]:
        status = result_data.get("status")
        msg = result_data.get("message", "Operation finished.")
        print(f"\n[{status.upper()}] {msg}")

    elif tool_name == "validate_data":
        val_rep = result_data.get("validation_report", {})
        print("\n" + "=" * 55)
        print("             VALIDATION RESULTS")
        print("=" * 55)
        print(f"  • Total Validated : {val_rep.get('total_records', 0)}")
        print(f"  • Valid Records   : {val_rep.get('valid_records', 0)}")
        print(f"  • Invalid Records : {val_rep.get('invalid_records', 0)}")
        print(f"  • Quality Score   : {val_rep.get('quality_score', 100)}%")
        issues = val_rep.get("issues", [])
        if issues:
            print(f"  • Issues Detected ({len(issues)}):")
            for iss in issues[:5]:
                print(f"      - Row {iss.get('row')}, [{iss.get('column')}]: {iss.get('error')}")
            if len(issues) > 5:
                print(f"      ... and {len(issues) - 5} more issues.")
        print("=" * 55)

    else:
        print(f"\n[Response] {json.dumps(result_data, indent=2)}")


async def resolve_intent_with_llm(user_input: str, discovered_tools: List[Any]) -> Dict[str, Any]:
    """
    Use OpenRouter LLM to interpret user natural-language commands
    and map them to discovered MCP tools without calling tools unnecessarily.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return resolve_intent_fallback(user_input)

    tools_desc = []
    for t in discovered_tools:
        schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", {})
        tools_desc.append({
            "name": t.name,
            "description": t.description,
            "parameters": schema
        })

    prompt = f"""You are the controller for a Data Standardization & Preprocessing MCP Client.
You have access ONLY to the following discovered MCP tools on the server:
{json.dumps(tools_desc, indent=2)}

User input: "{user_input}"

Instructions:
1. Determine whether this request requires invoking an MCP database tool.
2. If it is a greeting, general knowledge, explanation, or help request, set "tool_name": null and provide a helpful response in "message". DO NOT call any tool unnecessarily.
3. If it requires a database tool, set "tool_name" to the exact tool name and extract all required arguments in "arguments".
4. For destructive operations (delete_row, delete_column, edit_data, delete_duplicates), note whether confirmation is required.

Respond STRICTLY in JSON format:
{{
  "requires_tool": true/false,
  "tool_name": "exact_tool_name_or_null",
  "arguments": {{}},
  "message": "explanation or response to user"
}}
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8001",
        "X-Title": "MCP Interactive Client"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 800
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                return json.loads(content)
    except Exception as e:
        # Fallback to local rule-based intent resolver
        pass

    return resolve_intent_fallback(user_input)


def resolve_intent_fallback(user_input: str) -> Dict[str, Any]:
    """
    Deterministic rule-based intent parser when offline or without OpenRouter API key.
    Ensures tools are not called unnecessarily for conversational queries.
    """
    cmd = user_input.strip().lower()

    # 1. Non-tool queries (greetings, general chat, help)
    if cmd in ["hi", "hello", "hey", "who are you", "what are you", "what can you do"]:
        return {
            "requires_tool": False,
            "tool_name": None,
            "arguments": {},
            "message": "Hello! I am the independent MCP Client connected to the Data Standardization Server. I can query records, inspect schema, check data quality, or update rows."
        }
    if "help" in cmd:
        return {
            "requires_tool": False,
            "tool_name": None,
            "arguments": {},
            "message": "Available command examples:\n  • 'Show all records' or 'Find customers in Hyderabad'\n  • 'Check data quality'\n  • 'Show database columns'\n  • 'Change customer ID 15's city to Hyderabad'\n  • 'Delete row 20'\n  • 'tools' (inspect discovered MCP tools)"
        }

    # 2. Extract Data (Search/Show records)
    if any(k in cmd for k in ["show all", "list all", "all records", "get records", "show customers", "view customers", "extract"]):
        search_term = ""
        # Check for 'from <city>' or 'in <city>'
        m = re.search(r'(?:from|in|named)\s+([a-zA-Z0-9\s]+)', user_input, re.IGNORECASE)
        if m:
            search_term = m.group(1).strip()
        return {
            "requires_tool": True,
            "tool_name": "extract_data",
            "arguments": {"search": search_term, "limit": 50, "offset": 0},
            "message": f"Extracting customer records{f' matching {search_term}' if search_term else ''}..."
        }
    if any(k in cmd for k in ["find", "search", "lookup"]):
        # Extract search query
        clean = re.sub(r'^(find|search|lookup)\s+(customer|customers|records|for)?\s*', '', user_input, flags=re.IGNORECASE).strip()
        clean = re.sub(r'^(from|in|named)\s*', '', clean, flags=re.IGNORECASE).strip()
        return {
            "requires_tool": True,
            "tool_name": "extract_data",
            "arguments": {"search": clean, "limit": 50, "offset": 0},
            "message": f"Searching database for '{clean}'..."
        }

    # 3. Check Data (Quality, count, audit)
    if any(k in cmd for k in ["quality", "check data", "check quality", "audit", "health", "how many records", "count", "missing"]):
        return {
            "requires_tool": True,
            "tool_name": "check_data",
            "arguments": {"table_name": "customers"},
            "message": "Running database health & quality audit..."
        }

    # 4. Get Column (Schema, columns, fields)
    if any(k in cmd for k in ["columns", "schema", "fields", "data types", "get column"]):
        return {
            "requires_tool": True,
            "tool_name": "get_column",
            "arguments": {},
            "message": "Retrieving active database columns & schema metadata..."
        }

    # 5. Delete Row
    m_del_row = re.search(r'delete\s+(?:the\s+)?row\s+(?:id\s+)?(?:#)?(\d+)', user_input, re.IGNORECASE)
    if m_del_row:
        row_id = int(m_del_row.group(1))
        return {
            "requires_tool": True,
            "tool_name": "delete_row",
            "arguments": {"row_id": row_id, "confirm": False},
            "message": f"Requesting deletion of row #{row_id}."
        }

    # 6. Delete Column
    m_del_col = re.search(r'delete\s+(?:the\s+)?column\s+([a-zA-Z0-9_]+)', user_input, re.IGNORECASE)
    if m_del_col:
        col_name = m_del_col.group(1).strip()
        return {
            "requires_tool": True,
            "tool_name": "delete_column",
            "arguments": {"column_name": col_name, "confirm": False},
            "message": f"Requesting deletion of column '{col_name}'."
        }

    # 7. Delete Duplicates
    if "duplicate" in cmd and any(k in cmd for k in ["delete", "remove", "clean", "purge"]):
        return {
            "requires_tool": True,
            "tool_name": "delete_duplicates",
            "arguments": {"table_name": "customers", "confirm": False},
            "message": "Requesting duplicate purge."
        }

    # 8. Edit Data
    m_edit = re.search(r'(?:change|update|edit|set)\s+(?:customer\s+)?(?:id\s+)?(?:#)?(\d+)[^\w]+([a-zA-Z_]+)\s+(?:to|=)\s+([a-zA-Z0-9\s@\.\-]+)', user_input, re.IGNORECASE)
    if m_edit:
        row_id = int(m_edit.group(1))
        col_key = m_edit.group(2).strip().lower()
        new_val = m_edit.group(3).strip()
        # Map common names
        col_map = {"city": "city", "name": "customer_name", "customer": "customer_name", "phone": "phone_number", "email": "email", "date": "signup_date"}
        target_col = col_map.get(col_key, col_key)
        return {
            "requires_tool": True,
            "tool_name": "edit_data",
            "arguments": {"row_id": row_id, "updates": {target_col: new_val}, "confirm": False},
            "message": f"Preparing edit for Row #{row_id}: {target_col} = {new_val}"
        }

    # 9. Fallback if request is not understood
    return {
        "requires_tool": False,
        "tool_name": None,
        "arguments": {},
        "message": f"I couldn't map '{user_input}' to a specific database tool.\nType 'help' for examples or 'tools' to see available MCP tools."
    }


async def run_interactive_client(server_url: str = DEFAULT_SERVER_URL):
    """Main interactive terminal loop for the independent MCP Client."""
    client = MCPClient(server_url=server_url)

    print("\n" + "=" * 70)
    print("  Data Standardization & Preprocessing — MCP Interactive Client")
    print("=" * 70)
    print(f"  Target Server Endpoint : {server_url} (Streamable HTTP)")
    print("  Database Access Mode   : Exclusively via MCP Server (No direct SQL)")
    print("=" * 70)
    print("Connecting to MCP Server and discovering tools...")

    try:
        discovered_tools = await client.list_tools()
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"  [ERROR] Connection Failed: Could not reach MCP Server")
        print("=" * 70)
        print(f"  Endpoint attempted: {server_url}")
        print("  Please start the server first in another terminal:")
        print("    venv\\Scripts\\python.exe run_server.py\n")
        print(f"  Details: {str(e)}")
        print("=" * 70)
        return

    print(f"\n[Success] Connected! Discovered {len(discovered_tools)} MCP tools from server:")
    for t in discovered_tools:
        first_line_desc = t.description.strip().split("\n")[0] if t.description else "No description"
        print(f"  • {t.name:<18} : {first_line_desc}")

    print("\nCommands:")
    print("  • Type natural language queries (e.g. 'Show all records', 'Find customers in Mumbai')")
    print("  • 'tools' : Display full schemas of discovered tools")
    print("  • 'help'  : Show example queries")
    print("  • 'exit'  : Quit the client session")
    print("=" * 70 + "\n")

    while True:
        try:
            user_input = input("MCP Client> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting MCP Client session.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Session terminated. Goodbye!")
            break

        if user_input.lower() in ["help", "?"]:
            print("\nAvailable command examples:")
            print("  • 'Show all records' or 'Find customers in Hyderabad'")
            print("  • 'Check data quality' (audits nulls, duplicates, invalid formats)")
            print("  • 'Show database columns' (view schema)")
            print("  • 'Change customer ID 15 city to Hyderabad'")
            print("  • 'Delete row 20' (prompts confirmation)")
            print("  • 'tools' (inspect schema of all discovered MCP tools)")
            print("  • 'exit' to quit\n")
            continue

        if user_input.lower() in ["tools", "list-tools"]:
            print(f"\nDiscovered Tools on {server_url}:")
            for t in discovered_tools:
                schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", {})
                print(f"\n--- Tool: {t.name} ---")
                print(f"Description: {t.description}")
                print(f"Parameters : {json.dumps(schema, indent=2)}")
            continue

        # Resolve intent
        intent = await resolve_intent_with_llm(user_input, discovered_tools)

        if not intent.get("requires_tool") or not intent.get("tool_name"):
            print(f"\n{intent.get('message', 'No tool required for this input.')}\n")
            continue

        tool_name = intent.get("tool_name")
        arguments = intent.get("arguments", {})

        # Verify tool is valid
        valid_tool_names = [t.name for t in discovered_tools]
        if tool_name not in valid_tool_names:
            print(f"\n[Warning] Tool '{tool_name}' was not discovered on the server.\nAvailable tools: {valid_tool_names}\n")
            continue

        # Handle two-phase confirmation for destructive actions in CLI
        if tool_name in ["delete_row", "delete_column", "delete_duplicates", "edit_data"]:
            if not arguments.get("confirm"):
                # Pre-run or ask confirmation
                if tool_name == "delete_row":
                    row_id = arguments.get("row_id")
                    confirm = input(f"Confirm deleting Row #{row_id}? [y/N]: ").strip().lower()
                    if confirm not in ["y", "yes"]:
                        print("Operation cancelled. No rows deleted.\n")
                        continue
                    arguments["confirm"] = True

                elif tool_name == "delete_column":
                    col_name = arguments.get("column_name")
                    confirm = input(f"Confirm deleting Column '{col_name}'? [y/N]: ").strip().lower()
                    if confirm not in ["y", "yes"]:
                        print("Operation cancelled. No columns deleted.\n")
                        continue
                    arguments["confirm"] = True

                elif tool_name == "delete_duplicates":
                    confirm = input(f"Confirm purging all duplicate records? [y/N]: ").strip().lower()
                    if confirm not in ["y", "yes"]:
                        print("Operation cancelled.\n")
                        continue
                    arguments["confirm"] = True

                elif tool_name == "edit_data":
                    # First call with confirm=False to retrieve diff preview
                    try:
                        raw_preview = await client.call_tool("edit_data", arguments)
                        preview_data = json.loads(raw_preview)
                        if preview_data.get("status") == "needs_confirmation":
                            print("\n" + preview_data.get("readable_preview", ""))
                            confirm = input("\nConfirm these changes? [y/N]: ").strip().lower()
                            if confirm not in ["y", "yes"]:
                                print("Update cancelled. Database remains unchanged.\n")
                                continue
                            arguments["confirm"] = True
                        else:
                            display_tool_result("edit_data", preview_data)
                            continue
                    except Exception as err:
                        print(f"\n[Error] {str(err)}\n")
                        continue

        # Execute tool over Streamable HTTP
        print(f"\n[Executing MCP Tool: {tool_name} with arguments {arguments}]...")
        try:
            raw_result = await client.call_tool(tool_name, arguments)
            display_tool_result(tool_name, raw_result)
        except Exception as e:
            print(f"\n[Tool Execution Error] {str(e)}")

        print()


def main():
    server_url = DEFAULT_SERVER_URL
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        server_url = sys.argv[1]
    asyncio.run(run_interactive_client(server_url=server_url))


if __name__ == "__main__":
    main()
