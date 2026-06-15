"""
engine.py - API Testing Engine
Reads test cases from Excel, executes HTTP requests, writes results.
Supports request chaining via {{variable}} substitution and JSONPath extraction.
"""

import json
import logging
import re
from typing import Optional

import pandas as pd
import requests
from jsonpath_ng.ext import parse as jsonpath_parse

# --- Constants ---
RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_ERROR = "ERROR"

REQUIRED_COLUMNS = ["Method", "URL", "Headers", "Body", "ExpectedStatus", "ExpectedResponseContains"]

VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def substitute_variables(text, variables: dict):
    """Replace every {{name}} in text with variables[name] (as string)."""
    if text is None or pd.isna(text) or not isinstance(text, str):
        return text

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in variables:
            logger.warning(f"Variable '{{{{{name}}}}}' not defined; leaving placeholder as-is")
            return match.group(0)
        return str(variables[name])

    return VAR_PATTERN.sub(replace, text)


def parse_json_field(value: Optional[str], field_name: str) -> dict:
    """Safely parse JSON from Excel cell."""
    if pd.isna(value) or not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {field_name}: {e}")
        return {}


def extract_variables(response_text: str, extract_config, variables: dict) -> None:
    """Apply JSONPath expressions to the response and store results in variables."""
    if extract_config is None or pd.isna(extract_config) or not str(extract_config).strip():
        return

    try:
        config = json.loads(extract_config)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in ExtractVariables: {e}")
        return

    try:
        response_json = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Response is not valid JSON; cannot extract variables")
        return

    for var_name, path in config.items():
        try:
            matches = jsonpath_parse(path).find(response_json)
            if matches:
                variables[var_name] = matches[0].value
                logger.info(f"Extracted {var_name} = {matches[0].value!r}")
            else:
                logger.warning(f"JSONPath '{path}' for '{var_name}' found no match")
        except Exception as e:
            logger.warning(f"Failed to extract '{var_name}' using path '{path}': {e}")


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

    if expected_response is None or pd.isna(expected_response):
        expected_clean = ""
    else:
        expected_clean = str(expected_response).strip().lower()
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
    variables: dict = {}  # Shared store for chained requests

    # Use session for connection pooling
    with requests.Session() as session:
        for index, row in df.iterrows():
            logger.info(f"Running test {index + 1}: {row['Method']} {row['URL']}")

            # Substitute {{var}} placeholders BEFORE parsing JSON
            raw_url = substitute_variables(str(row["URL"]), variables)
            raw_headers = substitute_variables(row.get("Headers"), variables)
            raw_body = substitute_variables(row.get("Body"), variables)

            headers = parse_json_field(raw_headers, "Headers")
            body = parse_json_field(raw_body, "Body")

            status, response, error = execute_request(
                session, row["Method"], raw_url, headers, body, timeout
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

                # Extract variables from successful response for later tests
                if "ExtractVariables" in df.columns:
                    extract_variables(response, row.get("ExtractVariables"), variables)

            df.at[index, "ActualStatus"] = str(status) if status else "N/A"
            df.at[index, "ActualResponse"] = response[:1000]  # Truncate long responses
            df.at[index, "Result"] = result
            df.at[index, "Notes"] = notes

    df.to_excel(output_path, index=False)
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Summary: {summary}")

    return summary
