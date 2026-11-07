"""plains_cabin_02 — 4x4 smaller log cabin, thatch roof, front porch (BUILDINGS.md, variation of cabin_01).
Same camera/light/palette as plains_cabin_01 v4. Run: blender -b --python build_cabin_02.py [-- names]"""
import bpy, bmesh, math, random, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
random.seed(7)
D='/workspace/houses_next_delivery/cabin_02'; OUT=D+'/out'
W,H=1600,1300; ANCHOR=[800,560]; TILE00=Vector((0.5,3.5,0))
ONLY=sys.argv[sys.argv.index('--')+1].split(',') if '--' in sys.argv else None
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
LAYERS=['BACK','FRONT','FRONT_LOW','ROOF','DOOR_CLOSED','DOOR_OPEN']
C={}
for n in LAYERS:
    c=bpy.data.collections.new(n); s.collection.children.link(c); C[n]=c
# ---------- materials ----------
img=None
with bpy.data.libraries.load('/workspace/houses_next_delivery/cabin_v4/plains_cabin_01_v4_orig.blend') as (src,dst):
    dst.images=[i for i in src.images if i=='pine_yellow.jpg']
img=bpy.data.images['pine_yellow.jpg']
def ramp_mat(name,lo,hi,rough_bump=0.25,scale=(1.4,1.4,1.4),tex='img',wave=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; N=nt.nodes; L=nt.links
    bs=N['Principled BSDF']; bs.inputs['Roughness'].default_value=0.85
    tc=N.new('ShaderNodeTexCoord'); mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=scale
    L.new(tc.outputs['Object'],mp.inputs['Vector'])
    if tex=='img':
        t=N.new('ShaderNodeTexImage'); t.image=img; t.projection='BOX'; t.projection_blend=0.25
        L.new(mp.outputs['Vector'],t.inputs['Vector']); fac=t.outputs['Color']
    else:
        wv=N.new('ShaderNodeTexWave'); wv.wave_type='BANDS'; wv.bands_direction=wave
        wv.inputs['Scale'].default_value=WSC.get(name,9); wv.inputs['Distortion'].default_value=WDI.get(name,6); wv.inputs['Detail'].default_value=8
        nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=3.5; nz.inputs['Detail'].default_value=8
        mx=N.new('ShaderNodeMix'); mx.data_type='FLOAT'; mx.inputs[0].default_value=0.45
        L.new(mp.outputs['Vector'],wv.inputs['Vector']); L.new(mp.outputs['Vector'],nz.inputs['Vector'])
        L.new(wv.outputs['Fac'],mx.inputs[2]); L.new(nz.outputs['Fac'],mx.inputs[3]); fac=mx.outputs[0]
    r=N.new('ShaderNodeValToRGB'); el=r.color_ramp.elements
    el[0].position=0.40 if tex=='img' else 0.2; el[0].color=(*lo,1); el[1].position=0.92 if tex=='img' else 0.85; el[1].color=(*hi,1)
    L.new(fac,r.inputs['Fac']); L.new(r.outputs['Color'],bs.inputs['Base Color'])
    b=N.new('ShaderNodeBump'); b.inputs['Strength'].default_value=rough_bump; L.new(fac,b.inputs['Height']); L.new(b.outputs['Normal'],bs.inputs['Normal'])
    return m
k=1.3*2.4
WSC={'Thatch':70,'LogX':14,'LogY':14,'Trim':10,'Floor':12}; WDI={'Thatch':1.5,'LogX':5,'LogY':5,'Trim':4,'Floor':4}
LO,HI=(0.040,0.028,0.018),(0.27,0.19,0.12)
WOODX=ramp_mat('LogX',LO,HI,0.3,(0.25,1,1),'wave','Y')
WOODY=ramp_mat('LogY',LO,HI,0.3,(1,0.25,1),'wave','X')
WOOD=WOODX
WOODL=ramp_mat('Trim',(0.05,0.035,0.023),(0.30,0.21,0.135),0.2,(1,1,0.3),'wave','X')
FLOOR=ramp_mat('Floor',(0.035,0.025,0.016),(0.22,0.155,0.10),0.2,(1,0.25,1),'wave','X')
THATCH=ramp_mat('Thatch',(0.045,0.040,0.028),(0.30,0.255,0.165),rough_bump=0.8,scale=(1,0.25,1),tex='wave',wave='X')
DARK=bpy.data.materials.new('DarkRecess'); DARK.use_nodes=True; DARK.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.012,0.010,0.009,1); DARK.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1
IRON=bpy.data.materials.new('Iron'); IRON.use_nodes=True; p=IRON.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value=(0.05,0.048,0.045,1); p.inputs['Metallic'].default_value=0.8; p.inputs['Roughness'].default_value=0.6
# ---------- helpers ----------
def box(name,coll,lo,hi,mat,bevel=0.0,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.active_object; o.name=name
    for c in o.users_collection: c.objects.unlink(o)
    coll.objects.link(o)
    o.location=[(a+b)/2 for a,b in zip(lo,hi)]; o.scale=[(b-a) for a,b in zip(lo,hi)]
    if rot: o.rotation_euler=rot
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('bev','BEVEL'); m.width=bevel; m.segments=3
    o.data.materials.append(mat); return o
WALL_H=2.2; CH=0.244; T=0.30; EXT=0.17
SOUTH,NORTH,WEST,EAST=0.25,3.75,0.25,3.75
def segs(a,b,holes,z0,z1):
    out=[(a,b)]
    for h0,h1,hz0,hz1 in holes:
        if z1<=hz0+1e-4 or z0>=hz1-1e-4: continue
        nxt=[]
        for p,q in out:
            if q<=h0 or p>=h1: nxt.append((p,q)); continue
            if p<h0: nxt.append((p,h0))
            if q>h1: nxt.append((h1,q))
        out=nxt
    return out
def wall(coll,axis,pos,a,b,holes,phase,zmax=WALL_H,tag=''):
    n=0; z=phase
    if phase>0: # half log at foot
        for p,q in segs(a,b,holes,0,phase):
            lo,hi=((p,pos-T/2,0),(q,pos+T/2,phase)) if axis=='x' else ((pos-T/2,p,0),(pos+T/2,q,phase))
            box(f'log{tag}{n}',coll,lo,hi,WOODX if axis=='x' else WOODY,0.035); n+=1
    while z<zmax-1e-4:
        z1=min(z+CH,zmax)
        jit=random.uniform(-0.03,0.03)
        for p,q in segs(a-EXT+jit,b+EXT-jit,holes,z,z1):
            t=T*random.uniform(0.92,1.05)
            lo,hi=((p,pos-t/2,z),(q,pos+t/2,z1)) if axis=='x' else ((pos-t/2,p,z),(pos+t/2,q,z1))
            box(f'log{tag}{n}',coll,lo,hi,WOODX if axis=='x' else WOODY,0.06); n+=1
        z=z1
DOOR=(1.10,1.90,0.0,1.66); WIN_S=(2.30,3.05,0.88,1.56); WIN_E=(1.70,2.35,0.88,1.56)
# BACK: north + west walls, floor
wall(C['BACK'],'x',NORTH,WEST,EAST,[],0.0,tag='N')
wall(C['BACK'],'y',WEST,SOUTH,NORTH,[],CH/2,tag='W')
for i in range(15):
    x0=0.1+i*0.254; box(f'plank{i}',C['BACK'],(x0,0.1,0.0),(x0+0.248,3.9,0.03),FLOOR,0.008)
# FRONT: south + east walls with openings
wall(C['FRONT'],'x',SOUTH,WEST,EAST,[DOOR,WIN_S],0.0,tag='S')
wall(C['FRONT'],'y',EAST,SOUTH,NORTH,[WIN_E],CH/2,tag='E')
def frame(coll,axis,pos,h0,h1,z0,z1,name,sill=True):
    tw=0.09
    if axis=='x':
        box(name+'L',coll,(h0-tw,pos-T/2-0.03,z0),(h0,pos+T/2+0.03,z1+tw),WOODL,0.015)
        box(name+'R',coll,(h1,pos-T/2-0.03,z0),(h1+tw,pos+T/2+0.03,z1+tw),WOODL,0.015)
        box(name+'T',coll,(h0-tw-0.05,pos-T/2-0.04,z1),(h1+tw+0.05,pos+T/2+0.04,z1+tw+0.02),WOODL,0.015)
        if sill and z0>0.1: box(name+'B',coll,(h0-tw,pos-T/2-0.07,z0-0.07),(h1+tw,pos+T/2+0.03,z0),WOODL,0.015)
        if sill and z0>0.1: box(name+'D',coll,(h0,pos+0.02,z0),(h1,pos+T/2,z1),DARK)
    else:
        box(name+'L',coll,(pos-T/2-0.03,h0-tw,z0),(pos+T/2+0.03,h0,z1+tw),WOODL,0.015)
        box(name+'R',coll,(pos-T/2-0.03,h1,z0),(pos+T/2+0.03,h1+tw,z1+tw),WOODL,0.015)
        box(name+'T',coll,(pos-T/2-0.04,h0-tw-0.05,z1),(pos+T/2+0.04,h1+tw+0.05,z1+tw+0.02),WOODL,0.015)
        box(name+'B',coll,(pos-T/2-0.03,h0-tw,z0-0.07),(pos+T/2+0.07,h1+tw,z0),WOODL,0.015)
        box(name+'D',coll,(pos-T/2,h0,z0),(pos-0.02,h1,z1),DARK)
frame(C['FRONT'],'x',SOUTH,DOOR[0],DOOR[1],0.0,DOOR[3],'DoorFrame',sill=False)
box('Threshold',C['FRONT'],(DOOR[0]-0.05,SOUTH-T/2-0.06,0),(DOOR[1]+0.05,SOUTH+T/2,0.06),WOODL,0.01)
frame(C['FRONT'],'x',SOUTH,WIN_S[0],WIN_S[1],WIN_S[2],WIN_S[3],'WinS')
frame(C['FRONT'],'y',EAST,WIN_E[0],WIN_E[1],WIN_E[2],WIN_E[3],'WinE')
# shutters (closed one, open one) on south window
box('ShutterL',C['FRONT'],(WIN_S[0]-0.42,SOUTH-T/2-0.07,WIN_S[2]),(WIN_S[0]-0.1,SOUTH-T/2-0.03,WIN_S[3]),WOODL,0.01)
# porch
PY0,PY1=-0.85,SOUTH-T/2
for i in range(16):
    x0=0.05+i*0.244; box(f'deck{i}',C['FRONT'],(x0,PY0,0.0),(x0+0.238,PY1,0.09),FLOOR,0.01)
box('deckBeam',C['FRONT'],(0.03,PY0-0.02,-0.05),(3.97,PY0+0.12,0.08),WOOD,0.02)
SLOPE=0.72; EAVE_Z=lambda y: WALL_H+(y-SOUTH)*SLOPE if y<2.0 else WALL_H+(NORTH-y)*SLOPE
for px in (0.25,3.75):
    zt=EAVE_Z(-0.70)-0.10
    box(f'post{px}',C['FRONT'],(px-0.09,-0.79,0.0),(px+0.09,-0.61,zt),WOOD,0.03)
box('plate',C['FRONT'],(0.05,-0.80,EAVE_Z(-0.7)-0.24),(3.95,-0.60,EAVE_Z(-0.7)-0.08),WOOD,0.03)
# FRONT_LOW: copy of front (south/east walls + porch deck) cut at CUT
CUT=0.30
for o in list(C['FRONT'].objects):
    if o.name.startswith(('post','plate','Shutter','WinE','WinS')): continue
    if o.name.startswith(('log','DoorFrame','Threshold','deck')):
        bb=[o.matrix_world@Vector(v) for v in o.bound_box]
        if min(v.z for v in bb)>=CUT: continue
        n=o.copy(); n.data=o.data.copy(); n.name=o.name+'_low'; C['FRONT_LOW'].objects.link(n)
        n.modifiers.clear()
        n.data.transform(n.matrix_world); n.matrix_world.identity()
        bm=bmesh.new(); bm.from_mesh(n.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-5,plane_co=(0,0,CUT),plane_no=(0,0,1),clear_outer=True)
        bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary])
        bm.to_mesh(n.data); bm.free()
        m=n.modifiers.new('bev','BEVEL'); m.width=0.03; m.segments=2
# gables (vertical boards): west in BACK, east in FRONT
def gable(coll,x,name):
    y0,y1=SOUTH-T/2,NORTH+T/2; ym=2.0; zt=WALL_H+(ym-SOUTH)*SLOPE
    bm=bmesh.new()
    prof=[(y0,WALL_H-0.02),(y1,WALL_H-0.02),(ym,zt)]
    A=[bm.verts.new((x-0.07,y,z)) for y,z in prof]; B=[bm.verts.new((x+0.07,y,z)) for y,z in prof]
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(3): bm.faces.new((A[i],A[(i+1)%3],B[(i+1)%3],B[i]))
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new(name,me); coll.objects.link(o); me.materials.append(WOODL)
    for i in range(1,14):  # board seams
        yy=y0+i*0.25; top=WALL_H+min(yy-SOUTH,NORTH-yy)*SLOPE
        if top>WALL_H+0.05: box(f'{name}s{i}',coll,(x+(0.07 if x>2 else -0.075),yy-0.012,WALL_H),(x+(0.075 if x>2 else -0.07),yy+0.012,top-0.02),DARK)
gable(C['BACK'],WEST,'GableW'); gable(C['FRONT'],EAST,'GableE')
# DOORS
def door(coll,name,openang):
    import mathutils
    parts=[]
    for i in range(4):
        x0=DOOR[0]+0.02+i*0.19
        parts.append(box(f'{name}b{i}',coll,(x0,SOUTH-0.03,0.04),(x0+0.185,SOUTH+0.03,DOOR[3]-0.02),WOODL,0.01))
    for zz in (0.3,1.3):
        parts.append(box(f'{name}s{zz}',coll,(DOOR[0]+0.05,SOUTH-0.07,zz),(DOOR[1]-0.05,SOUTH-0.03,zz+0.07),IRON))
    parts.append(box(f'{name}ring',coll,(DOOR[1]-0.2,SOUTH-0.09,0.82),(DOOR[1]-0.14,SOUTH-0.03,0.9),IRON))
    if openang:
        piv=Vector((DOOR[0]+0.02,SOUTH,0)); R=mathutils.Matrix.Rotation(math.radians(openang),4,'Z')
        for o in parts:
            o.matrix_world=mathutils.Matrix.Translation(piv)@R@mathutils.Matrix.Translation(-piv)@o.matrix_world
door(C['DOOR_CLOSED'],'Door',0); door(C['DOOR_OPEN'],'DoorOpen',-80)
# ROOF: thatch slabs
def slab(name,y_ridge,y_eave,x0,x1,thick=0.32,nx=120,ny=18,zoff=0.0,rag=0.05):
    bm=bmesh.new(); vs=[]
    for j in range(ny+1):
        row=[]; t=j/ny; y=y_ridge+(y_eave-y_ridge)*t
        for i in range(nx+1):
            x=x0+(x1-x0)*i/nx
            z=EAVE_Z(y)+0.06+zoff+ (random.uniform(-0.06,0.0) if j==ny else 0)
            row.append(bm.verts.new((x+ (random.uniform(-0.03,0.03) if i in (0,nx) else 0),y+(random.uniform(-rag,rag) if j==ny else 0),z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx): bm.faces.new((vs[j][i],vs[j][i+1],vs[j+1][i+1],vs[j+1][i]))
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); C['ROOF'].objects.link(o); me.materials.append(THATCH)
    so=o.modifiers.new('sol','SOLIDIFY'); so.thickness=thick; so.offset=1.0
    tx=bpy.data.textures.new(name+'n','CLOUDS'); tx.noise_scale=0.08
    dp=o.modifiers.new('disp','DISPLACE'); dp.texture=tx; dp.strength=0.035; dp.mid_level=0.5
    return o
def rows(name,yr,ye,n):
    step=(ye-yr)/n
    for k in range(n):
        a=yr+k*step; b=yr+(k+1)*step
        slab(f'{name}{k}',a-0.18*(1 if step>0 else -1),b,-0.40-random.uniform(0,0.04),4.40+random.uniform(0,0.04),thick=0.15,ny=6,zoff=0.035*(n-k),rag=0.045)
rows('ThatchS',2.04,-1.0,11); rows('ThatchN',1.96,NORTH+0.62,7)
bpy.ops.mesh.primitive_cylinder_add(radius=0.16,depth=4.86,location=(2.0,2.0,WALL_H+(2.0-SOUTH)*SLOPE+0.50),rotation=(0,math.pi/2,0),vertices=24)
rid=bpy.context.active_object; rid.name='Ridge'
for c in rid.users_collection: c.objects.unlink(rid)
C['ROOF'].objects.link(rid); rid.data.materials.append(THATCH)
# under-thatch seal so no light leaks
def seal(name,y_r,y_e):
    bm=bmesh.new(); a=[bm.verts.new((x,y,EAVE_Z(y)+0.03)) for x,y in ((-0.38,y_r),(4.38,y_r),(4.38,y_e),(-0.38,y_e))]
    bm.faces.new(a); me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o=bpy.data.objects.new(name,me); C['ROOF'].objects.link(o); me.materials.append(DARK)
seal('SealS',2.05,-0.95); seal('SealN',1.95,NORTH+0.58)
# binding battens
for yy in (0.6,-0.4):
    pass
# ---------- light / camera ----------
def sun(name,energy,color,rot):
    l=bpy.data.lights.new(name,'SUN');l.energy=energy;l.color=color;l.angle=math.radians(3)
    o=bpy.data.objects.new(name,l);s.collection.objects.link(o);o.rotation_euler=[math.radians(a) for a in rot]
sun('V4Sun_key',3.2,(1.0,0.93,0.84),(40,0,-150)); sun('V4Sun_fill',0.6,(0.82,0.86,0.95),(60,0,40))
w=bpy.data.worlds.new('W'); s.world=w; w.use_nodes=True; nt=w.node_tree; nt.nodes.clear()
bg=nt.nodes.new('ShaderNodeBackground'); out=nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(bg.outputs[0],out.inputs[0])
bg.inputs[0].default_value=(0.55,0.58,0.62,1); bg.inputs[1].default_value=0.22
cd=bpy.data.cameras.new('Cam'); cam=bpy.data.objects.new('Camera',cd); s.collection.objects.link(cam); s.camera=cam
cd.type='ORTHO'; cd.sensor_fit='HORIZONTAL'; cd.ortho_scale=W/(192/math.sqrt(2))
cam.rotation_euler=(math.radians(60),0,math.radians(45)); cam.location=(12,-12,12)
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.render.threads_mode='FIXED'; s.render.threads=3
s.render.resolution_x=W; s.render.resolution_y=H; s.render.film_transparent=True
s.cycles.samples=int(__import__("os").environ.get("SAMP","96")); s.cycles.use_denoising=True
s.view_settings.view_transform='Standard'; s.view_settings.look='None'; s.view_settings.exposure=-0.2
bpy.context.view_layer.update()
p0=world_to_camera_view(s,cam,TILE00); cd.shift_x=1; bpy.context.view_layer.update(); px=world_to_camera_view(s,cam,TILE00)
cd.shift_x=0; cd.shift_y=1; bpy.context.view_layer.update(); py=world_to_camera_view(s,cam,TILE00)
cd.shift_x=(ANCHOR[0]/W-p0.x)/(px.x-p0.x); cd.shift_y=((1-ANCHOR[1]/H)-p0.y)/(py.y-p0.y)
bpy.ops.wm.save_as_mainfile(filepath=D+'/plains_cabin_02.blend')
for name,c in [('back','BACK'),('front','FRONT'),('front_low','FRONT_LOW'),('roof','ROOF'),('door_closed','DOOR_CLOSED'),('door_open','DOOR_OPEN')]:
    if ONLY and name not in ONLY: continue
    for n in LAYERS: C[n].hide_render=(n!=c)
    s.render.filepath=OUT+'/'+name+'.png'; bpy.ops.render.render(write_still=True); print('RENDERED',name,flush=True)
for n in LAYERS: C[n].hide_render=n not in ('BACK','FRONT','ROOF','DOOR_CLOSED')
bpy.ops.wm.save_as_mainfile(filepath=D+'/plains_cabin_02.blend'); print('DONE')
