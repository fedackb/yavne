# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bpy


class YAVNEPanel(bpy.types.Panel):
    bl_category = 'Shading / UVs'
    bl_idname = 'VIEW3D_PT_yavne'
    bl_label = 'Y.A.V.N.E.'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    addon_key = __package__.split('.')[0]

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        addon = context.user_preferences.addons[self.addon_key]
        self.addon_props = addon.preferences

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        self.draw_display_properties_ui(context, layout)
        self.draw_vertex_normal_weight_ui(context, layout)
        self.draw_face_normal_influence_ui(context, layout)

        layout.separator()

        self.draw_edit_vertex_normals_ui(context, layout)

        layout.separator()

        self.draw_merge_vertex_normals_ui(context, layout)

        layout.separator()

        self.draw_transfer_shading_ui(context, layout)

        layout.separator()

        self.draw_update_vertex_normals_ui(context, layout)

    def draw_display_properties_ui(self, context, layout):
        mesh = context.active_object.data
        view_3d_theme = context.user_preferences.themes['Default'].view_3d

        row = layout.row(align = True)
        row.alignment = 'CENTER'

        row.prop(mesh, 'show_normal_loop', text = '', icon = 'LOOPSEL')
        row.prop(view_3d_theme, 'split_normal', text = '')
        row.prop(context.tool_settings, 'normal_size', text = 'Size')
        row.active = mesh.use_auto_smooth

    def draw_vertex_normal_weight_ui(self, context, layout):
        addon_props = self.addon_props

        col = layout.column(align = True)

        col.label('Vertex Normal Weight:')

        row = col.row(align = True)

        row.prop(addon_props, 'vertex_normal_weight', text = '')

        op = row.operator('mesh.yavne_manage_vertex_normal_weight', text = '', icon = 'VERTEXSEL')
        op.action = 'GET'
        op.type = addon_props.vertex_normal_weight

        op = row.operator('mesh.yavne_manage_vertex_normal_weight', text = '', icon = 'ZOOMIN')
        op.action = 'SET'
        op.type = addon_props.vertex_normal_weight
        op.update = True

    def draw_face_normal_influence_ui(self, context, layout):
        addon_props = self.addon_props

        col = layout.column(align = True)

        row = col.row()
        row.label('Face Normal Influence:')

        row = col.row(align = True)

        row.prop(addon_props, 'face_normal_influence', text = '')

        op = row.operator('mesh.yavne_manage_face_normal_influence', text = '', icon = 'FACESEL')
        op.action = 'GET'
        op.type = addon_props.face_normal_influence

        op = row.operator('mesh.yavne_manage_face_normal_influence', text = '', icon = 'ZOOMIN')
        op.action = 'SET'
        op.type = addon_props.face_normal_influence
        op.update = True

    def draw_edit_vertex_normals_ui(self, context, layout):
        addon_props = self.addon_props

        col = layout.column(align = True)
        row = col.row(align = True)

        row.operator('mesh.yavne_get_normal_vector', text = 'Get')
        row.operator('mesh.yavne_set_normal_vector', text = 'Set')
        col.prop(addon_props, 'normal_buffer', text = '')

    def draw_merge_vertex_normals_ui(self, context, layout):
        addon_props = self.addon_props

        col = layout.column(align = True)
        row = col.row(align = True)

        op = row.operator('mesh.yavne_merge_vertex_normals', text = 'Merge')
        op.distance = addon_props.merge_distance
        op.unselected = addon_props.merge_unselected

        row.prop(addon_props, 'merge_unselected', text = '', icon = 'ROTACTIVE')

        col.prop(addon_props, 'merge_distance', text = 'Distance')

    def draw_transfer_shading_ui(self, context, layout):
        addon_props = self.addon_props
        obj_curr = context.active_object

        col = layout.column(align = True)

        # Generate a collection of potential shading sources.
        available_sources = addon_props.available_sources
        available_sources.clear()
        for obj in context.scene.objects:
            if obj.type == 'MESH' and obj != obj_curr:
                item = available_sources.add()
                item.name = obj.name

        # Confirm that the current shading source is still available.
        if (addon_props.source and
            addon_props.source not in addon_props.available_sources
        ):
            addon_props.source = ''

        col.operator('mesh.yavne_transfer_shading')

        row = col.row(align = True)

        row.prop_search(
            addon_props, 'source', addon_props, 'available_sources', text = '',
            icon = 'OBJECT_DATA'
        )
        row.operator('view3d.yavne_pick_shading_source', text = '', icon = 'EYEDROPPER')

    def draw_update_vertex_normals_ui(self, context, layout):
        addon_props = self.addon_props

        col = layout.column(align = True)
        row = col.row(align = True)

        row.operator('mesh.yavne_update_vertex_normals')
        row.prop(addon_props, 'show_update_options', text = '', icon = 'SCRIPTWIN')

        if addon_props.show_update_options:
            box = col.box()

            col = box.column(align = True)

            col.prop(addon_props, 'use_linked_face_weights')

            row = col.row()

            row.prop(addon_props, 'link_angle')
            row.active = addon_props.use_linked_face_weights

            col = box.column(align = True)

            col.prop(addon_props, 'use_auto_smooth')

            row = col.row()

            row.prop(addon_props, 'smooth_angle')
            row.active = addon_props.use_auto_smooth
