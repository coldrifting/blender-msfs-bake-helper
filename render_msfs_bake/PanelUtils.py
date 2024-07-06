import bpy
from bpy.types import Operator, Context, Object

def get_high(context: Context) -> Object:
    settings = context.scene.msfs_properties
    return settings.src_obj


def get_low(context: Context) -> Object:
    settings = context.scene.msfs_properties
    return settings.dst_obj


def prev_pow_of_two(val) -> int:
    newVal = 1 << (val.bit_length() - 1)
    if newVal == val and newVal > bpy.context.scene.msfs_properties.min_res:
        newVal = newVal >> 1

    return newVal


def next_pow_of_two(val) -> int:
    newVal = 1 << val.bit_length()
    if newVal == val and newVal < bpy.context.scene.msfs_properties.max_res:
        newVal = newVal << 1

    return newVal


def toggle_vis(obj: Object) -> None:
    if obj is not None:
        obj.hide_set(not obj.hide_get())

    
class MSFSBake_ToggleHighLowVis(Operator):
    bl_idname = "view3d.toggle_high_low_vis"
    bl_label = "Toggle High / Low poly Mesh"
    bl_description = "Toggles visiblity between High and Low poly mesh in viewport"

    def execute(self, context: Context) -> None:
        obj_high = get_high(context)
        obj_low  = get_low(context)

        if obj_high and obj_low:
            high_vis = obj_high.hide_get()
            low_vis = obj_low.hide_get()

            if high_vis and not low_vis or (high_vis and low_vis) or  (not high_vis and not low_vis):
                obj_low.hide_set(True)
                obj_high.hide_set(False)

            elif (low_vis and not high_vis):
                obj_low.hide_set(False)
                obj_high.hide_set(True)

        return {'FINISHED'}
    

class MSFSBake_ToggleObjVisHigh(Operator):
    bl_idname = "view3d.toggle_obj_vis_high"
    bl_label = "Toggle High poly Mesh"
    bl_description = "Toggles visiblity of High poly mesh in viewport"

    def execute(self, context: Context) -> None:
        toggle_vis(get_high(context))
        return {'FINISHED'}
    

class MSFSBake_ToggleObjVisLow(Operator):
    bl_idname = "view3d.toggle_obj_vis_low"
    bl_label = "Toggle Low poly Mesh"
    bl_description = "Toggles visiblity of Low poly mesh in viewport"

    def execute(self, context: Context) -> None:
        toggle_vis(get_low(context))
        return {'FINISHED'}


class MSFSBake_ToggleWidthLock(Operator):
    bl_idname = "view3d.toggle_width_lock"
    bl_label = "Toggle Width Lock"
    bl_description = "Toggles linking width to height for output image"

    def execute(self, context: Context) -> None:
        settings = context.scene.msfs_properties
        settings.output_are_dimensions_linked = not settings.output_are_dimensions_linked
        settings.output_height = settings.output_width
        return {'FINISHED'}
    

class MSFSBake_WidthMinus(Operator):
    bl_idname = "view3d.width_minus"
    bl_label = "Reduce Width"
    bl_description = "Reduces width of output image to next smallest power of two"
    
    def execute(self, context: Context) -> None:
        settings = context.scene.msfs_properties
        settings.output_width = prev_pow_of_two(settings.output_width)
        if settings.output_are_dimensions_linked:
            settings.output_height = settings.output_width
        return {'FINISHED'}
    

class MSFSBake_WidthPlus(Operator):
    bl_idname = "view3d.width_plus"
    bl_label = "Increase Width"
    bl_description = "Increases width of output image to next largest power of two"
    
    def execute(self, context: Context) -> None:
        settings = context.scene.msfs_properties
        settings.output_width = next_pow_of_two(settings.output_width)
        if settings.output_are_dimensions_linked:
            settings.output_height = settings.output_width
        return {'FINISHED'}
    

class MSFSBake_HeightMinus(Operator):
    bl_idname = "view3d.height_minus"
    bl_label = "Reduce Height"
    bl_description = "Reduces Height of output image to next smallest power of two"
    
    def execute(self, context: Context) -> None:
        settings = context.scene.msfs_properties
        settings.output_height = prev_pow_of_two(settings.output_height)
        return {'FINISHED'}
    

class MSFSBake_HeightPlus(Operator):
    bl_idname = "view3d.height_plus"
    bl_label = "Increase Height"
    bl_description = "Increases Height of output image to next largest power of two"
    
    def execute(self, context: Context) -> None:
        settings = context.scene.msfs_properties
        settings.output_height = next_pow_of_two(settings.output_height)
        return {'FINISHED'}