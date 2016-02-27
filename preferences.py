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


class YAVNEPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__.split('.')[0]

    vertex_normal_weight = bpy.props.EnumProperty(
        name = 'Vertex Normal Weight',
        description = (
            'Determines how each vertex normal is calculated as the ' +
            'weighted average of adjacent face normals'
        ),
        default = 'ANGLE',
        items = [
            ('UNIFORM', 'Uniform', 'Face normals are averaged evenly.', '', -1),
            ('ANGLE', 'Corner Angle', 'Face normals are averaged according to the corner angle of a shared vertex in each face. This is the smooth shading approach used by Blender.', '', 0),
            ('AREA', 'Face Area', 'Face normals are averaged according to the area of each face.', '', 1),
            ('COMBINED', 'Combined', 'Face normals are averaged according to both corner angle and face area.', '', 2),
            ('UNWEIGHTED', 'Unweighted', 'Face normals are not averaged; vertex normals are fixed.', '', 3)
        ]
    )

    face_normal_influence = bpy.props.EnumProperty(
        name = 'Face Normal Influence',
        description = (
            'Determines which face normals participate in vertex normal ' +
            'calculations'
        ),
        default = 'MEDIUM',
        items = [
            ('WEAK', 'Weak', 'Face normal participates only if a vertex is not influenced by either a medium or strong face.', '', -1),
            ('MEDIUM', 'Medium', 'Face normal participates only if a vertex is not influenced by a strong face.', '', 0),
            ('STRONG', 'Strong', 'Face normal always participates.', '', 1)
        ]
    )

    source = bpy.props.StringProperty(
        name = 'Shading Source',
        description = 'Source object from which to transfer interpolated normals'
    )

    available_sources = bpy.props.CollectionProperty(
        type = bpy.types.PropertyGroup
    )

    normal_buffer = bpy.props.FloatVectorProperty(
        name = 'Normal Vector Buffer',
        description = 'Stored world space normal vector',
        step = 1,
        precision = 2,
        size = 3,
        subtype = 'XYZ'
    )

    merge_distance = bpy.props.FloatProperty(
        name = 'Merge Distance',
        description = 'Maximum allowed distance between merged vertex normals',
        default = 0.0001,
        min = 0.0,
        soft_max = 1.0,
        step = 0.01,
        precision = 4
    )

    merge_unselected = bpy.props.BoolProperty(
        name = 'Unselected',
        description = (
            'Unselected vertex normals within given distance of selected ' +
            'vertices are also merged.'
        ),
        default = False
    )
