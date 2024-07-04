import bpy
from bpy.types import NodeTree, Image, Object, Context, Node
from mathutils import Vector

SRC_BSDF_ID     = "MSFSBake_Input_BSDF" 
SRC_COLOR_ID    = "MSFSBake_Input_ColorMap"
SRC_NRM_ID      = "MSFSBake_Input_NormalMap"
SRC_NRM_CONV_ID = "MSFSBake_Input_NormalMapConverter"

DST_MATERIAL_NAME = "MSFSBake_Output_Material"
DST_NODE_NAME     = "MSFSBake_Output_Node"
DST_TEXTURE_NAME  = "MSFSBake_Output_Texture"


def get_output_node(ntree: NodeTree) -> Node:
    for node in ntree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            return node

    return ntree.nodes.new("ShaderNodeOutputMaterial")


def add_node_unique(ntree: NodeTree, name: str, type: str, location: Vector) -> Node:
    node = ntree.nodes.get(name, None)
    if node is None:
        node = ntree.nodes.new(type)
        node.name = name
        
    node.label = name
        
    node.location = location
    return node


def remove_node(ntree: NodeTree, name: str) -> None:
    node_to_delete = ntree.nodes.get(name, None)
    if node_to_delete is not None:
        ntree.nodes.remove( node_to_delete )


def setup_render_settings(context: Context) -> None:
    settings = context.window_manager.msfs_properties
    render = bpy.data.scenes["Scene"].render
    
    # Save settings
    settings.prev_engine = render.engine

    settings.prev_src_hidden = settings.src_obj.hide_get()
    settings.prev_dst_hidden = settings.dst_obj.hide_get()

    settings.prev_selection = bpy.context.view_layer.objects.selected
    settings.prev_active = bpy.context.view_layer.objects.active

    # Setup
    bpy.ops.object.mode_set(mode='OBJECT')

    render.engine ='CYCLES'

    bpy.ops.object.select_all(action='DESELECT')
    settings.src_obj.select_set(True)
    settings.dst_obj.select_set(True)
    bpy.context.view_layer.objects.active = settings.dst_obj


def setup_source(src_obj: Object, img: Image, type: str) -> None:
    mat = src_obj.active_material
    tree = mat.node_tree
    links = tree.links

    output = get_output_node(tree)

    # Base Shader    
    bsdf = add_node_unique(tree, SRC_BSDF_ID, 'ShaderNodeBsdfDiffuse', output.location + Vector((-200, 200)))

    if type == 'DIFFUSE' or type == 'COMPOSITE':
        albd = add_node_unique(tree, SRC_COLOR_ID, "ShaderNodeTexImage", output.location + Vector((-500, 500)))
        albd.image = img
        links.new( albd.outputs['Color'], bsdf.inputs['Color'] )

    elif type == 'NORMAL':
        nrm = add_node_unique(tree, SRC_NRM_ID, "ShaderNodeTexImage", output.location + Vector((-700, 0)))
        nrm.image = img
        nrm_conv = add_node_unique(tree, SRC_NRM_CONV_ID, "ShaderNodeNormalMap", output.location + Vector((-400, 0)))
        links.new( nrm.outputs['Color'], nrm_conv.inputs['Color'] )
        links.new( nrm_conv.outputs['Normal'], bsdf.inputs['Normal'] )

    # Redirect Output
    links.new( bsdf.outputs['BSDF'], output.inputs['Surface'] )


def setup_destination(dst_obj: Object, w: int, h: int) -> Image:
    mat = bpy.data.materials.get(DST_MATERIAL_NAME)
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name=DST_MATERIAL_NAME)

    dst_obj.data.materials.append(mat)
    dst_obj.active_material = mat

    mat.use_nodes = True
    ntree_out = mat.node_tree

    output_node = add_node_unique(ntree_out, DST_NODE_NAME, "ShaderNodeTexImage", Vector((0, 0)))

    output_node.image = bpy.data.images.get(DST_TEXTURE_NAME, None)
    if output_node.image is None:
        output_node.image = bpy.data.images.new(DST_TEXTURE_NAME, width=w, height=h)

    output_node.select = True
    ntree_out.nodes.active = output_node
    return output_node.image

def save_img(img: Image, folder: str, filename: str, suffix: str) -> None:
    img.filepath_raw = f'{folder}\\{filename}_{suffix}.png'
    img.file_format = 'PNG'
    img.save()


def restore_render_settings(context: Context) -> None:
    settings = context.window_manager.msfs_properties
    render = bpy.data.scenes["Scene"].render

    # Restore settings
    if settings.prev_engine == 'EEVEE':
        render.engine = 'EEVEE'
    if settings.prev_engine == 'WORKBENCH':
        render.engine = 'WORKBENCH'

    settings.src_obj.hide_set(settings.prev_src_hidden)
    settings.dst_obj.hide_set(settings.prev_dst_hidden)

    bpy.context.view_layer.objects.selected = settings.prev_selection
    bpy.context.view_layer.objects.active   = settings.prev_active


def restore_source(src_obj: Object) -> None:
    # Remove extra added nodes
    mat = src_obj.active_material
    tree = mat.node_tree
    links = tree.links
    remove_node(tree, SRC_BSDF_ID)
    remove_node(tree, SRC_COLOR_ID)
    remove_node(tree, SRC_NRM_ID)
    remove_node(tree, SRC_NRM_CONV_ID)

    # Relink default msfs shader
    shader = tree.nodes.get('Principled BSDF', None)
    output = get_output_node(tree)
    if shader is not None:
        links.new( shader.outputs['BSDF'], output.inputs['Surface'] )


def restore_destination(dst_obj: Object) -> None:
    m = bpy.data.materials.get(DST_MATERIAL_NAME, None)
    if m is not None:
        bpy.data.materials.remove(m)

    x = dst_obj.material_slots.get('', None)
    while x is not None:
        dst_obj.active_material_index = x.slot_index
        bpy.ops.object.material_slot_remove()

        x = dst_obj.material_slots.get('', None)
