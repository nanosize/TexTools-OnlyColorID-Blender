from pathlib import Path
import ast
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = REPO_ROOT / "addon_src" / "textools_mini_blender"
EXPECTED_FILES = {
	"__init__.py",
	"mini_bake.py",
	"mini_color.py",
	"op_color_assign.py",
	"op_color_clear.py",
	"op_color_convert_texture.py",
	"op_color_convert_vertex_colors.py",
	"op_color_from_directions.py",
	"op_color_from_elements.py",
	"op_color_from_materials.py",
	"op_color_io_export.py",
	"op_color_io_import.py",
	"op_color_select.py",
	"op_color_select_vertex.py",
	"op_meshtex_create.py",
	"op_meshtex_pattern.py",
	"op_meshtex_trim.py",
	"op_meshtex_trim_collapse.py",
	"op_meshtex_wrap.py",
	"op_select_islands_outline.py",
	"settings.py",
	"utilities_meshtex.py",
	"utilities_ui.py",
	"utilities_uv.py",
}


def _parse(path: Path) -> ast.AST:
	return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_addon_file_set_is_minimal():
	actual = {path.name for path in ADDON_DIR.glob("*.py")}
	assert actual == EXPECTED_FILES


def test_source_files_parse():
	for path in ADDON_DIR.glob("*.py"):
		_parse(path)


def test_bl_info_targets_blender_5():
	module = _parse(ADDON_DIR / "__init__.py")
	bl_info = None
	for node in module.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == "bl_info":
					bl_info = ast.literal_eval(node.value)
	assert bl_info is not None
	assert bl_info["name"] == "TexTools-mini-Blender"
	assert tuple(bl_info["blender"]) >= (5, 0, 0)


def test_operator_namespace_is_ttmini():
	pattern = re.compile(r'bl_idname\s*=\s*"([^"]+)"')
	for path in ADDON_DIR.glob("op_*.py"):
		content = path.read_text(encoding="utf-8")
		for match in pattern.finditer(content):
			assert ".textools_" not in match.group(1)
			assert ".ttmini_" in match.group(1)


def test_mini_color_get_material_is_not_recursive():
	module = _parse(ADDON_DIR / "mini_color.py")
	get_material = None
	for node in module.body:
		if isinstance(node, ast.FunctionDef) and node.name == "get_material":
			get_material = node
			break
	assert get_material is not None

	for call in ast.walk(get_material):
		if not isinstance(call, ast.Call):
			continue
		if isinstance(call.func, ast.Name):
			assert call.func.id != "assign_color"
