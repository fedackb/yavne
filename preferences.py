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
import math
from .types import FaceNormalInfluence, VertexNormalWeight


class YAVNEPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__.split('.')[0]

    vertex_normal_weight = VertexNormalWeight.create_property()

    face_normal_influence = FaceNormalInfluence.create_property()

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
        min = 0.0001,
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

    show_update_options = bpy.props.BoolProperty(
        name = 'Update Options',
        description = 'Show/hide options for updating vertex normals.',
        default = False
    )

    use_linked_face_weights = bpy.props.BoolProperty(
        name = 'Linked Face Weights',
        description = (
            'Factor linked face areas into the calculation of face weighted ' +
            'vertex normals.'
        ),
        default = True
    )

    link_angle = bpy.props.FloatProperty(
        name = 'Link Angle',
        description = (
            'Maximum angle between faces to be considered as linked\n\n' +
            'e.g. Coplanar faces have a link angle of zero degrees.'
        ),
        default = math.radians(2.0),
        min = 0.0,
        max = math.pi,
        step = 10,
        precision = 1,
        subtype = 'ANGLE'
    )

    use_auto_smooth = bpy.props.BoolProperty(
        name = 'Auto Smooth',
        description = 'Auto smooth based on angle between faces.',
        default = True
    )

    smooth_angle = bpy.props.FloatProperty(
        name = 'Smooth Angle',
        description = 'Maximum angle between faces to be considered as smooth',
        default = math.radians(89.9),
        min = 0.0,
        max = math.pi,
        step = 10,
        precision = 1,
        subtype = 'ANGLE'
    )
