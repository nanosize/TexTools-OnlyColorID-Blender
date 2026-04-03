import bpy


def _build_override(window, screen, area, region):
	return {
		"window": window,
		"screen": screen,
		"area": area,
		"region": region,
		"scene": bpy.context.scene,
		"edit_object": bpy.context.edit_object,
		"active_object": bpy.context.active_object,
		"selected_objects": bpy.context.selected_objects,
	}


def GetContextView3D():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type != "VIEW_3D":
				continue
			for region in area.regions:
				if region.type == "WINDOW":
					return _build_override(window, screen, area, region)
	return None


def GetContextViewUV():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type != "IMAGE_EDITOR" or area.ui_type != "UV":
				continue
			for region in area.regions:
				if region.type == "WINDOW":
					return _build_override(window, screen, area, region)
	return None
