# TexTools-mini-Blender

`TexTools-mini-Blender` is a stripped Blender add-on that keeps only two feature groups from the original TexTools-based codebase:

- `Color ID`
- `Mesh UV Tool`

The add-on source lives in [`addon_src/textools_mini_blender`](./addon_src/textools_mini_blender). It is namespaced as `ttmini` to avoid operator and UI collisions with the original add-on.

## Blender target

- Minimum Blender version: `5.0`

## Verification

- `pytest`
- Blender CLI smoke test via `scripts/blender_smoke_test.py`
- Blender CLI operator smoke test via `scripts/blender_ops_smoke.py`
- Blender CLI ZIP install/update smoke tests via `scripts/blender_zip_ops_smoke.py` and `scripts/blender_zip_update_smoke.py`

## Distribution

- Latest install ZIP: `dist/TexTools-mini-Blender-latest-clean.zip`
