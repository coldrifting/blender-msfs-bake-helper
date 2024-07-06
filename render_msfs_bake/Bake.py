import bpy
import re
from bpy.types import Context, Object, Image, NodeTree, ShaderNodeTexImage, ShaderNodeOutputMaterial, ShaderNodeBsdfDiffuse, ShaderNodeNormalMap, Material
from . Settings import MSFSBake_Settings

SRC_OBJ_NAME = "MSFSBake_Input_Object_Copy"
DST_OBJ_NAME = "MSFSBake_Output_Object_Copy"

SRC_MATERIAL_NAME = "MSFSBake_Input_Material"
DST_MATERIAL_NAME = "MSFSBake_Output_Material"
DST_TEXTURE_NAME  = "MSFSBake_Output_Texture"

class MSFSBake_Bake(bpy.types.Operator):
    bl_idname = "msfsbake.bake"
    bl_label = "Bake selected mesh maps"
    bl_description = "Bakes all selected mesh maps"

    def execute(self, context: Context) -> None:
        settings : MSFSBake_Settings = context.scene.msfs_properties

        # Basic validation
        if settings.src_obj is None or settings.dst_obj is None:
           self.report({"ERROR"}, "Input or target object not set")
           return {"CANCELLED"}
        
        if settings.src_obj == settings.dst_obj:
           self.report({"ERROR"}, "Input and target objects can not be the same")
           return {"CANCELLED"}
        
        if (not settings.render_is_diffuse_enabled and 
            not settings.render_is_normal_enabled and 
            not settings.render_is_composite_enabled):
           self.report({"ERROR"}, "No textures selected to bake")
           return {"CANCELLED"}
        
        if settings.src_obj.active_material is None:
           self.report({"ERROR"}, "Input object has no material")
           return {"CANCELLED"}

        # Get input images
        tex_color : Image = settings.src_obj.active_material.msfs_base_color_texture
        if tex_color is None and settings.render_is_diffuse_enabled:
            tex_color = find_image(settings.src_obj.active_material, ["ALBD", "DIFF", "COL"])
            
        tex_normal : Image = settings.src_obj.active_material.msfs_normal_texture
        if tex_normal is None and settings.render_is_normal_enabled:
            tex_normal = find_image(settings.src_obj.active_material, ["NORM", "NRM"])

        tex_composite : Image = settings.src_obj.active_material.msfs_occlusion_metallic_roughness_texture
        if tex_composite is None and settings.render_is_composite_enabled:
            tex_composite = find_image(settings.src_obj.active_material, ["COMP"])
            
        # Texture validation
        if tex_color is None and settings.render_is_diffuse_enabled:
            self.report({"ERROR"}, "No color map found on input object to bake")
            return {"CANCELLED"}
        
        if tex_normal is None and settings.render_is_normal_enabled:
            self.report({"ERROR"}, "No normal map found on input object to bake")
            return {"CANCELLED"}
        
        if tex_composite is None and settings.render_is_composite_enabled:
            self.report({"ERROR"}, "No composite map found on input object to bake")
            return {"CANCELLED"}



        # Setup high poly source object
        src : Object = settings.src_obj.copy()
        src.data = src.data.copy()
        src.name = SRC_OBJ_NAME
        src.hide_render = False

        # Setup high poly material
        src_mat = bpy.data.materials.new(name=SRC_MATERIAL_NAME)
        src_mat.use_nodes = True
        src_mat.node_tree.nodes.clear()
        src_out_node : ShaderNodeOutputMaterial = src_mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        src_bsdf_node : ShaderNodeBsdfDiffuse = src_mat.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        src_mat.node_tree.links.new(src_out_node.inputs['Surface'], src_bsdf_node.outputs['BSDF'])
        src.active_material = src_mat

        # Setup low poly destination object
        dst : Object = settings.dst_obj.copy()
        dst.data = dst.data.copy()
        dst.name = DST_OBJ_NAME
        dst.hide_render = False

        # Setup low poly material
        dst_mat = bpy.data.materials.new(name=DST_MATERIAL_NAME)
        dst.data.materials.clear()
        dst.data.materials.append(dst_mat)
        dst.active_material = dst_mat

        dst_mat.use_nodes = True
        ntree_out : NodeTree = dst_mat.node_tree
        dst_output_node : ShaderNodeTexImage = dst_mat.node_tree.nodes.new("ShaderNodeTexImage")
        dst_output_node.image = bpy.data.images.new(DST_TEXTURE_NAME, width=settings.output_width, height=settings.output_height)
        dst_output_node.select = True
        ntree_out.nodes.active = dst_output_node
        
        # Bake
        bpy.context.view_layer.layer_collection.collection.objects.link(src)
        bpy.context.view_layer.layer_collection.collection.objects.link(dst)

        # Adjust position
        if settings.obj_align:
            dst.location = src.location

        bpy.data.scenes["Scene"].render.engine = 'CYCLES'
        image_out : Image = dst_output_node.image

        objs = [src, dst]
        with bpy.context.temp_override(selected_objects=objs, active_object=dst):
            if settings.render_is_diffuse_enabled:
                # Diffuse
                src_tex_color_node : ShaderNodeTexImage = src_mat.node_tree.nodes.new("ShaderNodeTexImage")
                src_tex_color_node.image = tex_color
                src_mat.node_tree.links.new(src_bsdf_node.inputs['Color'], src_tex_color_node.outputs['Color'])

                bake(settings, 'DIFFUSE')
                save_image(image_out, settings.output_folder, settings.output_file_prefix, "ABLD")

            if settings.render_is_normal_enabled:
                # Normal
                src_normal_map_node : ShaderNodeNormalMap = src_mat.node_tree.nodes.new("ShaderNodeNormalMap")
                src_tex_normal_node : ShaderNodeTexImage = src_mat.node_tree.nodes.new("ShaderNodeTexImage")
                src_tex_normal_node.image = tex_normal

                src_mat.node_tree.links.new(src_normal_map_node.inputs['Color'], src_tex_normal_node.outputs['Color'])
                src_mat.node_tree.links.new(src_bsdf_node.inputs['Normal'], src_normal_map_node.outputs['Normal'])

                bake(settings, 'NORMAL')
                save_image(image_out, settings.output_folder, settings.output_file_prefix, "NORM")

            if settings.render_is_composite_enabled:
                # Composite
                src_tex_composite_node : ShaderNodeTexImage = src_mat.node_tree.nodes.new("ShaderNodeTexImage")
                src_tex_composite_node.image = tex_composite
                src_mat.node_tree.links.new(src_bsdf_node.inputs['Color'], src_tex_composite_node.outputs['Color'])
                
                bake(settings, 'COMPOSITE')
                save_image(image_out, settings.output_folder, settings.output_file_prefix, "COMP")

        cleanup(objs, src_mat, dst_mat)
        
        return {"FINISHED"}


def cleanup(objs, src_mat, dst_mat):
    # Cleanup copies and extra materials
    with bpy.context.temp_override(selected_objects=objs):
        bpy.ops.object.delete()

    if src_mat is not None:
        bpy.data.materials.remove(src_mat)

    if dst_mat is not None:
        bpy.data.materials.remove(dst_mat)



def bake(settings: MSFSBake_Settings, bake_type : str):
    bpy.ops.object.bake(type='NORMAL' if bake_type == 'NORMAL' else 'DIFFUSE',
                        margin_type='EXTEND',
                        margin=settings.output_padding,
                        use_selected_to_active=True,
                        max_ray_distance=settings.render_ray_dist,
                        cage_extrusion=settings.render_extrusion,
                        pass_filter={'COLOR'} if bake_type != "Normal" else None)


def find_image(src_mat: Material, search_suffix : list[str]) -> Image | None:
    if src_mat is not None and src_mat.use_nodes is True:
        regex_name = re.compile(r"^.*_(" + "|".join(search_suffix) + r")$", re.IGNORECASE)          
        regex_file = re.compile(r"^.*_(" + "|".join(search_suffix) + r").*\.(PNG|DDS)$", re.IGNORECASE)            
        for node in src_mat.node_tree.nodes:
            if isinstance(node, ShaderNodeTexImage):
                if regex_file.match(node.image.filepath) or regex_name.match(node.image.name):
                    return node.image
            
    return None


def save_image(img: Image, folder: str, filename: str, suffix: str) -> None:
    img.filepath_raw = f'{folder}\\{filename}_{suffix}.png'
    img.file_format = 'PNG'
    img.save()
