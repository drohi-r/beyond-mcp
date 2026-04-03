---
name: zone-alignment
description: Use when aligning, adjusting, or correcting projection zone geometry in BEYOND. Applies to zone setup, geometric correction (keystone, pincushion, bow, shear, linearity, symmetry), projector axis control, and multi-zone alignment workflows.
---

# Zone Alignment

Use this skill when the operator needs to adjust zone geometry — position, size, rotation, keystone, or other geometric corrections for projection mapping.

## Workflow

1. **Select the target zone.**
   - `zone_setup_select` with the zone index
   - Or navigate with `zone_setup_next_zone` / `zone_setup_prev_zone`

2. **Set basic geometry.**
   - `zone_setup_set` "xposition", value — horizontal position
   - `zone_setup_set` "yposition", value — vertical position
   - `zone_setup_set` "xsize", value — horizontal scale
   - `zone_setup_set` "ysize", value — vertical scale
   - `zone_setup_set` "zrotation", value — rotation

3. **Apply geometric corrections (if needed).**
   - Keystone: `zone_setup_set` "xkeystone" / "ykeystone"
   - Pincushion: `zone_setup_set` "xpincussion" / "ypincussion"
   - Bow: `zone_setup_set` "xbow" / "ybow"
   - Shear: `zone_setup_set` "xshear" / "yshear"
   - Linearity: `zone_setup_set` "xlinearity" / "ylinearity"
   - Symmetry: `zone_setup_set` "xsymmetry" / "ysymmetry"

4. **Fine-tune corner points (if needed).**
   - `zone_setup_set` "ax", value — corner A X
   - `zone_setup_set` "ay", value — corner A Y
   - `zone_setup_set` "bx", value — corner B X
   - `zone_setup_set` "by", value — corner B Y

5. **Check projector axis orientation.**
   - `projector_swap_xy` — swap X/Y axes if projection is rotated 90 degrees
   - `projector_invert_x` — mirror horizontally if image is flipped
   - `projector_invert_y` — mirror vertically if image is upside down

6. **Adjust projector output geometry.**
   - `set_projector_size` — scale the output
   - `set_projector_position` — shift the output

## Alignment order

For best results, correct in this order:
1. Projector axis orientation (swap/invert) — gets the image roughly right
2. Zone position and size — gross alignment
3. Rotation — match surface angle
4. Keystone — correct for projector angle
5. Pincushion/bow — correct for lens distortion
6. Linearity/symmetry — fine geometric tuning
7. Shear — final skew correction
8. Corner points — pixel-level precision

## Multi-zone alignment

When aligning multiple zones:
1. Use `store_zone_selection` to save current selection
2. Work on one zone at a time with `zone_setup_select`
3. Use `zone_setup_next_zone` / `zone_setup_prev_zone` to cycle
4. Use `restore_zone_selection` when done

## Parameter navigation

Instead of specifying parameter names, you can navigate the parameter list:
- `zone_setup_select_param` index — jump to a specific parameter
- `zone_setup_next_param` / `zone_setup_prev_param` — step through parameters

## Safety notes

- Zone setup changes take effect immediately on the laser output.
- Work with low brightness during alignment to reduce eye safety risk.
- Use `set_master_brightness` to dim output during alignment, restore after.
