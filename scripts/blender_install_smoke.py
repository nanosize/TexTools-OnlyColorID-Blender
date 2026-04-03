from __future__ import annotations

import pathlib
import traceback

import addon_utils
import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
ADDON_ZIP = ROOT / "dist" / "TexTools-mini-Blender-package.zip"
MODULE_NAME = "textools_mini_blender"


def main() -> None:
	bpy.ops.preferences.addon_install(filepath=str(ADDON_ZIP), overwrite=True)
	addon_utils.enable(MODULE_NAME, default_set=False)
	assert addon_utils.check(MODULE_NAME)[1]
	module = __import__(MODULE_NAME)
	print("INSTALL_OK", module.bl_info["name"], module.bl_info["version"])


if __name__ == "__main__":
	try:
		main()
	except Exception:
		traceback.print_exc()
		raise SystemExit(1)
