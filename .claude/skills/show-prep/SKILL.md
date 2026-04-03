---
name: show-prep
description: Use when preparing BEYOND for a show, verifying connectivity, setting defaults, checking zones, or doing a pre-show walkthrough. Applies to show-readiness checks, default parameter setting, zone verification, and system warm-up.
---

# Show Prep

Use this skill before a live show to verify that BEYOND is reachable, zones are configured, and master parameters are at safe defaults.

## Workflow

1. **Verify connectivity.**
   - `health_check` — confirm BEYOND target is reachable
   - `get_server_config` — verify host, port, safety settings

2. **Set safe master defaults.**
   - `set_master_brightness` 100 — full brightness
   - `set_master_zoom` 100 — full zoom
   - `set_master_scan_rate` 100 — default scan rate
   - `set_master_speed` 1.0 — normal playback speed
   - `set_master_alpha` 255 — full opacity
   - `set_master_visible_points` 100 — all points visible

3. **Reset master geometry.**
   - `set_master_size` 100, 100 — full size
   - `set_master_position` 0, 0 — centered
   - `set_master_rotation` 0, 0, 0 — no rotation
   - `set_master_rotation_speed` 0, 0, 0 — no continuous rotation

4. **Clear effects.**
   - `set_master_effect` 1, -1 — stop FX slot 1
   - `set_master_effect` 2, -1 — stop FX slot 2
   - `set_master_effect` 3, -1 — stop FX slot 3
   - `set_master_effect` 4, -1 — stop FX slot 4

5. **Unmute all zones.**
   - `unmute_all_zones` — ensure nothing is accidentally muted

6. **Enable laser output.**
   - `enable_laser_output` — undo any leftover blackout

7. **Set beat source.**
   - Confirm with operator: timer, audio, or manual
   - `beat_source_timer` / `beat_source_audio` / `beat_source_manual`
   - `set_bpm` to the event tempo if known

8. **Set cue mode.**
   - Confirm with operator: single, one-per, or multi
   - `set_cue_mode_single` / `set_cue_mode_one_per` / `set_cue_mode_multi`

## Pre-show checklist

- [ ] Health check passes
- [ ] Master brightness at 100
- [ ] Master geometry reset to defaults
- [ ] All FX slots stopped
- [ ] All zones unmuted
- [ ] Laser output enabled
- [ ] BPM and beat source set
- [ ] Cue mode confirmed with operator

## Safety notes

- Always confirm with the operator before enabling laser output on a rig that may have audience-facing projectors.
- If `BEYOND_CONFIRM_DESTRUCTIVE` is enabled, destructive operations like blackout will require `confirm=true`.
- Use `preview_osc` to verify any uncertain commands before sending.
