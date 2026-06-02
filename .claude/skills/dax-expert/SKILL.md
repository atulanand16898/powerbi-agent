# DAX Expert Skill

## Description
Expert in DAX (Data Analysis Expressions) for Power BI and Analysis Services.
Load this skill when the user asks about DAX formulas, measures, calculated
columns, time intelligence, CALCULATE, context transition, or formula errors.

---

## Core Concepts

### Filter Context vs Row Context
- **Filter context**: What filters are active (from slicers, visuals, CALCULATE)
- **Row context**: The current row being evaluated (in calculated columns, iterators)
- **Context transition**: When CALCULATE converts row context into filter context

### CALCULATE — The Most Important Function
```dax
CALCULATE(<expression>, <filter1>, <filter2>, ...)
```
- Modifies the filter context before evaluating the expression
- Filters are AND'd together (all must be true)
- Use ALL(), REMOVEFILTERS() to clear filters

---

## Common Patterns

### Basic Aggregations
```dax
Total Sales = SUM(Sales[Amount])
Average Price = AVERAGE(Sales[UnitPrice])
Order Count = COUNTROWS(Sales)
Distinct Customers = DISTINCTCOUNT(Sales[CustomerID])
```

### Conditional Aggregation
```dax
Sales in Category A =
CALCULATE(
    SUM(Sales[Amount]),
    Products[Category] = "A"
)
```

### Time Intelligence
```dax
-- Year-to-Date
YTD Sales = CALCULATE(SUM(Sales[Amount]), DATESYTD('Date'[Date]))

-- Previous Year
PY Sales = CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR('Date'[Date]))

-- Year-over-Year Growth %
YoY Growth % =
VAR CurrentYear = SUM(Sales[Amount])
VAR PreviousYear = CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0)

-- Rolling 12 Months
Rolling 12M =
CALCULATE(
    SUM(Sales[Amount]),
    DATESINPERIOD('Date'[Date], LASTDATE('Date'[Date]), -12, MONTH)
)
```

### Iterator Functions
```dax
-- Use SUMX when you need row-by-row calculation
Revenue = SUMX(Sales, Sales[Qty] * Sales[UnitPrice])

-- Weighted Average
Weighted Avg Price = DIVIDE(SUMX(Sales, Sales[Qty] * Sales[Price]), SUM(Sales[Qty]))
```

### Variables (Always Use These)
```dax
-- VAR avoids repeated context evaluation and improves readability
Profit Margin =
VAR TotalRevenue = SUM(Sales[Revenue])
VAR TotalCost = SUM(Sales[Cost])
RETURN DIVIDE(TotalRevenue - TotalCost, TotalRevenue, 0)
```

### Ranking
```dax
Product Rank =
RANKX(
    ALL(Products[ProductName]),
    CALCULATE(SUM(Sales[Amount])),
    ,
    DESC,
    DENSE
)
```

---

## Performance Rules
1. Use VAR to avoid evaluating the same expression twice
2. Prefer DIVIDE() over "/" — handles division by zero gracefully
3. Avoid FILTER on large tables — prefer CALCULATETABLE or direct column filters
4. Avoid calculated columns when a measure will do — measures are computed on demand
5. Use ALL() carefully — it removes ALL filters from a table or column
6. RELATED() works in row context (calculated columns); use CALCULATE + filters in measures
