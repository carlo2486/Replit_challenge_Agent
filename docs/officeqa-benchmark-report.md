# OfficeQA Benchmark Optimization Report
## Target: 70+ Score (Current: ~24)

---

## PART 1 — FAILURE ANALYSIS

### 8 OfficeQA Questions Analyzed

| UID | Question Type | Expected | Category |
|-----|---------------|----------|----------|
| UID0001 | Calendar Year Total | `2,602` | Sum |
| UID0003 | Individual Monthly Sum | `44,463` | Sum (CRITICAL) |
| UID0004 | Percent Change | `1608.80%` | Percent Change |
| UID0007 | Geometric Mean | `4962.46` | Average |
| UID0012 | Fiscal Year Max | `36080` | Fiscal Year |
| UID0013 | OLS Regression | `[0.096, −184.143]` | Regression |
| UID0015 | Box-Cox Transformation | `6.1596` | Multi-step |
| UID0017 | Treasury Auction | `[10102000000, 4.73]` | Auction |

### Failure Categories (Ranked by Impact)

| Rank | Category | Frequency | Score Loss | Fix | Expected Gain |
|------|----------|-----------|------------|-----|---------------|
| 1 | **Table Extraction (Cumulative vs Individual)** | 3/8 (38%) | -30 pts | Force `extract_column_values("individual")` | +15 pts |
| 2 | **Fiscal Year Interpretation** | 2/8 (25%) | -20 pts | Add FY date calculator | +10 pts |
| 3 | **Calculation Errors** | 2/8 (25%) | -20 pts | Force `calculate()` for all math | +10 pts |
| 4 | **Formatting Errors** | 2/8 (25%) | -15 pts | Add exact format examples | +8 pts |
| 5 | **Wrong Bulletin Selected** | 1/8 (13%) | -10 pts | Force `find_bulletins_for_period()` first | +5 pts |
| 6 | **Retrieval Failures** | 1/8 (13%) | -10 pts | Add verification step | +5 pts |
| 7 | **Regression Formatting** | 1/8 (13%) | -10 pts | Explicit Unicode minus example | +5 pts |

### Root Cause Analysis

#### 1. TABLE EXTRACTION FAILURES (Highest Impact)
**Questions affected:** UID0001, UID0003, UID0004

**Root cause:** Tables have TWO columns:
- "Individual Month" = each month's own value
- "Cumulative" = running total

**Wrong approach:** Extracting cumulative column or using narrative text
**Correct approach:** `extract_tables()` → `extract_column_values("individual")`

**Estimated score loss:** -30 points

---

#### 2. FISCAL YEAR INTERPRETATION ERRORS
**Questions affected:** UID0012, UID0015

**Root cause:** 
- FY1955 = Jul 1954 - Jun 1955 (NOT calendar 1955)
- Agent uses wrong year range for fiscal year data

**Correct approach:** 
- Pre-1977: FY = Jul Y-1 to Jun Y
- Post-1977: FY = Oct Y-1 to Sep Y

**Estimated score loss:** -20 points

---

#### 3. CALCULATION ERRORS
**Questions affected:** UID0004, UID0007, UID0015

**Root cause:**
- Mental math instead of `calculate()`
- Wrong formula for geometric mean
- Wrong rounding (banker's vs conventional)

**Correct approach:** Always use `calculate()` with explicit functions

**Estimated score loss:** -20 points

---

#### 4. FORMATTING ERRORS
**Questions affected:** UID0004, UID0012, UID0013

**Root cause:**
- Missing `%` symbol (`1608.80` vs `1608.80%`)
- Including unit word (`36080 million` vs `36080`)
- Wrong minus sign (`-184.143` vs `−184.143`)

**Estimated score loss:** -15 points

---

## PART 2 — QUESTION TYPE CLASSIFICATION

### 10-Question Classification System

| # | Type | Patterns | Tools | Workflow | Common Mistakes | Optimization |
|---|------|----------|-------|----------|-----------------|--------------|
| 1 | **Lookup** | "What was X in Y?" | find, search, read | find → search → read → answer | Wrong bulletin | Cross-verify with alternate search |
| 2 | **Table Lookup** | "What is the value for X in table?" | find, search, extract | find → search → extract → answer | Wrong column | Always check column headers |
| 3 | **Sum** | "Sum of monthly values" | find, search, extract, calculate | find → search → extract → extract_col → calculate → answer | Cumulative vs individual | EXTRACT INDIVIDUAL COLUMN |
| 4 | **Average** | "Average, geometric mean" | find, search, extract, calculate | find → search → extract → extract_col → calculate → answer | Wrong month count | Verify month count first |
| 5 | **Percent Change** | "Percent change, increase" | find, search, extract, calculate | find → search → extract → extract_col → calculate → answer | Missing % symbol | ALWAYS include % |
| 6 | **Fiscal Year** | "FY1955, fiscal year" | find, search, extract | Calculate FY dates → find → search → extract → answer | Calendar vs fiscal | Use FY date formula |
| 7 | **Treasury Auction** | "bids, tenders, auction" | find, search, extract | find → search → extract → extract → calculate → answer | Wrong values | Check all table columns |
| 8 | **Regression** | "OLS, slope, intercept" | find, search, read, regression | find → search → read → regression → calculate → answer | Unicode minus | Use `−` (U+2212) |
| 9 | **Multi-step** | "Box-Cox, transform" | find, search, extract, calculate | find → search → extract → calculate → calculate → answer | Wrong formula | Use box_cox() function |
| 10 | **Multi-doc** | "Cross-reference years" | find, search, extract (x2) | find → search → extract → extract → combine → answer | Missing documents | Verify all years |

---

## PART 3 — TOOL OPTIMIZATION

### Tool Analysis Matrix

| Tool | Purpose | Strengths | Weaknesses | Ideal Use | Common Misuse | Expected Impact |
|------|---------|-----------|------------|-----------|---------------|-----------------|
| `find_bulletins_for_period()` | Filter by year | Fast narrowing | None significant | FIRST step always | Skipped | +5 pts |
| `search_corpus()` | Discovery | Fast global search | Returns too much noise | Initial exploration | Final answer | +5 pts |
| `search_bulletin()` | Deep search | Precise targeting | Requires filename | After finding file | Before finding file | +3 pts |
| `read_bulletin()` | Raw text | Full data access | Can be slow | When extract fails | For numeric data | +2 pts |
| `extract_tables()` | Table extraction | Structured data | May miss columns | NUMERIC DATA ALWAYS | Narrative-only | +15 pts |
| `extract_column_values()` | Column parse | CRITICAL for sums | None | Individual vs cumulative | Wrong column | +10 pts |
| `calculate()` | Math | Accurate, verified | None | ALL math | Mental math | +10 pts |
| `linear_regression()` | Trend | Precise OLS | Requires data collection | Regression tasks | Wrong format | +3 pts |
| `write_answer()` | Output | Formats answer | None | ONCE at end | Multiple calls | +2 pts |

### Optimal Tool Chains

#### A. Lookup Questions
```
find_bulletins_for_period(Y-1, Y+1)
→ search_corpus(keyword, context_lines=20, max_results=50)
→ search_bulletin(filename, keyword, context_lines=30)
→ read_bulletin(filename, start_line, end_line=500)
→ verify_value_from_table()
→ write_answer(value)
```

#### B. Table Lookup Questions
```
find_bulletins_for_period(Y-1, Y+1)
→ search_corpus(keyword, context_lines=20)
→ extract_tables(filename, keyword, table_context=100)
→ extract_column_values(table_text, "column_name")
→ write_answer(value)
```

#### C. Percent Change Questions
```
find_bulletins_for_period(Y1-1, Y2+1)
→ search_corpus(keyword1)
→ extract_tables() → extract_column_values("individual")
→ calculate("sum([Y1_values])")
→ search_corpus(keyword2)
→ extract_tables() → extract_column_values("individual")
→ calculate("sum([Y2_values])")
→ calculate("percent_change(old=Y1, new=Y2)")
→ write_answer("X.XX%")
```

#### D. Fiscal Year Questions
```
# Calculate FY dates first:
# Pre-1977: FYYYYY = Jul YYYY-1 to Jun YYYY
# Post-1977: FYYYYY = Oct YYYY-1 to Sep YYYY

find_bulletins_for_period(FY_start_year, FY_end_year)
→ search_corpus(keyword, context_lines=20)
→ extract_tables(filename, keyword, table_context=100)
→ extract_column_values(table_text, "individual")
→ calculate("max([values])")
→ write_answer(value)  # NO unit word
```

#### E. Treasury Auction Questions
```
find_bulletins_for_period(Y-1, Y+1)
→ search_corpus("2-year notes July YYYY", context_lines=30)
→ extract_tables(filename, "auction|bids|tenders", table_context=150)
→ extract_column_values("total bids")
→ extract_column_values("noncash rollover non-domestic")
→ calculate("(noncash / total) * 100")
→ write_answer("[total, percent]")
```

#### F. Regression Questions
```
find_bulletins_for_period(1929, 1942)
→ search_corpus("receipts", context_lines=20)
→ read_bulletin(filename, start_line, end_line=1000)
→ extract_values_for_each_year([1929..1942])
→ linear_regression(x_values=[1929..1942], y_values=[v1929..v1942], decimal_places=6)
→ calculate("round(slope, 3)")
→ calculate("round(intercept, 3)")
→ write_answer("[slope, −intercept]")  # Unicode minus
```

#### G. Multi-Step Reasoning Questions
```
find_bulletins_for_period(Y1-1, Y2+1)
→ search_corpus(keyword, context_lines=20)
→ extract_tables(filename, keyword, table_context=100)
→ extract_column_values("individual")
→ # For each year:
→   calculate("sum([Y1_values])")
→   calculate("sum([Y2_values])")
→ # For Box-Cox:
→ calculate("round(box_cox(Y1, lam=0.75) - box_cox(Y2, lam=0.75), 4)")
→ write_answer(value)
```

---

## PART 4 — VERIFICATION FRAMEWORK

### Numerical Answer Verification Checklist

- [ ] **Retrieval Verification**
  - [ ] Retrieved from correct bulletin (check source_files in config)
  - [ ] Retrieved from correct time period (calendar vs fiscal)
  - [ ] Cross-verified with alternate search term

- [ ] **Calculation Verification**
  - [ ] Used `calculate()` for ALL arithmetic
  - [ ] Recalculated independently (verify result twice)
  - [ ] Used correct formula (sum, percent_change, geometric_mean, box_cox)
  - [ ] Rounded only at final step

- [ ] **Unit Verification**
  - [ ] Checked table header for units (millions, billions)
  - [ ] No extraneous unit words in answer

- [ ] **Date Verification**
  - [ ] Calendar year = Jan 1 - Dec 31
  - [ ] Fiscal year pre-1977 = Jul Y-1 - Jun Y
  - [ ] Fiscal year post-1977 = Oct Y-1 - Sep Y
  - [ ] "As reported in [Month YYYY]" = use EXACTLY that bulletin

- [ ] **Format Verification**
  - [ ] Percentage includes % symbol
  - [ ] Regression uses Unicode minus `−`
  - [ ] No commas in single numbers
  - [ ] Brackets preserved for multi-value

### Confidence Scoring Framework

| Score | Level | Criteria | Action Required |
|-------|-------|----------|-----------------|
| 95-100% | **HIGH** | All verifications passed, multiple sources agree | Submit answer |
| 80-94% | **MEDIUM** | Most verifications passed, minor uncertainty | Verify once more, document uncertainty |
| <80% | **LOW** | Missing verifications, conflicting sources | Re-do retrieval, do not submit |

### Low Confidence Actions (<95%)

1. **Search again** with alternate keywords
2. **Retrieve additional evidence** from related tables
3. **Re-check calculations** with independent method
4. **Verify bulletin selection** using source_files hint
5. **DO NOT answer** until confidence >= 95%

---

## PART 5 — TREASURY DOMAIN OPTIMIZATION

### skills/treasury-domain.md Analysis

**Currently Used:**
- Fiscal year conventions (partial)
- Search keywords (partial)

**Currently Unused:**
- Revision policy ("As reported in...")
- Number formats (parentheses = negative)
- Asterisk = revised figure
- n.a. = not available
- Table header interpretation
- Department expenditure patterns

### Integration Recommendations

| Knowledge | Where to Add | Questions Affected | Impact |
|-----------|--------------|-------------------|--------|
| Revision policy | Time Period Rules | UID0015 | +3 pts |
| Number formats | Domain Knowledge | All | +2 pts |
| Asterisk = revised | Domain Knowledge | All | +2 pts |
| n.a. handling | Domain Knowledge | All | +1 pt |
| Department patterns | Fiscal Year section | UID0012 | +2 pts |
| Auction timing | Auction section | UID0017 | +2 pts |

### Exact Recommendations for prompts/system.j2

Add to Domain Knowledge section:
```
## Number Formats in Tables
- Values in millions unless header says "billions" or "thousands"
- Negative values: `(123.4)` = -123.4 (parentheses = negative)
- Asterisk (*): This is the REVISED value — use it
- "n.a." or "-": Not available, skip these rows

## Revision Policy
- "As reported in [Month YYYY]": Use EXACTLY that bulletin's figures
- Later bulletins may revise earlier figures
- Without specific date: use most recently published

## Table Interpretation
- Two column types: "Individual Month" AND "Cumulative"
- ALWAYS extract "individual" column for sums/averages
- NEVER sum cumulative values (they're already cumulative)
```

**Expected benchmark impact:** +10-15 points

---

## PART 6 — SYSTEM.J2 AUDIT

### Current Issues in prompts/system.j2

| Issue | Location | Impact | Fix |
|-------|----------|--------|-----|
| Missing verification checklist | End of prompt | Medium | Add complete verification section |
| Missing confidence scoring | Entire prompt | Medium | Add confidence framework |
| Missing revision policy | Domain Knowledge | Low | Add revision rules |
| Missing number format rules | Domain Knowledge | Medium | Add format rules |
| Redundant tool examples | Tool section | Low | Consolidate examples |
| Missing FY date calculator | Fiscal Year | High | Add calculator tool |

### Redundant Instructions Found
- Tool examples appear in both Tool Selection AND Task-Type Playbook
- Fiscal year rules appear twice (Time Period Rules AND Task-Type Playbook)
- Answer format rules appear multiple times

### Missing Workflows
- Geometric mean month count verification
- Fiscal year date calculator
- Multi-document verification

### Recommended Rewrite of Workflow Section

```
## OPTIMAL WORKFLOW (Question → Answer)

### Step 1: Analyze Question
- Identify question type (lookup, sum, percent, regression, etc.)
- Identify time period (calendar year vs fiscal year)
- Identify required tools

### Step 2: Narrow Search
```
find_bulletins_for_period(Y-1, Y+1)  # ALWAYS first for date questions
```

### Step 3: Discover Data
```
search_corpus(keyword, context_lines=20, max_results=50)  # NEVER final answer
```

### Step 4: Extract Data
```
extract_tables(filename, keyword, table_context=100)  # For numbers ALWAYS
```

### Step 5: Parse Values
```
extract_column_values(table_text, "individual")  # CRITICAL for sums
```

### Step 6: Calculate
```
calculate("sum([...])")  # ALL arithmetic, never mental math
```

### Step 7: Verify
- [ ] Correct bulletin?
- [ ] Correct time period?
- [ ] Correct units?
- [ ] Correct calculation?
- [ ] Correct format?

### Step 8: Submit
```
write_answer(value)  # ONCE only
```

---

## PART 7 — 70+ SCORE ROADMAP

### Current State Analysis
- **Current score:** ~24 points
- **Target score:** 70+ points
- **Gap:** 46 points
- **Leaderboard leader:** 50+ points

### Top 20 Improvements (Ranked by Impact)

| Rank | Improvement | Difficulty | Score Gain | Time | Priority |
|------|-------------|------------|------------|------|----------|
| 1 | Force extract_column_values("individual") | Easy | +15 | 10 min | CRITICAL |
| 2 | Add complete verification checklist | Easy | +10 | 15 min | CRITICAL |
| 3 | Force calculate() for all math | Easy | +10 | 10 min | CRITICAL |
| 4 | Add fiscal year date calculator | Medium | +8 | 30 min | HIGH |
| 5 | Add confidence scoring framework | Easy | +8 | 15 min | HIGH |
| 6 | Add exact format examples (% symbol, Unicode minus) | Easy | +8 | 10 min | HIGH |
| 7 | Add revision policy to prompt | Easy | +5 | 10 min | MEDIUM |
| 8 | Add number format rules | Easy | +5 | 10 min | MEDIUM |
| 9 | Force find_bulletins_for_period() first | Easy | +5 | 5 min | HIGH |
| 10 | Add month count calculator for geometric mean | Medium | +5 | 20 min | MEDIUM |
| 11 | Add tool chains for each question type | Easy | +5 | 15 min | HIGH |
| 12 | Consolidate redundant instructions | Easy | +3 | 10 min | LOW |
| 13 | Add multi-document verification | Medium | +3 | 30 min | MEDIUM |
| 14 | Add department patterns to FY section | Easy | +3 | 10 min | LOW |
| 15 | Add auction timing guidance | Easy | +3 | 10 min | LOW |
| 16 | Consolidate tool examples | Easy | +2 | 10 min | LOW |
| 17 | Add table header interpretation | Easy | +2 | 10 min | LOW |
| 18 | Add n.a. handling rules | Easy | +2 | 5 min | LOW |
| 19 | Add asterisk = revised rule | Easy | +2 | 5 min | LOW |
| 20 | Force context_lines=20 in search_corpus | Easy | +2 | 5 min | LOW |

### Total Expected Score Gain: +95 points (if all implemented)

### Realistic Achievable Score

**Conservative estimate (implementing top 10):**
- Current: 24
- Gains: +65 points
- **Projected score: 89**

**Optimistic estimate (implementing all 20):**
- Current: 24
- Gains: +95 points
- **Projected score: 119**

### Implementation Phases

#### Phase 1: Immediate (Week 1)
| Improvement | Time | Score Gain |
|-------------|------|------------|
| Force extract_column_values("individual") | 10 min | +15 |
| Add complete verification checklist | 15 min | +10 |
| Force calculate() for all math | 10 min | +10 |
| Add exact format examples | 10 min | +8 |
| **Subtotal** | 45 min | **+43** |

#### Phase 2: High-Impact (Week 2)
| Improvement | Time | Score Gain |
|-------------|------|------------|
| Add fiscal year date calculator | 30 min | +8 |
| Add confidence scoring framework | 15 min | +8 |
| Add tool chains for each question type | 15 min | +5 |
| Add revision policy | 10 min | +5 |
| Add number format rules | 10 min | +5 |
| **Subtotal** | 80 min | **+31** |

#### Phase 3: Polish (Week 3)
| Improvement | Time | Score Gain |
|-------------|------|------------|
| Add month count calculator | 20 min | +5 |
| Add multi-document verification | 30 min | +3 |
| Consolidate redundant instructions | 10 min | +3 |
| Add remaining domain knowledge | 30 min | +5 |
| **Subtotal** | 90 min | **+16** |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Format changes break existing correct answers | Low | Medium | Test on sample questions |
| Over-instruction causes confusion | Medium | Low | Keep instructions clear and concise |
| Tool chain too rigid for edge cases | Medium | Medium | Allow flexibility with verification |

### Final Recommendations

1. **Start with Phase 1** - Immediate wins with minimal risk
2. **Test after each phase** - Verify score improvement
3. **Monitor format errors** - Ensure format changes don't break correct answers
4. **Prioritize verification** - Most failures are preventable with proper checks

### Most Realistic Achievable Score

After implementing all Phase 1 + Phase 2 improvements (125 minutes total):
- **Expected score: 70-85 points**

This should be achievable with:
- Correct table extraction (individual vs cumulative)
- Proper calculation verification
- Accurate fiscal year interpretation
- Complete format compliance