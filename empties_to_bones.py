bl_info = {
	"name": "Empties to Bones",
	"author": "Artell",
	"version": (1, 0),
	"blender": (2, 80, 0),
	"location": "3D View > Tool> Empties to Bone",
	"description": "Convert a hierarchy made of empties to an armature with bones",
	"category": "Animation"}

import bpy
import math
from mathutils import Vector, Euler, Matrix

# CLASSES
#############################################################################
class EB_create_armature(bpy.types.Operator):
    """Convert the selected empties to bones. Bones are constrained to empties, then can be baked (search for NLA bake function in the F3 search menu)"""
    bl_idname = "eb.create_armature"
    bl_label = "create_armature"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == "EMPTY"   
           
    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        try:
            _create_armature()

        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}
        
        
# GENERIC FUNCTIONS
#############################################################################
def set_active_object(object_name):
     bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
     bpy.data.objects[object_name].select_set(state=True)
     
def get_edit_bone(name):
    return bpy.context.object.data.edit_bones.get(name)
     
def get_pose_bone(name):
    return bpy.context.active_object.pose.bones.get(name)
        
def mat3_to_vec_roll(mat):
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv @ mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll

def vec_roll_to_mat3(vec, roll):
    target = Vector((0, 0.1, 0))
    nor = vec.normalized()
    axis = target.cross(nor)
    if axis.dot(axis) > 0.0000000001: # this seems to be the problem for some bones, no idea how to fix
        axis.normalize()
        theta = target.angle(nor)
        bMatrix = Matrix.Rotation(theta, 3, axis)
    else:
        updown = 1 if target.dot(nor) > 0 else -1
        bMatrix = Matrix.Scale(updown, 3)               
        bMatrix[2][2] = 1.0

    rMatrix = Matrix.Rotation(roll, 3, nor)
    mat = rMatrix @ bMatrix
    return mat
    
# OPERATOR FUNCTIONS
#############################################################################
def _create_armature():    
    # store selected empties
    empties_names = [i.name for i in bpy.context.selected_objects if i.type == "EMPTY"]

    # Create armature and bones
    # add a new armature
    bpy.ops.object.armature_add(enter_editmode=False, location=(0, 0, 0), rotation=(0,0,0))
    armature_name = bpy.context.active_object.name
    armature = bpy.data.objects.get(armature_name)
    bpy.ops.object.mode_set(mode='EDIT')
    # delete the default bone
    b_to_del = armature.data.edit_bones[0]
    armature.data.edit_bones.remove(b_to_del)

    # create bones
    bones_dict = {}
    for emp_name in empties_names:
        emp = bpy.data.objects.get(emp_name)
        vec, roll = mat3_to_vec_roll(emp.matrix_world.to_3x3())
        new_bone = armature.data.edit_bones.new(emp_name)
        new_bone.head = emp.matrix_world.to_translation()
        new_bone.tail = new_bone.head + (vec)
        new_bone.roll = roll
        parent_name = None
        if emp.parent:
            parent_name = emp.parent.name
        bones_dict[emp_name] = parent_name

    # parent bones
    for b in bones_dict:
        bone_parent_name = bones_dict[b]
        if bone_parent_name == None:
            continue
        bone_parent = get_edit_bone(bone_parent_name)
        if bone_parent:
            get_edit_bone(b).parent = bone_parent
            
    # constrain bones
    bpy.ops.object.mode_set(mode='POSE')
    for b in bones_dict:
        bone = get_pose_bone(b)
        cns_loc = bone.constraints.new("COPY_LOCATION")
        emp = bpy.data.objects.get(b)
        cns_loc.target = emp
        
        cns_rot = bone.constraints.new("COPY_ROTATION")
        emp = bpy.data.objects.get(b)
        cns_rot.target = emp        
        
        
###########  UI PANELS  ###################

class EB_PT_menu(bpy.types.Panel):
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"    
    bl_label = "Empties to Bones"
    bl_idname = "EB_PT_menu"

    def draw(self, context):
        layout = self.layout
        object = context.object
        scene = context.scene
        
        col = layout.column(align=True)   
        col.operator("eb.create_armature", text="Create Armature")
        

###########  REGISTER  ##################
classes = (EB_create_armature, EB_PT_menu)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
def unregister():
    from bpy.utils import unregister_class    
    for cls in reversed(classes):
        unregister_class(cls)           
   
if __name__ == "__main__":
    register()