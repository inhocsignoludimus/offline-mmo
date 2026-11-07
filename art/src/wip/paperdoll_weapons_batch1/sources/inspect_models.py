import bpy,json
from mathutils import Vector
from pathlib import Path
out={}
for name in ['shortsword','dagger','hand_axe','mace','longbow','staff','wand','buckler']:
 p=Path('/workspace/flare-game/art_src/characters/hero')/(name+'.blend');bpy.ops.wm.open_mainfile(filepath=str(p));a=[]
 for o in bpy.data.objects:
  if o.type=='ARMATURE':o.data.pose_position='REST'
 bpy.context.view_layer.update()
 for o in bpy.data.objects:
  if o.type!='MESH' or not len(o.data.vertices):continue
  a.append({'name':o.name,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'parent_bone':o.parent_bone,'matrix':[list(r) for r in o.matrix_world],'verts':len(o.data.vertices),'materials':[m.name if m else None for m in o.data.materials],'groups':[g.name for g in o.vertex_groups],'bounds':[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)]})
 out[name]=a
Path('/workspace/paperdoll_weapons_batch1/work/model_inspection.json').write_text(json.dumps(out,indent=1))
