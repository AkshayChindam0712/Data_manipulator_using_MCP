import os
import re
import json
import httpx
import pandas as pd
try:
    from .database import STANDARD_COLUMNS
except ImportError:
    from database import STANDARD_COLUMNS
from dotenv import load_dotenv

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_curr_dir)
load_dotenv()
load_dotenv(os.path.join(_parent_dir, ".env"))

ABBREVIATIONS = {
    "cust": "customer",
    "client": "customer",
    "buyer": "customer",
    "ph": "phone",
    "mob": "mobile",
    "tel": "telephone",
    "addr": "address",
    "loc": "location",
    "dt": "date",
    "nm": "name",
    "num": "number",
    "no": "number"
}

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def detect_file_format(filename: str) -> str:
    filename_lower = filename.lower()
    if filename_lower.endswith('.csv'):
        return 'csv'
    elif filename_lower.endswith(('.xls', '.xlsx')):
        return 'excel'
    return 'unknown'

def read_file(filepath: str, format: str) -> pd.DataFrame:
    try:
        if format == 'csv':
            return pd.read_csv(filepath)
        elif format == 'excel':
            return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
    return None

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Trim strings, handle blank strings, drop completely empty rows."""
    cleaned = df.copy()
    cleaned = cleaned.dropna(how='all')
    for col in cleaned.columns:
        if cleaned[col].dtype == 'object':
            cleaned[col] = cleaned[col].apply(lambda x: str(x).strip() if pd.notnull(x) else None)
            cleaned[col] = cleaned[col].apply(lambda x: None if x == '' or x == 'nan' else x)
    return cleaned

def normalize_text(text: str) -> str:
    """Lowercase, strip, replace delimiters with spaces, remove special characters."""
    t = text.lower().strip()
    t = re.sub(r'[_\-\.\/]+', ' ', t)
    t = re.sub(r'[^a-z0-9\s]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def expand_abbreviations(text: str) -> str:
    """Expand common abbreviations like cust -> customer, ph -> phone, etc."""
    words = normalize_text(text).split()
    expanded = [ABBREVIATIONS.get(w, w) for w in words]
    return " ".join(expanded)

def collapsed_alpha(text: str) -> str:
    """Collapse all characters into a single alphanumeric string for comparison."""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def inspect_sample_data(sample_values: list) -> tuple:
    """
    Inspect sample values to determine if they match email, phone, date, etc.
    Returns: (predicted_column, confidence_score, description)
    """
    if not sample_values:
        return "none", 0.0, "No sample data provided"

    clean_samples = [str(s).strip() for s in sample_values if pd.notnull(s) and str(s).strip() != ""]
    if not clean_samples:
        return "none", 0.0, "Sample data is completely empty"

    total = len(clean_samples)

    # 1. Email Check
    email_matches = sum(1 for s in clean_samples if EMAIL_REGEX.match(s))
    if email_matches / total >= 0.5:
        return "email", 0.96, f"Data values matched email address pattern ({email_matches}/{total} samples)"

    # 2. Date Check (Check date BEFORE phone to prevent ISO/delimited dates from matching digit counts)
    date_matches = 0
    for s in clean_samples:
        if validate_date_val(s) and any(c.isdigit() for c in s) and len(s) >= 4 and not EMAIL_REGEX.match(s):
            date_matches += 1
    if date_matches / total >= 0.5:
        return "signup_date", 0.95, f"Data values matched date pattern ({date_matches}/{total} samples)"

    # 3. Phone Check
    phone_matches = 0
    for s in clean_samples:
        if validate_date_val(s) or EMAIL_REGEX.match(s):
            continue
        digits = re.sub(r'\D', '', s)
        if 7 <= len(digits) <= 15:
            phone_matches += 1
    if phone_matches / total >= 0.5:
        return "phone_number", 0.95, f"Data values matched phone number pattern ({phone_matches}/{total} samples)"

    return "none", 0.0, "Sample data is non-specific"

def keyword_classify_column(input_col: str, standard_columns: list = None, sample_values: list = None) -> tuple:
    """
    Enhanced Column Classification:
    Combines Column Name Normalization + Aliases/Keywords + Sample Data Inspection.
    High confidence (>= 90%) is assigned to standard aliases and recognizable data patterns.
    """
    if standard_columns is None:
        standard_columns = STANDARD_COLUMNS

    norm_input = normalize_text(input_col)
    exp_input = expand_abbreviations(input_col)
    col_input = collapsed_alpha(input_col)

    # 1. Exact match with standardized database column name
    for col in standard_columns:
        target_name = col["column_name"]
        target_norm = normalize_text(target_name)
        target_col = collapsed_alpha(target_name)
        if norm_input == target_norm or col_input == target_col or exp_input == target_norm:
            return target_name, 1.0, f"Exact match with database column '{target_name}'"

    # 2. Match with known aliases
    for col in standard_columns:
        target_name = col["column_name"]
        raw_aliases = col.get("aliases", [])
        
        for alias in raw_aliases:
            alias_norm = normalize_text(alias)
            alias_exp = expand_abbreviations(alias)
            alias_col = collapsed_alpha(alias)

            # Check full match, expanded match, or collapsed match
            if norm_input == alias_norm or exp_input == alias_norm or exp_input == alias_exp or col_input == alias_col:
                return target_name, 0.96, f"Matched standard alias '{alias}' for '{target_name}'"

    # 3. Inspect Sample Values to resolve or boost confidence
    if sample_values:
        sample_pred, sample_conf, sample_reason = inspect_sample_data(sample_values)
        if sample_pred != "none" and sample_conf >= 0.90:
            # Check if input column has any relation (e.g. Contact, Detail, Tele, Mail)
            return sample_pred, sample_conf, f"Sample data strongly matches {sample_pred} ({sample_reason})"

    # 4. Partial token overlap across aliases
    best_candidate = "none"
    best_score = 0.0
    best_reason = "No match"

    input_words = set(exp_input.split())
    for col in standard_columns:
        target_name = col["column_name"]
        for alias in col.get("aliases", []):
            alias_words = set(expand_abbreviations(alias).split())
            if input_words and alias_words:
                overlap = len(input_words & alias_words) / max(len(input_words), len(alias_words))
                if overlap > best_score:
                    best_score = overlap
                    best_candidate = target_name
                    best_reason = f"Partial match with alias '{alias}'"

    if best_score >= 0.65:
        score = round(0.70 + (best_score * 0.18), 2)
        # If samples also mildly corroborate
        return best_candidate, score, best_reason

    return "none", 0.30, "No clear keyword or alias match found"

async def llm_classify_column(input_col: str, sample_values: list, standard_columns: list = None) -> tuple:
    """
    Step 2: If keyword & sample confidence is below 90%, send to OpenRouter LLM.
    Returns: (matched_column_name, confidence_score, explanation)
    """
    if standard_columns is None:
        standard_columns = STANDARD_COLUMNS

    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key or openrouter_api_key == "your_openrouter_api_key_here":
        return "none", 0.0, "OpenRouter API Key not configured"

    schema_info = []
    for col in standard_columns:
        schema_info.append(
            f"- '{col['column_name']}': {col['description']}. Data type: {col['data_type']}. "
            f"Known aliases: {col.get('aliases', [])}. Sample valid values: {col.get('sample_values', [])}"
        )
    schema_text = "\n".join(schema_info)

    clean_samples = [str(s) for s in sample_values if pd.notnull(s) and str(s).strip()][:5]

    prompt = f"""You are a database data standardization expert.
We have a target database table with these standardized columns:
{schema_text}

An uploaded file has an input column named: '{input_col}'
Sample values from this column: {clean_samples}

Task:
Determine which target database column this input column maps to, or 'none' if it does not fit any.
Calculate your confidence score between 0.00 and 1.00 (e.g. 0.94 for strong match, 0.65 for weak/ambiguous match).

Respond strictly in valid JSON format:
{{
  "matched_column": "target_column_name_or_none",
  "confidence": 0.94,
  "reasoning": "brief explanation"
}}
"""

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "MCP Data Standardization System"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1000
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                return "none", 0.0, f"Local mode fallback (LLM returned status {resp.status_code})"
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            parsed = json.loads(content)
            matched = parsed.get("matched_column", "none")
            conf = float(parsed.get("confidence", 0.0))
            reasoning = parsed.get("reasoning", "LLM classification")
            
            valid_targets = [c["column_name"] for c in standard_columns] + ["none"]
            if matched not in valid_targets:
                matched = "none"

            return matched, conf, reasoning
    except Exception as e:
        print(f"LLM Classification error for column '{input_col}': {e}")
        return "none", 0.0, f"LLM error: {str(e)}"

def validate_email_val(val) -> bool:
    if val is None:
        return True
    if isinstance(val, (pd.Series, list)):
        return False
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    return bool(EMAIL_REGEX.match(str(val).strip()))

def validate_phone_val(val) -> bool:
    if val is None:
        return True
    if isinstance(val, (pd.Series, list)):
        return False
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    s = str(val).strip()
    if not s or s.lower() in ('none', 'nan', 'null', 'nat'):
        return True
    # An ISO date string is not a phone number
    if re.match(r'^\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2}$', s):
        return False
    digits = re.sub(r'\D', '', s)
    return 7 <= len(digits) <= 15

def validate_date_val(val) -> bool:
    if val is None:
        return True
    if isinstance(val, (pd.Series, list)):
        return False
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    s = str(val).strip()
    if not s or s.lower() in ('none', 'nan', 'null', 'nat'):
        return True
    # Ensure there is a date delimiter or it has standard length
    if not re.search(r'[\-\/\.]', s) and not (len(s) == 8 and s.isdigit()):
        return False
    try:
        pd.to_datetime(s)
        return True
    except Exception:
        return False

def standardize_single_date(val):
    if val is None:
        return None
    if isinstance(val, (pd.Series, list)):
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    s = str(val).strip()
    if not s or s.lower() in ('none', 'nan', 'null', 'nat'):
        return None
    try:
        dt = pd.to_datetime(s)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return s

def standardize_single_phone(val):
    if val is None:
        return None
    if isinstance(val, (pd.Series, list)):
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    s = str(val).strip()
    if not s or s.lower() in ('none', 'nan', 'null', 'nat'):
        return None
    digits = re.sub(r'\D', '', s)
    return digits if digits else s

def validate_records(records: list) -> dict:
    total = len(records)
    if total == 0:
        return {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "issues": [],
            "quality_score": 100.0
        }

    issues = []
    invalid_rows = set()

    for idx, r in enumerate(records):
        row_num = idx + 1
        name = r.get("customer_name")
        if not name or str(name).strip() == "":
            issues.append({"row": row_num, "column": "customer_name", "error": "Customer name is missing or empty"})
            invalid_rows.add(idx)

        email = r.get("email")
        if email and not validate_email_val(email):
            issues.append({"row": row_num, "column": "email", "error": f"Invalid email format: '{email}'"})
            invalid_rows.add(idx)

        phone = r.get("phone_number")
        if phone and not validate_phone_val(phone):
            issues.append({"row": row_num, "column": "phone_number", "error": f"Invalid phone format: '{phone}'"})
            invalid_rows.add(idx)

        date_val = r.get("signup_date")
        if date_val and not validate_date_val(date_val):
            issues.append({"row": row_num, "column": "signup_date", "error": f"Invalid date value: '{date_val}'"})
            invalid_rows.add(idx)

    invalid_count = len(invalid_rows)
    valid_count = total - invalid_count
    quality_score = max(0.0, round(((valid_count / total) * 100.0) - (len(issues) * 2.0), 2))

    return {
        "total_records": total,
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "issues": issues,
        "quality_score": quality_score
    }
