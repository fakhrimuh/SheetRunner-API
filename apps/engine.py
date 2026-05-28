"""
engine.py - API Testing Engine
Reads test cases from Excel, executes HTTP requests, writes results.
"""

import logging
from typing import Optional

import pandas as pd
import requests

# --- Constants ---
RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_ERROR = "ERROR"

REQUIRED_COLUMNS = ["Method", "URL", "Headers", "Body", "ExpectedStatus", "ExpectedResponseContains"]

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_json_field(value: Optional[str], field_name: str) -> dict:
    """Safely parse JSON from Excel cell."""
    if pd.isna(value) or not value:
        return {}
    try:
        import json
        return json.loads(value)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {field_name}: {e}")
        return {}


def validate_dataframe(df: pd.DataFrame) -> None:
    """Ensure required columns exist."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def execute_request(session: requests.Session, method: str, url: str, 
                    headers: dict, body: dict, timeout: int = 30) -> tuple[int, str, str]:
    """
    Execute HTTP request with error handling.
    Returns: (status_code, response_text, error_message)
    """
    try:
        response = session.request(
            method=method,
            url=url,
            headers=headers,
            json=body if body else None,
            timeout=timeout
        )
        return response.status_code, response.text, ""
    
    except requests.Timeout:
        return 0, "", "Request timed out"
    except requests.ConnectionError:
        return 0, "", "Connection failed"
    except requests.RequestException as e:
        return 0, "", f"Request error: {str(e)}"


def evaluate_result(actual_status: int, expected_status: int,
                    actual_response: str, expected_response: str) -> tuple[str, str]:
    """Compare actual vs expected results."""
    status_match = actual_status == int(expected_status)
    
    expected_clean = str(expected_response).strip().lower() if expected_response else ""
    response_match = expected_clean in actual_response.lower() if expected_clean else True
    
    if status_match and response_match:
        return RESULT_PASS, "Validation successful"
    
    notes = []
    if not status_match:
        notes.append(f"Status: expected {expected_status}, got {actual_status}")
    if not response_match:
        notes.append(f"Response missing: '{expected_response}'")
    
    return RESULT_FAIL, "; ".join(notes)


def run_test(excel_path: str, output_path: str, timeout: int = 30) -> dict:
    """
    Main test runner.
    Returns: Summary dict with pass/fail/error counts.
    """
    logger.info(f"Loading test cases from: {excel_path}")
    
    df = pd.read_excel(excel_path)
    validate_dataframe(df)
    
    # Initialize result columns
    for col in ["ActualStatus", "ActualResponse", "Result", "Notes"]:
        df[col] = ""
    
    summary = {"pass": 0, "fail": 0, "error": 0}
    
    # Use session for connection pooling
    with requests.Session() as session:
        for index, row in df.iterrows():
            logger.info(f"Running test {index + 1}: {row['Method']} {row['URL']}")
            
            headers = parse_json_field(row.get("Headers"), "Headers")
            body = parse_json_field(row.get("Body"), "Body")
            
            status, response, error = execute_request(
                session, row["Method"], row["URL"], headers, body, timeout
            )
            
            if error:
                result, notes = RESULT_ERROR, error
                summary["error"] += 1
            else:
                result, notes = evaluate_result(
                    status, row["ExpectedStatus"],
                    response, row.get("ExpectedResponseContains", "")
                )
                summary["pass" if result == RESULT_PASS else "fail"] += 1
            
            df.at[index, "ActualStatus"] = str(status) if status else "N/A"
            df.at[index, "ActualResponse"] = response[:1000]  # Truncate long responses
            df.at[index, "Result"] = result
            df.at[index, "Notes"] = notes
    
    df.to_excel(output_path, index=False)
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Summary: {summary}")
    
    return summary