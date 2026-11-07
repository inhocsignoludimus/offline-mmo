import bpy,bmesh,math,sys,json,os
from mathutils import Vector
from pathlib import Path
s,it=sys.argv[-2:];R=Path(os.environ.get('WEAPON_BATCH_DIR','/workspace/paperdoll_weapons_batch1'));W=R/'work';W.mkdir(parents=True,exist_ok=True);S=1.8/458
SOURCE_DIR=Path(os.environ.get('WEAPON_SOURCE_DIR','/workspace/flare-game/art_src/characters/hero'))
source=SOURCE_DIR/(('iron_buckler' if it=='buckler' else it)+'.blend');bpy.ops.wm.open_mainfile(filepath=str(source));ob=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent_type=='BONE' and o.name not in ['HumanMale','ShadowPlane'])
# Freeze actual source local geometry. Every silhouette is the original model, not a placeholder.
source_object_name=ob.name
V=[v.co.copy() for v in ob.data.vertices];F=[tuple(p.vertices) for p in ob.data.polygons];M=[p.material_index for p in ob.data.polygons];names=[m.name for m in ob.data.materials]
uv=[tuple(x.uv) for x in ob.data.uv_layers.active.data] if ob.data.uv_layers.active else None
if it=='staff':
 # The native crystal floated 0.033m above the wooden socket. Seat the same crystal mesh, no new primitive.
 ids={i for p in ob.data.polygons if 'Crystal' in names[p.material_index] for i in p.vertices}
 for i in ids:V[i].x+=.038
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for x in list(bpy.data.materials):
 if x.library is None:bpy.data.materials.remove(x)
def material(name,col,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;L=m.node_tree.links;p=n['Principled BSDF'];p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 tc=n.new('ShaderNodeTexCoord');nz=n.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=150;nz.inputs['Detail'].default_value=3;L.new(tc.outputs['Generated'],nz.inputs[0]);bu=n.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.12;bu.inputs['Distance'].default_value=.00015;L.new(nz.outputs['Fac'],bu.inputs['Height']);L.new(bu.outputs[0],p.inputs['Normal']);return m
steel=material('fixed worn steel',(.24,.25,.26),.85,.43);iron=material('fixed dark iron',(.115,.12,.125),.75,.57);wood=material('fixed seasoned wood',(.12,.064,.027),0,.7);gold=material('fixed bronze fittings',(.21,.14,.055),.78,.48);leather=material('hueable leather or cloth',(.34,.34,.34),0,.72);string=material('fixed undyed bowstring',(.27,.23,.17),0,.9);crystal=material('fixed muted blue crystal',(.08,.16,.20),.2,.28)
# Non-placeholder wood uses fine longitudinal grain on original mesh.
n=wood.node_tree.nodes;L=wood.node_tree.links;p=n['Principled BSDF'];tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(2,48,48) if it!='longbow' and it!='wand' else (48,48,2);L.new(tc.outputs['Generated'],mp.inputs[0]);nz=n.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=5;nz.inputs['Detail'].default_value=3;L.new(mp.outputs[0],nz.inputs[0]);cr=n.new('ShaderNodeValToRGB');cr.color_ramp.elements[0].color=(.035,.017,.007,1);cr.color_ramp.elements[1].color=(.19,.105,.045,1);L.new(nz.outputs['Fac'],cr.inputs[0]);L.new(cr.outputs[0],p.inputs['Base Color'])
roles=[];mats=[]
for name in names:
 if any(k in name for k in ['Leather','ClothWrap']):mat=leather;role='hue'
 elif 'Wood' in name:mat=wood;role='fixed'
 elif 'Crystal' in name:mat=crystal;role='fixed'
 elif 'Gold' in name:mat=gold;role='fixed'
 elif 'String' in name:mat=string;role='fixed'
 elif 'Iron' in name:mat=iron;role='fixed'
 else:mat=steel;role='fixed'
 mats.append(mat);roles.append(role)
if it=='buckler':
 m=material('fixed original iron buckler UV',(.25,.25,.25),.8,.5);n=m.node_tree.nodes;L=m.node_tree.links;p=n['Principled BSDF'];tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(SOURCE_DIR/'iron_buckler_diffuse.png'));L.new(tx.outputs['Color'],p.inputs['Base Color']);tx.image.pack();nm=n.new('ShaderNodeTexImage');nm.image=bpy.data.images.load(str(SOURCE_DIR/'iron_buckler_normal.png'));nm.image.colorspace_settings.name='Non-Color';nm.image.pack();no=n.new('ShaderNodeNormalMap');no.inputs['Strength'].default_value=.7;L.new(nm.outputs[0],no.inputs['Color']);L.new(no.outputs[0],p.inputs['Normal']);mats=[m];roles=['fixed']
gmain=(48,237) if s=='m' else (35,216);goff=(243,237) if s=='m' else (251,218)
def w(x,y,d):return ((x-150)*S,d,(480-y)*S)
# Axes, grip origins and size derived from native mesh inspection, in approved-body pixel coordinates.
conf={'shortsword':(0,-1,-.028,150,-8),'dagger':(0,-1,.032,95,-10),'hand_axe':(0,1,0,150,-4),'mace':(0,-1,.10,165,-5),'longbow':(2,1,0,330,0),'staff':(0,-1,-.013,400,-6),'wand':(2,1,-.45,100,-9)}
coords=[]
if it=='buckler':
 gx,gy=goff;scale=76/(max(v.x for v in V)-min(v.x for v in V))
 for v in V:coords.append(w(gx+v.x*scale*.96,gy-v.y*scale,-.09-v.z*scale*S))
else:
 axis,sign,origin,length,angle=conf[it];k=length/(max(v[axis] for v in V)-min(v[axis] for v in V));sn=math.sin(math.radians(angle));cs=math.cos(math.radians(angle));gx,gy=gmain
 for v in V:
  a=(v[axis]-origin)*sign*k
  if axis==0:cross=v.y*k*(-1 if it=='hand_axe' else 1);dep=-v.z*k*S
  else:cross=(-v.y*k*.68 if it=='longbow' else v.x*k);dep=(-v.x*k*S if it=='longbow' else -v.y*k*S)
  coords.append(w(gx+a*sn+cross*cs,gy-a*cs+cross*sn,-.09+dep))
me=bpy.data.meshes.new(it+'_real_source_mesh');me.from_pydata(coords,[],F);me.update();obj=bpy.data.objects.new(it,me);bpy.context.collection.objects.link(obj)
for m in mats:me.materials.append(m)
for p,idx in zip(me.polygons,M):p.material_index=idx
if uv and len(uv)==len(me.loops):
 layer=me.uv_layers.new(name='source_uv')
 for a,b in zip(layer.data,uv):a.uv=b
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Preserve hard blade edges; subtle bevel is physical edge softness, not shape replacement.
be=obj.modifiers.new('subpixel steel edge bevel','BEVEL');be.width=.00045;be.segments=2
sc=bpy.context.scene
camd=bpy.data.cameras.new('front paperdoll');camd.type='ORTHO';camd.ortho_scale=480*S;cam=bpy.data.objects.new('camera',camd);sc.collection.objects.link(cam);cam.location=(0,-5,240*S);cam.rotation_euler=(math.pi/2,0,0);sc.camera=cam
world=bpy.data.worlds.new('studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;sc.world=world
for name,loc,pow,size in [('key',(-1.4,-2.5,3.1),150,2.5),('fill',(1.7,-2.2,1.8),65,3),('top',(.3,.5,2.9),60,2)]:
 l=bpy.data.lights.new(name,'AREA');l.energy=pow;l.shape='DISK';l.size=size;o=bpy.data.objects.new(name,l);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.samples=96;sc.cycles.use_denoising=True;sc.cycles.device='CPU';sc.render.threads_mode='FIXED';sc.render.threads=3;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=True;sc.render.resolution_percentage=100;sc.render.resolution_x=600;sc.render.resolution_y=960;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='16';sc.use_nodes=False;sc.render.use_border=False;sc.render.use_compositing=False
bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{it}_{s}.blend'),compress=True)
hm=bpy.data.materials.new('other-layer holdout');hm.use_nodes=True;n=hm.node_tree.nodes;n.remove(n['Principled BSDF']);h=n.new('ShaderNodeHoldout');hm.node_tree.links.new(h.outputs[0],n['Material Output'].inputs[0])
for tag in ['fixed','hue']:
 if not any(roles[p.material_index]==tag for p in me.polygons):continue
 for i,m in enumerate(mats):obj.data.materials[i]=m if roles[i]==tag else hm
 sc.render.filepath=str(W/f'{it}_{s}_{tag}_raw.png');bpy.ops.render.render(write_still=True);print('DONE',s,it,tag,flush=True)
(W/f'{it}_{s}.json').write_text(json.dumps({'item':it,'source':str(source),'source_object':source_object_name,'source_materials':names,'roles':roles,'grip_pixel':goff if it=='buckler' else gmain,'size_pixels':76 if it=='buckler' else conf[it][3],'static_only':True},indent=2))
