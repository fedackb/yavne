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
import bmesh
import bgl
import math
import os
from mathutils import Vector
from multiprocessing import Process
from multiprocessing.sharedctypes import Array
from .types import (
    FaceAreaCache, LinkedFaceAreaCache, FaceNormalInfluence, VertexNormalWeight, Vec3
)
from .utils import (
    split_loops, pick_object, loop_space_transform, get_num_procs
)


class YAVNEBase(bpy.types.Operator):
    bl_idname = 'mesh.yavne_base'
    bl_label = 'YAVNE Base Operator'
    bl_options = {'INTERNAL'}

    addon_key = __package__.split('.')[0]

    @classmethod
    def poll(cls, context):
        # An active mesh object in Edit mode is required, and the operator is
        # only valid in 'VIEW_3D' space.
        obj_curr = context.active_object
        return (
            obj_curr and
            obj_curr.type == 'MESH' and
            obj_curr.mode == 'EDIT' and
            context.space_data.type == 'VIEW_3D'
        )

    def __init__(self):
        mesh = bpy.context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        vert_int_layers = bm.verts.layers.int
        face_int_layers = bm.faces.layers.int
        loop_float_layers = bm.loops.layers.float

        # Reference addon.
        self.addon = bpy.context.user_preferences.addons[self.addon_key]

        # Ensure that the 'vertex-normal-weight' custom data layer exists.
        if not 'vertex-normal-weight' in vert_int_layers.keys():
            vert_int_layers.new('vertex-normal-weight')

        # Ensure that the 'face-normal-influence' custom data layer exists.
        if not 'face-normal-influence' in face_int_layers.keys():
            face_int_layers.new('face-normal-influence')

        # Ensure that loop-space normal custom data layers exist.
        if not 'loop-normal-x' in loop_float_layers.keys():
            loop_float_layers.new('loop-normal-x')
        if not 'loop-normal-y' in loop_float_layers.keys():
            loop_float_layers.new('loop-normal-y')
        if not 'loop-normal-z' in loop_float_layers.keys():
            loop_float_layers.new('loop-normal-z')

        # Update the mesh.
        bmesh.update_edit_mesh(mesh)


class ManageVertexNormalWeight(YAVNEBase):
    bl_idname = 'mesh.yavne_manage_vertex_normal_weight'
    bl_label = 'Manage Vertex Normal Weight'
    bl_description = (
        'Select vertices by vertex normal weight, or assign vertex normal ' +
        'weight to selected vertices.'
    )
    bl_options = {'UNDO'}

    action = bpy.props.EnumProperty(
        name = 'Operator Action (Get or Set)',
        description = '',
        default = 'GET',
        items = [
            ('GET', 'Get', 'Selects vertices by given vertex normal weight', '', 0),
            ('SET', 'Set', 'Assigns given vertex normal weight to selected vertices', '', 1)
        ]
    )

    type = VertexNormalWeight.create_property()

    update = bpy.props.BoolProperty(
        name = 'Update Vertex Normals',
        description = 'Update vertex normals at the end of a "Set" action.',
        default = True
    )

    def execute(self, context):
        obj_curr = context.active_object
        obj_curr.update_from_editmode()
        mesh = obj_curr.data
        bm = bmesh.from_edit_mesh(mesh)
        vertex_normal_weight_layer = bm.verts.layers.int['vertex-normal-weight']
        loop_normal_x_layer = bm.loops.layers.float['loop-normal-x']
        loop_normal_y_layer = bm.loops.layers.float['loop-normal-y']
        loop_normal_z_layer = bm.loops.layers.float['loop-normal-z']

        # Determine enumerated vertex normal weight value.
        vertex_normal_weight = VertexNormalWeight[self.type].value

        # Select vertices by given vertex normal weight.
        if self.action == 'GET':
            context.tool_settings.mesh_select_mode = (True, False, False)
            for v in bm.verts:
                if v[vertex_normal_weight_layer] == vertex_normal_weight:
                    v.select = True
                else:
                    v.select = False
            bm.select_mode = {'VERT'}
            bm.select_flush_mode()

        # Assign given vertex normal weight to selected vertices.
        elif self.action == 'SET':
            selected_verts = [v for v in bm.verts if v.select]
            for v in selected_verts:
                v[vertex_normal_weight_layer] = vertex_normal_weight

            #  Set unweighted vertex normal component values.
            if self.type == 'UNWEIGHTED':
                mesh.calc_normals_split()
                for v in selected_verts:
                    for loop in v.link_loops:
                        vn_local = mesh.loops[loop.index].normal
                        vn_loop = loop_space_transform(loop, vn_local)
                        loop[loop_normal_x_layer] = vn_loop.x
                        loop[loop_normal_y_layer] = vn_loop.y
                        loop[loop_normal_z_layer] = vn_loop.z
                mesh.free_normals_split()

        # Update the mesh.
        bmesh.update_edit_mesh(mesh)
        if self.action == 'SET' and self.update:
            bpy.ops.mesh.yavne_update_vertex_normals()

        return {'FINISHED'}


class ManageFaceNormalInfluence(YAVNEBase):
    bl_idname = 'mesh.yavne_manage_face_normal_influence'
    bl_label = 'Manage Face Normal Influence'
    bl_description = (
        'Select faces by normal vector influence, or assign normal ' +
        'vector influence to selected faces.'
    )
    bl_options = {'UNDO'}

    action = bpy.props.EnumProperty(
        name = 'Operator Action (Get or Set)',
        description = '',
        default = 'GET',
        items = [
            ('GET', 'Get', 'Selects faces by given normal vector influence', '', 0),
            ('SET', 'Set', 'Assigns given normal vector influence to selected faces', '', 1)
        ]
    )

    type = FaceNormalInfluence.create_property()

    update = bpy.props.BoolProperty(
        name = 'Update Vertex Normals',
        description = 'Update vertex normals at the end of a "Set" action.',
        default = True
    )

    def execute(self, context):
        mesh = bpy.context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        face_normal_influence_layer = bm.faces.layers.int['face-normal-influence']

        # Determine enumerated face normal influence value.
        face_normal_influence = FaceNormalInfluence[self.type].value

        # Select faces by given normal vector influence.
        if self.action == 'GET':
            context.tool_settings.mesh_select_mode = (False, False, True)
            for f in bm.faces:
                if f[face_normal_influence_layer] == face_normal_influence:
                    f.select = True
                else:
                    f.select = False
            bm.select_mode = {'FACE'}
            bm.select_flush_mode()

        # Assign given face normal influence to selected faces.
        elif self.action == 'SET' and mesh.total_face_sel:
            selected_faces = [f for f in bm.faces if f.select]
            for f in selected_faces:
                f[face_normal_influence_layer] = face_normal_influence

        # Update the mesh.
        bmesh.update_edit_mesh(mesh)
        if self.action == 'SET' and self.update:
            bpy.ops.mesh.yavne_update_vertex_normals()

        return {'FINISHED'}


class PickShadingSource(YAVNEBase):
    bl_idname = 'view3d.yavne_pick_shading_source'
    bl_label = 'Pick Shading Source'
    bl_description = 'Pick object from which to transfer interpolated normals.'
    bl_options = set()

    def execute(self, context):
        obj_curr = context.active_object
        scene = context.scene

        # Exit Edit mode, if necessary.
        self.initially_in_edit_mode = context.mode == 'EDIT_MESH'
        if self.initially_in_edit_mode:
            bpy.ops.object.mode_set(mode = 'OBJECT')

        # Populate a list of objects that are valid as shading sources.
        self.available_sources = [
            obj
            for obj in scene.objects
            if (obj.type == 'MESH' and
                obj != obj_curr and
                obj.is_visible(scene)
            )
        ]

        # Hide objects that are visible but invalid as shading sources.
        self.temporarily_hidden_objects = [
            obj
            for obj in scene.objects
            if ((obj.type != 'MESH' and obj.is_visible(scene)) or
                obj == obj_curr
            )
        ]
        for obj in self.temporarily_hidden_objects:
            obj.hide = True

        # Display the operator's instructions in the active area's header.
        context.area.header_text_set('LMB: Pick, Escape: Cancel')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            region = context.region
            rv3d = context.region_data
            sv3d = context.space_data
            x, y = event.mouse_region_x, event.mouse_region_y
            available_sources = self.available_sources

            # Determine the view's clipping distances.
            if rv3d.view_perspective == 'CAMERA':
                near = sv3d.camera.data.clip_start
                far = sv3d.camera.data.clip_end
            else:
                near = sv3d.clip_start
                far = sv3d.clip_end

            # Attempt to pick a mesh object under the cursor.
            hit = pick_object(region, rv3d, x, y, near, far, available_sources)

            # Set the shading source accordingly.
            self.addon.preferences.source = hit[0].name if hit else ''

            self.finish(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            self.finish(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        # Reveal  temporarily hidden objects.
        for obj in self.temporarily_hidden_objects:
            obj.hide = False

        # Return to Edit mode, if necessary.
        if self.initially_in_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # Restore  active area's header to its initial state.
        context.area.header_text_set()


class GetNormalVector(YAVNEBase):
    bl_idname = 'mesh.yavne_get_normal_vector'
    bl_label = 'Get Normal Vector'
    bl_description = 'Copy selected face/vertex normal vector to a buffer.'

    @classmethod
    def poll(cls, context):
        # Exactly one vertex or face must be selected.
        mesh = context.active_object.data
        return (
            super().poll(context) and
            (mesh.total_vert_sel == 1 or mesh.total_face_sel == 1)
        )

    def execute(self, context):
        mesh = context.active_object.data
        if mesh.total_face_sel == 1:
            return self.get_face_normal(context)
        elif mesh.total_vert_sel == 1:
            return self.get_vertex_normal(context)
        else:
            return {'CANCELLED'}

    def modal(self, context, event):
        context.area.tag_redraw()
        self.show_usage(context)

        # Confirm selection.
        if event.type == 'RET' and event.value == 'PRESS':
            self.store_vertex_normal(context)
            self.finish(context)
            return {'FINISHED'}

        # Select previous split normal.
        elif event.type == 'LEFT_ARROW' and event.value == 'PRESS':
            self.normals_idx = (self.normals_idx - 1) % self.num_normals

        # Select next split normal.
        elif event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
            self.normals_idx = (self.normals_idx + 1) % self.num_normals

        # Cancel operation.
        elif event.type == 'ESC':
            self.finish(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def get_face_normal(self, context):
        obj_curr = context.active_object
        mesh = obj_curr.data
        model_matrix = obj_curr.matrix_world
        bm = bmesh.from_edit_mesh(mesh)

        # Determine which face is selected.
        selected_face = [f for f in bm.faces if f.select][0]

        # Store selected face normal.
        vn_global = model_matrix * selected_face.normal
        self.addon.preferences.normal_buffer = vn_global

        return {'FINISHED'}

    def get_vertex_normal(self, context):
        obj_curr = context.active_object
        obj_curr.update_from_editmode()
        model_matrix = obj_curr.matrix_world
        mesh = obj_curr.data
        mesh.calc_normals_split()
        bm = bmesh.from_edit_mesh(mesh)

        # Determine which vertex is selected.
        selected_vert = [v for v in bm.verts if v.select][0]
        self.vertex_co = model_matrix * selected_vert.co

        # Gather world space normal vectors associated with selected vertex.
        normals = set(
            (model_matrix * mesh.loops[loop.index].normal).to_tuple()
            for loop in selected_vert.link_loops
        )
        self.normals = list(normals)
        self.normals_idx = 0
        self.num_normals = len(self.normals)

        # Return early if selected vertex is not part of a face.
        if not self.num_normals:
            return {'CANCELLED'}

        # Store the only normal vector associated with selected vertex.
        elif self.num_normals == 1:
            self.store_vertex_normal(context)
            return {'FINISHED'}

        # Allow user to select one of multiple normal vectors.
        else:
            # Temporarily hide vertex normals.
            self.saved_show_normal_vertex = mesh.show_normal_vertex
            mesh.show_normal_vertex = False
            self.saved_show_normal_loop = mesh.show_normal_loop
            mesh.show_normal_loop = False
            self.saved_show_normal_face = mesh.show_normal_face
            mesh.show_normal_face = False

            # Add render callback.
            self.post_view_handle = bpy.types.SpaceView3D.draw_handler_add(
                self.post_view_callback,
                (context,),
                'WINDOW',
                'POST_VIEW'
            )

            # Transfer control to interactive mode of operation.
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

    def show_usage(self, context):
        vn_global = self.normals[self.normals_idx]

        # Display usage instructions in the active area's header.
        usage = (
            'Left/Right: Select Normal    Enter: Confirm    ' +
            'Escape: Cancel    Normal: ({0:.2}, {1:.2}, {2:.2})'
        ).format(*vn_global)
        context.area.header_text_set(usage)

    def store_vertex_normal(self, context):
        # Store current vertex normal in property buffer.
        vn_global = Vector(self.normals[self.normals_idx])
        self.addon.preferences.normal_buffer = vn_global

    def finish(self, context):
        mesh = context.active_object.data

        # Reveal temporarily hidden vertex normals.
        mesh.show_normal_vertex = self.saved_show_normal_vertex
        mesh.show_normal_loop = self.saved_show_normal_loop
        mesh.show_normal_face = self.saved_show_normal_face

        # Remove render callback.
        bpy.types.SpaceView3D.draw_handler_remove(
            self.post_view_handle,
            'WINDOW'
        )

        # Restore active area's header to its initial state.
        context.area.header_text_set()

    def post_view_callback(self, context):
        start = self.vertex_co
        normal_size = context.tool_settings.normal_size
        view_3d_theme = context.user_preferences.themes['Default'].view_3d

        default_color = view_3d_theme.split_normal
        highlight_color = [0.25, 1.0, 0.56]

        # Draw all normals of selected vertex.
        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor3f(*default_color)
        bgl.glLineWidth(1)
        for vn_global in self.normals:
            end = start + Vector(vn_global) * normal_size
            bgl.glVertex3f(*start)
            bgl.glVertex3f(*end)
        bgl.glEnd()

        # Highlight selected normal.
        bgl.glColor3f(*highlight_color)
        bgl.glLineWidth(2)
        bgl.glBegin(bgl.GL_LINES)
        end = start + Vector(self.normals[self.normals_idx]) * normal_size
        bgl.glVertex3f(*start)
        bgl.glVertex3f(*end)
        bgl.glEnd()


class SetNormalVector(YAVNEBase):
    bl_idname = 'mesh.yavne_set_normal_vector'
    bl_label = 'Set Normal Vector'
    bl_description = 'Assign stored normal vector to selected vertices.'
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # At least one vertex must be selected.
        mesh = context.active_object.data
        return (
            super().poll(context) and
            mesh.total_vert_sel > 0
        )

    def execute(self, context):
        obj_curr = context.active_object
        mesh = obj_curr.data
        bm = bmesh.from_edit_mesh(mesh)
        normal_buffer = self.addon.preferences.normal_buffer
        vertex_normal_weight_layer = bm.verts.layers.int['vertex-normal-weight']
        loop_normal_x_layer = bm.loops.layers.float['loop-normal-x']
        loop_normal_y_layer = bm.loops.layers.float['loop-normal-y']
        loop_normal_z_layer = bm.loops.layers.float['loop-normal-z']

        # Assign stored world space normal vector to all selected vertices.
        vn_local = obj_curr.matrix_world.inverted() * normal_buffer
        for v in [v for v in bm.verts if v.select]:
            v[vertex_normal_weight_layer] = VertexNormalWeight.UNWEIGHTED.value
            for loop in v.link_loops:
                vn_loop = loop_space_transform(loop, vn_local)
                loop[loop_normal_x_layer] = vn_loop.x
                loop[loop_normal_y_layer] = vn_loop.y
                loop[loop_normal_z_layer] = vn_loop.z

        # Update the mesh.
        bpy.ops.mesh.yavne_update_vertex_normals()
        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}


class MergeVertexNormals(YAVNEBase):
    bl_idname = 'mesh.yavne_merge_vertex_normals'
    bl_label = 'Merge Vertex Normals'
    bl_description = (
        'Merge selected vertex normals within given distance of each other.'
    )
    bl_options = {'REGISTER', 'UNDO'}

    distance = bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum allowed distance between merged vertex normals',
        default = 0.0001,
        min = 0.0001
    )

    unselected = bpy.props.BoolProperty(
        name = 'Unselected',
        description = (
            'Unselected vertex normals within given distance of selected ' +
            'vertices are also merged.'
        ),
        default = False
    )

    @classmethod
    def poll(cls, context):
        # At least one vertex must be selected.
        mesh = context.active_object.data
        return (
            super().poll(context) and
            mesh.total_vert_sel > 0
        )

    def execute(self, context):
        obj_curr = context.active_object
        obj_curr.update_from_editmode()
        mesh = obj_curr.data
        bm = bmesh.from_edit_mesh(mesh)
        vertex_normal_weight_layer = bm.verts.layers.int['vertex-normal-weight']
        loop_normal_x_layer = bm.loops.layers.float['loop-normal-x']
        loop_normal_y_layer = bm.loops.layers.float['loop-normal-y']
        loop_normal_z_layer = bm.loops.layers.float['loop-normal-z']
        merge_distance_squared = self.distance ** 2

        # Organize vertices into discrete space.
        cells = {}
        selected_verts = set(v for v in bm.verts if v.select)
        for v in (bm.verts if self.unselected else selected_verts):
            v_co = v.co
            x = v_co.x // self.distance
            y = v_co.y // self.distance
            z = v_co.z // self.distance

            # Ensure that the cell exists.
            if not x in cells:
                cells[x] = {}
            if not y in cells[x]:
                cells[x][y] = {}
            if not z in cells[x][y]:
                cells[x][y][z] = []

            # Add vertex reference to the cell.
            cells[x][y][z].append(v)

        # Merge vertex normals in the vicinity of each selected vertex.
        mesh.calc_normals_split()
        while selected_verts:
            v_curr = selected_verts.pop()
            v_curr_co = v_curr.co
            v_curr_normal_count = len(set(
                mesh.loops[loop.index].normal.to_tuple()
                for loop in v_curr.link_loops
            ))
            x = v_curr_co.x // self.distance
            y = v_curr_co.y // self.distance
            z = v_curr_co.z // self.distance

            # Search adjacent cells for vertices.
            nearby_verts = []
            for i in [x - 1, x, x + 1]:
                for j in [y - 1, y, y + 1]:
                    for k in [z - 1, z, z + 1]:

                        # Add contents of current cell to search results.
                        if i in cells and j in cells[i] and k in cells[i][j]:
                            nearby_verts.extend(cells[i][j][k])

            # Exclude vertices that are outside of given merge distance.
            mergeable_verts = [
                v
                for v in nearby_verts
                if (v.co - v_curr_co).length_squared <= merge_distance_squared
            ]

            # Calculate merged normal.
            vn_local = Vector()
            for v in mergeable_verts:

                # Average normals of current vertex.
                vn = Vector()
                for loop in v.link_loops:
                    vn += mesh.loops[loop.index].normal
                vn.normalize()

                # Include current, averaged vertex normal in merged normal.
                vn_local += vn
            vn_local.normalize()

            # Assign merged normal to all vertices within given merge distance.
            if v_curr_normal_count > 1 or len(mergeable_verts) > 1:
                for v in mergeable_verts:
                    v[vertex_normal_weight_layer] = VertexNormalWeight.UNWEIGHTED.value
                    for loop in v.link_loops:
                        vn_loop = loop_space_transform(loop, vn_local)
                        loop[loop_normal_x_layer] = vn_loop.x
                        loop[loop_normal_y_layer] = vn_loop.y
                        loop[loop_normal_z_layer] = vn_loop.z

            # Indicate which selected vertices have been merged.
            local_selection = [v for v in mergeable_verts if v.select]
            selected_verts.difference_update(local_selection)

        # Update the mesh.
        bpy.ops.mesh.yavne_update_vertex_normals()
        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}


class TransferShading(YAVNEBase):
    bl_idname = 'mesh.yavne_transfer_shading'
    bl_label = 'Transfer Shading'
    bl_description = (
        'Transfer interpolated normals from source object to nearest, ' +
        'selected vertices.'
    )
    bl_options = set()

    @classmethod
    def poll(cls, context):
        # The source and target objects must be distinct, and at least one
        # vertex must be selected from the target object.
        addon = context.user_preferences.addons[cls.addon_key]
        source = addon.preferences.source
        obj_curr = context.active_object
        return (
            super().poll(context) and
            source and source != obj_curr and
            obj_curr.data.total_vert_sel
        )

    def execute(self, context):
        obj_curr = context.active_object
        mesh = obj_curr.data
        mesh.use_auto_smooth = True
        modifiers = obj_curr.modifiers
        source = self.addon.preferences.source

        # Modifiers can only be applied in Object mode.
        bpy.ops.object.mode_set(mode = 'OBJECT')

        # Group selected vertices.
        selected_vertices = [v.index for v in mesh.vertices if v.select]
        selected_vertices_group = obj_curr.vertex_groups.new('Selected')
        selected_vertices_group.add(selected_vertices, 1, 'ADD')

        # Add data transfer modifier.
        data_xfer_modifier = modifiers.new(name = '', type = 'DATA_TRANSFER')
        data_xfer_modifier.object = bpy.data.objects[source]
        data_xfer_modifier.use_loop_data = True
        data_xfer_modifier.data_types_loops = {'CUSTOM_NORMAL'}
        data_xfer_modifier.loop_mapping = 'POLYINTERP_NEAREST'

        # Move data transfer modifier to the top of the stack.
        while modifiers[0] != data_xfer_modifier:
            bpy.ops.object.modifier_move_up(modifier = data_xfer_modifier.name)

        # Apply data transfer modifier.
        bpy.ops.object.modifier_apply(modifier = data_xfer_modifier.name)

        # Delete the vertex group.
        obj_curr.vertex_groups.remove(selected_vertices_group)

        # Return to Edit mode.
        bpy.ops.object.mode_set(mode = 'EDIT')

        # Lock transferred normals.
        bpy.ops.mesh.yavne_manage_vertex_normal_weight(
            action = 'SET',
            type = 'UNWEIGHTED',
            update = True
        )

        return {'FINISHED'}


class UpdateVertexNormals(YAVNEBase):
    bl_idname = 'mesh.yavne_update_vertex_normals'
    bl_label = 'Update Vertex Normals'
    bl_description = (
        'Recalculate vertex normals based on weights, face normal ' +
        'influences, and sharp edges.'
    )
    bl_options = set()

    def __init__(self):
        super().__init__()
        self.procs = []

    def __del__(self):
        if hasattr(super(), '__del__'):
            super().__del__()

        # Cleanup any lingering processes.
        for p in self.procs:
            p.terminate()

    def worker(self, bm, out, chunk, total):
        '''
        Calculates a chunk of split normals data

        Parameters:
            bm (bmesh.types.BMesh): BMesh data
            out (Array<Vec3>): Output sequence of split normals as ctype structs
            chunk (int): Chunk of data to process in range [0, total)
            total (int): Total number of chunks

        Pre:
            Output sequence shall be large enough to accommodate all split
            normals with given chunk of data.

        Post:
            Output sequence is modified.
        '''
        face_normal_influence_layer = bm.faces.layers.int['face-normal-influence']
        vertex_normal_weight_layer = bm.verts.layers.int['vertex-normal-weight']
        loop_normal_x_layer = bm.loops.layers.float['loop-normal-x']
        loop_normal_y_layer = bm.loops.layers.float['loop-normal-y']
        loop_normal_z_layer = bm.loops.layers.float['loop-normal-z']

        # Create a cache for face areas.
        if self.addon.preferences.use_linked_face_weights:
            area_cache = LinkedFaceAreaCache(self.addon.preferences.link_angle)
        else:
            area_cache = FaceAreaCache()

        # Determine the auto smooth angle.
        if self.addon.preferences.use_auto_smooth:
            smooth_angle = self.addon.preferences.smooth_angle
        else:
            smooth_angle = math.pi

        # Determine which vertices are within the chunk of data.
        first = int(chunk / total * len(bm.verts))
        last = int((chunk + 1) / total * len(bm.verts))

        # Calculate loop normals.
        for idx in [i + first for i in range(last - first)]:
            v = bm.verts[idx]
            vertex_normal_weight = v[vertex_normal_weight_layer]

            # Split vertex linked loops into shading groups.
            for loop_group in split_loops(v, smooth_angle):

                # Determine which face type most influences this vertex.
                influence_max = max((
                    loop.face[face_normal_influence_layer]
                    for loop in loop_group
                ))

                # Ignore all but the most influential face normals.
                loop_subgroup = [
                    loop
                    for loop in loop_group
                    if loop.face[face_normal_influence_layer] == influence_max
                ]

                # Average face normals according to vertex normal weight.
                vn_local = Vector()
                if vertex_normal_weight == VertexNormalWeight.UNIFORM.value:
                    for loop in loop_subgroup:
                        vn_local += loop.face.normal
                elif vertex_normal_weight == VertexNormalWeight.ANGLE.value:
                    for loop in loop_subgroup:
                        vn_local += loop.calc_angle() * loop.face.normal
                elif vertex_normal_weight == VertexNormalWeight.AREA.value:
                    for loop in loop_subgroup:
                        area = area_cache.get(loop.face)
                        vn_local +=  area * loop.face.normal
                elif vertex_normal_weight == VertexNormalWeight.COMBINED.value:
                    for loop in loop_subgroup:
                        area = area_cache.get(loop.face)
                        vn_local += loop.calc_angle() * area * loop.face.normal
                elif vertex_normal_weight == VertexNormalWeight.UNWEIGHTED.value:
                    for loop in loop_subgroup:
                        vn_loop = Vector((
                            loop[loop_normal_x_layer],
                            loop[loop_normal_y_layer],
                            loop[loop_normal_z_layer]
                        ))
                        vn_local += loop_space_transform(loop, vn_loop, True)

                # Assign calculated vertex normal to all loops in the group.
                vn_local.normalize()
                for loop in loop_group:
                    split_normal = out[loop.index]
                    split_normal.x, split_normal.y, split_normal.z = vn_local

    def execute(self, context):
        # Split normal data can only be written from Object mode.
        bpy.ops.object.mode_set(mode = 'OBJECT')

        # Retrieve mesh data.
        mesh = context.active_object.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # Enable mesh flags.
        mesh.use_auto_smooth = True
        mesh.show_edge_sharp = True

        # Prepare mesh to be processed.
        mesh.calc_normals_split()
        bm.verts.ensure_lookup_table()
        split_normals = Array(Vec3, len(mesh.loops), lock = False)

        # Execute in parallel for large datasets if supported by the system.
        if len(bm.verts) > 5000 and not os.name == 'nt':

            # Create a team of worker processes.
            num_procs = get_num_procs()
            for i in range(num_procs):
                self.procs.append(Process(
                    target = self.worker,
                    args = (bm, split_normals, i, num_procs)
                ))

            # Start processes.
            for p in self.procs:
                p.start()

            # Wait until all processes have finished.
            while len(self.procs) > 0:
                p = self.procs.pop()
                p.join()

        # Otherwise, execute serially.
        else:
            self.worker(bm, split_normals, 0, 1)

        # Write split normal data to the mesh, and return to Edit mode.
        mesh.normals_split_custom_set([(n.x, n.y, n.z) for n in split_normals])
        bpy.ops.object.mode_set(mode = 'EDIT')

        # Cleanup.
        mesh.free_normals_split()
        bm.free()

        return {'FINISHED'}
