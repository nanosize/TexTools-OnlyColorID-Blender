import bpy
import bmesh


class op(bpy.types.Operator):
	bl_idname = "uv.ttmini_meshtex_create"
	bl_label = "UV Mesh"
	bl_description = "Create a new Mesh from the selected UVs of the active Object"
	bl_options = {'REGISTER', 'UNDO'}

	#apply_scale : bpy.props.BoolProperty(name="Scale to Object", default=True, description="Apply scale to the UV Mesh for its extent to be similar to the Object dimensions.")

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		return create_uv_mesh(self, context, bpy.context.active_object)


def _get_mesh_attribute(mesh, name):
	try:
		return mesh.attributes[name]
	except (AttributeError, KeyError):
		return None


def _uv_equals(uv_a, uv_b, epsilon=1e-6):
	return (uv_a - uv_b).length <= epsilon


def _loops_share_uv_edge(loop_a, loop_b, uv_layer):
	return (
		_uv_equals(loop_a[uv_layer].uv, loop_b.link_loop_next[uv_layer].uv)
		and _uv_equals(loop_a.link_loop_next[uv_layer].uv, loop_b[uv_layer].uv)
	)


def _snapshot_uv_face_selection(obj, select_all=False):
	mesh = obj.data
	if select_all:
		return {polygon.index for polygon in mesh.polygons}

	selected_faces = set()
	selected_loops = set()

	uv_face_attr = _get_mesh_attribute(mesh, ".uv_select_face")
	if uv_face_attr is not None:
		selected_faces.update(
			index
			for index, entry in enumerate(uv_face_attr.data)
			if entry.value
		)

	uv_vert_attr = _get_mesh_attribute(mesh, ".uv_select_vert")
	if uv_vert_attr is not None:
		selected_loops.update(
			index
			for index, entry in enumerate(uv_vert_attr.data)
			if entry.value
		)

	for polygon in mesh.polygons:
		if any(loop_index in selected_loops for loop_index in polygon.loop_indices):
			selected_faces.add(polygon.index)

	mesh_face_attr = _get_mesh_attribute(mesh, ".select_poly")
	if mesh_face_attr is not None and not selected_faces:
		mesh_selected_faces = {
			index
			for index, entry in enumerate(mesh_face_attr.data)
			if entry.value
		}
		selected_faces = mesh_selected_faces

	return selected_faces


def _collect_islands(selected_faces, uv_layer):
	remaining = set(selected_faces)
	islands = []

	while remaining:
		face = remaining.pop()
		island = {face}
		stack = [face]

		while stack:
			current = stack.pop()
			for loop in current.loops:
				for linked_loop in loop.edge.link_loops:
					linked_face = linked_loop.face
					if linked_face is current or linked_face not in remaining:
						continue
					if _loops_share_uv_edge(loop, linked_loop, uv_layer):
						remaining.remove(linked_face)
						island.add(linked_face)
						stack.append(linked_face)
						break

		islands.append(island)

	return islands


def _collect_boundary_edges(islands, uv_layer):
	face_to_island = {
		face: island_index
		for island_index, island in enumerate(islands)
		for face in island
	}
	selected_faces = set(face_to_island)
	boundary_edges = set()

	for face in selected_faces:
		for loop in face.loops:
			edge = loop.edge
			linked_loops = [linked for linked in edge.link_loops if linked.face in selected_faces]
			if len(linked_loops) <= 1:
				boundary_edges.add(edge)
				continue

			if any(
				face_to_island[linked.face] != face_to_island[face]
				for linked in linked_loops
				if linked.face is not face
			):
				boundary_edges.add(edge)
				continue

			if not any(
				linked.face is not face and _loops_share_uv_edge(loop, linked, uv_layer)
				for linked in linked_loops
			):
				boundary_edges.add(edge)

	return boundary_edges


def _has_uv_select_mode_context():
	screen = getattr(bpy.context, "screen", None)
	if screen is None:
		return False
	for area in screen.areas:
		if area.type != "IMAGE_EDITOR":
			continue
		if getattr(area, "ui_type", None) == "UV":
			return True
	return False



def create_uv_mesh(self, context, obj, sk_create=True, bool_scale=True, delete_unselected=True, restore_selected=False):
	# New object management
	mode = bpy.context.active_object.mode
	bpy.ops.object.mode_set(mode='OBJECT')
	selected_face_indices = _snapshot_uv_face_selection(obj, select_all=(mode == 'OBJECT'))
	bpy.ops.object.select_all(action='DESELECT')

	mesh_obj = obj.copy()
	mesh_obj.data = obj.data.copy()
	obj.users_collection[0].objects.link(mesh_obj)

	mesh_obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = mesh_obj
	
	obj_name = mesh_obj.name = obj.name + "_UV_Mesh"

	# Shape Keys management
	if mesh_obj.data.shape_keys:
		if len(mesh_obj.data.shape_keys.key_blocks) > 1:
			for i in range(len(mesh_obj.data.shape_keys.key_blocks)):
				bpy.context.object.active_shape_key_index = 0
				bpy.ops.object.shape_key_remove(all=False)
	if sk_create:
		mesh_obj.shape_key_add(name="model", from_mix=True)
		mesh_obj.shape_key_add(name="uv", from_mix=True)
		mesh_obj.active_shape_key_index = 1
		bpy.context.active_object.active_shape_key.value = 1

	bpy.ops.object.mode_set(mode='EDIT')

	selection_mode = bpy.context.scene.tool_settings.uv_select_mode
	pre_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	bpy.context.scene.tool_settings.use_uv_select_sync = False

	bm = bmesh.from_edit_mesh(mesh_obj.data)
	bm.faces.ensure_lookup_table()
	uv_layers = bm.loops.layers.uv.verify()
	selected_faces = {
		bm.faces[index]
		for index in selected_face_indices
		if index < len(bm.faces)
	}

	faces_by_island = _collect_islands(selected_faces, uv_layers)

	if not faces_by_island:
		bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
		obj.select_set( state = True, view_layer = None)
		bpy.context.view_layer.objects.active = obj
		bpy.context.scene.tool_settings.use_uv_select_sync = pre_sync
		bpy.ops.object.mode_set(mode=mode)
		if not restore_selected:
			return {'CANCELLED'}
		else:	# For the Relax operator
			return {'CANCELLED'}, None, None

	if delete_unselected:
		if mode != 'OBJECT':
			delete_faces = list({face for faces in faces_by_island for face in faces}.symmetric_difference(bm.faces))
			if delete_faces:
				bmesh.ops.delete(bm, geom=delete_faces, context='FACES')
	else:	# Needed for the Relax operator
	 	#for face in {face for faces in faces_by_island for face in faces}.symmetric_difference(bm.faces):
		#	if face.select:
		#		face.select_set(False)
		#bpy.ops.mesh.split()
		bpy.ops.mesh.select_all(action='DESELECT')
		selection_loops = {loop for faces in faces_by_island for face in faces for loop in face.loops}
		for faces in faces_by_island:
			for face in faces:
				for edge in face.edges:
					if not set(edge.link_loops).issubset(selection_loops):
						edge.select_set(True)
		bpy.ops.mesh.edge_split(type='EDGE')
		bmesh.update_edit_mesh(mesh_obj.data)
		bpy.ops.mesh.select_all(action='SELECT')	#TODO REFINE

	if bool_scale:
		length_view = 0
		length_uv = 0
		for faces in faces_by_island:
			for face in faces:
				length_uv += (face.loops[0].link_loop_next[uv_layers].uv - face.loops[0][uv_layers].uv).length
				length_view += face.loops[0].edge.calc_length()

	# Reshape mesh to mimic UVs
	for faces in faces_by_island:
		for face in faces:
			for loop in face.loops:
				loop.vert.co = (loop[uv_layers].uv.x, loop[uv_layers].uv.y, 0)

	#Scale
	if bool_scale:
		if length_uv > 0 and length_view > 0:
			scale = length_view / length_uv
		else:
			scale = 1

		scaled_verts = set()
		for faces in faces_by_island:
			for face in faces:
				for loop in face.loops:
					if loop.vert not in scaled_verts:
						loop.vert.co *= scale
						scaled_verts.add(loop.vert)

	boundary_edges = _collect_boundary_edges(faces_by_island, uv_layers)
	if boundary_edges:
		bmesh.ops.split_edges(bm, edges=list(boundary_edges))

	bmesh.update_edit_mesh(mesh_obj.data)
	bpy.context.scene.tool_settings.use_uv_select_sync = pre_sync

	if mode == 'EDIT' and not restore_selected:
		# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
		if _has_uv_select_mode_context():
			bpy.ops.uv.select_mode(type='VERTEX')
		bpy.context.scene.tool_settings.uv_select_mode = selection_mode
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.mode_set(mode=mode)
	else:
		bpy.ops.object.mode_set(mode=mode)


	if not restore_selected:
		return {'FINISHED'}
	else:	# For the Relax operator
		return bm, uv_layers, faces_by_island
