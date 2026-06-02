# M Query / Power Query Skill

## Description
Expert in Power Query M language for data transformation in Power BI and Excel.
Load this skill when the user asks about Power Query, M language, ETL steps,
data transformation, query folding, or data source connections.

---

## M Language Basics

### Structure of a Query
```m
let
    Source = Csv.Document(File.Contents("C:\data.csv"), [Delimiter=","]),
    PromotedHeaders = Table.PromoteHeaders(Source),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"Date", type date},
        {"Amount", type number}
    }),
    FilteredRows = Table.SelectRows(ChangedTypes, each [Amount] > 0)
in
    FilteredRows
```

---

## Common Transformations

### Filter Rows
```m
// Keep rows where Sales > 1000
Table.SelectRows(Source, each [Sales] > 1000)

// Multiple conditions
Table.SelectRows(Source, each [Sales] > 1000 and [Region] = "North")
```

### Add Custom Column
```m
Table.AddColumn(Source, "Full Name", each [First] & " " & [Last])
Table.AddColumn(Source, "Tax Amount", each [Price] * 0.1, type number)
```

### Group By
```m
Table.Group(Source, {"Category"}, {
    {"Total Sales", each List.Sum([Sales]), type number},
    {"Row Count", each Table.RowCount(_), type number}
})
```

### Pivot / Unpivot
```m
// Unpivot (wide to long — useful for year columns)
Table.UnpivotOtherColumns(Source, {"Product"}, "Year", "Sales")

// Pivot
Table.Pivot(Source, List.Distinct(Source[Year]), "Year", "Sales", List.Sum)
```

### Merge (Join) Tables
```m
// Left join
Table.NestedJoin(
    Sales, {"ProductID"},
    Products, {"ProductID"},
    "ProductDetails",
    JoinKind.LeftOuter
)
```

### Parameters
```m
// Define a parameter
StartDate = #date(2024, 1, 1),

// Use in filter
Table.SelectRows(Source, each [Date] >= StartDate)
```

---

## Query Folding Rules
Query folding = pushing transformations to the data source (SQL, etc.)

**These fold:** Filter, Sort, Select columns, Merge, Group By, basic type changes
**These break folding:** Custom columns with complex logic, Table.Buffer(), most text functions

To check: Right-click a step → "View Native Query" (grayed out = folding broke)

---

## Performance Tips
1. Filter rows early — before joins and expensive transformations
2. Select only needed columns — reduces memory
3. Avoid Table.Buffer() unless you need to prevent re-evaluation
4. Use query parameters instead of hardcoded values
5. Disable load for staging/helper queries (right-click → "Enable Load" unchecked)
