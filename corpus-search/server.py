"""Corpus search MCP server for OfficeQA.

Provides tools to efficiently search, read, and extract data from the
697 U.S. Treasury Bulletin files at /app/corpus/.
"""

import json
import math
import os
import re
import subprocess
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("corpus-search")

CORPUS_DIR = Path("/app/corpus")
INDEX_FILE = CORPUS_DIR / "index.txt"
ANSWER_FILE = Path("/app/answer.txt")


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
def search_corpus(keyword: str, context_lines: int = 5, max_results: int = 30) -> str:
    """Search all Treasury Bulletin files for a keyword and return matching lines with context.

    Use this to find which bulletins contain specific financial data
    (e.g., "national defense", "expenditures", "receipts").

    Args:
        keyword: Search term (case-insensitive). Use specific phrases like
                 "national defense" or "total expenditures".
        context_lines: Number of lines of context to show around each match (default 5).
        max_results: Maximum number of matches to return (default 30).
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "-i", "-n", f"--context={context_lines}", keyword, str(CORPUS_DIR)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = result.stdout.splitlines()
        if len(lines) > max_results * (context_lines * 2 + 2):
            lines = lines[: max_results * (context_lines * 2 + 2)]
            lines.append(f"\n... (truncated, {len(result.stdout.splitlines())} total lines matched)")
        return "\n".join(lines) if lines else f"No matches found for '{keyword}'"
    except subprocess.TimeoutExpired:
        return "Search timed out — try a more specific keyword"


@mcp.tool()
def search_bulletin(filename: str, keyword: str, context_lines: int = 10) -> str:
    """Search a single Treasury Bulletin file for a keyword with surrounding context.

    Use this to drill into a specific bulletin after identifying it with search_corpus.

    Args:
        filename: Bulletin filename, e.g. 'treasury_bulletin_1941_01.txt'
        keyword: Search term (case-insensitive).
        context_lines: Lines of context around each match (default 10).
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    try:
        result = subprocess.run(
            ["grep", "-i", "-n", f"--context={context_lines}", keyword, str(filepath)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout if result.stdout else f"No matches for '{keyword}' in {filename}"
    except subprocess.TimeoutExpired:
        return "Search timed out"


@mcp.tool()
def read_bulletin(filename: str, start_line: int = 1, end_line: int = 200) -> str:
    """Read a section of a Treasury Bulletin file by line range.

    Use this to read tables or sections in full after locating them with search tools.

    Args:
        filename: Bulletin filename, e.g. 'treasury_bulletin_1941_01.txt'
        start_line: First line to read (1-indexed, default 1).
        end_line: Last line to read (default 200). Increase for large tables.
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    lines = filepath.read_text().splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    end = min(total, end_line)
    selected = lines[start:end]
    header = f"[{filename} — lines {start+1}–{end} of {total}]\n"
    return header + "\n".join(selected)


@mcp.tool()
def extract_tables(filename: str, keyword: str, table_context: int = 60) -> str:
    """Extract markdown tables near a keyword match in a bulletin file.

    Finds the keyword, then returns the surrounding block likely to contain
    the full table (rows starting with '|').

    Args:
        filename: Bulletin filename, e.g. 'treasury_bulletin_1941_01.txt'
        keyword: Keyword to locate the table (case-insensitive).
        table_context: Number of lines to scan around the match for table rows (default 60).
    """
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        return f"File not found: {filename}"
    lines = filepath.read_text().splitlines()
    results = []
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            start = max(0, i - 5)
            end = min(len(lines), i + table_context)
            block = lines[start:end]
            table_lines = [
                l for l in block if l.strip().startswith("|") or l.strip().startswith("#") or keyword.lower() in l.lower()
            ]
            results.append(f"[Match at line {i+1}]\n" + "\n".join(block))
            if len(results) >= 3:
                break
    return "\n\n---\n\n".join(results) if results else f"No matches for '{keyword}' in {filename}"


@mcp.tool()
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.

    Supports: +, -, *, /, **, sqrt(), log(), sum([...]), round(), abs(), geometric_mean([...]).

    Args:
        expression: A Python-safe math expression, e.g.
                    'sum([1234.5, 678.9, 432.1])'
                    'round((1234.5 * 678.9) ** (1/2), 2)'
                    'geometric_mean([100, 200, 400])'
    """
    def geometric_mean(values):
        n = len(values)
        return math.exp(sum(math.log(v) for v in values) / n)

    safe_globals = {
        "__builtins__": {},
        "sum": sum,
        "round": round,
        "abs": abs,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pow": pow,
        "math": math,
        "geometric_mean": geometric_mean,
    }
    try:
        result = eval(expression, safe_globals)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def write_answer(answer: str) -> str:
    """Write the final answer to /app/answer.txt.

    Call this ONCE when you are confident in your answer.
    Write only the numerical value — no units, dollar signs, or commas.

    Args:
        answer: The final numerical answer as a string, e.g. '1234.56' or '9876'
    """
    cleaned = answer.strip().replace(",", "").replace("$", "")
    ANSWER_FILE.write_text(cleaned + "\n")
    return f"Answer written: {cleaned}"
