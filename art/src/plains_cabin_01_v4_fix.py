"""plains_cabin_01 v4: local lights, less rosy wood, debris removal, full front_low ~0.2, 3 threads."""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
D='/workspace/houses_next_delivery/cabin_v4'
BLEND=D+'/plains_cabin_01_v4.blend'; OUT=D+'/out'
W,H=2200,1600; ANCHOR=[1052,852]; TILE00=Vector((0.5,3.5,0))
CUT=float(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else 0.42
ONLY=sys.argv[sys.argv.index('--')+2].split(',') if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+2 else None
bpy.ops.wm.open_mainfile(filepath=BLEND)
s=bpy.context.scene
# lights: remove broken lib refs, add local rig
for o in list(bpy.data.objects):
    if o.name in ('Lighting','Sun','Sun.001','Sun.002') or o.name.startswith('V4Sun'):
        bpy.data.objects.remove(o,do_unlink=True)
def sun(name,energy,color,rot):
    l=bpy.data.lights.new(name,'SUN');l.energy=energy;l.color=color;l.angle=math.radians(3)
    o=bpy.data.objects.new(name,l);s.collection.objects.link(o);o.rotation_euler=[math.radians(a) for a in rot]
sun('V4Sun_key',3.2,(1.0,0.93,0.84),(40,0,-150))   # upper-left key (Flare)
sun('V4Sun_fill',0.6,(0.82,0.86,0.95),(60,0,40))
w=s.world; w.use_nodes=True; nt=w.node_tree; nt.nodes.clear()
bg=nt.nodes.new('ShaderNodeBackground'); out=nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(bg.outputs[0],out.inputs[0])
bg.inputs[0].default_value=(0.55,0.58,0.62,1); bg.inputs[1].default_value=0.22
# tone: explicit weathered brown ramp (Flare GT ~ RGB 96,63,52), neutral hue node
RAMPS={'WoodYellow':((0.109,0.062,0.040),(0.624,0.374,0.234)),'Wood':((0.094,0.060,0.040),(0.499,0.312,0.205)),
 'WoodLight':((0.140,0.087,0.056),(0.749,0.468,0.296)),'Floor timber':((0.094,0.060,0.038),(0.530,0.328,0.212))}
for m in bpy.data.materials:
    if not m.use_nodes or m.name not in RAMPS: continue
    for n in m.node_tree.nodes:
        if n.type=='HUE_SAT':
            n.inputs['Hue'].default_value=0.5; n.inputs['Saturation'].default_value=1.0; n.inputs['Value'].default_value=1.0
        if n.type=='VALTORGB':
            el=n.color_ramp.elements
            while len(el)>2: el.remove(el[-1])
            tex=next(x for x in m.node_tree.nodes if x.type=='TEX_IMAGE'); hs=next(x for x in m.node_tree.nodes if x.type=='HUE_SAT')
            m.node_tree.links.new(tex.outputs['Color'],n.inputs['Fac']); m.node_tree.links.new(n.outputs['Color'],hs.inputs['Color'])
            el[0].position=0.40; el[0].color=(*RAMPS[m.name][0],1); el[1].position=0.92; el[1].color=(*RAMPS[m.name][1],1)
# debris removal in BackWalls
o=bpy.data.objects['BackWalls']; bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen=set(); kill=[]
for v in bm.verts:
    if v.index in seen: continue
    st=[v]; comp=[]; seen.add(v.index)
    while st:
        x=st.pop(); comp.append(x)
        for e in x.link_edges:
            y=e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    ps=[o.matrix_world@x.co for x in comp]
    ymax=max(p.y for p in ps); ymin=min(p.y for p in ps); xmin=min(p.x for p in ps)
    if (ymax<0.7 and len(comp)<12) or (xmin>4.3 and ymax-ymin>1.0 and len(comp)<12):
        kill+=comp
bmesh.ops.delete(bm,geom=list(set(kill)),context='VERTS'); bm.to_mesh(o.data); bm.free()
print('KILLED verts',len(set(kill)))
# front_low rebuild
for x in list(bpy.data.collections['FRONT_LOW'].objects): bpy.data.objects.remove(x,do_unlink=True)
for srcname in ('FrontWalls','DoorFrame'):
    src=bpy.data.objects[srcname]; low=src.copy(); low.data=src.data.copy(); low.name=srcname+'_Low'
    bpy.data.collections['FRONT_LOW'].objects.link(low)
    low.data.transform(low.matrix_world); low.matrix_world=Matrix.Identity(4)
    bm=bmesh.new(); bm.from_mesh(low.data)
    dele=[f for f in bm.faces if not (f.calc_center_median().y<0.75 or f.calc_center_median().x>4.25)]
    bmesh.ops.delete(bm,geom=dele,context='FACES')
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-5,plane_co=(0,0,CUT),plane_no=(0,0,1),clear_outer=True)
    # cap top so the cut reads as solid log sections
    bm.to_mesh(low.data); bm.free()
# render setup
cam=s.camera; cam.data.type='ORTHO'; cam.data.sensor_fit='HORIZONTAL'; cam.data.ortho_scale=W/(192/math.sqrt(2))
cam.rotation_euler=(math.radians(60),0,math.radians(45)); cam.location=(12,-12,12)
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.render.threads_mode='FIXED'; s.render.threads=3
s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100; s.render.film_transparent=True
s.cycles.samples=96; s.cycles.use_denoising=True
s.view_settings.view_transform='Standard'; s.view_settings.look='None'; s.view_settings.exposure=-0.2
cam.data.shift_x=cam.data.shift_y=0; bpy.context.view_layer.update()
p0=world_to_camera_view(s,cam,TILE00); cam.data.shift_x=1; bpy.context.view_layer.update(); px=world_to_camera_view(s,cam,TILE00)
cam.data.shift_x=0; cam.data.shift_y=1; bpy.context.view_layer.update(); py=world_to_camera_view(s,cam,TILE00)
cam.data.shift_x=(ANCHOR[0]/W-p0.x)/(px.x-p0.x); cam.data.shift_y=((1-ANCHOR[1]/H)-p0.y)/(py.y-p0.y)
cols=['BACK','FRONT','FRONT_LOW','ROOF','DOOR_CLOSED','DOOR_OPEN']
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
for name,c in [('back','BACK'),('front','FRONT'),('front_low','FRONT_LOW'),('roof','ROOF'),('door_closed','DOOR_CLOSED'),('door_open','DOOR_OPEN')]:
    if ONLY and name not in ONLY: continue
    for n in cols: bpy.data.collections[n].hide_render=(n!=c)
    s.render.filepath=OUT+'/'+name+'.png'; bpy.ops.render.render(write_still=True); print('RENDERED',name,flush=True)
for n in cols: bpy.data.collections[n].hide_render=n not in ('BACK','FRONT','ROOF','DOOR_CLOSED')
bpy.ops.wm.save_as_mainfile(filepath=BLEND); print('DONE')
