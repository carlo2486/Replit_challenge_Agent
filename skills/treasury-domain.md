# U.S. Treasury Bulletin Domain Knowledge

## Corpus structure
- 697 monthly issues, named `treasury_bulletin_YYYY_MM.txt`
- Parsed as Markdown with pipe-delimited tables (`|col|col|`)
- Covers roughly 1939–2000

## Common table types and search keywords

### Budget expenditures by function
- Keywords: "national defense", "budget expenditures", "functional classification"
- Headers often: `| Function | Month | Cumulative | Year |`
- Annual totals appear in Jan/Feb bulletin of the FOLLOWING year
- Fiscal year data (pre-1977: Jul–Jun) vs calendar year — check the table header

### Budget receipts
- Keywords: "receipts", "individual income tax", "net of refunds"
- Often reported in billions (not millions) — check unit row in table

### Department/agency expenditures
- Keywords: "department", "agency", "expenditures by department"
- Look for tables with a row per department and columns for months/totals
- Highest spender is usually Department of Defense in post-WWII years

### Treasury auction / debt issuance
- Keywords: "public debt", "treasury bills", "treasury notes", "auction results"
- Contains: "total bids", "accepted", "noncompetitive", "foreign", "rollover"
- Auction results appear in bulletin 1–2 months after the auction
- For 2-year notes maturing July 1984: look in bulletins from mid-1984

### Interest on public debt
- Keywords: "net interest", "interest on the public debt", "outlays"
- Reported in both millions (detailed) and billions (summary tables)

## Fiscal year conventions
- Pre-1977: FY starts July 1, ends June 30. FY1955 = Jul 1954 – Jun 1955.
- Post-1977: FY starts Oct 1, ends Sep 30. FY1981 = Oct 1980 – Sep 1981.

## Revision policy
- Later bulletins may revise earlier figures.
- "As reported in [Month YYYY]" means use EXACTLY that bulletin's figure.
- For most tasks without a specific publication date, use the most recently published figure.

## Number formats in tables
- Values in millions of dollars unless header says "billions" or "thousands"
- Negative values shown with minus sign or parentheses: `(123.4)` = -123.4
- Asterisk (*) = revised figure; use this revised value
- "n.a." or "-" = not available
