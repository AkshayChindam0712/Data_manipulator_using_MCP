import sys
import os

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
for p in [_curr_dir, _parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv()
load_dotenv(os.path.join(_parent_dir, ".env"))

import base64
import io
import json
import re
import pandas as pd
from mcp.server.mcpserver import MCPServer

try:
    from server.database import (
        init_db,
        STANDARD_COLUMNS,
        get_db,
        query_db,
        execute_db,
        insert_customers,
        delete_customer_row,
        delete_customer_column,
        delete_duplicate_customers,
        get_customer_by_id,
        update_customer_row,
        search_customers_by_name,
        get_active_db_columns,
        save_file_metadata,
        save_column_metadata,
        sanitize_for_json
    )
    from server.data_processor import (
        detect_file_format,
        read_file,
        clean_dataframe,
        validate_records,
        validate_email_val,
        validate_phone_val,
        validate_date_val,
        standardize_single_date,
        standardize_single_phone,
        keyword_classify_column,
        llm_classify_column
    )
except ImportError:
    from database import (
        init_db,
        STANDARD_COLUMNS,
        get_db,
        query_db,
        execute_db,
        insert_customers,
        delete_customer_row,
        delete_customer_column,
        delete_duplicate_customers,
        get_customer_by_id,
        update_customer_row,
        search_customers_by_name,
        get_active_db_columns,
        save_file_metadata,
        save_column_metadata,
        sanitize_for_json
    )
    from data_processor import (
        detect_file_format,
        read_file,
        clean_dataframe,
        validate_records,
        validate_email_val,
        validate_phone_val,
        validate_date_val,
        standardize_single_date,
        standardize_single_phone,
        keyword_classify_column,
        llm_classify_column
    )

mcp = MCPServer("DataStandardizationServer")

@mcp.tool()
def get_column() -> str:
    """
    Return the target standardized database columns.
    Shows column names, data types, aliases, descriptions, and sample values.
    Reflects the actual active columns in the database.
    """
    active_cols = get_active_db_columns()
    return json.dumps({
        "status": "success",
        "table": "customers",
        "columns": active_cols
    }, indent=2)

@mcp.tool()
def check_data(table_name: str = "customers") -> str:
    """
    Check missing values, duplicate records, invalid values, and data quality.
    Returns a comprehensive data-quality report.
    """
    conn = get_db()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Table read error: {str(e)}"})
    finally:
        conn.close()

    total_rows = len(df)
    if total_rows == 0:
        return json.dumps({
            "status": "success",
            "table_name": table_name,
            "total_records": 0,
            "missing_values": {},
            "duplicate_records": 0,
            "invalid_emails": 0,
            "invalid_phones": 0,
            "invalid_dates": 0,
            "data_quality_score": 100.0,
            "summary": "Database table is currently empty."
        }, indent=2)

    # Missing values
    missing_by_col = df.isnull().sum().to_dict()
    for col in df.columns:
        if df[col].dtype == 'object':
            empty_count = (df[col].astype(str).str.strip() == '').sum()
            missing_by_col[col] = int(missing_by_col[col] + empty_count)
        else:
            missing_by_col[col] = int(missing_by_col[col])

    # Duplicate records (ignoring primary key 'id' and 'created_at' if present)
    content_cols = [c for c in df.columns if c not in ['id', 'created_at']]
    duplicate_count = int(df.duplicated(subset=content_cols).sum()) if content_cols else 0

    # Check invalid formats
    invalid_emails = 0
    if "email" in df.columns:
        invalid_emails = int((~df["email"].apply(validate_email_val)).sum())

    invalid_phones = 0
    if "phone_number" in df.columns:
        invalid_phones = int((~df["phone_number"].apply(validate_phone_val)).sum())

    invalid_dates = 0
    if "signup_date" in df.columns:
        invalid_dates = int((~df["signup_date"].apply(validate_date_val)).sum())

    # Overall Data Quality Score (0 to 100%)
    total_cells = total_rows * max(1, len(content_cols))
    total_missing = sum(missing_by_col.get(c, 0) for c in content_cols)
    total_invalid = invalid_emails + invalid_phones + invalid_dates
    
    penalty = (total_missing / max(1, total_cells)) * 40.0 + \
              (duplicate_count / max(1, total_rows)) * 30.0 + \
              (total_invalid / max(1, total_cells)) * 30.0
    quality_score = max(0.0, round(100.0 - penalty, 2))

    report = {
        "status": "success",
        "table_name": table_name,
        "total_records": total_rows,
        "missing_values": missing_by_col,
        "duplicate_records": duplicate_count,
        "invalid_emails": invalid_emails,
        "invalid_phones": invalid_phones,
        "invalid_dates": invalid_dates,
        "data_quality_score": quality_score,
        "summary": f"Data quality score is {quality_score}%. Found {duplicate_count} duplicate(s) and {total_invalid} invalid format value(s)."
    }
    return json.dumps(sanitize_for_json(report), indent=2, allow_nan=False)

@mcp.tool()
def extract_data(search: str = "", limit: int = 1000, offset: int = 0) -> str:
    """
    Retrieve standardized data from the database.
    Supports searching across records and filtering.
    Default limit is 1000 to display full datasets. Set limit=0 or -1 for all records.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active columns dynamically
    cursor.execute("PRAGMA table_info(customers)")
    cols = [row["name"] for row in cursor.fetchall()]
    cols_str = ", ".join(cols) if cols else "*"

    base_query = f"SELECT {cols_str} FROM customers"
    params = []
    
    if search and search.strip():
        clean_search = search.strip()
        nospace_search = re.sub(r'\s+', '', clean_search)
        term_std = f"%{clean_search}%"
        term_nospace = f"%{nospace_search}%"
        search_clauses = []
        for c in cols:
            if c not in ['id', 'created_at']:
                search_clauses.append(f"({c} LIKE ? OR REPLACE({c}, ' ', '') LIKE ?)")
                params.extend([term_std, term_nospace])
        if search_clauses:
            base_query += " WHERE " + " OR ".join(search_clauses)
        
    # Count total
    count_query = f"SELECT COUNT(*) FROM ({base_query})"
    cursor.execute(count_query, params)
    total_matched = cursor.fetchone()[0]

    # Retrieve page
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        lim = 1000

    try:
        off = int(offset)
    except (TypeError, ValueError):
        off = 0

    if lim <= 0 or lim >= 50000:
        paged_query = base_query + " ORDER BY id DESC"
        paged_params = list(params)
    else:
        paged_query = base_query + " ORDER BY id DESC LIMIT ? OFFSET ?"
        paged_params = list(params) + [lim, off]
    
    df = pd.read_sql_query(paged_query, conn, params=paged_params)
    conn.close()

    # Convert NaN / NaT / Inf to None across all column types
    df = df.astype(object).where(pd.notna(df), None)
    records = sanitize_for_json(df.to_dict(orient="records"))
    
    payload = {
        "status": "success",
        "total_count": total_matched,
        "returned_count": len(records),
        "limit": limit,
        "offset": offset,
        "columns": cols,
        "records": records
    }
    return json.dumps(sanitize_for_json(payload), indent=2, allow_nan=False)

@mcp.tool()
def validate_data(records_json: str) -> str:
    """
    Validate records against the standardized database columns.
    Checks data types and common fields such as email, phone, and date.
    """
    try:
        records = json.loads(records_json)
        if isinstance(records, dict):
            records = [records]
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Invalid JSON format: {str(e)}"})

    report = validate_records(records)
    return json.dumps({
        "status": "success",
        "validation_report": sanitize_for_json(report)
    }, indent=2, allow_nan=False)

@mcp.tool()
def add_row(row_json: str, confirm_mappings: str = "{}") -> str:
    """
    Manually add a row without uploading a file.
    Standardizes and validates entered fields against database schema.
    If a field has low confidence, requires confirmation.
    Inserts standardized record into SQLite.
    """
    try:
        raw_row = json.loads(row_json)
        confirmed = json.loads(confirm_mappings)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"JSON parsing error: {str(e)}"})

    standardized_record = {}
    unresolved_fields = []

    active_db_cols = get_active_db_columns()
    standard_col_names = [c["column_name"] for c in active_db_cols if c["column_name"] not in ["id", "created_at"]]

    for key, val in raw_row.items():
        if val is None or str(val).strip() == "":
            continue
            
        clean_key = key.strip()
        
        # 1. If explicit confirmed mapping exists
        if clean_key in confirmed:
            mapped_target = confirmed[clean_key]
            if mapped_target != "skip" and mapped_target in standard_col_names:
                standardized_record[mapped_target] = str(val).strip()
            continue

        # 2. Check keyword/alias with sample data
        matched_target, conf, reason = keyword_classify_column(clean_key, active_db_cols, [val])
        
        if conf >= 0.90 and matched_target in standard_col_names:
            standardized_record[matched_target] = str(val).strip()
        else:
            # Requires confirmation
            unresolved_fields.append({
                "field": clean_key,
                "value": val,
                "suggested_column": matched_target if matched_target != "none" else standard_col_names[0],
                "confidence": conf,
                "reason": reason
            })

    # If any fields need confirmation
    if unresolved_fields:
        return json.dumps({
            "status": "needs_confirmation",
            "message": "Some fields have confidence below 90% and require user confirmation.",
            "unresolved_fields": unresolved_fields,
            "standardized_so_far": standardized_record
        }, indent=2)

    # Standardize values
    if "signup_date" in standardized_record:
        standardized_record["signup_date"] = standardize_single_date(standardized_record["signup_date"])
    if "phone_number" in standardized_record:
        standardized_record["phone_number"] = standardize_single_phone(standardized_record["phone_number"])

    # Validate
    val_report = validate_records([standardized_record])
    
    # Insert
    inserted = insert_customers([standardized_record])
    
    return json.dumps({
        "status": "success",
        "message": "Row successfully standardized, validated, and inserted into database.",
        "inserted_record": standardized_record,
        "validation_report": val_report
    }, indent=2)

@mcp.tool()
def delete_row(row_id: int, confirm: bool = False) -> str:
    """
    Delete a specific row from the database using its unique ID.
    Asks for confirmation before deleting.
    Prevents accidental deletion of multiple rows.
    """
    if not confirm:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, email FROM customers WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return json.dumps({
                "status": "error",
                "message": f"Row with ID {row_id} does not exist in the database."
            }, indent=2)
        desc = row["customer_name"] or row["email"] or f"ID {row_id}"
        return json.dumps({
            "status": "needs_confirmation",
            "message": f"Confirmation required: Are you sure you want to permanently delete row #{row_id} ('{desc}')?",
            "row_id": row_id
        }, indent=2)

    res = delete_customer_row(row_id)
    return json.dumps({
        "status": "success" if res["success"] else "error",
        "message": res["message"],
        "deleted_row_id": row_id if res["success"] else None
    }, indent=2)

@mcp.tool()
def delete_column(column_name: str, confirm: bool = False) -> str:
    """
    Safely delete a column from the database table.
    Shows the column name and asks for confirmation before deleting.
    """
    col_clean = column_name.strip()
    if col_clean.lower() in ['id', 'created_at']:
        return json.dumps({
            "status": "error",
            "message": f"Protected column '{col_clean}' cannot be deleted."
        }, indent=2)

    if not confirm:
        return json.dumps({
            "status": "needs_confirmation",
            "message": f"Confirmation required: Are you sure you want to permanently remove column '{col_clean}' from the database? All records in this column will be deleted.",
            "column_name": col_clean
        }, indent=2)

    res = delete_customer_column(col_clean)
    return json.dumps({
        "status": "success" if res["success"] else "error",
        "message": res["message"],
        "deleted_column": col_clean if res["success"] else None
    }, indent=2)

@mcp.tool()
def delete_duplicates(table_name: str = "customers", confirm: bool = False) -> str:
    """
    Find and delete duplicate records from the database table.
    Keeps the first occurrence and removes redundant duplicates.
    Shows duplicate count and requires confirmation if confirm is False.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [row["name"] for row in cursor.fetchall()]
    content_cols = [c for c in cols if c not in ['id', 'created_at']]
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        conn.close()
        return json.dumps({"status": "error", "message": f"Database read error: {str(e)}"}, indent=2)
    conn.close()

    if len(df) == 0 or not content_cols:
        return json.dumps({
            "status": "success",
            "message": "No records or columns to evaluate for duplicates.",
            "duplicate_count": 0,
            "deleted_count": 0
        }, indent=2)

    dup_mask = df.duplicated(subset=content_cols, keep='first')
    duplicate_count = int(dup_mask.sum())

    if duplicate_count == 0:
        return json.dumps({
            "status": "success",
            "message": "No duplicate records found in the database.",
            "duplicate_count": 0,
            "deleted_count": 0
        }, indent=2)

    if not confirm:
        return json.dumps({
            "status": "needs_confirmation",
            "message": f"Found {duplicate_count} duplicate record(s). Do you confirm deleting them to retain only unique records?",
            "duplicate_count": duplicate_count
        }, indent=2)

    res = delete_duplicate_customers(table_name)
    return json.dumps({
        "status": "success" if res["success"] else "error",
        "message": res["message"],
        "deleted_count": res.get("deleted_count", 0),
        "deleted_ids": res.get("deleted_ids", [])
    }, indent=2)

@mcp.tool()
def edit_data(row_id: int = None, customer_name: str = None, updates_json: str = None, confirm: bool = False) -> str:
    """
    Modify existing rows in the database by unique row ID or customer name search.
    Supports searching database based on customer name.
    Supports changing one or multiple column values.
    Validates new values before updating.
    Shows current values, proposed changes, and asks for confirmation before saving.
    Returns the updated row as a readable result.
    """
    # 1. Resolve row by row_id or search by customer_name
    current_row = None
    if row_id and int(row_id) > 0:
        row_id = int(row_id)
        current_row = get_customer_by_id(row_id)
        if not current_row:
            return json.dumps({
                "status": "error",
                "message": f"Row with ID {row_id} does not exist in the database."
            }, indent=2)
    elif customer_name and str(customer_name).strip():
        name_term = str(customer_name).strip()
        matches = search_customers_by_name(name_term)
        if not matches:
            return json.dumps({
                "status": "error",
                "message": f"No customer found matching '{name_term}' in the database."
            }, indent=2)
            
        # If no updates_json was provided, this call is a search query
        if not updates_json or updates_json.strip() == "" or updates_json.strip() == "{}":
            return json.dumps({
                "status": "search_results",
                "search_term": name_term,
                "count": len(matches),
                "results": matches
            }, indent=2)
            
        if len(matches) == 1:
            current_row = matches[0]
            row_id = current_row["id"]
        else:
            return json.dumps({
                "status": "multiple_matches",
                "message": f"Found {len(matches)} customers matching '{name_term}'. Please specify unique Row ID to edit.",
                "search_term": name_term,
                "matches": matches
            }, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": "Please specify a row_id or customer_name to select a record."
        }, indent=2)

    # 2. Parse updates
    try:
        if isinstance(updates_json, dict):
            raw_updates = updates_json
        else:
            raw_updates = json.loads(updates_json)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Invalid updates JSON format: {str(e)}"
        }, indent=2)

    if not raw_updates or not isinstance(raw_updates, dict):
        return json.dumps({
            "status": "error",
            "message": "Updates must be a non-empty JSON object of column names and values."
        }, indent=2)

    # 3. Standardize column names based on active columns & aliases
    active_cols = get_active_db_columns()
    col_name_map = {}
    for c in active_cols:
        target = c["column_name"]
        col_name_map[target.lower()] = target
        for a in c.get("aliases", []):
            col_name_map[a.lower().replace("_", "").replace(" ", "")] = target
            col_name_map[a.lower()] = target

    cleaned_updates = {}
    for k, v in raw_updates.items():
        k_clean = str(k).strip()
        k_norm = k_clean.lower()
        k_collapsed = k_norm.replace("_", "").replace(" ", "")
        
        target_col = col_name_map.get(k_norm) or col_name_map.get(k_collapsed) or k_clean
        if target_col in ['id', 'created_at']:
            continue
        cleaned_updates[target_col] = str(v).strip() if v is not None else None

    if not cleaned_updates:
        return json.dumps({
            "status": "error",
            "message": "No valid updatable columns provided. Columns 'id' and 'created_at' cannot be modified."
        }, indent=2)

    # 4. Validate new values
    if "customer_name" in cleaned_updates:
        name_val = cleaned_updates["customer_name"]
        if not name_val or name_val.strip() == "":
            return json.dumps({
                "status": "error",
                "message": "Validation error: customer_name cannot be empty."
            }, indent=2)

    if "email" in cleaned_updates and cleaned_updates["email"]:
        email_val = cleaned_updates["email"]
        if not validate_email_val(email_val):
            return json.dumps({
                "status": "error",
                "message": f"Validation error: Invalid email format '{email_val}'."
            }, indent=2)

    if "phone_number" in cleaned_updates and cleaned_updates["phone_number"]:
        phone_val = standardize_single_phone(cleaned_updates["phone_number"])
        cleaned_updates["phone_number"] = phone_val
        if not validate_phone_val(phone_val):
            return json.dumps({
                "status": "error",
                "message": f"Validation error: Invalid phone number format '{cleaned_updates['phone_number']}'."
            }, indent=2)

    if "signup_date" in cleaned_updates and cleaned_updates["signup_date"]:
        date_val = standardize_single_date(cleaned_updates["signup_date"])
        cleaned_updates["signup_date"] = date_val
        if not validate_date_val(date_val):
            return json.dumps({
                "status": "error",
                "message": f"Validation error: Invalid date format '{cleaned_updates['signup_date']}'. Expected YYYY-MM-DD."
            }, indent=2)

    # 5. Detect changes (diff)
    diff = []
    current_lines = []
    changes_lines = []

    for col, new_val in cleaned_updates.items():
        old_val = current_row.get(col)
        old_str = "" if old_val is None else str(old_val).strip()
        new_str = "" if new_val is None else str(new_val).strip()
        
        diff.append({
            "column": col,
            "old_value": old_val,
            "new_value": new_val,
            "changed": old_str != new_str
        })
        if old_str != new_str:
            current_lines.append(f"{col} = {old_val if old_val is not None else '<empty>'}")
            changes_lines.append(f"{col} = {new_val if new_val is not None else '<empty>'}")

    has_actual_changes = any(d["changed"] for d in diff)
    if not has_actual_changes:
        return json.dumps({
            "status": "info",
            "message": f"No modifications detected for Row #{row_id}. New values are identical to current values.",
            "row_id": row_id,
            "current_values": current_row
        }, indent=2)

    # Readable text preview
    preview_text = f"Row ID: {row_id}\n\nCurrent:\n" + "\n".join(current_lines) + "\n\nChanges:\n" + "\n".join(changes_lines) + "\n\nConfirm changes?"

    # 6. If not confirmed, require confirmation
    if not confirm:
        return json.dumps({
            "status": "needs_confirmation",
            "row_id": row_id,
            "message": f"Confirmation required to update Row #{row_id}.",
            "readable_preview": preview_text,
            "current_values": {d["column"]: d["old_value"] for d in diff if d["changed"]},
            "new_values": {d["column"]: d["new_value"] for d in diff if d["changed"]},
            "diff": [d for d in diff if d["changed"]]
        }, indent=2)

    # 7. Apply updates after confirmation
    update_dict = {d["column"]: d["new_value"] for d in diff if d["changed"]}
    res = update_customer_row(row_id, update_dict)
    if not res.get("success"):
        return json.dumps({
            "status": "error",
            "message": res.get("message", "Failed to update row.")
        }, indent=2)

    updated_row = res.get("updated_row", {})
    
    # Readable result text
    readable_lines = [
        "Data updated successfully.\n",
        f"ID: {row_id}"
    ]
    for col in ["customer_name", "email", "phone_number", "city", "signup_date"]:
        if col in updated_row and updated_row[col] is not None:
            col_label = col.replace("_", " ").title()
            readable_lines.append(f"{col_label}: {updated_row[col]}")
    for k, v in updated_row.items():
        if k not in ["id", "created_at", "customer_name", "email", "phone_number", "city", "signup_date"] and v is not None:
            readable_lines.append(f"{k.replace('_', ' ').title()}: {v}")

    readable_output = "\n".join(readable_lines)

    return json.dumps({
        "status": "success",
        "message": f"Data updated successfully for Row #{row_id}.",
        "row_id": row_id,
        "updated_row": updated_row,
        "readable_output": readable_output,
        "changes": [d for d in diff if d["changed"]]
    }, indent=2)

@mcp.tool()
def get_row(row_id: int) -> str:
    """Retrieve a single customer row by ID."""
    row = get_customer_by_id(row_id)
    if not row:
        return json.dumps({"status": "error", "message": f"Row with ID {row_id} does not exist."})
    return json.dumps({"status": "success", "row": row})

@mcp.tool()
def batch_insert(records_json: str) -> str:
    """Batch insert a list of standardized customer records into the database."""
    try:
        records = json.loads(records_json) if isinstance(records_json, str) else records_json
        count = insert_customers(records)
        return json.dumps({
            "status": "success",
            "inserted_count": count,
            "message": f"Successfully inserted {count} records into the customers table."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to batch insert records: {str(e)}"
        })

@mcp.tool()
async def upload_classify_standardize(
    filename: str,
    file_content_base64: str = "",
    file_content_text: str = "",
    confirmed_mappings_json: str = "{}",
    proceed_with_insert: bool = False
) -> str:
    """
    Complete data-import workflow MCP tool:
    1. Accepts CSV or Excel data through base64 or text.
    2. Rejects unsupported file types with a clear error.
    3. Reads uploaded data on the server into DataFrame.
    4. Matches incoming columns against canonical schema using aliases, keywords & rules.
    5. Calculates confidence scores.
    6. Automatically accepts mappings with confidence >= 90% (0.90).
    7. For mappings < 90%, uses OpenRouter LLM to suggest mappings.
    8. If confidence remains < 90%, returns proposed mappings and clarification questions.
    9. Standardizes column names, dates, phones, and validates records.
    10. Inserts valid standardized records into SQLite only after confirmations are complete.
    11. Returns structured result with mapping decisions, confidence scores, validation summary,
        inserted count, rejected count, and outstanding confirmation requests.
    """
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB limit
    
    # 1. Format check
    fmt = detect_file_format(filename)
    if fmt == 'unknown':
        return json.dumps({
            "status": "error",
            "error_type": "UNSUPPORTED_FORMAT",
            "message": f"Unsupported file format for '{filename}'. Only CSV and Excel (.xlsx, .xls) files are accepted."
        })
    
    # 2. Decode content
    raw_bytes = None
    if file_content_base64:
        try:
            raw_bytes = base64.b64decode(file_content_base64)
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to decode base64 file content: {str(e)}"})
    elif file_content_text:
        raw_bytes = file_content_text.encode('utf-8')
    else:
        return json.dumps({"status": "error", "message": "No file content provided in file_content_base64 or file_content_text."})
    
    if len(raw_bytes) > MAX_FILE_SIZE:
        return json.dumps({"status": "error", "message": f"File exceeds maximum allowed size of 15MB (received {len(raw_bytes)} bytes)."})
    
    # 3. Read data safely in memory
    df = None
    try:
        if fmt == 'csv':
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes))
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding='latin-1')
        elif fmt == 'excel':
            df = pd.read_excel(io.BytesIO(raw_bytes))
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error parsing {fmt.upper()} data: {str(e)}"})
    
    if df is None or df.empty:
        return json.dumps({"status": "error", "message": "Uploaded file is empty or could not be converted to records."})

    # Clean empty rows and strings
    df = clean_dataframe(df)
    if df.empty:
        return json.dumps({"status": "error", "message": "File contains no valid non-empty data rows."})
    
    # Save file metadata to server database
    file_id = save_file_metadata(filename, fmt)

    # 4. Target canonical database columns
    active_cols = get_active_db_columns()
    target_candidates = [c for c in active_cols if c.get("column_name") != "created_at"]
    if not target_candidates:
        target_candidates = STANDARD_COLUMNS

    # User-provided confirmed mappings (if answering clarification questions)
    user_confirmations = {}
    if confirmed_mappings_json:
        try:
            user_confirmations = json.loads(confirmed_mappings_json) if isinstance(confirmed_mappings_json, str) else confirmed_mappings_json
        except Exception:
            user_confirmations = {}

    mapping_decisions = []
    clarification_questions = []
    unconfirmed_columns = []

    for col in df.columns:
        col_str = str(col).strip()
        sample_vals = df[col].dropna().head(5).tolist()

        # Check if user already confirmed mapping for this column
        if col_str in user_confirmations:
            user_target = user_confirmations[col_str]
            mapping_decisions.append({
                "input_column": col_str,
                "standardized_column": user_target,
                "confidence": 1.0,
                "confidence_pct": 100,
                "method": "User Confirmed",
                "reason": "Explicit user confirmation",
                "sample_values": [str(s) for s in sample_vals[:3]],
                "requires_confirmation": False
            })
            continue

        # Step 4 & 5: Match against schema using aliases, keywords & rules
        std_col, conf, reason = keyword_classify_column(col_str, target_candidates, sample_vals)
        method = "Keyword/Alias"

        # Step 6 & 7: If confidence < 90% (0.90), use OpenRouter LLM
        if conf < 0.90:
            llm_std, llm_conf, llm_reason = await llm_classify_column(col_str, sample_vals, target_candidates)
            if llm_std != "none" and llm_conf >= 0.90:
                std_col = llm_std
                conf = llm_conf
                reason = f"OpenRouter LLM: {llm_reason}"
                method = "OpenRouter LLM"
            elif llm_std != "none" and llm_conf > conf:
                std_col = llm_std
                conf = llm_conf
                reason = f"OpenRouter LLM: {llm_reason}"
                method = "OpenRouter LLM"
            else:
                # LLM determined column does not map to schema
                std_col = "none"
                conf = 0.0
                reason = f"OpenRouter LLM: {llm_reason}"
                method = "OpenRouter LLM"

        # Step 8: If still < 90%, require confirmation
        requires_confirm = conf < 0.90
        if requires_confirm:
            unconfirmed_columns.append(col_str)
            suggested = std_col if std_col != "none" else None
            clarification_questions.append({
                "input_column": col_str,
                "suggested_match": suggested,
                "confidence_pct": int(round(conf * 100)),
                "question": f"Column '{col_str}' had low matching confidence ({int(round(conf * 100))}%). Suggested: '{suggested or 'skip'}'. How should it be mapped?",
                "options": [c["column_name"] for c in target_candidates] + ["skip"]
            })
            mapping_decisions.append({
                "input_column": col_str,
                "standardized_column": "skip",
                "suggested_match": suggested,
                "confidence": round(conf, 2),
                "confidence_pct": int(round(conf * 100)),
                "method": "Awaiting User Confirmation",
                "reason": reason,
                "sample_values": [str(s) for s in sample_vals[:3]],
                "requires_confirmation": True
            })
        else:
            mapping_decisions.append({
                "input_column": col_str,
                "standardized_column": std_col,
                "suggested_match": std_col,
                "confidence": round(conf, 2),
                "confidence_pct": int(round(conf * 100)),
                "method": method,
                "reason": reason,
                "sample_values": [str(s) for s in sample_vals[:3]],
                "requires_confirmation": False
            })

    # Extract preview rows for inspection/UI
    preview_df = df.head(5).astype(object).where(pd.notna(df.head(5)), None)
    preview_rows = sanitize_for_json(preview_df.to_dict(orient="records"))

    # If user hasn't explicitly instructed to proceed with insertion, return classification preview
    if not proceed_with_insert:
        return json.dumps({
            "status": "needs_confirmation" if unconfirmed_columns else "ready",
            "file_id": file_id,
            "filename": filename,
            "format": fmt,
            "columns": list(df.columns),
            "total_rows": len(df),
            "preview_rows": preview_rows,
            "classification": mapping_decisions,
            "mapping_decisions": mapping_decisions,
            "unconfirmed_count": len(unconfirmed_columns),
            "requires_user_action": bool(unconfirmed_columns),
            "clarification_questions": clarification_questions,
            "target_columns": [c["column_name"] for c in target_candidates],
            "message": f"Found {len(unconfirmed_columns)} column(s) with confidence below 90% requiring user confirmation." if unconfirmed_columns else "All columns mapped with confidence >= 90%. Ready to standardize and insert.",
            "next_steps": "Call upload_classify_standardize with confirmed_mappings_json and proceed_with_insert=true to ingest into the database."
        }, indent=2)


    # 9. Standardize column names & values
    rename_map = {}
    seen_targets = set()
    for m in mapping_decisions:
        inp = m["input_column"]
        target = m["standardized_column"]
        if target and target != "skip":
            if target not in seen_targets:
                seen_targets.add(target)
                rename_map[inp] = target
                save_column_metadata(file_id, inp, target, "TEXT", m["confidence"], m["method"])

    std_df = df.rename(columns=rename_map)
    std_df = std_df.loc[:, ~std_df.columns.duplicated()].copy()

    # Filter to only known standard columns in schema
    valid_col_names = [c["column_name"] for c in target_candidates]
    cols_to_keep = [c for c in std_df.columns if c in valid_col_names]

    if not cols_to_keep:
        return json.dumps({
            "status": "error",
            "file_id": file_id,
            "filename": filename,
            "mapping_decisions": mapping_decisions,
            "message": "No input columns could be mapped to any standard database columns. No records were stored."
        }, indent=2)

    subset_df = std_df[cols_to_keep].copy()
    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()].copy()

    # Format standardization
    if "signup_date" in subset_df.columns:
        date_col = subset_df["signup_date"]
        if isinstance(date_col, pd.DataFrame):
            date_col = date_col.iloc[:, 0]
        subset_df["signup_date"] = date_col.apply(standardize_single_date)

    if "phone_number" in subset_df.columns:
        phone_col = subset_df["phone_number"]
        if isinstance(phone_col, pd.DataFrame):
            phone_col = phone_col.iloc[:, 0]
        subset_df["phone_number"] = phone_col.apply(standardize_single_phone)

    subset_df = subset_df.where(pd.notna(subset_df), None)
    records = subset_df.to_dict(orient="records")
    records = sanitize_for_json(records)

    # Validate records
    val_report = validate_records(records)
    
    # Filter valid vs rejected records
    invalid_rows_indices = {issue["row"] - 1 for issue in val_report.get("issues", []) if issue.get("column") == "customer_name"}
    valid_records = [r for idx, r in enumerate(records) if idx not in invalid_rows_indices]
    rejected_count = len(records) - len(valid_records)

    # 10. Insert valid standardized records into SQLite
    inserted_count = 0
    if valid_records:
        inserted_count = insert_customers(valid_records)

    # 11. Structured Return
    return json.dumps({
        "status": "success",
        "file_id": file_id,
        "filename": filename,
        "format": fmt,
        "total_rows": len(df),
        "inserted_count": inserted_count,
        "rejected_count": rejected_count,
        "mapping_decisions": mapping_decisions,
        "validation_summary": {
            "total_validated": val_report.get("total_records", 0),
            "valid_records": val_report.get("valid_records", 0),
            "invalid_records": val_report.get("invalid_records", 0),
            "quality_score": val_report.get("quality_score", 100.0),
            "issues_count": len(val_report.get("issues", [])),
            "sample_issues": val_report.get("issues", [])[:5]
        },
        "validation_report": sanitize_for_json(val_report),
        "outstanding_confirmations": clarification_questions if (unconfirmed_columns and proceed_with_insert) else [],
        "message": f"Successfully processed '{filename}': {inserted_count} record(s) inserted into database ({rejected_count} rejected due to missing customer name)."
    }, indent=2)

# Streamable HTTP Application
app = mcp.streamable_http_app(streamable_http_path="/mcp")

def run_server(host: str = "127.0.0.1", port: int = 8001):
    import uvicorn
    init_db()
    print("=" * 70)
    print("  Data Standardization MCP Server (Streamable HTTP)")
    print("=" * 70)
    print(f"  MCP Server Endpoint: http://{host}:{port}/mcp")
    print("  Transport: Streamable HTTP")
    print("  SQLite Database: Exclusively owned and accessed by this server")
    print("  Registered Tools: get_column, check_data, extract_data, validate_data,")
    print("                    add_row, edit_data, delete_row, delete_column,")
    print("                    delete_duplicates, get_row, batch_insert,")
    print("                    upload_classify_standardize")
    print("=" * 70)
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()
