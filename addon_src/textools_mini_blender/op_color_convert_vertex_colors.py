import bpy

from . import mini_color


gamma = 2.2



class op(bpy.types.Operator):
	bl_idname = "uv.ttmini_color_convert_to_vertex_colors"
	bl_label = "Pack Texture"
	bl_description = "Pack ID Colors into single texture and UVs"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if len(bpy.context.selected_objects) != 1:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True


	def execute(self, context):
		convert_vertex_colors(self, context)
		return {'FINISHED'}



def convert_vertex_colors(self, context):
	obj = bpy.context.active_object
	layer = mini_color.ensure_color_layer(obj.data)

	for i in range(len(obj.material_slots)):
		slot = obj.material_slots[i]
		if slot.material:
			color = list(mini_color.get_color(i))
			color[0] = pow(color[0], 1 / gamma)
			color[1] = pow(color[1], 1 / gamma)
			color[2] = pow(color[2], 1 / gamma)
			rgba = mini_color.safe_color(color)

			for polygon in obj.data.polygons:
				if polygon.material_index != i:
					continue
				for loop_index in polygon.loop_indices:
					layer.data[loop_index].color = rgba

	obj.data.update()
	mini_color.update_properties_tab()
	mini_color.update_view_mode()
	bpy.ops.ui.ttmini_popup('INVOKE_DEFAULT', message="Vertex colors assigned")
