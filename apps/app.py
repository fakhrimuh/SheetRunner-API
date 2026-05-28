"""
app.py - GUI for Excel API Automation
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from apps.engine import run_test


def choose_file() -> None:
    """Open file dialog and run tests."""
    filepath = filedialog.askopenfilename(
        title="Select test case file",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    if not filepath:
        return

    default_name = os.path.splitext(os.path.basename(filepath))[0] + "_result.xlsx"
    output = filedialog.asksaveasfilename(
        title="Save results as",
        defaultextension=".xlsx",
        initialfile=default_name,
        filetypes=[("Excel Files", "*.xlsx")]
    )

    if not output:
        return
    
    try:
        summary = run_test(filepath, output)
        
        messagebox.showinfo(
            "Complete",
            f"Results saved to:\n{output}\n\n"
            f"✓ Passed: {summary['pass']}\n"
            f"✗ Failed: {summary['fail']}\n"
            f"⚠ Errors: {summary['error']}"
        )
    except ValueError as e:
        messagebox.showerror("Invalid File", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"Test execution failed:\n{str(e)}")


def main() -> None:
    """Initialize and run the GUI."""
    root = tk.Tk()
    root.title("Excel API Automation")
    root.geometry("400x200")
    root.resizable(False, False)
    
    tk.Label(
        root,
        text="Excel Based API Automation",
        font=("Arial", 14)
    ).pack(pady=20)
    
    tk.Button(
        root,
        text="Upload Excel & Run",
        command=choose_file,
        height=2,
        width=25
    ).pack(pady=20)
    
    root.mainloop()


if __name__ == "__main__":
    main()