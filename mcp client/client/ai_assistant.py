import os
import json
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .mcp_client import mcp_client

def sanitize_for_json(data):
    """Recursively sanitize data structures for JSON serialization."""
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

# Ensure .env is loaded
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.5-flash"

SYSTEM_PROMPT = """You are the AI Assistant for the MCP Data Standardization and Database Engine.
Your job is to understand user requests in natural language and select the appropriate Model Context Protocol (MCP) tool to inspect, query, or safely modify the database.

Available MCP Tools:
1. `extract_data(search: string, limit: integer)`:
   - Use for querying, listing, searching, or filtering records in the database.
   - Example requests: "Show me all records", "Find customers from Hyderabad", "How many records are in the database?", "List customers", "show whole records".
   - When the user asks for all records, whole records, entire table, or general listing without specifying a small limit, ALWAYS pass `limit=0` or `limit=1000` to retrieve the entire dataset. Never limit to 50 unless the user specifically asked for 50.
   - If user asks for count, use extract_data with limit=1 to get total_count.
   - If user searches for a specific city/name/email/term, pass `search`.

2. `check_data(table_name: string = "customers")`:
   - Inspect data quality, missing values, duplicates, and invalid email/phone/date formats.
   - Example requests: "Check for missing email addresses", "Check data quality", "How many duplicates?", "Scan database health".

3. `get_column()`:
   - Retrieve available database schema, column names, data types, aliases, and descriptions.
   - Example requests: "Show me the available database columns", "What columns do we have?", "What is the schema?".

4. `validate_data(records: list)`:
   - Validate specific data records against target schema.

5. `add_row(row: object)`:
   - Add a new customer row.
   - Example requests: "Add a new customer named Rahul from Mumbai", "Insert customer John with email john@example.com".
   - Parameter `row` must be an object with column keys (e.g., {"customer_name": "Rahul", "city": "Mumbai"}).

6. `edit_data(row_id: integer, customer_name: string, updates: object)`:
   - Modify an existing customer record by row ID or customer name.
   - Example requests: "Change customer ID 15's city to Hyderabad", "Update email for customer John".
   - Parameter `updates` contains the column names and new values (e.g., {"city": "Hyderabad"}).

7. `delete_row(row_id: integer)`:
   - Delete a specific row by its unique ID.
   - Example requests: "Delete the row with ID 20", "Remove customer #5".

8. `delete_column(column_name: string)`:
   - Safely remove an unused column from schema.
   - Example requests: "Remove the unused column named notes", "Delete column middle_name".

9. `delete_duplicates(table_name: string = "customers")`:
   - Find and delete duplicate records.
   - Example requests: "Delete duplicate records", "Clean up duplicates".

10. `upload_classify_standardize(filename: string, file_content_base64: string, file_content_text: string, proceed_with_insert: boolean)`:
   - Complete file import tool: classifies columns, standardizes formats, validates records, and ingests into SQLite database.
   - Example requests: "Import customer data", "Process and upload spreadsheet".

SAFETY AND CONFIRMATION RULES:
- Never directly delete all rows or delete all columns.
- If a request is vague or missing required details (e.g. "update customer" without row ID or changes, "delete a row" without ID), respond directly asking for the missing information.
- Always be concise, helpful, and professional.
"""

MCP_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": "Retrieve or search customer records from the database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter records (e.g. city name, customer name, email)."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return (default 1000 to retrieve complete dataset, or pass 0 for all records)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_data",
            "description": "Check data quality score, missing values, duplicates, and invalid format counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to check (default 'customers')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_column",
            "description": "Retrieve all available active database columns, data types, aliases, and descriptions.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_data",
            "description": "Validate records against standardized schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "records": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of record dictionaries to validate."
                    }
                },
                "required": ["records"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_row",
            "description": "Add a new customer row into the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "row": {
                        "type": "object",
                        "description": "Dictionary of column names and values to insert."
                    }
                },
                "required": ["row"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_data",
            "description": "Modify an existing customer row in the database by ID or customer name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "row_id": {
                        "type": "integer",
                        "description": "Unique row ID to modify."
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name to find and modify if row ID is not specified."
                    },
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of column names and updated values."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_row",
            "description": "Safely delete a customer row by its unique ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "row_id": {
                        "type": "integer",
                        "description": "Unique row ID to delete."
                    }
                },
                "required": ["row_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_column",
            "description": "Safely delete an unused column from the database schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column_name": {
                        "type": "string",
                        "description": "Name of the column to delete."
                    }
                },
                "required": ["column_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_duplicates",
            "description": "Find and delete duplicate records from the database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to clean duplicates from (default 'customers')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_classify_standardize",
            "description": "Upload, classify, standardize, and store CSV or Excel data into the SQLite database. Can be used for importing files or processing standardized data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file (e.g. data.csv, leads.xlsx)."
                    },
                    "file_content_base64": {
                        "type": "string",
                        "description": "Base64 encoded content of the file."
                    },
                    "file_content_text": {
                        "type": "string",
                        "description": "Plain text CSV content if base64 is not provided."
                    },
                    "proceed_with_insert": {
                        "type": "boolean",
                        "description": "True to insert into database, False to only classify and preview."
                    }
                },
                "required": ["filename"]
            }
        }
    }
]

WRITE_TOOLS = {"add_row", "edit_data", "delete_row", "delete_column", "delete_duplicates", "upload_classify_standardize"}


def get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        # Check current working directory .env
        load_dotenv()
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
    return key


async def call_openrouter(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "MCP Data Standardization AI Assistant"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "tools": MCP_TOOLS_SPEC,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Retry up to 2 times if OpenRouter returns 429 credit verification delay
        last_resp = None
        for attempt in range(3):
            resp = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            last_resp = resp
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429 and attempt < 2:
                import asyncio
                await asyncio.sleep(1.0)
                continue
            else:
                break
        
        error_detail = last_resp.text
        try:
            err_json = last_resp.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_detail = err_json["error"]["message"]
        except Exception:
            pass
        raise RuntimeError(f"OpenRouter LLM error ({last_resp.status_code}): {error_detail}")


async def execute_confirmed_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute write operations after user confirmation via MCP Client."""
    if tool_name == "add_row":
        row = tool_args.get("row", {})
        res = await mcp_client.add_row(row=row)
        return {
            "status": res.get("status", "success"),
            "tool": "add_row",
            "message": res.get("message", "New customer row added successfully."),
            "data": res
        }

    elif tool_name == "edit_data":
        row_id = tool_args.get("row_id")
        customer_name = tool_args.get("customer_name")
        updates = tool_args.get("updates", {})
        res = await mcp_client.edit_data(row_id=row_id, customer_name=customer_name, updates=updates, confirm=True)
        return {
            "status": res.get("status", "success"),
            "tool": "edit_data",
            "message": res.get("message", "Customer record updated successfully."),
            "data": res
        }

    elif tool_name == "delete_row":
        row_id = int(tool_args.get("row_id", 0))
        res = await mcp_client.delete_row(row_id=row_id, confirm=True)
        return {
            "status": res.get("status", "success"),
            "tool": "delete_row",
            "message": res.get("message", f"Row ID {row_id} deleted successfully."),
            "data": res
        }

    elif tool_name == "delete_column":
        column_name = str(tool_args.get("column_name", "")).strip()
        res = await mcp_client.delete_column(column_name=column_name, confirm=True)
        return {
            "status": res.get("status", "success"),
            "tool": "delete_column",
            "message": res.get("message", f"Column '{column_name}' deleted successfully."),
            "data": res
        }

    elif tool_name == "delete_duplicates":
        table_name = tool_args.get("table_name", "customers")
        res = await mcp_client.delete_duplicates(table_name=table_name, confirm=True)
        return {
            "status": res.get("status", "success"),
            "tool": "delete_duplicates",
            "message": res.get("message", f"Duplicate records cleaned up successfully."),
            "data": res
        }

    elif tool_name == "upload_classify_standardize":
        res = await mcp_client.upload_classify_standardize(
            filename=tool_args.get("filename", "upload.csv"),
            file_content_base64=tool_args.get("file_content_base64", ""),
            file_content_text=tool_args.get("file_content_text", ""),
            confirmed_mappings=tool_args.get("confirmed_mappings", {}),
            proceed_with_insert=True
        )
        return {
            "status": res.get("status", "success"),
            "tool": "upload_classify_standardize",
            "message": res.get("message", "File processed and imported into SQLite database."),
            "data": res
        }

    else:
        raise ValueError(f"Unknown tool for execution: {tool_name}")


async def process_assistant_message(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    confirmed_action: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main Assistant flow:
    1. If confirmed_action is provided, directly executes the MCP tool with confirm=True.
    2. Otherwise, calls OpenRouter LLM to understand intent and select MCP tool.
    3. If tool is read-only, executes immediately via MCP client and formats result.
    4. If tool is write-operation, checks safety and generates a confirmation request.
    """
    if conversation_history is None:
        conversation_history = []

    # 1. Handle explicit confirmation of a previous pending action
    if confirmed_action and confirmed_action.get("confirmed"):
        tool_name = confirmed_action.get("tool_name")
        tool_args = confirmed_action.get("tool_args", {})
        try:
            result = await execute_confirmed_tool(tool_name, tool_args)
            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": result.get("message", "Operation executed successfully."),
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": result.get("data"),
                "requires_confirmation": False,
                "executed": True
            })
        except ConnectionError:
            return sanitize_for_json({
                "status": "error",
                "role": "assistant",
                "message": "MCP Server is offline (http://127.0.0.1:8001/mcp). Tools cannot be executed. Please start the MCP server separately: 'venv\\Scripts\\python.exe backend/server/mcp_server.py'.",
                "tool_called": tool_name,
                "requires_confirmation": False
            })
        except Exception as e:
            return sanitize_for_json({
                "status": "error",
                "role": "assistant",
                "message": f"Failed to execute operation: {str(e)}",
                "tool_called": tool_name,
                "requires_confirmation": False
            })

    # 2. Build messages payload for OpenRouter
    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Add recent history (last 6 turns for context)
    for msg in conversation_history[-6:]:
        if msg.get("role") in ["user", "assistant"]:
            llm_messages.append({"role": msg["role"], "content": msg.get("content", "")})
    
    llm_messages.append({"role": "user", "content": user_message})

    # 3. Call OpenRouter LLM
    try:
        response_data = await call_openrouter(llm_messages)
    except Exception as e:
        return sanitize_for_json({
            "status": "error",
            "role": "assistant",
            "message": f"AI Assistant could not connect to OpenRouter: {str(e)}. Please check your API key and connection.",
            "tool_called": None
        })

    choice = response_data.get("choices", [{}])[0].get("message", {})
    tool_calls = choice.get("tool_calls", [])
    direct_content = choice.get("content", "")

    # 4. If no tool was chosen by LLM, reply with conversational content
    if not tool_calls:
        return sanitize_for_json({
            "status": "success",
            "role": "assistant",
            "message": direct_content or "I understand your request, but no database operation was required. How can I help you?",
            "tool_called": None,
            "requires_confirmation": False
        })

    # 5. Extract selected tool and parsed arguments
    primary_call = tool_calls[0]
    tool_name = primary_call.get("function", {}).get("name", "")
    raw_args = primary_call.get("function", {}).get("arguments", "{}")
    
    try:
        tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except Exception:
        tool_args = {}

    # 6. Safety check: Handle Write Operations (Requires Confirmation)
    if tool_name in WRITE_TOOLS:
        try:
            # Pre-validate before asking confirmation
            preview = {}
            message = ""

            if tool_name == "delete_row":
                row_id = tool_args.get("row_id")
                if not row_id or int(row_id) <= 0:
                    return sanitize_for_json({
                        "status": "warning",
                        "role": "assistant",
                        "message": "Please specify a valid numeric Row ID to delete.",
                        "tool_called": tool_name
                    })
                
                row_id = int(row_id)
                row_res = await mcp_client.get_row(row_id)
                current_row = row_res.get("row") if row_res.get("status") == "success" else None
                if not current_row:
                    return sanitize_for_json({
                        "status": "error",
                        "role": "assistant",
                        "message": f"Row with ID {row_id} does not exist in the database.",
                        "tool_called": tool_name
                    })
                
                name = current_row.get("customer_name") or current_row.get("email") or f"ID #{row_id}"
                preview = {
                    "row_id": row_id,
                    "customer_name": current_row.get("customer_name"),
                    "email": current_row.get("email"),
                    "city": current_row.get("city")
                }
                message = f"Are you sure you want to permanently delete row #{row_id} ('{name}')?"

            elif tool_name == "delete_column":
                col_name = str(tool_args.get("column_name", "")).strip()
                if not col_name:
                    return sanitize_for_json({
                        "status": "warning",
                        "role": "assistant",
                        "message": "Please specify the column name you would like to delete.",
                        "tool_called": tool_name
                    })
                if col_name.lower() in ["id", "created_at"]:
                    return sanitize_for_json({
                        "status": "error",
                        "role": "assistant",
                        "message": f"Protected column '{col_name}' cannot be deleted.",
                        "tool_called": tool_name
                    })
                
                cols_res = await mcp_client.get_column()
                active_cols = [c.get("column_name") for c in cols_res.get("columns", [])]
                if col_name not in active_cols:
                    return sanitize_for_json({
                        "status": "error",
                        "role": "assistant",
                        "message": f"Column '{col_name}' does not exist in the database schema.",
                        "tool_called": tool_name
                    })
                
                preview = {"column_name": col_name}
                message = f"Are you sure you want to permanently delete column '{col_name}' from the database? All records in this column will be removed."

            elif tool_name == "add_row":
                row_data = tool_args.get("row", {})
                if not row_data:
                    return sanitize_for_json({
                        "status": "warning",
                        "role": "assistant",
                        "message": "Please provide the customer details to add (e.g. name, city, email).",
                        "tool_called": tool_name
                    })
                preview = row_data
                fields_str = ", ".join(f"{k}: {v}" for k, v in row_data.items())
                message = f"Confirm adding new customer record with values ({fields_str})?"

            elif tool_name == "edit_data":
                row_id = tool_args.get("row_id")
                customer_name = tool_args.get("customer_name")
                updates = tool_args.get("updates", {})

                if not updates:
                    return sanitize_for_json({
                        "status": "warning",
                        "role": "assistant",
                        "message": "Please specify which column(s) and new value(s) to update.",
                        "tool_called": tool_name
                    })

                # Check target row
                target_row = None
                if row_id:
                    row_id = int(row_id)
                    row_res = await mcp_client.get_row(row_id)
                    target_row = row_res.get("row") if row_res.get("status") == "success" else None
                    if not target_row:
                        return sanitize_for_json({
                            "status": "error",
                            "role": "assistant",
                            "message": f"Row with ID {row_id} does not exist in the database.",
                            "tool_called": tool_name
                        })
                elif customer_name:
                    search_res = await mcp_client.search_customers(customer_name)
                    matches = []
                    if isinstance(search_res.get("results"), list):
                        matches = search_res["results"]
                    elif isinstance(search_res.get("data"), list):
                        matches = search_res["data"]
                    elif isinstance(search_res.get("matches"), list):
                        matches = search_res["matches"]
                    elif search_res.get("status") == "needs_confirmation":
                        matches = [search_res.get("current_values", {})]
                    elif search_res.get("row"):
                        matches = [search_res["row"]]
                    if not matches:
                        return sanitize_for_json({
                            "status": "error",
                            "role": "assistant",
                            "message": f"No customer found matching '{customer_name}'.",
                            "tool_called": tool_name
                        })
                    if len(matches) > 1:
                        return sanitize_for_json({
                            "status": "warning",
                            "role": "assistant",
                            "message": f"Found {len(matches)} customers matching '{customer_name}'. Please specify unique Row ID.",
                            "tool_called": tool_name,
                            "data": {"matches": matches}
                        })
                    target_row = matches[0]
                    row_id = target_row.get("id")
                    tool_args["row_id"] = row_id
                else:
                    return sanitize_for_json({
                        "status": "warning",
                        "role": "assistant",
                        "message": "Please specify the row ID or customer name to edit.",
                        "tool_called": tool_name
                    })

                current_values = {k: target_row.get(k) for k in updates.keys()}
                preview = {
                    "row_id": row_id,
                    "customer_name": target_row.get("customer_name"),
                    "current_values": current_values,
                    "proposed_updates": updates
                }
                changes_desc = ", ".join(f"{k} from '{current_values.get(k)}' to '{v}'" for k, v in updates.items())
                message = f"Confirm changing Row #{row_id} ({changes_desc})?"

            elif tool_name == "delete_duplicates":
                preview = {"action": "delete_duplicates"}
                message = "Confirm scanning and deleting all redundant duplicate records in the database?"

            elif tool_name == "upload_classify_standardize":
                fn = tool_args.get("filename", "file")
                preview = {"filename": fn, "proceed_with_insert": True}
                message = f"Confirm standardizing and inserting data from '{fn}' into SQLite database?"

            return sanitize_for_json({
                "status": "needs_confirmation",
                "role": "assistant",
                "message": message,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "preview": preview,
                "requires_confirmation": True
            })

        except ConnectionError:
            return sanitize_for_json({
                "status": "error",
                "role": "assistant",
                "message": "MCP Server is offline (http://127.0.0.1:8001/mcp). Tools cannot be executed. Please start the MCP server separately using 'venv\\Scripts\\python.exe backend/server/mcp_server.py'.",
                "tool_called": tool_name
            })

    # 7. Execute Read-Only Tools immediately via MCP Client
    try:
        if tool_name == "extract_data":
            search_query = tool_args.get("search", "")
            raw_limit = tool_args.get("limit")
            # If limit is 50, missing, or <= 0, expand to 1000 to return whole records
            if raw_limit is None or int(raw_limit) == 50 or int(raw_limit) <= 0:
                limit = 1000
            else:
                limit = int(raw_limit)
            data_res = await mcp_client.extract_data(search=search_query, limit=limit)
            
            total = data_res.get("total_count", 0)
            returned = data_res.get("returned_count", 0)
            
            if search_query:
                summary_msg = f"Found {total} record(s) matching '{search_query}'."
            else:
                summary_msg = f"Retrieved {returned} of {total} total records in the database."
            
            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": summary_msg,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": data_res,
                "data_type": "table",
                "requires_confirmation": False
            })

        elif tool_name == "check_data":
            table_name = tool_args.get("table_name", "customers")
            check_res = await mcp_client.check_data(table_name=table_name)
            
            q_score = check_res.get("data_quality_score", 100)
            total = check_res.get("total_records", 0)
            duplicates = check_res.get("duplicate_records", 0)
            invalid_emails = check_res.get("invalid_emails", 0)
            invalid_phones = check_res.get("invalid_phones", 0)
            invalid_dates = check_res.get("invalid_dates", 0)
            missing = check_res.get("missing_values", {})
            missing_total = sum(missing.values()) if isinstance(missing, dict) else 0

            summary_msg = (
                f"Data Quality Score: {q_score}%. "
                f"Evaluated {total} records: found {duplicates} duplicate(s), "
                f"{missing_total} missing value(s), and {invalid_emails + invalid_phones + invalid_dates} invalid format(s)."
            )

            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": summary_msg,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": check_res,
                "data_type": "quality_report",
                "requires_confirmation": False
            })

        elif tool_name == "get_column":
            col_res = await mcp_client.get_column()
            cols = col_res.get("columns", [])
            col_names = [c.get("column_name", c) if isinstance(c, dict) else c for c in cols]
            
            summary_msg = f"The database has {len(cols)} active column(s): {', '.join(col_names)}."
            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": summary_msg,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": col_res,
                "data_type": "schema",
                "requires_confirmation": False
            })

        elif tool_name == "validate_data":
            records = tool_args.get("records", [])
            val_res = await mcp_client.validate_data(records=records)
            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": "Validation completed.",
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": val_res,
                "data_type": "validation",
                "requires_confirmation": False
            })

        elif tool_name == "upload_classify_standardize":
            fn = tool_args.get("filename", "")
            upload_res = await mcp_client.upload_classify_standardize(
                filename=fn,
                file_content_base64=tool_args.get("file_content_base64", ""),
                file_content_text=tool_args.get("file_content_text", ""),
                proceed_with_insert=tool_args.get("proceed_with_insert", False)
            )
            return sanitize_for_json({
                "status": "success",
                "role": "assistant",
                "message": upload_res.get("message", f"File '{fn}' processed via upload_classify_standardize tool."),
                "tool_called": tool_name,
                "tool_args": tool_args,
                "data": upload_res,
                "data_type": "upload_classification",
                "requires_confirmation": False
            })

        else:
            return sanitize_for_json({
                "status": "error",
                "role": "assistant",
                "message": f"Tool '{tool_name}' is not recognized.",
                "tool_called": tool_name
            })

    except ConnectionError:
        return sanitize_for_json({
            "status": "error",
            "role": "assistant",
            "message": "MCP Server is offline (http://127.0.0.1:8001/mcp). Tools cannot be executed. Please start the MCP server separately using 'venv\\Scripts\\python.exe backend/server/mcp_server.py'.",
            "tool_called": tool_name
        })
    except Exception as e:
        return sanitize_for_json({
            "status": "error",
            "role": "assistant",
            "message": f"Error running MCP tool '{tool_name}': {str(e)}",
            "tool_called": tool_name
        })
