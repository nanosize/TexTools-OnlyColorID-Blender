from __future__ import annotations

import importlib
import os
import pathlib
import sys
import traceback
import zipfile

import addon_utils
import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_NAME = "textools_mini_blender"


def _latest_clean_zip() -> pathlib.Path:
	candidates = sorted(ROOT.joinpath("dist").glob("TexTools-mini-Blender-*-clean.zip"))
	if not candidates:
		raise FileNotFoundError("clean zip not found in dist/")
	return candidates[-1]


def _write_versioned_zip(path: pathlib.Path, version: tuple[int, int, int]) -> None:
	source = ROOT / "addon_src" / MODULE_NAME
	version_text = f'"version": ({version[0]}, {version[1]}, {version[2]})'
	with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for file_path in source.rglob("*.py"):
			relative = pathlib.Path(MODULE_NAME) / file_path.relative_to(source)
			content = file_path.read_text(encoding="utf-8")
			if file_path.name == "__init__.py":
				content = content.replace('"version": (0, 1, 1)', version_text)
			archive.writestr(str(relative).replace("\\", "/"), content)


def _set_face_selection(obj, polygon_index: int) -> None:
	mesh = obj.data
	face_attr = mesh.attributes[".uv_select_face"]
	vert_attr = mesh.attributes[".uv_select_vert"]
	edge_attr = mesh.attributes[".uv_select_edge"]
	mesh_face_attr = mesh.attributes[".select_poly"]

	for attr in (face_attr, vert_attr, edge_attr, mesh_face_attr):
		for entry in attr.data:
			entry.value = False

	mesh_face_attr.data[polygon_index].value = True
	face_attr.data[polygon_index].value = True
	for loop_index in mesh.polygons[polygon_index].loop_indices:
		vert_attr.data[loop_index].value = True
		edge_attr.data[loop_index].value = True


def _assert_meshtex_operator() -> None:
	bpy.ops.object.select_all(action="DESELECT")
	bpy.ops.mesh.primitive_plane_add()
	obj = bpy.context.active_object
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

	bpy.ops.object.mode_set(mode="EDIT")
	bpy.ops.mesh.subdivide(number_cuts=1)
	bpy.ops.object.mode_set(mode="OBJECT")
	_set_face_selection(obj, 0)

	bpy.ops.object.mode_set(mode="EDIT")
	result = bpy.ops.uv.ttmini_meshtex_create()
	assert "FINISHED" in result


def _enable_and_import():
	importlib.invalidate_caches()
	if hasattr(addon_utils, "modules_refresh"):
		addon_utils.modules_refresh()
	addon_utils.enable(MODULE_NAME, default_set=False)
	assert addon_utils.check(MODULE_NAME)[1]
	return sys.modules[MODULE_NAME]


def _purge_modules() -> None:
	for name in list(sys.modules):
		if name == MODULE_NAME or name.startswith(f"{MODULE_NAME}."):
			del sys.modules[name]


def _disable_and_unload() -> None:
	addon_utils.disable(MODULE_NAME, default_set=False)
	_purge_modules()
	importlib.invalidate_caches()
	if hasattr(addon_utils, "modules_refresh"):
		addon_utils.modules_refresh()


def main() -> None:
	new_zip = _latest_clean_zip()
	fixture_root = pathlib.Path(os.environ.get("BLENDER_USER_SCRIPTS", ROOT / "dist"))
	fixture_root.mkdir(parents=True, exist_ok=True)
	old_zip = fixture_root / "TexTools-mini-Blender-old-fixture.zip"
	_write_versioned_zip(old_zip, (0, 1, 0))

	bpy.ops.preferences.addon_install(filepath=str(old_zip), overwrite=True)
	old_module = _enable_and_import()
	print("OLD_VERSION", old_module.bl_info["version"])
	_disable_and_unload()

	bpy.ops.preferences.addon_install(filepath=str(new_zip), overwrite=True)
	new_module = _enable_and_import()
	print("NEW_VERSION", new_module.bl_info["version"])
	print("UPDATED_MODULE", new_module.__file__)

	source = pathlib.Path(new_module.__file__).with_name("op_meshtex_create.py").read_text(encoding="utf-8")
	assert "getSelectionIslands(" not in source
	assert tuple(new_module.bl_info["version"]) >= (0, 1, 1)

	_assert_meshtex_operator()
	print("ZIP_UPDATE_OK", new_module.bl_info["name"], new_module.bl_info["version"])


if __name__ == "__main__":
	try:
		main()
	except Exception:
		traceback.print_exc()
		raise SystemExit(1)
