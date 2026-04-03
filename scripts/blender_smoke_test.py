from __future__ import annotations

import pathlib
import sys
import traceback

import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
ADDON_ROOT = ROOT / "addon_src"
sys.path.insert(0, str(ADDON_ROOT))


def main() -> None:
	import textools_mini_blender

	textools_mini_blender.register()
	try:
		info = textools_mini_blender.bl_info
		assert info["name"] == "TexTools-mini-Blender"
		assert tuple(info["blender"]) >= (5, 0, 0)
		assert hasattr(bpy.types.Scene, "ttmini_settings")
		print("SMOKE_OK", info["name"], info["version"])
	finally:
		textools_mini_blender.unregister()


if __name__ == "__main__":
	try:
		main()
	except Exception:
		traceback.print_exc()
		raise SystemExit(1)
