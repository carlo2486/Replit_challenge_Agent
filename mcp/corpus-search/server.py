"""Corpus search MCP server for OfficeQA.

Provides tools to efficiently search, read, and extract data from the
697 U.S. Treasury Bulletin files at /app/corpus/.
"""

import math
import os
import subprocess
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("corpus-search")

CORPUS_DIR  = Path("/app/corpus")
INDEX_FILE  = CORPUS_DIR / "index.txt"
ANSWER_FILE = Path("/app/answer.txt")


# ── Corpus navigation ────────────────────────────────────────────────────────

@mcp.tool()
def list_bulletins() -> str:
    """List all available Treasury Bulletin files in the corpus.

    Returns a sorted list of filenames so you can identify which
    bulletins cover the time period you need.
    """
    if not INDEX_FILE.exists():
        files = sorted(CORPUS_DIR.glob("treasury_bulletin_*.txt"))
        return "\n".join(f.name for f in files)
    return INDEX_FILE.read_text()


@mcp.tool()
def find_bulletins_for_period(start_year: int, end_year: int) -> str:
    """Return bulletin filenames that fall within a year range (inclusive).

    Useful for narrowing down which files to search before calling
    search_corpus or extract_tables.

    Args:
        start_year: First year to include (e.g. 1940).
        end_year:   Last year to include (e.g. 1955).
    """
    files = sorted(CORPUS_DIR.glob("treasury_bulletin_*.txt"))
    matched = []
    for f in files:
        parts = f.stem.split("_")
        if len(parts) >= 3:
            try:
                year = int(parts[2])
                if start_year <= year <= end_year:
                    matched.append(f.name)
            except ValueError:
                pass
    return "\n".join(matched) if matched else f"No bulletins found for {start_year}–{end_year}"


@mcp.tool()
def search_corpus(keyword: str, context_lines: int = 20, max_results: int = 50) -> str:
    """Search ALL Treasury Bulletin files for a keyword with surrounding context.

    Use this first to identify which bulletins contain your target data.

    Args:
        keyword: Case-insensitive search term, e.g. 'national defense', 'net interest'.
        context_lines: Lines of context around each match (default 20).
        max_results: Max matches to return (default 50).
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "-i", "-n", f"--context={context_lines}", keyword, str(CORPUS_DIR)],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.splitlines()
        cap = max_results * (context_lines * 2 + 2)
        if len(lines) > cap:
            total = len(lines)
            lines = lines[:cap]
            lines.append(f"\n... (truncated — {total} total lines matched, use a more specific keyword)")
        return "\n".join(lines) if lines else f"No matches found for '{keyword}'"
    except subprocess.TimeoutExpired:
        return "Search timed out — try a more specific keyword"


@mcp.tool()
def search_bulletin(filename: str, keyword: str, context_lines: int = 10) -> str:
    """Search a single bulletin file for a keyword with surrounding context.

    Use after search_corpus identifies promising files.

    Args:
        filename: e.g. 'treasury_bulletin_1941_01.txt'
        keyword: Case-insensitive search term.
        context_lines: Lines of context (default 10).
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    try:
        result = subprocess.run(
            ["grep", "-i", "-n", f"--context={context_lines}", keyword, str(filepath)],
            capture_output=True, text=True, timeout=15,
        )
        return result.stdout if result.stdout else f"No matches for '{keyword}' in {filename}"
    except subprocess.TimeoutExpired:
        return "Search timed out"


@mcp.tool()
def read_bulletin(filename: str, start_line: int = 1, end_line: int = 500) -> str:
    """Read a section of a bulletin file by line range.

    Args:
        filename: e.g. 'treasury_bulletin_1941_01.txt'
        start_line: First line (1-indexed, default 1).
        end_line: Last line (default 500). Increase for large tables.
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    lines = filepath.read_text().splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    end   = min(total, end_line)
    header = f"[{filename} — lines {start+1}–{end} of {total}]\n"
    return header + "\n".join(lines[start:end])


@mcp.tool()
def extract_tables(filename: str, keyword: str, table_context: int = 100) -> str:
    """Extract markdown tables near a keyword match in a bulletin file.

    Finds up to 3 keyword matches and returns the full surrounding block
    (rows starting with '|').

    Args:
        filename: e.g. 'treasury_bulletin_1941_01.txt'
        keyword: Keyword to locate the table (case-insensitive).
        table_context: Lines to scan around the match (default 100).
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    lines   = filepath.read_text().splitlines()
    results = []
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            start = max(0, i - 5)
            end   = min(len(lines), i + table_context)
            results.append(f"[Match at line {i+1}]\n" + "\n".join(lines[start:end]))
            if len(results) >= 3:
                break
    return "\n\n---\n\n".join(results) if results else f"No matches for '{keyword}' in {filename}"


@mcp.tool()
def extract_column_values(table_text: str, column_header: str) -> str:
    """Extract values from a specific column in markdown table text.

    Parses pipe-delimited table rows and returns values from the column
    matching the header (case-insensitive partial match).

    Useful for extracting individual month values vs cumulative totals.

    Args:
        table_text: Markdown table text (from extract_tables or read_bulletin).
        column_header: Column header to match (e.g., 'individual', 'monthly', 'cumulative').
    Returns:
        Comma-separated values from matching column, or error message.
    """
    import re
    if not table_text or not column_header:
        return "Error: both table_text and column_header are required"

    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return "Error: table must have at least a header row and one data row"

    # Find header row (first line with |)
    header_line = None
    for line in lines:
        if '|' in line:
            header_line = line
            break

    if not header_line:
        return "Error: no table header found"

    # Parse headers
    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    headers_lower = [h.lower() for h in headers]

    # Find matching column - prefer exact match first
    col_idx = None
    header_lower = column_header.lower()
    
    # First pass: exact match
    for i, h in enumerate(headers_lower):
        if h == header_lower:
            col_idx = i
            break
    
    # Second pass: partial match (original behavior)
    if col_idx is None:
        for i, h in enumerate(headers_lower):
            if header_lower in h:
                col_idx = i
                break

    if col_idx is None:
        return f"Error: column '{column_header}' not found. Available columns: {headers}"

    # Extract values from matching column
    values = []
    for line in lines[1:]:  # Skip header
        if '|' in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if col_idx < len(cells):
                val = cells[col_idx]
                # Skip separator lines (---)
                if not re.match(r'^-+$', val):
                    values.append(val)

    if not values:
        return f"Error: no values found in column '{column_header}'"

    return ", ".join(values)


# ── Math & statistics ────────────────────────────────────────────────────────

@mcp.tool()
def calculate(expression: str) -> str:
    """Safely evaluate a math expression. Uses conventional rounding (0.5 rounds up).

    Available functions: sum, round, abs, min, max, sqrt, log, log10, exp, pow,
    geometric_mean, percent_change, box_cox, percent_change_signed.

    Args:
        expression: Python-safe math expression, e.g.
            'sum([100.0, 200.0, 300.0])'
            'geometric_mean([500.1, 520.3, 498.7])'
            'percent_change(old=1200.0, new=1500.0)'
            'percent_change_signed(old=1200.0, new=1500.0)'
            'box_cox(value=51.5, lam=0.75)'
            'round(1234.5678, 2)'
    """
    def geometric_mean(values):
        # Filter positive values only, skip 0 and negatives
        positive_values = [v for v in values if v > 0]
        if not positive_values:
            raise ValueError("geometric_mean requires at least one positive value")
        n = len(positive_values)
        return math.exp(sum(math.log(v) for v in positive_values) / n)

    def conventional_round(value, ndigits=0):
        multiplier = 10 ** ndigits
        return math.floor(value * multiplier + 0.5) / multiplier

    def percent_change(old, new):
        """Absolute percent change: abs((new - old) / old) * 100"""
        if old == 0:
            raise ValueError("percent_change undefined when old value is 0")
        return abs((new - old) / old) * 100

    def percent_change_signed(old, new):
        """Signed percent change: ((new - old) / old) * 100"""
        if old == 0:
            raise ValueError("percent_change undefined when old value is 0")
        return ((new - old) / old) * 100

    def box_cox(value, lam):
        """Box-Cox transformation: (value^lambda - 1) / lambda, or log(value) if lambda==0."""
        if lam == 0:
            return math.log(value)
        return (value ** lam - 1) / lam

    safe_globals = {
        "__builtins__": {},
        "sum": sum, "round": conventional_round, "abs": abs,
        "min": min, "max": max, "sqrt": math.sqrt,
        "log": math.log, "log10": math.log10, "exp": math.exp,
        "pow": pow, "math": math,
        "geometric_mean": geometric_mean,
        "percent_change": percent_change,
        "percent_change_signed": percent_change_signed,
        "box_cox": box_cox,
    }
    try:
        result = eval(expression, safe_globals)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def linear_regression(x_values: list, y_values: list, decimal_places: int = 6) -> str:
    """Fit an Ordinary Least Squares (OLS) linear regression and return slope + intercept.

    Args:
        x_values: List of predictor values (e.g. years [1929, 1930, ...]).
        y_values: List of outcome values (e.g. receipts in billions).
        decimal_places: Number of decimal places for rounding (default 6).

    Returns:
        JSON string: {"slope": ..., "intercept": ...}
        Use this result with calculate() to round to the required precision.
    """
    import json
    n = len(x_values)
    if n != len(y_values) or n < 2:
        return json.dumps({"error": "x_values and y_values must be equal length lists with at least 2 points"})
    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n
    ss_xy  = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
    ss_xx  = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    if ss_xx == 0:
        return json.dumps({"error": "all x values are identical — cannot fit regression"})
    slope     = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    
    # Use conventional rounding (0.5 rounds up), not banker's rounding
    multiplier = 10 ** decimal_places
    slope_rounded = math.floor(slope * multiplier + 0.5) / multiplier
    intercept_rounded = math.floor(intercept * multiplier + 0.5) / multiplier
    
    return json.dumps({"slope": slope_rounded, "intercept": intercept_rounded})


# ── Output ───────────────────────────────────────────────────────────────────

@mcp.tool()
def parse_regression(json_str: str) -> str:
    """Parse JSON output from linear_regression and extract slope and intercept.

    Args:
        json_str: JSON string from linear_regression output, e.g.
            '{"slope": 0.123456, "intercept": -4.567890}'

    Returns:
        Human-readable string with slope and intercept values.
    """
    import json
    try:
        data = json.loads(json_str)
        if "error" in data:
            return f"Error: {data['error']}"
        return f"slope={data['slope']}, intercept={data['intercept']}"
    except Exception as e:
        return f"Error parsing JSON: {e}"

@mcp.tool()
def write_answer(answer: str) -> str:
    """Write the final answer to /app/answer.txt.

    IMPORTANT formatting rules:
    - Single number:  '1234.56'          (no $, no units)
    - Percentage:     '12.34%'           (keep the % symbol)
    - Multi-value:    '[0.123, -4.567]'  (keep brackets AND comma between values)
    - Two sub-answers:'[1234567, 12.34%]'(keep brackets AND comma)
    Thousand-separator commas (e.g. 1,234,567) are stripped automatically.

    Args:
        answer: Final answer string.
    """
    import re
    s = answer.strip()
    if s.startswith("[") and s.endswith("]"):
        # Strip thousand-separator commas first (digit,digit{3}), THEN split on separating commas
        inner = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s[1:-1])
        parts = [p.strip().replace("$", "") for p in inner.split(",")]
        cleaned = "[" + ", ".join(parts) + "]"
    else:
        cleaned = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s).replace("$", "")
    ANSWER_FILE.write_text(cleaned + "\n")
    return f"Answer written: {cleaned}"
