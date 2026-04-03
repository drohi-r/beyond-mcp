# Live Validation

This document records tools that were exercised against a real Pangolin BEYOND instance over LAN on `2026-04-03`.

Target used during validation:
- host: `192.168.20.179`
- transport: UDP OSC
- port: `8000`
- path: `beyond-mcp` running remotely against a live BEYOND session

## Live-Validated Tools

The following tools were sent live and visually confirmed in BEYOND:

- `display_popup`
- `set_bpm`
- `select_next_page`
- `select_prev_page`
- `select_next_tab`
- `select_prev_tab`
- `start_cue_by_name`
- `stop_cue_by_name`
- `set_master_brightness`

## Sent But Not Visually Confirmed

- `load_cue`
  The OSC send succeeded cleanly, but the current BEYOND workspace did not expose an obvious visible state change during validation.

## Build-Specific / Argument-Specific Behavior

- `display_preview("main", ...)`
  The OSC send succeeded, but `main` did not appear to be a valid preview identifier on the validated BEYOND build. The tool remains useful, but the preview name likely needs to match the local BEYOND configuration.

## Validation Notes

- These checks prove transport and tool wiring for the validated BEYOND build, not every possible workspace or UI state.
- For public safety, prefer running first-time tests with:
  - `BEYOND_SAFETY_PROFILE=show-safe`
  - host allowlisting via `BEYOND_ALLOWED_HOSTS`
- Use human-visible actions first when validating a new BEYOND installation:
  - popup display
  - BPM
  - page/tab navigation
  - non-critical cue start/stop
  - master brightness on a test target
