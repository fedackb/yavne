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


bl_info = {
    'name' : 'Y.A.V.N.E.',
    'description' : 'Yet another vertex normal editor',
    'location' : '3D View > Tool Shelf > Shading/UVs',
    'author' : 'Brett Fedack',
    'version' : (1, 9, 2),
    'blender' : (2, 79, 0),
    'category' : 'Mesh'
}

if 'bpy' not in locals():
    import bpy
    from . import operators
    from . import panel
    from . import preferences
else:
    import imp
    imp.reload(operators)
    imp.reload(panel)
    imp.reload(preferences)

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)
