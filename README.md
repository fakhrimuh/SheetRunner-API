# Excel API Automation

A simple desktop app to run API tests defined in an Excel spreadsheet. Upload an `.xlsx` file containing test cases, the app executes each HTTP request, validates the response, and writes the results back to a new Excel file.

Built with Python + Tkinter, packaged as a native app for **macOS** and **Windows**.

---

## Features

- Define API test cases in Excel — no code required
- One-click execution with a simple GUI
- Validates HTTP status code and response body content
- **Chained requests** — extract values from one response and reuse them in the next via `{{variable}}` placeholders and JSONPath
- Exports results to a new Excel file (Save As dialog)
- Connection pooling via `requests.Session` for faster runs
- Cross-platform: macOS (`.app`) and Windows (`.exe`)

---

## Download

Get the latest build from the [Releases](../../releases) page:

- **macOS** → `ExcelAPI-mac.zip` (unzip, drag `ExcelAPI.app` to Applications)
- **Windows** → `ExcelAPI.exe`

> On macOS, the first launch may require: right-click the app → **Open** → confirm (unsigned build).

---

## Excel Format

Your test file must contain these columns:

| Column                     | Description                   | Example                               |
| -------------------------- | ----------------------------- | ------------------------------------- |
| `TestID`                   | Identifier                    | `TC001`                               |
| `TestName`                 | Description                   | `Login Valid`                         |
| `Method`                   | HTTP method                   | `POST`                                |
| `URL`                      | Endpoint                      | `https://api.example.com/login`       |
| `Headers`                  | JSON object                   | `{"Content-Type":"application/json"}` |
| `Body`                     | JSON body (optional)          | `{"username":"john"}`                 |
| `ExpectedStatus`           | Expected HTTP code            | `200`                                 |
| `ExpectedResponseContains` | Substring to find in response | `token`                               |
| `ExtractVariables`         | _(optional)_ JSON map of variable name → JSONPath, used to save values from this response for later tests | `{"token":"$.token"}` |

After running, the app appends:

| Column           | Description                             |
| ---------------- | --------------------------------------- |
| `ActualStatus`   | Status code returned                    |
| `ActualResponse` | Response body (truncated to 1000 chars) |
| `Result`         | `PASS`, `FAIL`, or `ERROR`              |
| `Notes`          | Reason for failure if any               |

A sample file is included at [testdata/testCase.xlsx](testdata/testCase.xlsx).

---

## Chaining Requests

Many real-world test flows depend on previous responses (login → use token → fetch user → update profile). This app supports chaining via two simple rules:

### Rule 1 — Save a value from a response

In the `ExtractVariables` column, write a JSON map of `variable_name → JSONPath`:

```json
{"authToken": "$.token", "userId": "$.user.id"}
```

The app runs each JSONPath against the response and stores the result.

### Rule 2 — Reuse a saved value

Anywhere in `URL`, `Headers`, or `Body`, wrap the variable name in double curly braces:

```
https://api.example.com/users/{{userId}}/cart
{"Authorization": "Bearer {{authToken}}"}
```

### Full example

| TestID | Method | URL | Headers | Body | ExpectedStatus | ExtractVariables |
|---|---|---|---|---|---|---|
| TC001 | POST | `.../auth/login` | `{"Content-Type":"application/json"}` | `{"username":"john","password":"pwd"}` | 200 | `{"authToken":"$.token"}` |
| TC002 | GET | `.../products` | | | 200 | `{"firstId":"$[0].id"}` |
| TC003 | GET | `.../products/{{firstId}}` | `{"Authorization":"Bearer {{authToken}}"}` | | 200 | `{"category":"$.category"}` |
| TC004 | POST | `.../carts` | `{"Authorization":"Bearer {{authToken}}"}` | `{"productId":{{firstId}},"qty":2}` | 201 | |

### JSONPath cheat sheet

```
$.field             → field at root
$.parent.child      → nested field
$[0]                → first item of root array
$[-1]              → last item of array
$.list[0]          → first item inside "list"
$.list[0].id       → id of first item in "list"
$.a.b[2].c.d       → can nest arbitrarily deep
$..token           → any "token" anywhere in the response
```

### Tips

- **Variable names are free-form** — use anything (`token`, `myUserId`, `bearer`).
- **Numeric values stay numeric** in the JSON body — write `{"id":{{userId}}}` (no quotes around the placeholder).
- **String values need quotes** — write `{"name":"{{userName}}"}`.
- If a referenced variable was never extracted, the placeholder is left as-is and a warning is logged.

---

## Usage

1. Launch the app
2. Click **Upload Excel & Run**
3. Choose your test case file
4. Choose where to save the results
5. Wait for the summary popup

---

## Run from source

Requires Python 3.9+.

```bash
git clone <this-repo>
cd "Excel API"
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt
python -m apps.app
```

## Build the app yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ExcelAPI" \
  --paths . --hidden-import=openpyxl --hidden-import=pandas \
  apps/app.py
```

Output appears in `dist/`. Build must be done on the target OS — PyInstaller does not cross-compile.

---

## Tech Stack

- **Python 3.9+**
- **Tkinter** — GUI
- **pandas + openpyxl** — Excel I/O
- **requests** — HTTP client
- **jsonpath-ng** — JSONPath extraction for chained requests
- **PyInstaller** — packaging
