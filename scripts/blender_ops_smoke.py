from __future__ import annotations

import pathlib
import sys
import traceback

import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
ADDON_ROOT = ROOT / "addon_src"
sys.path.insert(0, str(ADDON_ROOT))


def _set_face_selection(obj, polygon_index: int) -> None:
	mesh = obj.data
	face_attr = mesh.attributes[".uv_select_face"]
	vert_attr = mesh.attributes[".uv_select_vert"]
	edge_attr = mesh.attributes[".uv_select_edge"]
	mesh_face_attr = mesh.attributes[".select_poly"]

	for entry in face_attr.data:
		entry.value = False
	for entry in vert_attr.data:
		entry.value = False
	for entry in edge_attr.data:
		entry.value = False
	for entry in mesh_face_attr.data:
		entry.value = False

	mesh_face_attr.data[polygon_index].value = True
	face_attr.data[polygon_index].value = True
	for loop_index in mesh.polygons[polygon_index].loop_indices:
		vert_attr.data[loop_index].value = True
		edge_attr.data[loop_index].value = True


def _assert_color_assign() -> None:
	from textools_mini_blender import mini_color, op_color_assign
	from textools_mini_blender.settings import tt_settings

	bpy.ops.object.select_all(action="DESELECT")
	bpy.ops.mesh.primitive_cube_add()
	obj = bpy.context.active_object
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

	tt_settings().color_assign_mode = "MATERIALS"
	op_color_assign.assign_color(None, bpy.context, 0)

	material = obj.material_slots[0].material
	assert material is not None
	expected = mini_color.safe_color(mini_color.get_color(0))
	assert tuple(round(value, 5) for value in material.diffuse_color[:4]) == tuple(
		round(value, 5) for value in expected
	)


def _assert_uv_mesh_create() -> None:
	from textools_mini_blender import op_meshtex_create

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
	result = op_meshtex_create.create_uv_mesh(
		None,
		bpy.context,
		obj,
		restore_selected=True,
	)
	assert isinstance(result, tuple) and len(result) == 3

	uv_mesh = bpy.data.objects.get(f"{obj.name}_UV_Mesh")
	assert uv_mesh is not None
	bpy.ops.object.mode_set(mode="OBJECT")
	bpy.context.view_layer.objects.active = uv_mesh
	uv_mesh.select_set(True)
	uv_mesh.update_from_editmode()
	assert len(uv_mesh.data.polygons) == 1
	assert uv_mesh.data.shape_keys is not None
	assert "uv" in uv_mesh.data.shape_keys.key_blocks
	assert all(abs(vertex.co.z) <= 1e-6 for vertex in uv_mesh.data.vertices)


def main() -> None:
	import textools_mini_blender

	textools_mini_blender.register()
	try:
		_assert_color_assign()
		_assert_uv_mesh_create()
		print("OPS_OK", textools_mini_blender.bl_info["name"], textools_mini_blender.bl_info["version"])
	finally:
		textools_mini_blender.unregister()


if __name__ == "__main__":
	try:
		main()
	except Exception:
		traceback.print_exc()
		raise SystemExit(1)
