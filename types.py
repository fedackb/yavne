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
from enum import Enum


class FaceNormalInfluence(Enum):
    '''
    Defines the set of face normal influence values
    '''

    WEAK = -1
    MEDIUM = 0
    STRONG = 1

    @classmethod
    def create_property(cls):
        '''
        Creates a bpy.props.EnumProperty representation of this enumeration
        '''
        return bpy.props.EnumProperty(
            name = 'Face Normal Influence',
            description = (
                'Determines which face normals participate in vertex normal ' +
                'calculations'
            ),
            default = 'MEDIUM',
            items = [(
                    'WEAK',
                    'Weak', (
                        'Face normal participates only if a vertex is not '   +
                        'influenced by either a medium or strong face.'
                    ),
                    '',
                    cls.WEAK.value
                ), (
                    'MEDIUM',
                    'Medium', (
                        'Face normal participates only if a vertex is not '   +
                        'influenced by a strong face.'
                    ),
                    '',
                    cls.MEDIUM.value
                ), (
                    'STRONG',
                    'Strong', (
                        'Face normal always participates.'
                    ),
                    '',
                    cls.STRONG.value
                )
            ]
        )


class VertexNormalWeight(Enum):
    '''
    Defines the set of vertex normal weight values
    '''

    UNIFORM = -1
    ANGLE = 0
    AREA = 1
    COMBINED = 2
    UNWEIGHTED = 3

    @classmethod
    def create_property(cls):
        '''
        Creates a bpy.props.EnumProperty representation of this enumeration
        '''
        return bpy.props.EnumProperty(
            name = 'Vertex Normal Weight',
            description = (
                'Determines how each vertex normal is calculated as the '     +
                'weighted average of adjacent face normals'
            ),
            default = 'ANGLE',
            items = [(
                    'UNIFORM',
                    'Uniform', (
                        'Face normals are averaged evenly.'
                    ),
                    '',
                    cls.UNIFORM.value
                ), (
                    'ANGLE',
                    'Corner Angle', (
                        'Face normals are averaged according to the corner '  +
                        'angle of a shared vertex in each face. This is the ' +
                        'smooth shading approach used by Blender.'
                    ),
                    '',
                    cls.ANGLE.value
                ), (
                    'AREA',
                    'Face Area', (
                        'Face normals are averaged according to the area of ' +
                        'each face.'
                    ),
                    '',
                    cls.AREA.value
                ), (
                    'COMBINED',
                    'Combined', (
                        'Face normals are averaged according to both corner ' +
                        'angle and face area.'
                    ),
                    '',
                    cls.COMBINED.value
                ), (
                    'UNWEIGHTED',
                    'Unweighted', (
                        'Face normals are not averaged; vertex normals are '  +
                        'fixed.'
                    ),
                    '',
                    cls.UNWEIGHTED.value
                )
            ]
        )
