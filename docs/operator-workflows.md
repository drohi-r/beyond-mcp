# Operator Workflows

These are practical, low-risk ways to validate and use `beyond-mcp` in a real environment.

## First Connection Check

Use this order on a new BEYOND target:

1. `get_server_config`
2. `health_check`
3. `preview_osc`
4. `display_popup`
5. `set_bpm`

Why this order:

- it confirms config and reachability first
- it proves OSC transport before touching show state
- it uses visible but low-risk actions

## Safe UI Validation

After transport is confirmed:

1. `select_next_page`
2. `select_prev_page`
3. `select_next_tab`
4. `select_prev_tab`

These are good second-stage tests because they are visible, reversible, and easy to confirm by eye.

## Non-Critical Cue Validation

For a safe cue test:

1. choose a clearly non-critical cue
2. `start_cue_by_name`
3. confirm behavior
4. `stop_cue_by_name`

`load_cue` may still be useful, but on the validated build it did not produce an obvious visible state change.

## Live Parameter Validation

Good first live parameter:

1. `set_master_brightness(50)`
2. confirm visible change
3. `set_master_brightness(100)` to restore

This is a clean way to verify live parameter control without touching projector geometry or zone routing.

## Show-Safe Defaults

For most real sessions:

- use `BEYOND_SAFETY_PROFILE=show-safe`
- keep `BEYOND_ALLOWED_HOSTS` explicit
- use named tools before raw OSC
- use `preview_osc` before high-risk calls
- use `confirm=true` only when you intentionally want a destructive action

## Raw OSC Guidance

Use `send_osc_raw` only when:

- the BEYOND command is not yet wrapped
- you have validated the exact OSC address against your installed build
- you understand the scope and live effect

Prefer adding a named tool later if the action becomes part of normal workflow.
