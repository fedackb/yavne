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
import math
import sys
from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d
)
from mathutils import Matrix, Vector


def split_loops(vert, angle = math.pi):
    '''
    Splits vertex linked loops into groups based on edge properties

    Parameters:
        vert (bmesh.types.BMVert): Common vertex shared by loops
        angle (float): Face edge angle threshold in radians

    Returns:
        list<list<bmesh.types.BMLoop>>: Grouped loops
    '''
    loop_groups = []

    # Split vertex linked loops into groups.
    link_loops = set(loop for loop in vert.link_loops)
    while len(link_loops) > 0:

        # Transfer a loop to a subgroup.
        loop_subgroup = [link_loops.pop()]
        loop_groups.append(loop_subgroup)

        # Find grouped loops in the forward direction.
        loop_curr = loop_subgroup[0]
        loop_next = loop_subgroup[0].link_loop_radial_next.link_loop_next
        while (
            loop_next in link_loops and
            loop_curr.edge.is_manifold and
            is_edge_smooth(loop_curr.edge) and
            loop_curr.edge.calc_face_angle() <= angle
        ):
            # Transfer next loop to the subgroup.
            link_loops.remove(loop_next)
            loop_subgroup.append(loop_next)

            # Advance to the next pair of loops.
            loop_curr = loop_next
            loop_next = loop_curr.link_loop_radial_next.link_loop_next

        # Find grouped loops in the reverse direction.
        loop_curr = loop_subgroup[0]
        loop_prev = loop_subgroup[0].link_loop_prev.link_loop_radial_prev
        while (
            loop_prev in link_loops and
            loop_prev.edge.is_manifold and
            is_edge_smooth(loop_prev.edge) and
            loop_prev.edge.calc_face_angle() <= angle
        ):
            # Transfer previous loop to the subgroup.
            link_loops.remove(loop_prev)
            loop_subgroup.append(loop_prev)

            # Retreat to the previous pair of loops.
            loop_curr = loop_prev
            loop_prev = loop_curr.link_loop_prev.link_loop_radial_prev

    return loop_groups


def pick_object(region, rv3d, x, y, near, far, objects):
    '''
    Selects an object underneath given screen coordinates

    Parameters:
        region (bpy.types.Region): Section of the UI in which to do picking
        rv3d (bpy.types.RegionView3D): 3D view region data
        near (float): Near clipping plane
        far (float): Far clipping plane
        objects (seq<bpy.types.Object>): Sequence of pickable objects

    Returns:
        (obj, location, normal, index): Reference to picked object and raycast
        hit information; otherwise None
            obj (bpy.types.Object): Nearest object in path of the ray
            location (Vector): Object space location of ray-face intersection
            normal (Vector): Normal vector of intersected face
            index (int): Index of intersected face
    '''
    blender_version = bpy.app.version

    # Determine ray extents.
    coord = Vector((x, y))
    ray_dir = region_2d_to_vector_3d(region, rv3d, coord)
    ray_start = region_2d_to_origin_3d(region, rv3d, coord) + ray_dir * near
    ray_end = ray_start + ray_dir * (far - near)

    # Pick a mesh object underneath given screen coordinates.
    result = None
    min_dist_squared = sys.float_info.max
    for obj in objects:

        # Skip objects that cannot participate in ray casting.
        if (not obj.type == 'MESH' or
            obj.mode == 'EDIT' or
            not obj.data.polygons
        ):
            continue

        # Cast ray in object space.
        inverse_model_matrix = obj.matrix_world.inverted()
        hit =  obj.ray_cast(
            inverse_model_matrix * ray_start,
            inverse_model_matrix * ray_end
        )
        if blender_version < (2, 76, 9):
            location, normal, index = hit
        else:
            location, normal, index = hit[1:]

        # Compare intersection distances.
        if index != -1:
            dist_squared = (obj.matrix_world * location - ray_start).length_squared

            # Record closer of the two hits.
            if dist_squared < min_dist_squared:
                min_dist_squared = dist_squared
                result = (obj, location, normal, index)

    return result


def loop_space_transform(loop, v, reverse = False):
    '''
    Transforms given vector from object space to loop-specific tangent space or
    vice versa if reverse flag is set

    Parameters:
        loop (bmesh.types.BMLoop): Loop from which to calculate tangent space
        v (mathutils.Vector): Input vector
        reverse (bool=False): Flag indicating direction of transformation

    Returns:
        mathutils.Vector: Transformed vector
    '''
    # Define ortho-normal, loop-specific tangent space.
    normal = loop.calc_normal()
    tangent = loop.calc_tangent()
    bitangent = normal.cross(tangent)

    # Transform given vector.
    m = Matrix((normal, tangent, bitangent))
    if reverse:
        m.transpose()
    v = m * v

    return v


def get_num_procs():
    '''
    Determines the number of processors automatically detected by Blender
      NOTE: multiprocessing.cpu_count() is unreliable

    Returns:
        int: Number of processors
    '''
    render = bpy.context.scene.render

    # Determine current scene's inital render settings.
    initially_fixed = (render.threads_mode == 'FIXED')
    initial_threads = render.threads

    # Infer processor count from the number of render threads.
    render.threads_mode = 'AUTO'
    result = render.threads

    # Restore current scene's render settings.
    if initially_fixed:
        render.threads_mode = 'FIXED'
        render.threads = initial_threads

    return result


def is_edge_smooth(edge):
    '''
    Determines if the given edge is smooth for shading purposes

    Parameters:
        edge (bmesh.types.BMEdge): Edge to evaluate

    Returns:
        bool: True if edge is smooth; False otherwise
    '''
    # Determine edge smoothness directly.
    result = edge.smooth

    # Infer edge smoothness from linked faces.
    if result:
        for f in edge.link_faces:
            if not f.smooth:
                result = False
                break

    return result


def get_linked_faces(face, angle = 0.0):
    '''
    Determines which faces are linked to given one

    Parameters:
        face (bmesh.types.BMFace): Face for which to get linked faces
        angle (float): Edge angle threshold in radians

    Returns:
        set<bmesh.types.BMFace>: Linked faces
    '''
    result = set()
    traversal_stack = [face]

    # Traverse staged faces.
    while len(traversal_stack) > 0:
        f_curr = traversal_stack.pop()

        # Accumulate results upon visiting a face.
        result.add(f_curr)

        # Search contiguous faces.
        for e in f_curr.edges:
            if e.is_contiguous:
                for f_linked in e.link_faces:
                    if f_linked not in result:

                        # Check if faces are within edge angle threshold.
                        if f_curr.normal.angle(f_linked.normal) <= angle:

                            # Stage linked face for traversal.
                            traversal_stack.append(f_linked)

    return result
