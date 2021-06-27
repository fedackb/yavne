# **Yet Another Vertex Normal Editor (Y.A.V.N.E.)**

This Blender addon provides a set of tools for editing vertex normals. As seen in the following image, Y.A.V.N.E. can dramatically improve the visual quality of a mesh without altering geometry.

![yavne](https://cloud.githubusercontent.com/assets/8960984/13205008/723b6f74-d89a-11e5-8e46-2e85e79caf6f.png)

### **Download** ###

Select one of the following links depending on the version of Blender that you are using:

* [Blender 2.80+](https://github.com/fedackb/yavne/archive/master.zip)
* [Blender 2.79](https://github.com/fedackb/yavne/archive/2.79.zip)

### **User Interface** ###

Y.A.V.N.E. is available within the **3D View > Sidebar > Tools** tab for any mesh object in Edit mode.

![location-2 80](https://user-images.githubusercontent.com/8960984/59981867-226b5200-95c7-11e9-86a3-2809ad02e8a0.png)

### **Vertex Normal Weight** ###

Vertex weight types determine how each vertex normal is calculated as the weighted average of adjacent face normals. Y.A.V.N.E. provides several weighting options:

* **Uniform** - Faces normals are averaged evenly.
* **Corner Angle** - Face normals are averaged according to the corner angle of a shared vertex in each face. This is the smooth shading approach used by Blender.
* **Face Area** - Face normals are averaged according to the area of each face.
* **Combined** - Face normals are averaged according to both corner angle and face area.
* **Unweighted** - Face normals are not averaged; vertex normals are static. "Set", "Merge", and "Transfer Shading" operators result in unweighted vertices.

![weight_comparison](https://cloud.githubusercontent.com/assets/8960984/13204443/5f340a38-d88d-11e5-9134-ad9f6588b7c5.png)

Each vertex has exactly one weight type. For quick-and-easy shading, it may be sufficient to assign the **Combined** weight type to all vertices of a mesh. However, thoughtful use of a variety of weight types often yields better results.

### **Face Normal Influence** ###

Face influence types determine which face normals are considered when calculating vertex normals. In the case that a vertex is shared by faces of different types, only normals from the most influential faces contribute to the resulting vertex normal.

![influence_comparison](https://cloud.githubusercontent.com/assets/8960984/13381747/ef774144-de20-11e5-9ae1-11fbee78ab64.png)

Faces have **Medium** influence by default. A typical workflow involves assigning **Weak** influence to transitional portions of a mesh, such as bevels (I). Alternatively, users can specify more influential areas by assigning **Strong** influence (II). It is even possible to use all three face influence types in a single mesh (III).

### **Get & Set Normals** ###

Basic manual editing of vertex normals is possible with the **Get** and **Set** tools.

**Set** simply assigns the stored normal vector to all selected vertices.

**Get** is a little more involved in that it has multiple modes of operation based on the user's current selection:

* A face normal is stored if exactly one face is selected.
* A vertex normal is stored if exactly one vertex is selected.
  * If the selected vertex has a split normal then the user may interactively select which one to store.
![get_split_normal](https://cloud.githubusercontent.com/assets/8960984/13381799/cf838176-de21-11e5-8313-2c78bbcdc94f.png)

### **Merge** ###

Merge is similar to Blender's "Remove Doubles" operator. However instead of welding vertices within a threshold distance of each other, this tool averages vertex normals.

It can be used to create seamless transitions across mesh boundaries, such as a split between the head and torso of a character.

![merge](https://cloud.githubusercontent.com/assets/8960984/13371937/82ee5684-dcef-11e5-8344-4193c8f38548.gif)

### **Transfer Shading** ###

Interpolated normals can be transferred from a source mesh to the nearest selected vertices of the target (active) mesh.

One scenario in which this tool might be useful is when a user wants to add detail along curved sections of a mesh. Cutting faces creates undesirable shading artifacts. By transferring shading from the original mesh, it is possible to correct such imperfections and achieve the desired result.

![transfer_shading](https://cloud.githubusercontent.com/assets/8960984/13205760/bf1b57d4-d8ac-11e5-9343-95043048170a.png)

### **Update Vertex Normals** ##

It is necessary to recalculate vertex normals after making changes to geometry. Options are available for adjusting how the calculation is performed.

**Linked Face Weights** factor the areas of adjacent faces into the calculation of face weighted vertex normals. For instance, all coplanar face areas are summed when this option is enabled and the corresponding link angle is set to zero degrees.

**Auto Smooth** sharpens edges based on the angle between faces. The behavior is similar to Blender's builtin Auto Smooth option.

![update_options](https://user-images.githubusercontent.com/8960984/49330829-6f1b0d00-f551-11e8-91fa-01b4dd8e77c8.png)

**Flat Face Shading** preserves shading discontinuities caused by flat faces.

### **Version History** ###

2.0.3

 * Disabled multiprocessing for POSIX OS
 * Moved UI from "Tool" to "Extended Tools" in sidebar

2.0.1

 * Exposed flat face shading as an option

2.0.0

 * Updated to support Blender 2.80

1.9.2

 * Forced sharp edge visibility
 * Fixed divide-by-zero exception with Merge tool

1.9.0

 * Added option to sharpen edges based on the angle between faces
 * Added option to factor linked face areas into the calculation of face weighted vertex normals
 * Added support for flat shaded faces
 * Implemented concurrent processing of vertex normals for Unix-like systems
 * Refactored unweighted vertex normals to use loop data layers
 * Optimized algorithm for splitting vertex normals

1.3.0

* Added "Merge" feature
* Added "Medium" face influence type

1.1.0

* Adapted code to be compatible with changes to "Object.ray_cast" interface

1.0.0

* Initial release
