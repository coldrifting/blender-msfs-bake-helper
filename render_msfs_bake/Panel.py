from bpy.types import Panel

class MSFSBake_Panel(Panel):
    bl_idname = "MSFSBAKE_PT_PANEL"
    bl_label = "MSFS Bake Helper"
    bl_category = "Bake Helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        settings = context.scene.msfs_properties

        layout = self.layout
        layout.label(text="Properties:")
        maincol = layout.column()

        # Object selection
        objbox = maincol.box()
        objboxcol = objbox.column()

        highPolyRow = objboxcol.row(align=True)
        highPolyRow.prop(settings, "src_obj", text="", icon="SPHERE")
        if settings.src_obj and not settings.src_obj.visible_get():
            highPolyRow.operator("view3d.toggle_obj_vis_high", icon="HIDE_ON", text="")
        else:
            highPolyRow.operator("view3d.toggle_obj_vis_high", icon="HIDE_OFF", text="")

        lowPolyRow = objboxcol.row(align=True)
        lowPolyRow.prop(settings, "dst_obj", text="", icon="MESH_ICOSPHERE")
        if settings.dst_obj and not settings.dst_obj.visible_get():
            lowPolyRow.operator("view3d.toggle_obj_vis_low", icon="HIDE_ON", text="")
        else:
            lowPolyRow.operator("view3d.toggle_obj_vis_low", icon="HIDE_OFF", text="")

        objboxcol.separator()
        objboxcol.operator("view3d.toggle_high_low_vis", text="Toggle High/Low")
        maincol.separator()

        # Bake distance settings
        maincol.prop(settings, "render_ray_dist")
        maincol.prop(settings, "render_extrusion")
        maincol.prop(settings, "obj_align", text="Origin Alignment", toggle=True)
        maincol.separator()

        # Bake dimensions and padding
        resbox = maincol.box()
        resboxcol = resbox.column(align=True)
        resboxwidtharea = resboxcol.row(align=True)
        resboxwidtharea.label(text="Width")
        resboxwidtharea.operator("view3d.width_minus", text="", icon="REMOVE")
        resboxwidtharea.prop(settings, "output_width", text="")
        resboxwidtharea.operator("view3d.width_plus", text="", icon="ADD")
        resboxheightarea = resboxcol.row(align=True)
        if settings.output_are_dimensions_linked:
            resboxheightarea.enabled = False
        else:
            resboxheightarea.enabled = True

        resboxheightarea.label(text="Height")
        resboxheightarea.operator("view3d.height_minus", text="", icon="REMOVE")
        resboxheightarea.prop(settings, "output_height", text="")
        resboxheightarea.operator("view3d.height_plus", text="", icon="ADD", )

        resboxpaddingarea = resboxcol.row(align=True)
        resboxpaddingarea.label(text="Padding")
        resboxpaddingarea.prop(settings, "output_padding", text="")
        
        linkarea = resboxcol.row(align=True)
        linkarea.label(text="Dimensions")
        if settings.output_are_dimensions_linked:
            settings
            linkarea.operator("view3d.toggle_width_lock", text="Linked", icon="LINKED")
        else:
            linkarea.operator("view3d.toggle_width_lock", text="Unlinked", icon="UNLINKED")
        maincol.separator()

        # Folder setup
        folderbox = maincol.box()
        folderboxcol = folderbox.column()
        folderboxcol.prop(settings, "output_folder", text="")
        filerow = folderboxcol.row()
        filerow.label(text="File Prefix")
        filerow.prop(settings, "output_file_prefix", text="")
        maincol.separator()

        # Bake map options
        bakeoptionsbox = maincol.box()
        bakeoptionsbox = bakeoptionsbox.column(align=True)
        bakeoptionsbox.prop(settings, "render_is_diffuse_enabled", toggle=True, text="Color", icon="SHADING_SOLID")
        bakeoptionsbox.prop(settings, "render_is_normal_enabled", toggle=True, text="Normal", icon="SHADING_RENDERED")
        bakeoptionsbox.prop(settings, "render_is_composite_enabled", toggle=True, text="Composite", icon="MATERIAL")
        maincol.separator()

        # Bake!
        maincol.operator("msfsbake.bake", text="Bake")
