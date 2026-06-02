"""
Power BI knowledge base with keyword search.
Contains DAX functions, M Query patterns, and Power BI concepts.
No external ML dependencies — uses fast keyword + scoring search.
"""

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# Knowledge base — DAX functions + Power BI concepts
# ---------------------------------------------------------------------------

DOCS: list[dict] = [
    # ── CALCULATE family ────────────────────────────────────────────────────
    {
        "id": "calculate",
        "category": "DAX Filter",
        "title": "CALCULATE",
        "syntax": "CALCULATE(<expression>[, <filter1>, <filter2>, ...])",
        "description": "Evaluates an expression in a modified filter context. The most powerful DAX function — it can add, remove, or override filters.",
        "example": "Sales YTD = CALCULATE(SUM(Sales[Amount]), DATESYTD('Date'[Date]))",
        "notes": "CALCULATE causes context transition: row context is converted to an equivalent filter context before filters are applied.",
        "tags": ["calculate", "filter", "context", "measure"],
    },
    {
        "id": "calculatetable",
        "category": "DAX Filter",
        "title": "CALCULATETABLE",
        "syntax": "CALCULATETABLE(<table>, [<filter1>, ...])",
        "description": "Returns a table in a modified filter context. Use instead of FILTER on large tables for better performance.",
        "example": "Top Products = CALCULATETABLE(Products, Products[Sales] > 1000)",
        "tags": ["calculatetable", "filter", "table", "performance"],
    },
    {
        "id": "all",
        "category": "DAX Filter",
        "title": "ALL / ALLEXCEPT / ALLSELECTED",
        "syntax": "ALL([<table> | <column>[, <column>[, ...]]])",
        "description": "ALL removes all filters. ALLEXCEPT removes filters except specified columns. ALLSELECTED respects slicer selections but ignores visual filters.",
        "example": "Market Share = DIVIDE(SUM(Sales[Amount]), CALCULATE(SUM(Sales[Amount]), ALL(Products)))",
        "tags": ["all", "allexcept", "allselected", "filter", "remove filter"],
    },
    # ── Aggregation ──────────────────────────────────────────────────────────
    {
        "id": "sumx",
        "category": "DAX Iterator",
        "title": "SUMX",
        "syntax": "SUMX(<table>, <expression>)",
        "description": "Iterates over each row of a table, evaluates the expression in that row context, and returns the sum of all results.",
        "example": "Revenue = SUMX(Sales, Sales[Qty] * Sales[UnitPrice])",
        "notes": "Use SUMX when you need row-level calculations. For simple column sums, SUM() is faster.",
        "tags": ["sumx", "iterator", "row context", "aggregation", "multiply"],
    },
    {
        "id": "averagex",
        "category": "DAX Iterator",
        "title": "AVERAGEX",
        "syntax": "AVERAGEX(<table>, <expression>)",
        "description": "Iterates over a table and returns the average of the expression evaluated for each row.",
        "example": "Avg Order Value = AVERAGEX(Orders, Orders[Qty] * Orders[Price])",
        "tags": ["averagex", "average", "iterator"],
    },
    {
        "id": "countrows",
        "category": "DAX Aggregation",
        "title": "COUNTROWS / COUNT / DISTINCTCOUNT",
        "syntax": "COUNTROWS(<table>)",
        "description": "COUNTROWS counts rows in a table. COUNT counts non-blank values in a column. DISTINCTCOUNT counts unique values.",
        "example": "Order Count = COUNTROWS(Sales)\nDistinct Customers = DISTINCTCOUNT(Sales[CustomerID])",
        "tags": ["countrows", "count", "distinctcount", "rows", "unique"],
    },
    {
        "id": "divide",
        "category": "DAX Math",
        "title": "DIVIDE",
        "syntax": "DIVIDE(<numerator>, <denominator>[, <alternateresult>])",
        "description": "Performs division and safely handles division by zero. Always prefer DIVIDE over the '/' operator.",
        "example": "Profit Margin = DIVIDE(SUM(Sales[Profit]), SUM(Sales[Revenue]), 0)",
        "tags": ["divide", "division", "error", "blank", "zero"],
    },
    # ── Time Intelligence ────────────────────────────────────────────────────
    {
        "id": "datesytd",
        "category": "DAX Time Intelligence",
        "title": "DATESYTD / DATESMTD / DATESQTD",
        "syntax": "DATESYTD(<dates>[, <year_end_date>])",
        "description": "Returns a table of dates from the start of the year/month/quarter to the current date. Used inside CALCULATE for cumulative totals.",
        "example": "YTD Sales = CALCULATE(SUM(Sales[Amount]), DATESYTD('Date'[Date]))",
        "tags": ["ytd", "mtd", "qtd", "year to date", "time intelligence", "cumulative"],
    },
    {
        "id": "sameperiodlastyear",
        "category": "DAX Time Intelligence",
        "title": "SAMEPERIODLASTYEAR",
        "syntax": "SAMEPERIODLASTYEAR(<dates>)",
        "description": "Returns a table of dates shifted back one year. Use for year-over-year comparisons.",
        "example": "PY Sales = CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR('Date'[Date]))",
        "tags": ["sameperiodlastyear", "previous year", "yoy", "year over year", "comparison"],
    },
    {
        "id": "datesinperiod",
        "category": "DAX Time Intelligence",
        "title": "DATESINPERIOD",
        "syntax": "DATESINPERIOD(<dates>, <start_date>, <number_of_intervals>, <interval>)",
        "description": "Returns a table of dates for a rolling period. Useful for rolling 7-day, 30-day, or 12-month calculations.",
        "example": "Rolling 12M = CALCULATE(SUM(Sales[Amount]), DATESINPERIOD('Date'[Date], LASTDATE('Date'[Date]), -12, MONTH))",
        "tags": ["datesinperiod", "rolling", "moving average", "12 month", "period"],
    },
    {
        "id": "totalytd",
        "category": "DAX Time Intelligence",
        "title": "TOTALYTD / TOTALMTD",
        "syntax": "TOTALYTD(<expression>, <dates>[, <filter>][, <year_end_date>])",
        "description": "Shorthand for CALCULATE with DATESYTD. Evaluates a year-to-date value.",
        "example": "YTD Sales = TOTALYTD(SUM(Sales[Amount]), 'Date'[Date])",
        "tags": ["totalytd", "totalmtd", "ytd", "shorthand", "time intelligence"],
    },
    # ── Logical / Conditional ────────────────────────────────────────────────
    {
        "id": "if",
        "category": "DAX Logical",
        "title": "IF / IF.EAGER",
        "syntax": "IF(<logical_test>, <value_if_true>[, <value_if_false>])",
        "description": "Returns one of two values based on a condition. IF.EAGER evaluates both branches (use when both branches have no side effects).",
        "example": "Sales Flag = IF(SUM(Sales[Amount]) > 10000, \"High\", \"Low\")",
        "tags": ["if", "conditional", "logical", "branch"],
    },
    {
        "id": "switch",
        "category": "DAX Logical",
        "title": "SWITCH",
        "syntax": "SWITCH(<expression>, <value1>, <result1>[, <value2>, <result2>]...[, <else>])",
        "description": "Evaluates an expression against a list of values and returns the matching result. Cleaner than nested IFs.",
        "example": "Quarter = SWITCH(MONTH('Date'[Date]), 1,\"Q1\",2,\"Q1\",3,\"Q1\",4,\"Q2\",5,\"Q2\",6,\"Q2\",\"Q3/Q4\")",
        "tags": ["switch", "case", "conditional", "nested if"],
    },
    # ── Table functions ──────────────────────────────────────────────────────
    {
        "id": "filter",
        "category": "DAX Table",
        "title": "FILTER",
        "syntax": "FILTER(<table>, <filter_expression>)",
        "description": "Returns a filtered table. Use only when needed — prefer direct column filters in CALCULATE for performance.",
        "example": "High Value Sales = FILTER(Sales, Sales[Amount] > 1000)",
        "notes": "FILTER iterates row by row, which is slow on large tables. Use CALCULATETABLE with column filters when possible.",
        "tags": ["filter", "table", "performance", "row iteration"],
    },
    {
        "id": "related",
        "category": "DAX Relationship",
        "title": "RELATED / RELATEDTABLE",
        "syntax": "RELATED(<column>)",
        "description": "RELATED retrieves a value from a related table (many-to-one). RELATEDTABLE returns a table from the one side of a relationship.",
        "example": "Product Category = RELATED(Products[Category])  -- in a calculated column on Sales",
        "notes": "RELATED works in row context (calculated columns). In measures, use CALCULATE with relationships.",
        "tags": ["related", "relatedtable", "relationship", "lookup", "join"],
    },
    {
        "id": "rankx",
        "category": "DAX Ranking",
        "title": "RANKX",
        "syntax": "RANKX(<table>, <expression>[, <value>][, <order>][, <ties>])",
        "description": "Returns the ranking of a value in a list of values across a table.",
        "example": "Product Rank = RANKX(ALL(Products[ProductName]), CALCULATE(SUM(Sales[Amount])), , DESC, DENSE)",
        "tags": ["rankx", "rank", "ranking", "top n"],
    },
    {
        "id": "var",
        "category": "DAX Variable",
        "title": "VAR / RETURN",
        "syntax": "VAR <name> = <expression>\nRETURN <result>",
        "description": "Variables store intermediate results, improving readability and performance by avoiding repeated evaluation.",
        "example": "Profit Margin =\nVAR Revenue = SUM(Sales[Revenue])\nVAR Cost = SUM(Sales[Cost])\nRETURN DIVIDE(Revenue - Cost, Revenue, 0)",
        "tags": ["var", "variable", "return", "performance", "readability"],
    },
    # ── Text functions ───────────────────────────────────────────────────────
    {
        "id": "concatenate",
        "category": "DAX Text",
        "title": "CONCATENATE / CONCATENATEX",
        "syntax": "CONCATENATEX(<table>, <expression>[, <delimiter>])",
        "description": "CONCATENATE joins two text strings. CONCATENATEX iterates a table and concatenates the expression results.",
        "example": "Full Name = CONCATENATE([First Name], \" \" & [Last Name])\nCategories = CONCATENATEX(Products, Products[Category], \", \")",
        "tags": ["concatenate", "concatenatex", "text", "string", "join"],
    },
    {
        "id": "format",
        "category": "DAX Text",
        "title": "FORMAT",
        "syntax": "FORMAT(<value>, <format_string>)",
        "description": "Converts a value to text with the specified format.",
        "example": "Month Year = FORMAT('Date'[Date], \"MMM YYYY\")\nFormatted Sales = FORMAT(SUM(Sales[Amount]), \"$#,##0\")",
        "tags": ["format", "text", "date format", "number format", "display"],
    },
    # ── M Query patterns ─────────────────────────────────────────────────────
    {
        "id": "m-filter",
        "category": "M Query",
        "title": "Filter Rows in M",
        "syntax": "Table.SelectRows(<table>, each <condition>)",
        "description": "Filters rows based on a condition. Supports query folding when used on database sources.",
        "example": "FilteredRows = Table.SelectRows(Source, each [Amount] > 0 and [Status] = \"Active\")",
        "tags": ["power query", "m query", "filter rows", "selectrows", "transform"],
    },
    {
        "id": "m-addcolumn",
        "category": "M Query",
        "title": "Add Custom Column in M",
        "syntax": "Table.AddColumn(<table>, <newColumnName>, <columnGeneratorFunction>)",
        "description": "Adds a new column to a table based on a function applied to each row.",
        "example": "WithRevenue = Table.AddColumn(Source, \"Revenue\", each [Qty] * [Price], type number)",
        "tags": ["power query", "m query", "add column", "custom column", "transform"],
    },
    {
        "id": "m-groupby",
        "category": "M Query",
        "title": "Group By in M",
        "syntax": "Table.Group(<table>, <key columns>, <aggregations>)",
        "description": "Groups rows by key columns and applies aggregation functions.",
        "example": "Grouped = Table.Group(Source, {\"Category\"}, {{\"Total\", each List.Sum([Sales]), type number}})",
        "tags": ["power query", "m query", "group by", "aggregate", "summarize"],
    },
    {
        "id": "m-merge",
        "category": "M Query",
        "title": "Merge (Join) Tables in M",
        "syntax": "Table.NestedJoin(<table1>, <key1>, <table2>, <key2>, <newColumnName>, <joinKind>)",
        "description": "Joins two tables. JoinKind options: LeftOuter, RightOuter, FullOuter, Inner, LeftAnti, RightAnti.",
        "example": "Merged = Table.NestedJoin(Sales, {\"ProductID\"}, Products, {\"ID\"}, \"Details\", JoinKind.LeftOuter)",
        "tags": ["power query", "m query", "merge", "join", "lookup", "nestedjoin"],
    },
    # ── Concepts ─────────────────────────────────────────────────────────────
    {
        "id": "context-transition",
        "category": "DAX Concept",
        "title": "Context Transition",
        "syntax": "N/A — concept",
        "description": "When CALCULATE is called inside a row context (e.g. in an iterator or calculated column), it converts the row context into an equivalent filter context before evaluating. This is called context transition.",
        "example": "-- In a calculated column, this creates a filter for the current row:\nSales Rank = RANKX(ALL(Sales), CALCULATE(SUM(Sales[Amount])))",
        "tags": ["context transition", "row context", "filter context", "calculate", "concept"],
    },
    {
        "id": "star-schema",
        "category": "Data Modeling",
        "title": "Star Schema",
        "syntax": "N/A — concept",
        "description": "The recommended data model for Power BI. One central fact table (Sales, Orders) surrounded by dimension tables (Date, Product, Customer). Relationships flow from dimension to fact (one-to-many).",
        "example": "Fact: Sales(OrderID, DateKey, ProductKey, CustomerKey, Amount)\nDim: Date(DateKey, Year, Month...), Product(ProductKey, Name, Category...)",
        "tags": ["star schema", "data model", "fact table", "dimension", "modeling"],
    },
    {
        "id": "rls",
        "category": "Power BI Security",
        "title": "Row-Level Security (RLS)",
        "syntax": "N/A — concept",
        "description": "Restricts data access per user. Define roles with DAX filters in Power BI Desktop, then assign users in Power BI Service.",
        "example": "Role: SalesRegion\nDAX filter on Sales table: Sales[Region] = USERNAME()\nor with a mapping table: Sales[Region] IN SELECTCOLUMNS(FILTER(UserRegionMap, UserRegionMap[Email] = USERPRINCIPALNAME()), \"Region\", UserRegionMap[Region])",
        "tags": ["rls", "row level security", "security", "username", "userprincipalname", "roles"],
    },
    {
        "id": "date-table",
        "category": "Data Modeling",
        "title": "Date Table (Calendar Table)",
        "syntax": "CALENDAR / CALENDARAUTO",
        "description": "A dedicated date dimension is required for time intelligence DAX functions. Mark it as a Date Table in Power BI.",
        "example": "DateTable = CALENDAR(DATE(2020,1,1), DATE(2030,12,31))\n-- Then add columns: Year, Month, Quarter, WeekDay...",
        "tags": ["date table", "calendar", "time intelligence", "date dimension", "mark as date table"],
    },
]


# ---------------------------------------------------------------------------
# Search logic
# ---------------------------------------------------------------------------

def _score(doc: dict, query: str) -> int:
    """Score a doc against a query using keyword matching."""
    q = query.lower()
    words = set(re.split(r"\W+", q))
    score = 0

    # Title match — highest weight
    title = doc["title"].lower()
    if q in title:
        score += 20
    for w in words:
        if w and w in title:
            score += 5

    # Tag match
    for tag in doc.get("tags", []):
        if q in tag:
            score += 10
        for w in words:
            if w and len(w) > 2 and w in tag:
                score += 3

    # Description + notes match
    body = (doc.get("description", "") + " " + doc.get("notes", "")).lower()
    for w in words:
        if w and len(w) > 2 and w in body:
            score += 1

    # Category match
    cat = doc.get("category", "").lower()
    for w in words:
        if w and w in cat:
            score += 2

    return score


def search_docs(query: str, top_n: int = 3) -> list[dict]:
    """
    Search the Power BI knowledge base.

    Args:
        query: Natural language or keyword query
        top_n: Number of results to return

    Returns:
        List of matching docs, best match first
    """
    scored = [(doc, _score(doc, query)) for doc in DOCS]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = [doc for doc, score in scored if score > 0]
    return results[:top_n]


def format_doc(doc: dict) -> str:
    """Format a doc entry as readable text."""
    lines = [
        f"## {doc['title']} ({doc['category']})",
        f"**Syntax:** `{doc['syntax']}`",
        f"**Description:** {doc['description']}",
    ]
    if doc.get("notes"):
        lines.append(f"**Notes:** {doc['notes']}")
    if doc.get("example"):
        lines.append(f"**Example:**\n```dax\n{doc['example']}\n```")
    return "\n".join(lines)


def search_and_format(query: str, top_n: int = 3) -> str:
    """Search and return formatted results as a single string."""
    results = search_docs(query, top_n)
    if not results:
        return f"No documentation found for: '{query}'"
    return "\n\n---\n\n".join(format_doc(d) for d in results)
