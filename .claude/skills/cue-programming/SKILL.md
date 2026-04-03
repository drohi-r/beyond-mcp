---
name: cue-programming
description: Use when building, triggering, or managing cue sequences in BEYOND. Applies to cue selection, cue playback, cell navigation, page/tab organization, workspace loading, and live cue management during a show.
---

# Cue Programming

Use this skill when the operator needs to build or manage cue sequences, trigger cues, navigate the cue grid, or set up pages and tabs for a show.

## Workflow — Building a cue sequence

1. **Navigate to the right page/tab.**
   - `select_page` index — jump to a page
   - `select_tab_by_name` name — or select tab by name
   - `select_category_by_name` name — filter by content category

2. **Focus and trigger cues.**
   - `focus_cell` page, cue — focus on a specific cell
   - `start_cell` — start the focused cell
   - Or use name-based: `start_cue_by_name` name

3. **Control playback.**
   - `pause_cue` page, cue, 1 — pause a running cue
   - `pause_cue` page, cue, 0 — unpause
   - `restart_cue` page, cue — restart from beginning
   - `stop_cue_now` page, cue — immediate stop
   - `stop_cue_sync` page, cue, fade — stop with fade

4. **Navigate cue grid.**
   - `cue_down` / `cue_up` — move selection
   - `shift_focus` direction — shift by offset
   - `move_focus` dx, dy — move by delta
   - `focus_cell_index` index — jump to linear position

5. **Set cue mode for the situation.**
   - `set_cue_mode_single` — one cue at a time (safe for busking)
   - `set_cue_mode_one_per` — one per group (layer-based)
   - `set_cue_mode_multi` — multiple simultaneous (complex shows)

## Workflow — Live show operation

1. **Set click behavior for the session.**
   - `click_mode_select` — standard selection
   - `click_mode_flash` — momentary trigger
   - `click_mode_toggle` — toggle on/off
   - `click_mode_live` — live performance mode

2. **Set transitions.**
   - `set_transition_type` index — select transition effect
   - `set_master_transition_time` seconds — set crossfade duration

3. **Trigger cues by name.**
   - `start_cue_by_name` "intro_beams"
   - `start_cue_by_name` "verse_tunnels"
   - `stop_cue_by_name` "intro_beams"

4. **Quick stop.**
   - `unselect_all_cues` — deselect everything
   - `stop_all_sync` fade — graceful stop with fade
   - `stop_all_now` — emergency stop (destructive)

## Workflow — Workspace management

1. **Load a workspace for the event.**
   - `load_workspace` "festival_main"

2. **Load specific cues.**
   - `load_cue` "dj_set_1" — load without starting
   - `start_cue_by_name` "dj_set_1" — then trigger when ready

## Workflow — Atomic multi-cue triggers

Use OSC bundles to trigger multiple commands simultaneously:

```
send_osc_bundle '[
  ["/beyond/general/StartCue", ["beam_left"]],
  ["/beyond/general/StartCue", ["beam_right"]],
  ["/beyond/general/SetBpm", [128]]
]'
```

## Grid management

- `set_grid_size` columns, rows — resize the cue grid
- `select_grid` index — switch between grid layouts

## Beat sync

For beat-synced cue programming:
1. `set_bpm` to the track BPM
2. `beat_source_audio` for live audio input
3. Or `beat_source_manual` + `beat_tap` for manual sync
4. `beat_resync` to realign if drift occurs

## Safety notes

- `stop_all_now` is destructive — use `stop_all_sync` with a fade time for graceful stops.
- In `BEYOND_CONFIRM_DESTRUCTIVE` mode, emergency stops require `confirm=true`.
- Always verify cue names match your workspace with `select_cue` before triggering.
- Use `preview_osc` to inspect commands before sending in unfamiliar workspaces.
