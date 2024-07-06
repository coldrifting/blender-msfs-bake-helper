import bpy
from os import path
from bpy.types import Object, Context, Scene
from bpy.props import BoolProperty, StringProperty, FloatProperty, IntProperty, PointerProperty, EnumProperty


def check_ob_in_scene(scene: Scene) -> None:
    # Full paths are important for removing here
    settings = scene.msfs_properties

    # Remove deleted objects
    if settings.src_obj is not None:
        if not filter_objects(None, settings.src_obj):
           settings.src_obj = None

    if settings.dst_obj is not None:
        if not filter_objects(None, settings.dst_obj):
           settings.dst_obj = None


def update_file_prefix(_, context: Context) -> None:
    settings = context.scene.msfs_properties

    # Auto switch output file prefix
    if settings.dst_obj is not None:
        settings.output_file_prefix = settings.dst_obj.name
    else:
        settings.output_file_prefix = settings.default_prefix

def filter_objects(_, object : Object) -> bool:
    # Exclude Lights, Cameras, etc
    if object.type != "MESH":
        return False
    
    # Exclude unlinked objects
    if object.users == 0:
        return False
    
    # Exclude unchecked view layers
    return object.name in bpy.context.scene.objects and object.visible_get(view_layer=bpy.context.view_layer)

def update_width(_, context: Context) -> None:
    settings = context.scene.msfs_properties
    if settings.output_are_dimensions_linked:
        settings.output_height = settings.output_width
    
class MSFSBake_Settings(bpy.types.PropertyGroup):
    bl_idname = "msfsbake.settings"
    bl_label = "Bake selected mesh maps"
    bl_description = "Bakes all selected mesh maps"

    min_res = 8
    max_res = 8192
    default_res = 512
    default_padding = 2
    default_prefix = "BakedOutput"
    desktop = path.expanduser("~\\Desktop")

    # Save and restore user preferences and selection
    prev_engine = StringProperty(name="Prev Render Engine", default='EEVEE')
    prev_active = None
    prev_selection = []

    prev_src_hidden: BoolProperty(name="Source object previously hidden by user", default=False)
    prev_dst_hidden: BoolProperty(name="Destination object previously hidden by user", default=False)

    prev_src_name: StringProperty(name="Prev Src Name", default="")
    prev_dst_name: StringProperty(name="Prev Dst Name", default="")

    # Initalize Variables
    src_obj: PointerProperty(name="Source Object", type=Object, poll=filter_objects)
    dst_obj: PointerProperty(name="Destination Object", type=Object, poll=filter_objects, update=update_file_prefix)

    render_ray_dist: FloatProperty(name="Ray Distance", default=0.000, precision=3, min=0.0, step=1, subtype='DISTANCE')
    render_extrusion: FloatProperty(name="Extrusion Distance", default=0.10, precision=2, min=0.0, step=10, subtype='DISTANCE')
    obj_align: BoolProperty(name="Align Objects", default=True)

    output_width: IntProperty(name="Width", default=default_res, min=min_res, max=max_res, update=update_width)
    output_height: IntProperty(name="Height", default=default_res, min=min_res, max=max_res)
    output_padding: IntProperty(name="Padding", default=default_padding, min=0, max=64)
    output_are_dimensions_linked: BoolProperty(name="Link Dimensions", default=True)

    output_folder: StringProperty(name="Output Folder", default=desktop, description="Choose an export path", subtype='DIR_PATH')
    output_file_prefix: StringProperty(name="Output File Prefix", default="BakeOutput")

    render_is_diffuse_enabled: BoolProperty(name="Enable Diffuse Bake", default=True)
    render_is_normal_enabled: BoolProperty(name="Enable Normal Bake", default=True)
    render_is_composite_enabled: BoolProperty(name="Enable Composite Bake", default=True)


    # Add callback for deleted objects
    if not check_ob_in_scene in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(check_ob_in_scene)