import bpy
from bpy.types import Context

from . BakeUtils import (
    setup_source,
    setup_destination,
    setup_render_settings,

    restore_render_settings,
    restore_source,
    restore_destination,

    save_img
)


class MSFSBake_Bake(bpy.types.Operator):
    bl_idname = "msfsbake.bake"
    bl_label = "Bake selected mesh maps"
    bl_description = "Bakes all selected mesh maps"

    def execute(self, context: Context) -> None:
        settings = context.window_manager.msfs_properties

        # Check settings are valid
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
        
        color_tex = settings.src_obj.active_material.msfs_base_color_texture
        normal_tex = settings.src_obj.active_material.msfs_normal_texture
        composite_tex = settings.src_obj.active_material.msfs_occlusion_metallic_roughness_texture

        if settings.render_is_diffuse_enabled and color_tex is None:
           self.report({"ERROR"}, "No color map found on input object to bake")
           return {"CANCELLED"}
        
        if settings.render_is_normal_enabled and normal_tex is None:
           self.report({"ERROR"}, "No normal map found on input object to bake")
           return {"CANCELLED"}
        
        if settings.render_is_composite_enabled and composite_tex is None:
           self.report({"ERROR"}, "No composite map found on input object to bake")
           return {"CANCELLED"}
        
        # Setup for bake
        setup_render_settings(context)
        img_output = setup_destination(settings.dst_obj, settings.output_width, settings.output_height)

        # Attempt bake
        try:
            if settings.render_is_diffuse_enabled:
                setup_source(settings.src_obj, color_tex, 'DIFFUSE')

                bpy.ops.object.bake(type="DIFFUSE",
                                    margin_type='EXTEND',
                                    margin=settings.output_padding,
                                    use_selected_to_active=True,
                                    max_ray_distance=settings.render_ray_dist,
                                    cage_extrusion=settings.render_extrusion,)

                save_img(img_output, settings.output_folder, settings.output_file_prefix, "ALBD")

            if settings.render_is_normal_enabled:
                setup_source(settings.src_obj, normal_tex, 'NORMAL')

                bpy.ops.object.bake(type='NORMAL', 
                                    margin_type='EXTEND',
                                    margin=settings.output_padding,
                                    use_selected_to_active=True,
                                    max_ray_distance=settings.render_ray_dist,
                                    cage_extrusion=settings.render_extrusion)
                
                save_img(img_output, settings.output_folder, settings.output_file_prefix, "NORM")

            if settings.render_is_composite_enabled:
                setup_source(settings.src_obj, composite_tex, 'COMPOSITE')

                bpy.ops.object.bake(type="DIFFUSE",
                                    margin_type='EXTEND',
                                    margin=settings.output_padding,
                                    use_selected_to_active=True,
                                    max_ray_distance=settings.render_ray_dist,
                                    cage_extrusion=settings.render_extrusion)

                save_img(img_output, settings.output_folder, settings.output_file_prefix, "COMP")

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.report({"ERROR"}, "An error occured while baking")
            return {'CANCELLED'}

        finally:
            restore_source(settings.src_obj)
            restore_destination(settings.dst_obj)
            restore_render_settings(context)
            return {'FINISHED'}