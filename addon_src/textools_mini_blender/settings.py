import bpy


bversion = float(f"{bpy.app.version[0]}.{bpy.app.version[1]}")

selection_uv_mode = ""
selection_uv_loops = set()
selection_uv_pivot = ""
selection_uv_pivot_pos = (0, 0)

use_uv_sync = False
selection_mode = [False, False, True]
selection_vert_indexies = set()
selection_edge_indexies = set()
selection_face_indexies = set()
seam_edges = set()


def tt_settings():
	return bpy.context.scene.ttmini_settings


def prefs():
	return bpy.context.preferences.addons[__package__].preferences
