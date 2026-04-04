from __future__ import annotations

import pathlib
import traceback

import addon_utils
import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_NAME = "textools_mini_blender"


def _latest_clean_zip() -> pathlib.Path:
	candidates = sorted(ROOT.joinpath("dist").glob("TexTools-mini-Blender-*-clean.zip"))
	if not candidates:
		raise FileNotFoundError("clean zip not found in dist/")
	return candidates[-1]


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


def _assert_color_assign(module) -> None:
	bpy.ops.object.select_all(action="DESELECT")
	bpy.ops.mesh.primitive_cube_add()
	obj = bpy.context.active_object
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

	bpy.context.scene.ttmini_settings.color_assign_mode = "MATERIALS"
	module.op_color_assign.assign_color(None, bpy.context, 0)

	material = obj.material_slots[0].material
	assert material is not None


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

	uv_mesh = bpy.data.objects.get(f"{obj.name}_UV_Mesh")
	assert uv_mesh is not None
	bpy.ops.object.mode_set(mode="OBJECT")
	bpy.context.view_layer.objects.active = uv_mesh
	uv_mesh.select_set(True)
	uv_mesh.update_from_editmode()
	assert len(uv_mesh.data.polygons) == 1


def main() -> None:
	zip_path = _latest_clean_zip()
	bpy.ops.preferences.addon_install(filepath=str(zip_path), overwrite=True)
	addon_utils.enable(MODULE_NAME, default_set=False)
	assert addon_utils.check(MODULE_NAME)[1]

	module = __import__(MODULE_NAME)
	print("ZIP_MODULE", module.__file__)
	print("ZIP_USED", zip_path.name)

	_assert_color_assign(module)
	_assert_meshtex_operator()
	print("ZIP_OPS_OK", module.bl_info["name"], module.bl_info["version"])


if __name__ == "__main__":
	try:
		main()
	except Exception:
		traceback.print_exc()
		raise SystemExit(1)
