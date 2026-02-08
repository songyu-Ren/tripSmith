# CHANGELOG

## v0.2.1 (2026-02-06)

### Added

- Job stage field (stage) and failure metadata (error_code / error_message / next_action)
- Unified job polling hook in the frontend, reused by results and itinerary pages
- Itinerary page segmentation by Morning/Afternoon/Evening (accordion)
- Error panel supports copying details (details shown in dev)

### Changed

- Layered error_code taxonomy: VALIDATION / RATE_LIMIT / JOB / INTERNAL (unified format)
- Lightweight UI design tokens (background/border/buttons/inputs/card shadow) applied across core pages

### Fixed

- API client can still read request_id from headers when the body has no JSON
