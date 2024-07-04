import bpy

from .Settings import MSFSBake_Properties
from .Bake import MSFSBake_Bake
from .Panel import MSFSBake_Panel
from .PanelUtils import (
    MSFSBake_ToggleObjVisHigh,
    MSFSBake_ToggleObjVisLow,
    MSFSBake_ToggleHighLowVis,
    MSFSBake_ToggleWidthLock,
    MSFSBake_WidthMinus,
    MSFSBake_WidthPlus,
    MSFSBake_HeightMinus,
    MSFSBake_HeightPlus
)


bl_info = {
    "name": "MSFS Bake Helper",
    "author": "coldrifting",
    "description": "Bake LOD textures from MSFS materials without messing with nodes",
    "blender": (3, 6, 0),
    "location": "View3D",
    "warning": "",
    "category": "Render"
}


classes = (
        MSFSBake_Properties,
        MSFSBake_Bake,
        MSFSBake_Panel,
        MSFSBake_ToggleObjVisHigh,
        MSFSBake_ToggleObjVisLow,
        MSFSBake_ToggleHighLowVis,
        MSFSBake_ToggleWidthLock,
        MSFSBake_WidthMinus,
        MSFSBake_WidthPlus,
        MSFSBake_HeightMinus,
        MSFSBake_HeightPlus,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.msfs_properties = bpy.props.PointerProperty(type=MSFSBake_Properties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.msfs_properties