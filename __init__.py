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

import logging

bl_info = {
    'name' : 'Y.A.V.N.E.',
    'description' : 'Yet another vertex normal editor',
    'location' : '3D View > Tool Shelf > Shading/UVs',
    'author' : 'Brett Fedack',
    'version' : (2, 1, 1), 
    'blender' : (4, 5, 0), 
    'category' : 'Mesh'
}


if 'bpy' not in locals():
    import bpy
    from . import operators
    from . import panel
    from . import preferences
else:
    import importlib
    importlib.reload(operators)
    importlib.reload(panel)
    importlib.reload(preferences)

classes = (
    operators.MESH_OT_YAVNEBase,
    operators.MESH_OT_GetNormalVector,
    operators.MESH_OT_ManageFaceNormalInfluence,
    operators.MESH_OT_ManageVertexNormalWeight,
    operators.MESH_OT_MergeVertexNormals,
    operators.MESH_OT_PickShadingSource,
    operators.MESH_OT_SetNormalVector,
    operators.MESH_OT_TransferShading,
    operators.MESH_OT_UpdateVertexNormals,
    panel.MESH_PT_YAVNEPanel,
    preferences.YAVNEPrefs
)


def register():
    # Verify Blender version
    if bpy.app.version < (4, 5, 0):
        raise Exception("Y.A.V.N.E. 2.1+ requires Blender 4.5 or higher")

    # Configure the logging service.
    logging_format = (
        '[%(levelname)s] ' +
        '(%(asctime)s) ' +
        '{0}.%(module)s.%(funcName)s():L%(lineno)s'.format(__package__) +
        ' - %(message)s'
    )
    logging.basicConfig(
        level = logging.DEBUG,
        format = logging_format,
        datefmt = '%Y/%m/%d %H:%M:%S'
    )

    # Register this Blender addon.
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    # Unregister this Blender addon.
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
