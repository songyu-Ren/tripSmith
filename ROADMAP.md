# ROADMAP

This roadmap follows the principle of “small, shippable daily increments” and tracks next items by priority.

## Now (available)

- Trip / Constraints / Plan / Itinerary end-to-end flow (including exports)
- Saved plans: save a plan and generate an itinerary from saved plans
- Jobs: async execution, progress/stage, failure reasons, and next action
- Unified error response: error_code + request_id (dev can include details)
- Core UI: 3-page loop (home → results → itinerary) with error panel and retry

## Next (priorities)

### P0 (stability and contracts)

- Make packages/shared the single source of truth: generate types from API OpenAPI and add contract tests (OpenAPI changes should break the frontend build)
- Standardize job events: unify stage enums, fix stage→progress mapping, and thread request_id/trace_id through worker logs
- Expand error code taxonomy: map provider/LLM errors to PROVIDER.* / LLM.* and add observable metrics (failure rate, latency)

### P1 (usability and UX)

- Plan comparison upgrade: scorecard visualization, diff highlights, one-click dimension switching
- Editable itinerary: change time/POI, delete/reorder items, save with rollback
- Complete Loading/Skeleton/Empty states coverage and unify copywriting

### P2 (product expansion)

- Map experience: MapLibre + OSM (POI markers and route lines on itinerary page)
- Improve price alert engine: debouncing, threshold types (absolute/percent), frequency control
- Add one real provider reference implementation (keep the rest as stubs + mock fallbacks)
