import bpy

from . import mini_color


TEMP_COLOR_LAYER_NAME = "TTMini_temp"


def assign_vertex_color(obj):
	return mini_color.ensure_color_layer(obj.data, TEMP_COLOR_LAYER_NAME)


def get_image_material(image):
	material = bpy.data.materials.get(image.name)
	if material is None:
		material = bpy.data.materials.new(image.name)

	material.use_nodes = True
	nodes = material.node_tree.nodes
	links = material.node_tree.links
	nodes.clear()

	node_output = nodes.new("ShaderNodeOutputMaterial")
	node_output.location = (320, 0)
	node_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
	node_bsdf.location = (80, 0)
	node_image = nodes.new("ShaderNodeTexImage")
	node_image.location = (-220, 0)
	node_image.name = "image"
	node_image.image = image

	links.new(node_image.outputs["Color"], node_bsdf.inputs["Base Color"])
	links.new(node_bsdf.outputs["BSDF"], node_output.inputs["Surface"])
	nodes.active = node_image

	material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
	return material
