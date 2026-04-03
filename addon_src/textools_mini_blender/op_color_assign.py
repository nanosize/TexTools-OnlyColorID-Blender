import bpy

from . import mini_color
from .settings import tt_settings, prefs


gamma = 2.2


class op(bpy.types.Operator):
	bl_idname = "uv.ttmini_color_assign"
	bl_label = "Assign Color"
	bl_description = "Assign color to selected Objects or faces in Edit Mode"
	bl_options = {'UNDO'}

	index: bpy.props.IntProperty(description="Color Index", default=0)

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True

	def execute(self, context):
		assign_color(self, context, self.index)
		return {'FINISHED'}


def assign_color(self, context, index):
	selected_obj = bpy.context.selected_objects.copy()

	previous_mode = 'OBJECT'
	if len(selected_obj) == 1:
		previous_mode = bpy.context.active_object.mode

	for obj in selected_obj:
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		obj.select_set(True)
		bpy.context.view_layer.objects.active = obj

		if tt_settings().color_assign_mode == 'MATERIALS':
			bpy.ops.object.mode_set(mode='EDIT')
			if previous_mode == 'OBJECT':
				bpy.ops.mesh.select_all(action='SELECT')

			# Verify material slots
			for _ in range(index+1):
				if index >= len(obj.material_slots):
					bpy.ops.object.material_slot_add()

			mini_color.assign_slot(obj, index)

			# Assign to selection
			obj.active_material_index = index
			bpy.ops.object.material_slot_assign()

		else:  # mode == VERTEXCOLORS
			if previous_mode != 'OBJECT':
				selected_polygons = [polygon.index for polygon in obj.data.polygons if polygon.select]
			else:
				selected_polygons = [polygon.index for polygon in obj.data.polygons]

			color = list(mini_color.get_color(index))
			if prefs().bool_color_id_vertex_color_gamma:
				color[0] = pow(color[0], 1 / gamma)
				color[1] = pow(color[1], 1 / gamma)
				color[2] = pow(color[2], 1 / gamma)

			if not selected_polygons:
				selected_polygons = [polygon.index for polygon in obj.data.polygons]
			mini_color.set_polygons_color(obj, selected_polygons, color)

	# restore mode
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	for obj in selected_obj:
		obj.select_set(True)
	bpy.ops.object.mode_set(mode=previous_mode)

	# Show Material or Data Tab
	mini_color.update_properties_tab()

	# Change View mode
	mini_color.update_view_mode()
