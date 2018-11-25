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
from ctypes import Structure, c_double
from enum import Enum
from .utils import get_linked_faces


class Vec3(Structure):
    '''
    Represents a 3-dimensional vector as a ctype struct
    '''
    _fields_ = [('x', c_double), ('y', c_double), ('z', c_double)]


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


class Cache():
    '''
    Data structure for caching values

    Attributes:
        _cache (dict<tuple, Any>): Cached values
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initializes this cache
        '''
        self._cache = dict()

    def get(self, *args, **kwargs):
        '''
        Gets cached value or calculates a value if not already cached

        Returns:
            Any: Cached value
        '''
        if args not in self._cache:
            self._cache[args] = self._calc(*args, **kwargs)
        return self._cache[args]

    def _calc(self, *args, **kwargs):
        '''
        Abstract method to calculate a value

        Raises: NotImplementedError
        '''
        raise NotImplementedError


class FaceAreaCache(Cache):
    '''
    Data structure for caching face areas
    '''

    def _calc(self, face, *args, **kwargs):
        '''
        Calculates area of given face

        Parameters:
            face (bmesh.types.BMFace): Face for which to calculate the area

        Returns:
            float: Face area
        '''
        return face.calc_area()


class LinkedFaceAreaCache(Cache):
    '''
    Data structure for caching linked face areas

    Attributes:
        _angle (float): Edge angle threshold in radians
    '''

    def __init__(self, angle = 0.0, *args, **kwargs):
        '''
        Initializes this linked face area cache

        Parameters:
            angle (float): Edge angle threshold in radians
        '''
        super().__init__(angle, *args, **kwargs)
        self._angle = angle

    def _calc(self, face, *args, **kwargs):
        '''
        Calculates linked face area of given face

        Parameters:
            face (bmesh.types.BMFace): Face for which to calculate linked face area

        Post:
            Area values are cached for all faces linked to given face.

        Returns:
            float: Linked face area
        '''
        linked_faces = get_linked_faces(face, self._angle)
        linked_face_area = sum(f.calc_area() for f in linked_faces)
        for f in linked_faces:
            self._cache[(f, *args)] = linked_face_area
        return linked_face_area
