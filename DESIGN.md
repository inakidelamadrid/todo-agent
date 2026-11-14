---
name: todo-agent
description: A personal planner drawn as a midnight transit network; each category a coloured line, each item a station.
colors:
  midnight-enamel: "#0B1230"
  midnight-panel: "#08102A"
  midnight-popover: "#132050"
  midnight-muted: "#1A2858"
  midnight-input: "#2C417C"
  porcelain-ink: "#F2F4F7"
  midnight-muted-ink: "#A9B6DA"
  midnight-border: "rgb(242 244 247 / 0.22)"
  porcelain-ground: "#EEF1F6"
  porcelain-card: "#FFFFFF"
  porcelain-muted: "#E3E8F1"
  porcelain-border: "#D3D9E6"
  porcelain-input: "#C3CBDC"
  slate-muted-ink: "#4A5675"
  signal-scarlet: "#E21D2D"
  signal-scarlet-light: "#D01A29"
  focus-cobalt: "#6E95FF"
  focus-cobalt-light: "#1E5BFF"
  line-utilities-amber: "#FFC20E"
  line-utilities-amber-light: "#C28400"
  line-telecom-cobalt: "#3B74FF"
  line-telecom-cobalt-light: "#1E5BFF"
  line-streaming-scarlet: "#F0323F"
  line-streaming-scarlet-light: "#E21D2D"
  line-software-green: "#2BB65A"
  line-software-green-light: "#1E9E45"
  state-overdue: "#FF7A80"
  state-overdue-light: "#B3141F"
  state-due-soon: "#FFC20E"
  state-due-soon-light: "#8A5A00"
  state-paid: "#5DD98A"
  state-paid-light: "#17803A"
  destructive: "#FF6B72"
  destructive-light: "#B3141F"
typography:
  display:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.025em"
    fontFeature: "\"tnum\" 1"
  title:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Barlow, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  body-strong:
    fontFamily: "Barlow, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  label:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.33
    letterSpacing: "0.08em"
  button:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.43
    letterSpacing: "0.06em"
  station:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    letterSpacing: "0.06em"
rounded:
  sm: "6.4px"
  md: "8px"
  lg: "11.2px"
  full: "9999px"
spacing:
  xs: "6px"
  sm: "12px"
  md: "16px"
  gutter: "20px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.signal-scarlet}"
    textColor: "{colors.porcelain-card}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "32px"
  button-primary-sm:
    backgroundColor: "{colors.signal-scarlet}"
    textColor: "{colors.porcelain-card}"
    rounded: "{rounded.sm}"
    padding: "0 10px"
    height: "28px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "32px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    height: "28px"
  input:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain-ink}"
    rounded: "{rounded.md}"
    padding: "4px 10px"
    height: "32px"
  panel:
    backgroundColor: "{colors.midnight-panel}"
    textColor: "{colors.porcelain-ink}"
    rounded: "{rounded.lg}"
  rail:
    backgroundColor: "{colors.midnight-panel}"
    textColor: "{colors.porcelain-ink}"
    width: "240px"
  line-chip:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
  line-chip-active:
    backgroundColor: "{colors.midnight-muted}"
    textColor: "{colors.porcelain-ink}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
---

# Design System: todo-agent

## Overview

**Creative North Star: "The Midnight Transit Diagram"**

The product is drawn as a night-time metro map. Every recurring commitment sits on a coloured line, every item is a station on its day, and the reader's question ("what is next, what is left") is answered the way a platform sign answers it: condensed uppercase labels, tabular figures, saturated line inks on enamel. The default theme is midnight enamel (deep navy ground, deeper navy panels, porcelain ink); the light theme is porcelain (cool off-white ground, white panels, navy ink) with every line ink and state colour darkened to hold contrast. The navigation rail stays midnight in both themes, so the brand plate never changes.

Density is operational rather than airy: hairline-bordered panels stacked on a 20px gutter, 12px row rhythm, numbers that line up. Premium comes from restraint and finish (a single scarlet action, exact alignment, true transit typography), not from decoration. There are no shadows on the page itself, no gradients, no imagery; depth is tonal.

**Key Characteristics:**
- Midnight enamel and porcelain themes sharing one token set, switched by `prefers-color-scheme` or `data-theme`.
- Four category line inks are the only saturated hues besides the scarlet action and the state colours.
- Barlow Condensed for anything that reads like signage (headings, labels, buttons, station names); Barlow for running text.
- Tabular figures are opt-in (`tabular` utility) and applied to every money amount, date and day scale.
- Hairline borders and tonal panels instead of elevation.
- One signature: the network map, with ringed stations, interchange capsules and a TODAY tick.

## Colors

Midnight enamel and porcelain neutrals carrying four transit line inks, one scarlet action colour and three state colours.

### Primary
- **Signal Scarlet** (dark #E21D2D, light #D01A29): the single filled action per view (Add bill, the overdue row's Mark paid, form submit), the caret colour, and the active-nav underline in the rail. Never a background panel.

### Secondary
- **Line inks**: a category's identity everywhere it appears (network line, legend swatch, 20x4px row swatch, brand mark).
  - **Utilities Amber** (dark #FFC20E, light #C28400)
  - **Telecom Cobalt** (dark #3B74FF, light #1E5BFF); also the source of `::selection` (45% mix) and the focus ring family.
  - **Streaming Scarlet** (dark #F0323F, light #E21D2D)
  - **Software Green** (dark #2BB65A, light #1E9E45)

### Tertiary
- **State colours**: status text and icons, overdue station rings, the paid progress fill.
  - **Overdue** (dark #FF7A80, light #B3141F)
  - **Due Soon** (dark #FFC20E, light #8A5A00)
  - **Paid** (dark #5DD98A, light #17803A)
- **Focus Cobalt** (dark #6E95FF, light #1E5BFF): focus rings at 50% alpha, 3px.

### Neutral
- **Midnight Enamel** (#0B1230): dark page ground; light-theme ink and station ring colour; light-theme rail.
- **Midnight Panel** (#08102A): dark cards, table, network panel; dark-theme rail.
- **Midnight Popover** (#132050): popovers and sheets in dark.
- **Midnight Muted** (#1A2858): muted, secondary and accent surfaces; group header rows at 50%; the active legend chip.
- **Midnight Input** (#2C417C): input strokes and scrollbar thumb in dark.
- **Porcelain Ink** (#F2F4F7): dark-theme text and station rings; rail text in both themes.
- **Midnight Muted Ink** (#A9B6DA): secondary text in dark, and rail captions in both themes.
- **Midnight Border** (porcelain at 22%): every hairline in dark.
- **Porcelain Ground** (#EEF1F6), **Porcelain Card** (#FFFFFF), **Porcelain Muted** (#E3E8F1), **Porcelain Border** (#D3D9E6), **Porcelain Input** (#C3CBDC), **Slate Muted Ink** (#4A5675): the light-theme counterparts.

### Named Rules
**The Line Ink Rule.** A line ink means its category and nothing else. It is never used for status, emphasis or decoration outside the network, its legend, its row swatch and the brand mark.

**The One Scarlet Rule.** Scarlet fill is the action. A row-level action is outlined by default and only fills scarlet when that row is overdue; the page header carries the only always-filled button.

**The Two Inks Rule.** Every colour token exists as a dark/light pair; a new colour is not added until both values pass contrast on their own ground.

## Typography

**Display Font:** Barlow Condensed (with Barlow, sans-serif), weights 500 and 600
**Body Font:** Barlow (with ui-sans-serif, system-ui), weights 400, 500, 600

**Character:** a DIN-like transit pairing. The condensed cut is the signage voice, set uppercase and tracked for labels or tight and large for figures; the regular cut carries sentences quietly underneath.

### Hierarchy
- **Display** (600, 3rem desktop / 2.25rem mobile, tracking -0.025em): the page title, the month name.
- **Headline** (600, 2.25rem, line-height 1, tabular): the remaining-amount figure per currency.
- **Title** (600, 1.125rem to 1.5rem): popover and sheet titles, empty-state heading.
- **Body** (400, 0.875rem to 1rem): notes, sublines, descriptions. Item names use 600.
- **Label** (600, 0.75rem to 0.875rem, 0.08em, uppercase): column headers, group headers ("OVERDUE · 1"), panel names ("LINES", "MXN REMAINING"), currency codes beside amounts, rail status.
- **Button** (600, 0.875rem, 0.06em, uppercase): every button label.
- **Station** (600, 14px, 0.06em, uppercase, SVG): station names on the network map; overdue stations take the overdue colour.

### Named Rules
**The Signage Rule.** Condensed uppercase is reserved for things a transit sign would print: names of lines, stations, columns, groups, currencies and actions. Sentences stay in Barlow sentence case.

**The Aligned Figures Rule.** Every amount, date and day number uses tabular figures; the global default is proportional, so apply `tabular` explicitly.

## Layout

A two-column shell: a fixed 15rem (240px) midnight rail on the left (sticky, full height) and a main column capped at 90rem with 32px padding (16px on mobile, 24px/32px vertical). Below 768px the rail collapses to a top bar holding only the brand and nav; its status block hides and a one-line caption moves under the page title.

Main content is a single vertical stack on a 20px gutter: header (title left, controls right, wrapping), summary strip, network panel, table. Panels pad 24px horizontally and 12 to 16px vertically (16px on mobile). Table rows run 12px vertical padding; group header rows 8px.

The summary strip is a two-column grid divided by hairlines on desktop and stacked on mobile. The table becomes a stacked list below 768px. The network map keeps a 60rem minimum width and scrolls horizontally on narrow screens, with an edge fade mask and an initial scroll that keeps today (and any overdue station) in view.

## Elevation & Depth

The page is flat. Depth comes from tone: ground, then a darker (dark theme) or white (light theme) panel, outlined by a 1px hairline. Shadows appear only on floating layers that sit above the page.

### Shadow Vocabulary
- **Popover** (`shadow-md` plus a 1px ring of foreground at 10%): the Mark paid popover and selects.
- **Sheet** (`shadow-lg`, over a 10% black backdrop with a light blur): the bill form sheet.

### Named Rules
**The Flat Plate Rule.** Anything on the page itself (panels, rows, chips, buttons) has no shadow. Only layers that float over the page may cast one.

## Shapes

Gently rounded throughout, from one 0.5rem base radius: panels at 11.2px, buttons and inputs at 8px, small buttons, chips and nav items at 6.4px. Line swatches, progress bars and line strokes use fully round caps. The network vocabulary is geometric: 7px round-capped line strokes ending in short perpendicular terminus bars, 9px-radius station circles with a 4px ring, vertical capsules (26px wide, fully rounded) where stations on several lines share a day, and a 4px-radius TODAY tag.

## Components

### Buttons
Condensed, uppercase and tracked, so a button reads as a sign rather than a pill.
- **Shape:** 8px radius at default (32px tall), 6.4px at small (28px tall).
- **Primary:** Signal Scarlet fill, white label, 10px horizontal padding; hover drops to 80% opacity of the fill.
- **Outline:** transparent, 1px stroke of the ink at 60%; hover and open strengthen the stroke to full ink and add an 8% ink wash. Used for month navigation and row-level Mark paid.
- **Ghost:** no stroke; hover fills with the muted surface. Used for Undo and icon-only edit.
- **Focus / Active:** focus shows a 3px cobalt ring at 50% and a cobalt border; press nudges down 1px; disabled is 50% opacity.

### Chips (line legend)
- **Style:** 20x4px rounded line swatch plus the line name in Barlow 500; transparent at rest, muted surface on hover.
- **State:** the pressed chip holds the muted surface; every other chip drops to 55% opacity. `aria-pressed` carries the state.

### Cards / Containers
- **Corner Style:** 11.2px.
- **Background:** the card token (Midnight Panel / Porcelain Card).
- **Shadow Strategy:** none (The Flat Plate Rule).
- **Border:** 1px hairline; internal dividers are the same hairline.
- **Internal Padding:** 24px x, 12 to 16px y; 16px x on mobile.

### Inputs / Fields
- **Style:** 32px tall, 8px radius, 1px input-token stroke, transparent fill (input token at 30% in dark), 10px horizontal padding. Amount fields are tabular with the currency code as a label beside them.
- **Focus:** cobalt border plus a 3px cobalt ring at 50%; the caret is scarlet.
- **Error / Disabled:** destructive border with a 3px destructive ring at 20%, and a plain-language message in destructive below; disabled drops to 50%.

### Navigation
- **Style:** the midnight rail. Brand mark (three line inks converging on a ringed station) plus the product name in condensed uppercase. Nav items are Barlow 500 at 0.875rem with a 16px icon, 6.4px radius; the current item sits on a white 8% wash with a 2px Streaming Scarlet underline. Rail status sits at the foot: a 8px state-coloured dot, a condensed label and a one-line detail.
- **Mobile:** the rail becomes a top bar with brand and nav only.

### Status tags
Icon plus sentence-case text in the state colour, 0.875rem Barlow 500: warning triangle for overdue, clock for due soon, dashed circle for upcoming, check for paid. Never a filled badge.

### Network Map (signature)
The month drawn as a transit diagram inside a panel. A legend row of line chips heads it. A day scale (1, every fifth day, last day) runs across the top in muted tabular numerals with short ticks. Each category is a horizontal round-capped line in its ink with terminus bars. Each item is a station on its due day: an unfilled ring (card fill, ink-coloured 4px ring) when open, a solid fill when paid, an overdue-coloured ring with a 2s breathing halo when late. Station names alternate above and below the line to avoid collisions. Shared days draw an interchange capsule spanning the lines involved. Today is a 2px ink-coloured vertical rule ending in a filled TODAY tag. Selecting a legend chip thickens that line to 10px and dims the rest to 20%; clicking a station scrolls to and briefly highlights its table row.

### Motion
Short and functional. Station fill, line focus and chip state transition over 200ms; the paid progress bar eases out over 300ms; a selected row's highlight fades over 500ms; buttons press 1px. The overdue halo scales 0.7 to 1.5 and fades over 2s on an expo-out curve, and becomes a static 60% ring under reduced motion.

## Do's and Don'ts

### Do:
- **Do** give every new category a dark/light line-ink pair and use it only for that category (The Line Ink Rule).
- **Do** set every heading, label, button and station name in Barlow Condensed 600, uppercase and tracked (0.06 to 0.08em) when it is a label, tight (-0.025em) when it is a figure.
- **Do** apply tabular figures to every amount, date and day scale.
- **Do** keep page surfaces flat: card token, 1px hairline, 11.2px radius.
- **Do** keep the rail midnight in both themes.
- **Do** show status as icon plus coloured text, and as ring treatment on the map.

### Don't:
- **Don't** fill more than one action scarlet at the same level; row actions are outlined unless the row is overdue.
- **Don't** use a line ink for status, warning or decoration.
- **Don't** add shadows, gradients or glows to anything that sits on the page.
- **Don't** set sentences in condensed uppercase.
- **Don't** convert or merge currencies in a total; each currency gets its own figure.
