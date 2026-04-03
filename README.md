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
