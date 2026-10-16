import sqlite3
import pandas as pd
import numpy as np
import json
import math
import os
import re
_curr_dir = os.path.dirname(os.path.abspath(__file__))
_proj_root = os.path.dirname(_curr_dir)
DATA_DIR = os.path.join(_proj_root, 'data')
DB_PATH = os.path.join(DATA_DIR, 'database.sqlite')

def sanitize_for_json(data):
    """
    Recursively sanitize data structures to be strictly JSON-compliant:
    - NaN and Inf are converted to None (rendered as JSON null).
    - Pandas/NumPy NA/NaT types are converted to None.
    - Does not return the string 'NaN'.
    """
    if data is None:
        return None
    elif isinstance(data, (float, np.floating)):
        if math.isnan(data) or math.isinf(data):
            return None
        return float(data)
    elif isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_json(item) for item in data]
    elif pd.isna(data):
        return None
    return data

STANDARD_COLUMNS = [
    {
        "column_name": "id",
        "data_type": "INTEGER",
        "aliases": [
            "id", "customer_id", "cust_id", "customer id", "cust id", "client_id", 
            "client id", "user_id", "user id", "account_id", "account id", "acc_id", 
            "id_number", "id number", "id_no", "id no", "identifier", "unique_id", 
            "unique id", "uid", "record_id", "record id", "row_id", "row id", 
            "customer_number", "cust_no", "customer no", "serial_number", "sno", 
            "s_no", "sr_no", "index", "id#", "cust_num", "client_no", "user_no", 
            "cid", "uid_no", "custid", "clientid", "userid", "customer-id", "client-id"
        ],
        "sample_values": [1, 2, 3, 101],
        "description": "Unique record identifier"
    },
    {
        "column_name": "customer_name",
        "data_type": "TEXT",
        "aliases": [
            "customer", "customer name", "customer_name", "cust name", "cust_name", 
            "customername", "client", "client name", "client_name", "clientname", 
            "buyer", "buyer name", "full name", "fullname", "name", "customer full name",
            "customer-name", "contact person", "user name", "username", "cust", "cust_nm",
            "client info", "client_info", "customer info", "customer_info"
        ],
        "sample_values": ["John Doe", "Jane Smith", "Alice Cooper"],
        "description": "Full name of the customer"
    },
    {
        "column_name": "email",
        "data_type": "TEXT",
        "aliases": [
            "email", "email address", "email_address", "e-mail", "e-mail address", 
            "mail", "mail id", "mail_id", "email id", "emailid", "contact email", 
            "email-address", "customer email", "e_mail", "inbox"
        ],
        "sample_values": ["john@gmail.com", "jane@company.org", "alice@gmail.com"],
        "description": "Electronic mail address"
    },
    {
        "column_name": "phone_number",
        "data_type": "TEXT",
        "aliases": [
            "phone", "phone number", "phone_number", "mobile", "mobile number", 
            "mobile_number", "contact number", "contact_number", "telephone", 
            "telephone number", "tel", "phone no", "phone_no", "mobile no", 
            "mobile_no", "contact", "contact no", "ph", "mob", "cell", "phone-number",
            "cell number", "cellphone", "ph_no", "contact_num"
        ],
        "sample_values": ["9876543210", "+1-555-0199", "555-123-4567"],
        "description": "Primary phone/mobile number"
    },
    {
        "column_name": "city",
        "data_type": "TEXT",
        "aliases": [
            "city", "town", "city name", "location city", "customer city", 
            "location", "residence", "metro", "place", "city_name", "address_city"
        ],
        "sample_values": ["Hyderabad", "New York", "Mumbai", "London"],
        "description": "City or geographical location"
    },
    {
        "column_name": "signup_date",
        "data_type": "TEXT",
        "aliases": [
            "date", "created date", "creation date", "order date", "transaction date", 
            "date created", "timestamp", "signup date", "signup_date", "join date", 
            "join_date", "registered date", "registration date", "dob", "created_at", 
            "registered_at", "record date", "entry date", "joined", "joining date",
            "joined date", "joined_date", "joining_date", "join"
        ],
        "sample_values": ["2023-01-15", "2024-06-01", "2022-11-20"],
        "description": "Date of registration in YYYY-MM-DD format"
    }
]

def get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    
    # Standard customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            email TEXT,
            phone_number TEXT,
            city TEXT,
            signup_date TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Files metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            format TEXT,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Column classification history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            original_name TEXT,
            standardized_name TEXT,
            inferred_type TEXT,
            confidence REAL,
            source TEXT,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
    ''')

    # Seed sample customers if table is empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        sample_records = [
            ("John Doe", "john@gmail.com", "9876543210", "Hyderabad", "2023-01-15"),
            ("Jane Smith", "jane@yahoo.com", "9123456780", "Mumbai", "2023-02-20"),
            ("Alice Cooper", "alice@corp.com", "9988776655", "Bangalore", "2023-03-10")
        ]
        cursor.executemany("""
            INSERT INTO customers (customer_name, email, phone_number, city, signup_date)
            VALUES (?, ?, ?, ?, ?)
        """, sample_records)
    
    conn.commit()
    conn.close()

def save_file_metadata(filename, file_format):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (filename, format) VALUES (?, ?)", (filename, file_format))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def save_column_metadata(file_id, original, std, inferred_type, conf, source):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO file_columns (file_id, original_name, standardized_name, inferred_type, confidence, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_id, original, std, inferred_type, conf, source))
    conn.commit()
    conn.close()

def insert_customers(records: list):
    """Insert a list of standardized customer dicts into the customers table."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active columns from customers table
    cursor.execute("PRAGMA table_info(customers)")
    active_cols = [row["name"] for row in cursor.fetchall() if row["name"] not in ["id", "created_at"]]
    
    inserted_count = 0
    for r in records:
        cols_to_insert = [c for c in active_cols if c in r and r[c] is not None]
        if not cols_to_insert:
            # If standard known columns match
            cols_to_insert = [c for c in ["customer_name", "email", "phone_number", "city", "signup_date"] if c in active_cols and c in r]
        
        if cols_to_insert:
            placeholders = ", ".join(["?"] * len(cols_to_insert))
            col_names = ", ".join(cols_to_insert)
            values = tuple(r.get(c) for c in cols_to_insert)
            cursor.execute(f"INSERT INTO customers ({col_names}) VALUES ({placeholders})", values)
            inserted_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count

def get_customer_by_id(row_id: int) -> dict:
    """Retrieve a single customer row by unique ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (row_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return sanitize_for_json(dict(row))

def update_customer_row(row_id: int, updates: dict) -> dict:
    """Update column values for a specific row by unique ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (row_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": f"Row with ID {row_id} does not exist in the database."}
        
    cursor.execute("PRAGMA table_info(customers)")
    cols = [r["name"] for r in cursor.fetchall()]
    valid_updates = {k: v for k, v in updates.items() if k in cols and k not in ['id', 'created_at']}
    
    if not valid_updates:
        conn.close()
        return {"success": False, "message": "No valid column values provided for update."}
        
    set_clause = ", ".join([f"{k} = ?" for k in valid_updates.keys()])
    values = list(valid_updates.values()) + [row_id]
    
    cursor.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", values)
    conn.commit()
    
    cursor.execute("SELECT * FROM customers WHERE id = ?", (row_id,))
    updated = cursor.fetchone()
    conn.close()
    
    return {
        "success": True,
        "message": f"Row #{row_id} updated successfully.",
        "updated_row": sanitize_for_json(dict(updated))
    }

def delete_customer_row(row_id: int) -> dict:
    """Delete a specific row from the database using its unique ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, customer_name, email FROM customers WHERE id = ?", (row_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": f"Row with ID {row_id} does not exist in the database."}
        
    cursor.execute("DELETE FROM customers WHERE id = ?", (row_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted == 1:
        name_desc = row["customer_name"] or row["email"] or f"ID {row_id}"
        return {"success": True, "message": f"Row #{row_id} ('{name_desc}') was safely deleted."}
    return {"success": False, "message": "Failed to delete the specified row."}

def delete_customer_column(column_name: str) -> dict:
    """Safely delete a column from the customers table."""
    col_clean = column_name.strip()
    if col_clean.lower() in ['id', 'created_at']:
        return {"success": False, "message": f"Protected column '{col_clean}' cannot be deleted."}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(customers)")
    cols = [row["name"] for row in cursor.fetchall()]
    
    if col_clean not in cols:
        conn.close()
        return {"success": False, "message": f"Column '{col_clean}' does not exist in the database."}

    try:
        cursor.execute(f"ALTER TABLE customers DROP COLUMN {col_clean}")
        conn.commit()
        
        # Also remove from memory STANDARD_COLUMNS if present
        global STANDARD_COLUMNS
        STANDARD_COLUMNS = [c for c in STANDARD_COLUMNS if c["column_name"] != col_clean]
        
        conn.close()
        return {"success": True, "message": f"Column '{col_clean}' was successfully removed from the database."}
    except Exception as e:
        conn.close()
        return {"success": False, "message": f"Failed to drop column '{col_clean}': {str(e)}"}

def get_active_db_columns() -> list:
    """Inspect the database and return currently existing columns for the customers table."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(customers)")
    cols_info = cursor.fetchall()
    conn.close()
    
    result = []
    for c in cols_info:
        name = c["name"]
        # Find matching schema if any
        matching_meta = next((sc for sc in STANDARD_COLUMNS if sc["column_name"] == name), None)
        if matching_meta:
            result.append(matching_meta)
        else:
            result.append({
                "column_name": name,
                "data_type": c["type"] or "TEXT",
                "aliases": [name.lower(), name.replace("_", " ").lower()],
                "sample_values": [],
                "description": f"Custom column '{name}'"
            })
    return result

def query_db(query, params=()):
    conn = get_db()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        df = df.astype(object).where(pd.notna(df), None)
        records = sanitize_for_json(df.to_dict(orient='records'))
        return records
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def execute_db(query, params=()):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def delete_duplicate_customers(table_name: str = "customers") -> dict:
    """
    Find and delete duplicate records from the database table, keeping the first occurrence.
    Returns success status, count of deleted rows, and list of deleted IDs.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [row["name"] for row in cursor.fetchall()]
    content_cols = [c for c in cols if c not in ['id', 'created_at']]

    if not content_cols:
        conn.close()
        return {"success": True, "deleted_count": 0, "message": "No content columns available to evaluate duplicates."}

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    if len(df) == 0:
        conn.close()
        return {"success": True, "deleted_count": 0, "message": "Table is empty, no duplicates found."}

    dup_mask = df.duplicated(subset=content_cols, keep='first')
    dup_ids = [int(i) for i in df[dup_mask]['id'].tolist()]

    if not dup_ids:
        conn.close()
        return {"success": True, "deleted_count": 0, "message": "No duplicate records found."}

    placeholders = ",".join(["?"] * len(dup_ids))
    cursor.execute(f"DELETE FROM {table_name} WHERE id IN ({placeholders})", dup_ids)
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return {
        "success": True,
        "deleted_count": deleted_count,
        "deleted_ids": dup_ids,
        "message": f"Successfully deleted {deleted_count} duplicate record(s)."
    }

def search_customers_by_name(customer_name: str) -> list:
    """
    Search customers by customer_name using case-insensitive pattern match.
    Uses remove spacing for keyword matching in database to get details even without spacing
    (e.g. searching 'sairaja' matches 'sai raja').
    Returns matched customer records.
    """
    conn = get_db()
    cursor = conn.cursor()
    clean_term = customer_name.strip()
    nospace_term = re.sub(r'\s+', '', clean_term)
    term_std = f"%{clean_term}%"
    term_nospace = f"%{nospace_term}%"
    
    cursor.execute("""
        SELECT * FROM customers 
        WHERE customer_name LIKE ? 
           OR REPLACE(customer_name, ' ', '') LIKE ?
        ORDER BY id DESC LIMIT 50
    """, (term_std, term_nospace))
    rows = cursor.fetchall()
    conn.close()
    return sanitize_for_json([dict(r) for r in rows])

