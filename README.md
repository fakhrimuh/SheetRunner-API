# Excel API Automation

A simple desktop app to run API tests defined in an Excel spreadsheet. Upload an `.xlsx` file containing test cases, the app executes each HTTP request, validates the response, and writes the results back to a new Excel file.

Built with Python + Tkinter, packaged as a native app for **macOS** and **Windows**.

---

## Features

- Define API test cases in Excel — no code required
- One-click execution with a simple GUI
- Validates HTTP status code and response body content
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

After running, the app appends:

| Column           | Description                             |
| ---------------- | --------------------------------------- |
| `ActualStatus`   | Status code returned                    |
| `ActualResponse` | Response body (truncated to 1000 chars) |
| `Result`         | `PASS`, `FAIL`, or `ERROR`              |
| `Notes`          | Reason for failure if any               |

A sample file is included at [testdata/testCase.xlsx](testdata/testCase.xlsx).

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
- **PyInstaller** — packaging
