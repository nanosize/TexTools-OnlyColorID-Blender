bl_info = {
	"name": "TexTools-mini-Blender",
	"description": "Color ID and Mesh UV tools for Blender.",
	"author": "renderhjs, franMarz, Sav Martin, OpenAI Codex",
	"version": (0, 1, 0),
	"blender": (5, 0, 0),
	"category": "UV",
	"location": "UV Editor > Sidebar > TexTools-mini",
}


import bpy

from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup

from . import mini_color
from . import op_color_assign
from . import op_color_clear
from . import op_color_convert_texture
from . import op_color_convert_vertex_colors
from . import op_color_from_directions
from . import op_color_from_elements
from . import op_color_from_materials
from . import op_color_io_export
from . import op_color_io_import
from . import op_color_select
from . import op_color_select_vertex
from . import op_meshtex_create
from . import op_meshtex_pattern
from . import op_meshtex_trim
from . import op_meshtex_trim_collapse
from . import op_meshtex_wrap
from . import op_select_islands_outline
from . import utilities_meshtex


MAX_COLOR_IDS = 20


def _palette_defaults():
	defaults = []
	for index in range(MAX_COLOR_IDS):
		color = mini_color.get_color_id(index, MAX_COLOR_IDS)
		defaults.append((color[0], color[1], color[2]))
	return defaults


DEFAULT_PALETTE = _palette_defaults()
TTMINI_Settings_annotations = {}


def on_color_changed(index):
	def _update(self, context):
		mini_color.assign_color(index)
	return _update


def on_color_mode_changed(self, context):
	mini_color.update_properties_tab()
	mini_color.update_view_mode()


def on_meshtexture_wrap_changed(self, context):
	obj_uv = utilities_meshtex.find_uv_mesh(bpy.context.selected_objects)
	if not obj_uv or not obj_uv.data.shape_keys:
		return
	key_blocks = obj_uv.data.shape_keys.key_blocks
	if "uv" in key_blocks:
		key_blocks["uv"].value = self.meshtexture_wrap


class TTMINI_Preferences(AddonPreferences):
	bl_idname = __package__

	bool_color_id_vertex_color_gamma: BoolProperty(
		name="Gamma Correct Vertex Colors",
		description="Apply gamma correction when writing Color IDs into vertex colors",
		default=False,
	)

	def draw(self, context):
		self.layout.prop(self, "bool_color_id_vertex_color_gamma")


class TTMINI_Settings(PropertyGroup):
	color_assign_mode: EnumProperty(
		items=[
			("MATERIALS", "Materials", "Assign Color IDs through material slots"),
			("VERTEXCOLORS", "Vertex Colors", "Assign Color IDs through mesh color attributes"),
		],
		name="Mode",
		default="MATERIALS",
		update=on_color_mode_changed,
	)
	color_ID_count: IntProperty(
		name="Colors",
		description="Number of Color ID entries to show",
		default=6,
		min=1,
		max=MAX_COLOR_IDS,
	)
	vertex_color_threshold: FloatProperty(
		name="Threshold",
		description="Tolerance used when selecting by vertex color",
		default=0.01,
		min=0.0001,
		max=1.0,
	)
	meshtexture_wrap: FloatProperty(
		name="Wrap",
		description="Morph factor stored on the generated UV mesh",
		default=1.0,
		min=0.0,
		max=1.0,
		subtype="FACTOR",
		update=on_meshtexture_wrap_changed,
	)


for index, color in enumerate(DEFAULT_PALETTE):
	TTMINI_Settings_annotations[f"color_ID_color_{index}"] = FloatVectorProperty(
		name=f"Color {index + 1}",
		subtype="COLOR",
		size=3,
		min=0.0,
		max=1.0,
		default=color,
		update=on_color_changed(index),
	)


TTMINI_Settings.__annotations__.update(TTMINI_Settings_annotations)


class TTMINI_OT_popup(Operator):
	bl_idname = "ui.ttmini_popup"
	bl_label = "TexTools-mini-Blender"

	message: StringProperty()

	def execute(self, context):
		self.report({"INFO"}, self.message)
		return {"FINISHED"}

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self, width=320)

	def draw(self, context):
		self.layout.label(text=self.message)


class TTMINI_PT_base(Panel):
	bl_space_type = "IMAGE_EDITOR"
	bl_region_type = "UI"
	bl_category = "TexTools-mini"

	@classmethod
	def poll(cls, context):
		return context.area is not None and context.area.ui_type == "UV"


class TTMINI_PT_color_id(TTMINI_PT_base):
	bl_idname = "TTMINI_PT_color_id"
	bl_label = "Color ID"

	def draw(self, context):
		layout = self.layout
		settings = context.scene.ttmini_settings

		layout.prop(settings, "color_assign_mode", expand=True)

		row = layout.row(align=True)
		row.prop(settings, "color_ID_count")
		row.operator(op_color_clear.op.bl_idname, text="Clear", icon="TRASH")

		row = layout.row(align=True)
		row.operator(op_color_io_import.op.bl_idname, text="Import", icon="PASTEDOWN")
		row.operator(op_color_io_export.op.bl_idname, text="Export", icon="COPYDOWN")

		row = layout.row(align=True)
		row.operator(op_color_from_elements.op.bl_idname, text="From Elements")
		row.operator(op_color_from_materials.op.bl_idname, text="From Materials")
		row.operator(op_color_from_directions.op.bl_idname, text="From Directions")

		if settings.color_assign_mode == "MATERIALS":
			row = layout.row(align=True)
			row.operator(op_color_convert_texture.op.bl_idname, text="Pack Texture")
			row.operator(op_color_convert_vertex_colors.op.bl_idname, text="To Vertex Colors")
		else:
			layout.prop(settings, "vertex_color_threshold")

		select_operator = op_color_select.op.bl_idname
		if settings.color_assign_mode != "MATERIALS":
			select_operator = op_color_select_vertex.op.bl_idname

		grid = layout.grid_flow(columns=2, even_columns=True, even_rows=True, align=True)
		for index in range(settings.color_ID_count):
			box = grid.box()
			column = box.column(align=True)
			column.prop(settings, f"color_ID_color_{index}", text=f"ID {index + 1}")

			row = column.row(align=True)
			assign = row.operator(op_color_assign.op.bl_idname, text="Assign", icon="BRUSH_DATA")
			assign.index = index
			select = row.operator(select_operator, text="Select", icon="RESTRICT_SELECT_OFF")
			select.index = index


class TTMINI_PT_mesh_uv(TTMINI_PT_base):
	bl_idname = "TTMINI_PT_mesh_uv"
	bl_label = "Mesh UV Tool"

	def draw(self, context):
		layout = self.layout
		settings = context.scene.ttmini_settings

		row = layout.row(align=True)
		row.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon="MESH_GRID")
		row.operator(op_meshtex_pattern.op.bl_idname, text="Pattern", icon="MOD_ARRAY")

		layout.prop(settings, "meshtexture_wrap")

		row = layout.row(align=True)
		row.operator(op_meshtex_wrap.op.bl_idname, text="Wrap", icon="MOD_MESHDEFORM")
		row.operator(op_meshtex_trim.op.bl_idname, text="Trim", icon="MOD_BOOLEAN")
		row.operator(op_meshtex_trim_collapse.op.bl_idname, text="Collapse", icon="CHECKMARK")


classes = (
	TTMINI_Preferences,
	TTMINI_Settings,
	TTMINI_OT_popup,
	op_color_assign.op,
	op_color_clear.op,
	op_color_convert_texture.op,
	op_color_convert_vertex_colors.op,
	op_color_from_directions.op,
	op_color_from_elements.op,
	op_color_from_materials.op,
	op_color_io_export.op,
	op_color_io_import.op,
	op_color_select.op,
	op_color_select_vertex.op,
	op_meshtex_create.op,
	op_meshtex_pattern.op,
	op_meshtex_trim.op,
	op_meshtex_trim_collapse.op,
	op_meshtex_wrap.op,
	op_select_islands_outline.op,
	TTMINI_PT_color_id,
	TTMINI_PT_mesh_uv,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.ttmini_settings = PointerProperty(type=TTMINI_Settings)


def unregister():
	if hasattr(bpy.types.Scene, "ttmini_settings"):
		del bpy.types.Scene.ttmini_settings
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
