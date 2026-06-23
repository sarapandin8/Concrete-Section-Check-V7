# GIRDER.LIFT.QA1 — Generic Precast Lifting Stage Audit

## Purpose

Audit the existing non-Railway precast girder lifting-stage workflow and lock the observed engineering boundaries with regression tests. This is not a new lifting solver. The feature already exists and is routed through the Beam/Girder SLS staged workflow.

## Existing behavior confirmed

- Railway U-Girder remains on its dedicated one-web lifting route.
- Generic precast lifting is exposed for:
  - parametric I-girder
  - precast box beam / box-section beam family
  - plank girder interior/exterior
  - voided plank girder interior/exterior
- Generic lifting stage uses an individual precast unit basis.
- Auto load for generic lifting is limited to `Precast unit self-weight × lifting IF`.
- Wet slab/topping, barrier/sidewalk, wearing surface, other SDL, building SDL, building LL, and additional SDL are excluded from lifting auto load.
- Full-length SLS preview uses two-point lifting moment and shear functions for the Lifting stage.
- Lifting stage uses transfer prestress force state (`pe_transfer_eff_kN`) for station-based stress preview.
- Section Builder exposes generic lifting inputs without Railway-only wording:
  - `Lifting a/L`
  - `Lifting impact factor`
  - `Individual precast unit`

## Engineering boundary

This preview checks global top/bottom stresses for the precast unit during handling. It does not replace project-specific lifting insert design, local anchorage/hardware checks, end-zone bursting/splitting design, transfer/development length design, or certified lifting method statements.

## QA status

`tests/test_girder_lift_qa1_generic_precast_closeout.py` locks the routing, load basis, two-point lifting diagram handoff, transfer prestress force selection, and UI wording boundaries.
