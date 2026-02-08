# TripSmith Page Design Notes (MVP, Desktop-first)

## Global Styles
- Design tokens
  - Background: #0B1220 (dark) / #FFFFFF (light, toggleable by default)
  - Primary: #4F46E5 (accent buttons/links)
  - Success/Warning/Error: #16A34A / #F59E0B / #DC2626
  - Border/Dividers: rgba(148,163,184,0.25)
  - Radius: 12px (cards), 8px (buttons/inputs)
  - Shadow: card 0 10px 30px rgba(0,0,0,0.20)
- Typography
  - H1 28/36, H2 22/30, H3 18/26, Body 14/22, Caption 12/18
  - Use monospaced font for numbers and time fields (for alignment)
- Button states
  - Primary: solid primary by default; hover brightness +6%; disabled 40% opacity
  - Secondary: outlined + transparent background; subtle background on hover
- Link
  - Primary color by default; underline on hover; external link icon hint
- Layout system
  - Desktop: CSS Grid (12 columns, max-width 1200px, 24px horizontal padding)
  - Tablet/Mobile: breakpoints 1024/768/480, progressively collapse into single-column stacking; sidebar collapses into a drawer

---

## 1) Home (Trip requirements form)
### Meta Information
- title: TripSmith | AI itinerary planning
- description: Generate executable itineraries with pluggable providers and an agent workflow
- og:title/og:description same as above; og:type=website

### Page Structure
- Top navigation (full width) + requirements form card (centered) + notes/examples + footer

### Sections & Components
1. Top navigation (Flex)
   - Left: Logo (TripSmith)
   - Right: status area (short display of current user_id + “Reset”)
2. Requirements form (Card)
   - origin (input)
   - destination (input)
   - dates (start/end)
   - flexible dates (numeric input: ± days)
   - budget (total budget + currency)
   - travelers (numeric input)
   - preferences (multi-select/tags: pace, food, family, nightlife, walkability, etc.)
   - CTA: Generate plans (create Trip and navigate to results)
3. Notes section
   - Explain that mock mode works offline; real providers require keys (in `.env`)
4. Footer
   - Copy + GitHub link

---

## 2) Results (3 options)
### Meta Information
- title: TripSmith | Itinerary editor
- description: Edit constraints and preferences; trigger agent generation and iterate
- og:type=article (for sharing pages)

### Page Structure
- Back link + Trip summary + 3 plan cards (stack)

### Sections & Components
1. Trip summary
   - origin/destination, dates, budget, travelers, preference tags
   - Action: Regenerate plans
2. Plan cards (at least 3)
   - Title: Budget / Time-saver / Balanced
   - Flight summary: depart/arrive, transfers, duration, price
   - Stay summary: location, per-night, total
   - Metrics: total cost, total travel time, number of transfers, daily commute estimate
   - Explanation: scores and reasons (cost_score/time_score/comfort_score)
   - CTA: Generate detailed itinerary (go to itinerary page)
   - Secondary CTA: Subscribe to price alerts (modal: type/threshold/frequency)
3. Export
   - Link buttons: Export ICS / Export Markdown

### Responsive
- <=1024: sidebar collapses into a drawer; two-column becomes one; preview and editor can switch via tabs

---

## 3) Itinerary (day-by-day)
### Meta Information
- title: TripSmith | Settings
- description: Manage provider connections and default preferences

### Page Structure
- Back link + plan summary + day accordion (Day 1..n)

### Sections & Components
1. Day-by-day list
   - 3 time periods per day: Morning/Afternoon/Evening
   - Each item includes: POI name, estimated stay time, commute mode/duration, weather summary
2. Errors and conflicts
   - On generation failure, show backend error message and retry button
3. Export
   - Same as results: ICS/Markdown

---

## 4) Shared states and components
- GlobalToast: success/error notifications.
- LoadingSkeleton: waiting UI for plan/itinerary generation.
- ErrorCard: API error UI (includes request id and retry).
