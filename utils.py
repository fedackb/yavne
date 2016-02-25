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
import sys
import bmesh
from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d
)
from mathutils import Vector


class Node():
    '''
    Represents a node in an undirected graph

    Attributes:
        data: Information to store in this node
        neighbors (set<Node>): Adjacent nodes to this one
    '''
    def __init__(self, data):
        self.data = data
        self.neighbors = set()

    '''
    Creates edges between this node and all given nodes

    Parameters:
        *args: Argument list of Node objects
    '''
    def connect(self, *args):
        for node in args:
            self.neighbors.add(node)
            node.neighbors.add(self)

    '''
    Determines which nodes are reachable from this one

    Returns:
        set<Node>: Reachable nodes
    '''
    def getReachable(self):
        reachable = set()
        traversal_stack = [self]
        while len(traversal_stack) > 0:
            node = traversal_stack.pop()
            if node not in reachable:
                reachable.add(node)
                traversal_stack.extend(node.neighbors.difference(reachable))
        return reachable


def split_loops(vert):
    '''
    Splits vertex linked loops into groups based on face connectivity

    Parameters:
        vert (BVert): Common vertex shared by loops

    Returns:
        list<list<bpy.types.BMLoop>>: Grouped loops
    '''
    link_loop_nodes = set()
    edge_map = {}

    # Build a graph that describes the connectivity of linked loops.
    for loop in vert.link_loops:

        # Store loop information in a node.
        loop_node = Node(loop)
        link_loop_nodes.add(loop_node)

        # Connect loops via shared soft edges.
        for edge in [loop.edge, loop.link_loop_prev.edge]:
            if edge.smooth:
                if edge.index not in edge_map:
                    edge_node = Node(edge)
                    edge_map[edge.index] = edge_node
                else:
                    edge_node = edge_map[edge.index]
                loop_node.connect(edge_node)

    # Group loops according to node reachability.
    loop_groups = []
    while link_loop_nodes:
        loop_node = link_loop_nodes.pop()

        # Exclude nodes that contain edge data.
        reachable_loop_nodes = [
            node
            for node in loop_node.getReachable()
            if type(node.data) is bmesh.types.BMLoop
        ]

        # Group reachable loops.
        link_loop_nodes.difference_update(reachable_loop_nodes)
        loop_groups.append([node.data for node in reachable_loop_nodes])

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
