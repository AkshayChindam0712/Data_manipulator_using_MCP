# MCP-Based Data Standardization and Database Management System

A web application that standardizes tabular data (CSV/Excel) according to an existing SQLite database schema using keyword/alias matching, OpenRouter LLM classification, user verification, and Model Context Protocol (MCP) tools.

---

## Architecture

```text
Website (HTML, CSS, JS)
       ↓
FastAPI + Uvicorn Backend
       ↓
MCP Client
       ↓
MCP Server
       ↓
MCP Tools (check_data, extract_data, validate_data, get_column, add_row, delete_row, delete_column)
       ↓
SQLite Database (customers table) / Pandas / OpenRouter LLM
```

---

## 3 Main Modules on Website

### 1. Input CSV / Excel Files
- Upload CSV and Excel (`.xlsx`, `.xls`) files with automatic format detection.
- Raw data preview (first 5 records).
- **Enhanced Column Classification Workflow**:
  1. **Advanced Normalization**: Handles lowercase, strips delimiters (`_`, `-`, `/`), collapses alphanumeric strings, and expands abbreviations (`cust` &rarr; `customer`, `ph`/`mob` &rarr; `phone`, `addr` &rarr; `address`, etc.).
  2. **Comprehensive Alias Library**: Standard aliases for names, emails, phones, cities, and dates.
  3. **Sample Data Pattern Inspection**: Automatically detects email formats, phone digits, and dates in the sample values to boost confidence to **≥ 90%** automatically for standard columns.
  4. **OpenRouter LLM Fallback**: If confidence is **< 90%**, sends column name, target schema context, and data samples to OpenRouter LLM.
  5. **User Confirmation Interface**: If confidence remains **< 90%**, alerts the user with an interactive dropdown to confirm or manually select the target column.
- Cleans data (trims whitespace, formats YYYY-MM-DD dates, cleans phone digits).
- Standardizes and inserts records into SQLite `customers` table.

### 2. MCP Tools to Access Database
Execute all **7 MCP tools** directly from the UI:
1. **`check_data`**: Checks missing values, duplicate records, invalid formats (email, phone, dates), and calculates overall data quality score.
2. **`extract_data`**: Searches, filters, and retrieves records from the database, rendered as a **clean, human-readable table**.
3. **`validate_data`**: Validates records against standardized column types and rules.
4. **`get_column`**: Returns database schema, column names, data types, aliases, and sample values.
5. **`add_row`**: Standardizes, validates, and adds a single row manually without uploading a file.
6. **`delete_row`**: Safely deletes a specific record by its unique ID with safety confirmation protection.
7. **`delete_column`**: Safely drops a selected column from the database after confirmation.

### 3. Print Database
- Live view of the standardized SQLite database table.
- Total record counter.
- Search and filter bar across all fields.
- Real-time refresh button.

---

## Target Database Schema (`customers` table)

| Standardized Column | Data Type | Known Aliases | Sample Valid Value |
|---------------------|-----------|---------------|-------------------|
| `customer_name` | TEXT | `customer`, `customer name`, `cust_name`, `cust name`, `client name`, `name`, `full name`, `buyer` | John Doe |
| `email` | TEXT | `email`, `email address`, `e-mail`, `mail`, `mail id`, `contact email` | john@gmail.com |
| `phone_number` | TEXT | `phone`, `mobile`, `contact number`, `telephone`, `tel`, `phone no`, `cell` | 9876543210 |
| `city` | TEXT | `city`, `town`, `location`, `residence`, `city name`, `metro` | Hyderabad |
| `signup_date` | TEXT | `date`, `created date`, `registered_date`, `signup date`, `join date`, `timestamp` | 2023-01-15 |

---

## Independent Architecture: Server & Client Separation

The backend is separated into two decoupled components:
- `backend/server/`: Contains the independent MCP Server, SQLite database connection logic, SQLite operations, data classification/validation rules, and tool definitions. Exclusively owns and manages `data/database.sqlite`.
- `backend/client/`: Contains the independent MCP Client (`mcp_client.py`), AI Assistant LLM intent controller (`ai_assistant.py`), interactive CLI (`run_client.py`), Streamable HTTP transport connection logic, dynamic tool discovery, interactive command handling, and result rendering. Never connects to SQLite or executes SQL.

```
TERMINAL 1 (MCP Server)        <--- Streamable HTTP --->        TERMINAL 2 (MCP Client)
(Port 8001 /mcp)                                                 (Interactive CLI)
Exclusive SQLite Owner                                           Zero Database Imports
Hosts all MCP Tools                                              Natural Language Commands
```

---

## Setup & Running Independently

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure OpenRouter API Key
Secrets are maintained in the existing `.env` file on the server side:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 3. Terminal 1 — Start the Independent MCP Server
Run `mcp_server.py` directly to start the MCP server:
```powershell
.\venv\Scripts\python.exe backend/server/mcp_server.py
```
> Server initializes SQLite and listens at: `http://127.0.0.1:8001/mcp`

### 4. Terminal 2 — Start the Independent MCP Client
Run `mcp_client.py` (or `main.py`) directly to start the interactive client:
```powershell
.\venv\Scripts\python.exe backend/client/mcp_client.py
```
*(Or `.\venv\Scripts\python.exe backend/client/main.py`)*
> Connects to the server, dynamically discovers tools, and enters the natural-language command loop.

### 5. Terminal 3 (Optional) — Start the Website / FastAPI Dashboard
The existing FastAPI website and dashboard run separately via Uvicorn without starting or initializing the MCP server:
```powershell
.\venv\Scripts\uvicorn.exe backend.main:app --reload --port 8000
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## Sample Test Files Included

- **`data/sample_1_clients.csv`**: Contains `Customer`, `Contact Number`, `Mail`, `City`, `Date`.
- **`data/sample_2_customers.csv`**: Contains `Client Name`, `Phone No`, `Email Address`, `Town`, `Created_At`.
- **`data/sample_3_uncertain.csv`**: Contains `Cust_Name`, `Phone`, `Client Info`, `Location`, `Timestamp`.
- **`data/sample_4_excel.xlsx`**: Excel workbook with `Customer`, `Mobile`, `E-mail`, `City`, `Signup Date`.
