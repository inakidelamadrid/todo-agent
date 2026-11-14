---
version: 1
slug: "tures-bills-components-billsmonthview-tsx-500e004a"
primary_target: "web/src/features/bills/components/BillsMonthView.tsx"
related_targets: []
---

# Bills · monthly payments

Scope: the Bills route of the web app. Visitor mode: Operate.
Job: see this month's home bills (utilities, telecom, streaming, software) by due date, mark each paid with its actual amount, know what is left per currency (MXN, USD; never converted).
Constraints: frontend-only for now (Zustand persist, sample data labelled); functional code; shadcn/ui primitives restyled to the world.

## Direction contract

THESIS: The month is a transit network. Each bill category is a coloured line, each bill a station on its due day. It refuses the category default of summary cards above a badge list.

OWN-WORLD: Midnight enamel ground #0B1230 with deeper #08102A panels and porcelain #F2F4F7 ink. Line inks are amber (utilities), cobalt (internet and phone), scarlet (streaming) and green (software). Type is a condensed DIN-like transit sans in uppercase tracked labels over a regular sans body, with tabular figures. Controls are outlined porcelain buttons, and the primary action fills scarlet. Station marks are white rings.

STORY: You open the page and read MXN and USD remaining first. The network shows where today sits and what is ahead. The table tells you what to pay next. You pay something, it fills its station, and the totals update.

FIRST VIEWPORT: The left rail holds the brand, Bills (active) and system status. The top bar holds month navigation and Add bill. One strip shows remaining, paid and total for each currency. The network panel spans the full width with four lines over a 1–31 day scale, a porcelain "today" tick, and interchange capsules on shared days. Below it is the bill table grouped overdue / due soon / upcoming / paid, with Mark paid on each row.

FORM: Midnight transit diagram (catalog challenger wayfinding-cartography-signage-midnight-transit-diagram, chosen over assigned candidate 5). seed:c8dd95c8824e49cc. Signature interaction: click a line in the legend and that line burns brightest while the others dim and the table filters to it. Paying a bill fills its station with a 200ms porcelain fill.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
