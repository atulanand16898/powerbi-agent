# Report Builder Skill

## Description
Expert in Power BI report design, visualization best practices, and UX.
Load this skill when the user asks about choosing chart types, report layout,
color schemes, drillthrough, bookmarks, or dashboard design.

---

## Visualization Selection Guide

| Data Story | Best Visual |
|---|---|
| Compare categories | Bar / Column Chart |
| Show trend over time | Line Chart |
| Part of a whole | Donut / Pie (max 5 slices) |
| Distribution | Histogram / Box Plot |
| Correlation between 2 measures | Scatter Plot |
| Geographic data | Map / Filled Map |
| KPI vs target | Card + Gauge |
| Many categories + one measure | Treemap |
| Matrix with totals | Matrix visual |
| Detailed data table | Table visual |

---

## Report Design Principles

### Layout
- Use a 16:9 canvas (1280x720 default)
- Group related visuals in sections
- Use white space — don't cram everything in
- Place most important KPIs top-left (F-pattern reading)

### Color
- Use your organization's brand colors
- Max 5-6 distinct colors per report
- Use color to highlight, not decorate
- Diverging colors for positive/negative (green/red)
- Sequential colors for magnitude

### Interactivity
- Slicers on the left or top for filters
- Use drillthrough pages for detail views
- Bookmarks for "guided story" navigation
- Tooltips for additional context without clutter

---

## Performance Tips
1. Limit visuals per page to 8-10 max
2. Avoid high-cardinality slicers (thousands of values)
3. Use "Reduce rows" in query settings
4. Disable auto date/time (File → Options → Data Load)
5. Use aggregations for large datasets
