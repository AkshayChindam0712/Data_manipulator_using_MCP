# 🛠️ Database Manipulator using Model Context Protocol (MCP)

An intelligent, decoupled database manipulation and data standardization system built on the **Model Context Protocol (MCP)** using **Streamable HTTP transport**. 

This system bridges dirty, heterogeneous tabular datasets (CSV, Excel) into a clean, canonical SQLite database using an 8-step matching pipeline and dual-layer LLM intelligence powered by **Gemini 2.5 via OpenRouter**.

---

## 🏗️ Architecture Overview

The project is architected with a strict separation of concerns into two independent components:

```
┌────────────────────────────────────────────────────────┐
│                      Web Browser                       │
│           Interactive React & Vanilla UI               │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP (Port 8000)
┌───────────────────────────┴────────────────────────────┐
│                       MCP Client                       │
│  • FastAPI Web Server (main.py)                        │
│  • Client-side AI Assistant (OpenRouter Gemini 2.5)    │
│  • Interactive Column Mapper & Value Standardizer     │
│  • MCP Protocol SDK (mcp_client.py)                    │
└───────────────────────────▲────────────────────────────┘
                            │ Streamable HTTP (JSON-RPC)
                            │ Endpoint: http://127.0.0.1:8001/mcp
┌───────────────────────────┴────────────────────────────┐
│                       MCP Server                       │
│  • FastMCP Server Engine (mcp_server.py)               │
│  • 12 Standard Database & Manipulation Tools           │
│  • 8-Step Intelligent Column Matching Pipeline         │
│  • Data Validator & Standardizer (data_processor.py)   │
│  • Exclusive Owner of SQLite Database (database.py)    │
└───────────────────────────▲────────────────────────────┘
                            │ Direct Local Access
┌───────────────────────────┴────────────────────────────┐
│                SQLite Database Storage                 │
│                 (data/database.sqlite)                 │
└────────────────────────────────────────────────────────┘
```

> **Security & Protocol Note**: The MCP Client **never** touches SQLite or runs raw SQL queries. All database queries, insertions, edits, and deletions are strictly negotiated through standard MCP tool calls.

---

## 🌟 Key Features

1. **8-Step Intelligent Column Matching Pipeline**:
   - Automatically maps non-standard column headers (e.g. `Client_Num`, `Cust_ID`, `Mail_ID`, `City_Town`) to canonical database columns.
   - **Order of matching**:
     1. Exact Match (100% confidence)
     2. Predefined Aliases (96% confidence)
     3. Normalized Regex Pattern (95% confidence)
     4. Fuzzy Levenshtein Distance (85%–94% confidence)
     5. Semantic Keyword Matching (82% confidence)
     6. Substring Containment (80% confidence)
     7. OpenRouter LLM Classification (Gemini 2.5, 90%–95% confidence)
     8. User Confirmation fallback (if confidence < 90%)

2. **Automated Value Standardization**:
   - **Names**: Strips honorifics (`Mr.`, `Ms.`, `Dr.`, `Prof.`) and applies proper Title Case.
   - **Cities**: Expands abbreviations (`HYD` ➔ `Hyderabad`, `BLR` ➔ `Bengaluru`, `BOM` ➔ `Mumbai`, `NYC` ➔ `New York`).
   - **Phone Numbers**: Cleans punctuation and formats to standard numeric digits.
   - **Dates**: Converts arbitrary formats (`DD/MM/YYYY`, `MM-DD-YYYY`, Excel timestamps) into standard ISO-8601 `YYYY-MM-DD`.
   - **Emails**: Strips whitespaces, validates format, and converts to lowercase.

3. **12 MCP Tools for Full Database Manipulation**:
   - `upload_classify_standardize`: End-to-end ingest, mapping, validation, and storage.
   - `validate_data`: High-speed schema validation and quality scoring without storing.
   - `extract_data`: Search, filter, and fetch records with pagination.
   - `get_column`: Inspect canonical schema and column definitions.
   - `get_row`: Retrieve a specific customer record by primary key.
   - `check_data`: Audit row counts, missing values, and column summaries.
   - `add_row`: Insert a single standardized record.
   - `batch_insert`: Concurrently standardize and insert multiple records.
   - `edit_data`: Update customer fields with validation.
   - `delete_row`: Delete a single row by ID with confirmation safeguards.
   - `delete_column`: Drop a custom column from the table.
   - `delete_duplicates`: Deduplicate records based on email and name matching.

4. **Interactive Natural Language AI Assistant**:
   - Ask questions like: *"Show all customers from Hyderabad"*, *"Delete duplicates"*, or *"What is our overall data quality score?"*
   - The assistant translates conversational queries into precise MCP tool executions.

---

## 📁 Repository Directory Structure

```text
Database manipulator using MCP/
│
├── .gitignore                    # Root gitignore (protects secrets, venvs, DBs)
├── README.md                     # Comprehensive documentation
│
├── mcp server/                   # MCP Server Subproject
│   ├── .env                      # API keys (GIT IGNORED)
│   ├── .env.example              # Environment template
│   ├── requirements.txt          # Python dependencies
│   ├── data/
│   │   ├── database.sqlite       # Local SQLite database (GIT IGNORED)
│   │   └── sample_*.csv          # Sample testing datasets
│   └── server/
│       ├── mcp_server.py         # Main FastMCP server on port 8001
│       ├── database.py           # SQLite database schema & CRUD functions
│       └── data_processor.py     # Regex & LLM cleaning and validation
│
└── mcp client/                   # MCP Client & Web UI Subproject
    ├── .env                      # API keys & Server URL (GIT IGNORED)
    ├── .env.example              # Environment template
    ├── requirements.txt          # Python dependencies
    ├── client/
    │   ├── main.py               # FastAPI Web Server on port 8000
    │   ├── mcp_client.py         # Streamable HTTP MCP Client SDK
    │   ├── ai_assistant.py       # Conversational AI assistant
    │   └── cli_main.py           # Interactive terminal CLI mode
    └── frontend/
        ├── index.html            # Single Page Application
        ├── app.js                # Core UI logic & data rendering
        └── app.bundle.js         # Compiled UI bundle
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** installed
- An **OpenRouter API Key** (optional, but recommended for intelligent column mapping and AI chat). Get one free at [openrouter.ai](https://openrouter.ai/).

---

### 2. Environment Configuration

Copy the example environment files and add your API key:

#### For MCP Server:
Create `mcp server/.env`:
```ini
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
```

#### For MCP Client:
Create `mcp client/.env`:
```ini
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
MCP_SERVER_URL=http://127.0.0.1:8001/mcp
```

---

### 3. Installation

We recommend using separate Python virtual environments for server and client.

#### Terminal 1 — Setup & Run MCP Server:
```powershell
# Navigate to mcp server
cd "mcp server"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the MCP Server on Port 8001
python server/mcp_server.py
```
> The server will start on `http://127.0.0.1:8001/mcp`.

---

#### Terminal 2 — Setup & Run MCP Client:
```powershell
# Navigate to mcp client
cd "mcp client"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the Web Application on Port 8000
python client/main.py
```

---

### 4. Access the Application
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```
From the web UI, you can:
- **Upload CSV / Excel files**: Watch headers get classified automatically with confidence ratings.
- **Review Confirmation Questions**: Approve or override any uncertain columns before saving.
- **View & Manipulate Records**: Edit inline, delete rows, filter, search, or deduplicate.
- **Chat with AI Assistant**: Issue natural language commands to inspect and update the database.

---

## 🔒 Security & Git Best Practices

When committing to GitHub, sensitive and binary files are automatically excluded by [`.gitignore`](.gitignore):
- **`.env`**: Contains sensitive OpenRouter API keys. Always keep `.env` in `.gitignore` and only commit `.env.example`.
- **`venv/`**: Python virtual environments are local to your machine and must never be committed.
- **`data/*.sqlite`**: SQLite database files are binary and contain local state. Users running the project will have `init_db()` automatically generate a fresh SQLite database upon first run.
- **`__pycache__/`**: Python bytecode files (`.pyc`).

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
