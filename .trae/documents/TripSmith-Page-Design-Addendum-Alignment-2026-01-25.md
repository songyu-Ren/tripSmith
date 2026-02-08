# TripSmith Page Design Notes (Alignment Addendum, Desktop-first)

## Global Styles
- Layout
  - Desktop-first: 12-column CSS Grid (max-width 1200px, 24px gutter), centered main content.
  - Responsive breakpoints: 1024/768/480; tables and cards stack to a single column at <=768.
- Color and elevation
  - Background: #0B1220 (dark base)
  - Primary: #4F46E5 (buttons/links/highlights)
  - Border: rgba(148,163,184,0.25), card shadow 0 10px 30px rgba(0,0,0,0.20)
- Typography
  - H1 28/36，H2 22/30，H3 18/26，Body 14/22，Caption 12/18
  - Use monospaced font for time/price fields for alignment
- Interaction states
  - Primary button: hover brightness +6%; disabled 40% opacity
  - Link: underline on hover; external links include an icon

---

## 1) Home (Trip requirements form)
### Meta Information
- title: TripSmith | Travel planning
- description: Enter trip preferences and generate 3 explainable travel options
- og:title/og:description same as above; og:type=website

### Page Structure
- Top navigation (full width) + main form card (centered) + examples/notes (two-column info area) + footer

### Sections & Components
1. Top nav (Flex, left/right aligned)
   - Left: Logo (TripSmith)
   - Right: session area (short anonymous user_id display) + “Reset session” button
2. Requirements form (Card, Grid)
   - Two-column layout: origin/dates on the left, budget/travelers/preferences on the right; stacks to one column at <=768
   - Fields: origin, destination, start/end date, flex days, budget+currency, travelers, preferences (multi-select tags)
   - Validation: required field prompts + date range errors (inline + top summary)
   - CTA: Generate plans (create Trip then navigate to results page)
3. Example notes (Info panel)
   - Explain that “mock works end-to-end; real LLM/provider is optional”

---

## 2) Plan Results (3 options)
### Meta Information
- title: TripSmith | Plan results
- description: Review 3 options, generate a daily itinerary, export, and subscribe to alerts
- og:type=website

### Page Structure
- Back link + Trip summary bar + plan card list (vertical stack) + export section at the bottom

### Sections & Components
1. Trip summary bar (optional sticky)
   - Shows: origin/destination, dates, budget, travelers, preference tags
   - Action: Regenerate plans (secondary)
2. Plan cards (3 fixed)
   - Header: Budget / Time-saver / Balanced + key metric chips (total cost/total time/transfers/comfort)
   - Body: summary (3–6 lines) + “Why this option” (collapsible)
   - Actions:
     - Primary: Generate detailed itinerary (go to itinerary page)
     - Secondary: Subscribe to price alerts (modal form: type/threshold/frequency)
3. Export section (Card or inline)
   - Buttons: Export ICS, Export Markdown (download or new-tab preview)
4. State components
   - LoadingSkeleton for plan generation; ErrorCard (error copy + retry)

---

## 3) Itinerary (day-by-day)
### Meta Information
- title: TripSmith | Daily itinerary
- description: View and generate a day-by-day itinerary (Morning/Afternoon/Evening), with exports
- og:type=website

### Page Structure
- Back link + selected plan summary + day accordion (Day 1..n) + export section

### Sections & Components
1. Plan summary (compact card)
   - Shows the selected option title and key metrics
   - Action: Regenerate itinerary (secondary)
2. Day-by-day itinerary (Accordion)
   - Each day has 3 time periods: Morning/Afternoon/Evening (timeline-style)
   - Each item: POI name, estimated stay time, commute mode and duration, weather summary (show “N/A/Mock” if missing)
3. Exceptions and conflicts (inline notice)
   - On failure: show error + retry button; keep the last successful content
4. Export section
   - Same as results page: ICS/Markdown

---

## Alignment summary (for merging)
- Fix inconsistent itinerary-page meta/copy: remove “settings/provider connection” wording and unify on itinerary.
- Unify export UX: exports are not a standalone page; they are a shared module on results/itinerary pages.
- Unify information architecture: 3-page loop (home → results → itinerary); all core features are reachable from the home page.
