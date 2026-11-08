"""Gerador de casas em camadas (mesma câmera/luz/escala das cabanas do Ludimus: art/src/plains_cabin_02_build.py).
Monta cada casa por parâmetros (tamanho, parede, telhado, portas e janelas) e renderiza as camadas
back / front / front_low / roof / door_closed / door_open em art/buildings/<bioma>/<id>/.
Rodar com o bpy (pip install bpy, Python 3.11):
    SAMP=24 python3.11 art/src/gen_houses_bpy.py [id1,id2,...]
Coordenadas: tile (i, j) do jogo = Blender x em [i, i+1], y em [h-j-1, h-j]. A parede sul (y baixo) é a da frente.
"""
import bpy, bmesh, math, random, sys, os, json, shutil
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROPS_SRC = os.path.join(ROOT, 'art', 'buildings', 'plains', 'plains_cabin_01', 'props')

HOUSES = {
    # id: bioma, tamanho, parede, telhado, porta (i), janelas sul (i), janelas leste (j do jogo), extras
    'plains_timber_01': dict(biome='plains', size=(6, 5), wall='timber', roof='thatch', door=2, win_s=[4], win_e=[2], chimney=False),
    'plains_timber_02': dict(biome='plains', size=(5, 5), wall='timber', roof='shingle', door=1, win_s=[3], win_e=[1, 3], chimney=True),
    'plains_stone_01': dict(biome='plains', size=(7, 5), wall='stone', roof='slate', door=3, win_s=[1, 5], win_e=[2], chimney=True),
    'north_log_01': dict(biome='north', size=(5, 5), wall='log', roof='snow', door=2, win_s=[], win_e=[2], chimney=True),
    'north_stone_01': dict(biome='north', size=(6, 4), wall='stone', roof='snow', door=1, win_s=[3, 4], win_e=[1], chimney=True),
    'desert_adobe_01': dict(biome='outremer', size=(5, 5), wall='adobe', roof='flat', door=2, win_s=[], win_e=[2], chimney=False),
    'desert_adobe_02': dict(biome='outremer', size=(6, 4), wall='adobe', roof='flat', door=4, win_s=[1, 2], win_e=[1], chimney=False, awning=True),
    # cidades grandes: lojas próprias, castelo
    'city_tavern_01': dict(biome='plains', size=(8, 6), wall='timber', roof='shingle', door=3, win_s=[1, 5, 6], win_e=[1, 3], chimney=True, tall=True, win2=True, interior='tavern'),
    'city_forge_01': dict(biome='plains', size=(6, 5), wall='stone', roof='shingle', door=1, win_s=[], win_e=[2], chimney=True, big_chimney=True, open_front=True, interior='forge'),
    'city_bank_01': dict(biome='plains', size=(6, 5), wall='stone', roof='slate', door=2, win_s=[4], win_e=[1, 3], chimney=False, columns=True, tall=True, interior='bank'),
    'city_tower_01': dict(biome='plains', size=(4, 4), wall='stone', roof='slate', door=1, win_s=[], win_e=[1], chimney=False, WH=5.2, slope=1.7, win2=True, interior='mage'),
    'city_shop_01': dict(biome='plains', size=(5, 4), wall='timber', roof='shingle', door=2, win_s=[1, 3], win_e=[1], chimney=False, awning=True, tall=True, win2=True, interior='shop'),
    'city_keep_01': dict(biome='plains', size=(12, 9), wall='stone', roof='flat', door=5, win_s=[2, 9], win_e=[2, 5], chimney=False, WH=4.6, merlons=True, throne=True, win2=True),
    'north_tavern_01': dict(biome='north', size=(8, 6), wall='log', roof='snow', door=3, win_s=[1, 6], win_e=[2, 4], chimney=True, tall=True, interior='tavern'),
    'desert_palace_01': dict(biome='outremer', size=(12, 9), wall='adobe', roof='flat', door=5, win_s=[2, 9], win_e=[2, 5], chimney=False, WH=4.2, merlons=True, throne=True, win2=True),
    'ruins_chapel_01': dict(biome='ruins', size=(7, 6), wall='stone', roof='slate', door=3, win_s=[1, 5], win_e=[1, 3], chimney=False, tall=True),
}

ONLY = sys.argv[-1].split(',') if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else None
SAMP = int(os.environ.get('SAMP', '24'))
CUT = 0.30


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


# ---------------------------------------------------------------- materiais
def _mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = 0.88
    return m, nt, nt.nodes, nt.links, bs


def _uv(N, L, axis, scale=(1, 1, 1)):
    """coordenada no plano da parede (posição de mundo): x-z para paredes ao longo de x, y-z ao longo de y, x-y para chão/telhado"""
    geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
    cmb = N.new('ShaderNodeCombineXYZ')
    if axis == 'z':
        L.new(sep.outputs['X'], cmb.inputs[0]); L.new(sep.outputs['Y'], cmb.inputs[1])
    else:   # paredes: X+Y corre ao longo de qualquer parede (e nas pontas também), Z na altura
        ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; L.new(sep.outputs['X'], ad.inputs[0]); L.new(sep.outputs['Y'], ad.inputs[1])
        L.new(ad.outputs[0], cmb.inputs[0]); L.new(sep.outputs['Z'], cmb.inputs[1])
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale; L.new(cmb.outputs[0], mp.inputs['Vector'])
    return mp.outputs['Vector']


def mat_brick(name, axis, c1, c2, mortar, bw, bh, bump=0.6, offset=0.5):
    m, nt, N, L, bs = _mat(name)
    v = _uv(N, L, axis)
    br = N.new('ShaderNodeTexBrick'); br.offset = offset
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1); br.inputs['Mortar'].default_value = (*mortar, 1)
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = bw; br.inputs['Row Height'].default_value = bh
    br.inputs['Mortar Size'].default_value = 0.022; br.inputs['Bias'].default_value = 0.0; br.squash = 1.0; br.inputs['Mortar Smooth'].default_value = 0.2
    L.new(v, br.inputs['Vector'])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6; L.new(v, nz.inputs['Vector'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    L.new(br.outputs['Color'], mx.inputs['A']); L.new(nz.outputs['Color'], mx.inputs['B']); L.new(mx.outputs['Result'], bs.inputs['Base Color'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    sub = N.new('ShaderNodeMath'); sub.operation = 'ADD'; L.new(br.outputs['Fac'], sub.inputs[0]); L.new(nz.outputs['Fac'], sub.inputs[1])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs['Fac'], inv.inputs[1])
    L.new(inv.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])
    return m


def mat_noise(name, lo, hi, scale=4, bump=0.25, detail=8):
    m, nt, N, L, bs = _mat(name)
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    geo = N.new('ShaderNodeNewGeometry'); L.new(geo.outputs['Position'], nz.inputs['Vector'])
    r = N.new('ShaderNodeValToRGB'); el = r.color_ramp.elements; el[0].position = 0.3; el[0].color = (*lo, 1); el[1].position = 0.75; el[1].color = (*hi, 1)
    L.new(nz.outputs['Fac'], r.inputs['Fac']); L.new(r.outputs['Color'], bs.inputs['Base Color'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])
    return m


def mat_wood(name, axis, lo, hi, scale=9, bump=0.3):
    m, nt, N, L, bs = _mat(name)
    v = _uv(N, L, axis, (1, 0.25, 1) if axis != 'z' else (0.25, 1, 1))
    wv = N.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y' if axis != 'z' else 'X'
    wv.inputs['Scale'].default_value = scale; wv.inputs['Distortion'].default_value = 5; wv.inputs['Detail'].default_value = 8
    L.new(v, wv.inputs['Vector'])
    r = N.new('ShaderNodeValToRGB'); el = r.color_ramp.elements; el[0].position = 0.2; el[0].color = (*lo, 1); el[1].position = 0.85; el[1].color = (*hi, 1)
    L.new(wv.outputs['Fac'], r.inputs['Fac']); L.new(r.outputs['Color'], bs.inputs['Base Color'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; L.new(wv.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])
    return m


def mat_flat(name, rgb, metal=0.0, rough=0.9):
    m, nt, N, L, bs = _mat(name); bs.inputs['Base Color'].default_value = (*rgb, 1); bs.inputs['Metallic'].default_value = metal; bs.inputs['Roughness'].default_value = rough
    return m


def mat_snow_over(name, base_fn):
    """telhado com neve: o material base embaixo e branco por cima, mais branco onde a face olha para cima"""
    m = base_fn(name)
    nt = m.node_tree; N = nt.nodes; L = nt.links; bs = N['Principled BSDF']
    src = bs.inputs['Base Color'].links[0].from_socket
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 10
    geo = N.new('ShaderNodeNewGeometry'); L.new(geo.outputs['Position'], nz.inputs['Vector'])
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs[0])
    add = N.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'; L.new(nz.outputs['Fac'], add.inputs[0]); add.inputs[1].default_value = 0.9; L.new(sep.outputs['Z'], add.inputs[2])
    ramp = N.new('ShaderNodeValToRGB'); e = ramp.color_ramp.elements; e[0].position = 0.95; e[1].position = 1.12
    e[0].color = (0, 0, 0, 1); e[1].color = (1, 1, 1, 1); L.new(add.outputs[0], ramp.inputs['Fac'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(ramp.outputs['Color'], mx.inputs['Factor'])
    L.new(src, mx.inputs['A']); mx.inputs['B'].default_value = (0.86, 0.89, 0.94, 1); L.new(mx.outputs['Result'], bs.inputs['Base Color'])
    return m


def materials(spec):
    M = {}
    M['dark'] = mat_flat('Dark', (0.012, 0.010, 0.009), rough=1)
    M['iron'] = mat_flat('Iron', (0.05, 0.048, 0.045), metal=0.8, rough=0.6)
    M['trimx'] = mat_wood('TrimX', 'x', (0.05, 0.035, 0.023), (0.30, 0.21, 0.135), 10, 0.2)
    M['trimy'] = mat_wood('TrimY', 'y', (0.05, 0.035, 0.023), (0.30, 0.21, 0.135), 10, 0.2)
    M['beam'] = mat_wood('Beam', 'x', (0.025, 0.017, 0.012), (0.12, 0.08, 0.05), 14, 0.25)
    M['floor'] = mat_wood('Floor', 'z', (0.035, 0.025, 0.016), (0.22, 0.155, 0.10), 12, 0.2)
    w = spec['wall']
    if w == 'stone':
        for a in 'xy': M['wall' + a] = mat_brick('Stone' + a, a, (0.36, 0.33, 0.29), (0.22, 0.20, 0.18), (0.11, 0.10, 0.09), 0.78, 0.34, 1.0)
        M['floor'] = mat_brick('StoneFloor', 'z', (0.22, 0.21, 0.2), (0.16, 0.155, 0.15), (0.07, 0.07, 0.065), 0.6, 0.6, 0.4)
    elif w == 'adobe':
        for a in 'xy': M['wall' + a] = mat_noise('Adobe' + a, (0.45, 0.33, 0.21), (0.68, 0.53, 0.36), 3.0, 0.35)
        M['floor'] = mat_brick('Tile', 'z', (0.40, 0.22, 0.13), (0.34, 0.19, 0.11), (0.25, 0.2, 0.15), 0.5, 0.5, 0.3)
    elif w == 'timber':
        for a in 'xy': M['wall' + a] = mat_noise('Plaster' + a, (0.60, 0.54, 0.44), (0.86, 0.80, 0.68), 5.0, 0.2)
    else:   # toras
        M['wallx'] = mat_wood('LogX', 'x', (0.040, 0.028, 0.018), (0.27, 0.19, 0.12), 14, 0.3)
        M['wally'] = mat_wood('LogY', 'y', (0.040, 0.028, 0.018), (0.27, 0.19, 0.12), 14, 0.3)
    r = spec['roof']
    if r == 'thatch':
        M['roof'] = mat_wood('Thatch', 'z', (0.07, 0.055, 0.03), (0.42, 0.34, 0.19), 70, 0.9)
    elif r == 'slate':
        M['roof'] = mat_brick('Slate', 'z', (0.10, 0.11, 0.13), (0.07, 0.075, 0.09), (0.03, 0.03, 0.035), 0.32, 0.22, 0.9)
    elif r == 'shingle':
        M['roof'] = mat_brick('Shingle', 'z', (0.17, 0.10, 0.06), (0.12, 0.07, 0.045), (0.04, 0.03, 0.02), 0.28, 0.2, 0.9)
    elif r == 'snow':
        M['roof'] = mat_snow_over('Snow', lambda n: mat_brick(n, 'z', (0.14, 0.09, 0.06), (0.10, 0.065, 0.045), (0.04, 0.03, 0.02), 0.28, 0.2, 0.9))
    else:
        M['roof'] = M['wallx']
    M['stone'] = mat_brick('Chimney', 'x', (0.28, 0.27, 0.25), (0.2, 0.19, 0.18), (0.1, 0.1, 0.09), 0.4, 0.22, 0.8)
    M['cloth'] = mat_noise('Cloth', (0.35, 0.08, 0.06), (0.62, 0.20, 0.12), 6, 0.1)
    return M


# ---------------------------------------------------------------- geometria
def box(name, coll, lo, hi, mat, bevel=0.0, low=None):
    lo, hi = [min(a, b) for a, b in zip(lo, hi)], [max(a, b) for a, b in zip(lo, hi)]
    if hi[0] - lo[0] < 1e-4 or hi[1] - lo[1] < 1e-4 or hi[2] - lo[2] < 1e-4: return None
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    o.location = [(a + b) / 2 for a, b in zip(lo, hi)]; o.scale = [b - a for a, b in zip(lo, hi)]
    me.materials.append(mat)
    if bevel:
        m = o.modifiers.new('bev', 'BEVEL'); m.width = bevel; m.segments = 2; m.affect = 'EDGES'
    if low is not None and lo[2] < CUT:   # cópia cortada na altura do joelho para quando o jogador está dentro
        box(name + '_low', low, lo, (hi[0], hi[1], min(hi[2], CUT)), mat, bevel)
    return o


def segs(a, b, holes, z0, z1):
    out = [(a, b)]
    for h0, h1, hz0, hz1 in holes:
        if z1 <= hz0 + 1e-4 or z0 >= hz1 - 1e-4: continue
        nxt = []
        for p, q in out:
            if q <= h0 or p >= h1: nxt.append((p, q)); continue
            if p < h0: nxt.append((p, h0))
            if q > h1: nxt.append((h1, q))
        out = nxt
    return out


class House:
    def __init__(self, hid, spec):
        self.id, self.s = hid, spec
        self.w, self.h = spec['size']
        self.WH = spec.get('WH') or (2.9 if spec.get('tall') else 2.25)
        self.T = 0.42 if spec['wall'] in ('stone', 'adobe') else 0.30
        self.S, self.N, self.Wx, self.E = 0.3, self.h - 0.3, 0.3, self.w - 0.3
        random.seed(hash(hid) & 0xffff)

    def build(self, C, M):
        s, T, WH = self.s, self.T, self.WH
        door = (s['door'] + 0.12, s['door'] + 0.88, 0.0, 1.72)
        winS = [(i + 0.2, i + 0.8, 0.95, 1.6) for i in s['win_s']]
        winE = [(self.h - j - 0.8, self.h - j - 0.2, 0.95, 1.6) for j in s['win_e']]
        if s.get('win2'):   # segundo andar de janelas
            up = [WH - 1.15, WH - 0.5] if WH > 3.5 else [2.0, 2.55]
            winS += [(i + 0.25, i + 0.75, up[0], up[1]) for i in range(1, self.w - 1, 2) if i != s['door']]
            winE += [(self.h - j - 0.75, self.h - j - 0.25, up[0], up[1]) for j in range(1, self.h - 1, 2)]
        self.door = door
        # chão
        if s['wall'] in ('stone', 'adobe'):
            box('floor', C['BACK'], (0.1, 0.1, 0), (self.w - 0.1, self.h - 0.1, 0.04), M['floor'])
        else:
            n = int((self.w - 0.2) / 0.25)
            for i in range(n):
                x0 = 0.1 + i * 0.25; box(f'plank{i}', C['BACK'], (x0, 0.1, 0), (x0 + 0.245, self.h - 0.1, 0.035), M['floor'], 0.006)
        # paredes: fundo (norte, oeste) e frente (sul, leste)
        self.wall(C['BACK'], None, 'x', self.N, self.Wx - T / 2, self.E + T / 2, [], M)
        self.wall(C['BACK'], None, 'y', self.Wx, self.S - T / 2, self.N + T / 2, [], M)
        if s.get('open_front'):   # oficina aberta: só pilares de madeira e uma viga, dá para ver a forja de fora
            for x in [self.Wx] + [k + 0.5 for k in range(1, self.w - 1, 2)] + [self.E]:
                box('post', C['FRONT'], (x - 0.13, self.S - 0.13, 0), (x + 0.13, self.S + 0.13, WH), M['beam'], 0.02, C['FRONT_LOW'])
            box('lintel', C['FRONT'], (self.Wx - 0.15, self.S - 0.15, WH - 0.3), (self.E + 0.15, self.S + 0.15, WH), M['beam'], 0.02)
            box('sill', C['FRONT'], (self.Wx, self.S - 0.1, 0), (self.E, self.S + 0.1, 0.12), M['stone'], 0.02, C['FRONT_LOW'])
        else:
            self.wall(C['FRONT'], C['FRONT_LOW'], 'x', self.S, self.Wx - T / 2, self.E + T / 2, [door] + winS, M)
        self.wall(C['FRONT'], C['FRONT_LOW'], 'y', self.E, self.S - T / 2, self.N + T / 2, winE, M)
        for h0, h1, z0, z1 in winS: self.window(C['FRONT'], 'x', self.S, h0, h1, z0, z1, M)
        for h0, h1, z0, z1 in winE: self.window(C['FRONT'], 'y', self.E, h0, h1, z0, z1, M)
        if not s.get('open_front'):
            self.frame(C['FRONT'], C['FRONT_LOW'], 'x', self.S, door[0], door[1], 0, door[3], M)
            self.doors(C, M)
        if s.get('interior'): self.furnish(C['BACK'], M, s['interior'])
        if s['wall'] == 'timber': self.timber(C, M, [door] + winS, winE)
        if s['roof'] == 'flat': self.flat_roof(C, M)
        else: self.gable_roof(C, M)
        if s.get('columns'):   # pórtico de colunas na frente (banco)
            y = self.S - T / 2 - 0.9
            for k in range(self.w):
                x = 0.5 + k
                bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=WH, location=(x, y, WH / 2), vertices=20)
                c = bpy.context.active_object
                for cc in c.users_collection: cc.objects.unlink(c)
                C['FRONT'].objects.link(c); c.data.materials.append(M['wallx'])
                box('base', C['FRONT'], (x - 0.24, y - 0.24, 0), (x + 0.24, y + 0.24, 0.16), M['stone'], 0.02, C['FRONT_LOW'])
            box('entab', C['ROOF'], (0.1, y - 0.3, WH), (self.w - 0.1, self.S + T / 2, WH + 0.35), M['wallx'], 0.03)
            box('steps', C['FRONT'], (0.1, y - 0.45, 0), (self.w - 0.1, self.S - T / 2, 0.1), M['stone'], 0.02, C['FRONT_LOW'])
        if s.get('throne'):    # tapete do portão ao trono, trono no fundo, colunas de dentro
            d0, d1 = self.door[0], self.door[1]; cxm = (d0 + d1) / 2
            red = mat_noise('Carpet', (0.25, 0.03, 0.03), (0.45, 0.07, 0.06), 8, 0.05)
            gold = mat_flat('Gold', (0.7, 0.5, 0.15), metal=0.9, rough=0.35)
            box('carpet', C['BACK'], (cxm - 0.6, self.S + 0.2, 0.04), (cxm + 0.6, self.N - 1.0, 0.06), red)
            ty = self.N - 0.75
            box('dais', C['BACK'], (cxm - 1.3, ty - 0.9, 0), (cxm + 1.3, self.N - T / 2, 0.25), M['stone'], 0.02)
            box('seat', C['BACK'], (cxm - 0.45, ty - 0.35, 0.25), (cxm + 0.45, ty + 0.25, 0.75), gold, 0.03)
            box('cushion', C['BACK'], (cxm - 0.38, ty - 0.3, 0.75), (cxm + 0.38, ty + 0.2, 0.85), red, 0.03)
            box('back', C['BACK'], (cxm - 0.45, ty + 0.1, 0.75), (cxm + 0.45, ty + 0.3, 2.3), gold, 0.03)
            box('backc', C['BACK'], (cxm - 0.32, ty + 0.05, 0.9), (cxm + 0.32, ty + 0.12, 2.1), red)
            for ax in (-0.5, 0.5): box('arm', C['BACK'], (cxm + ax - 0.06, ty - 0.35, 0.75), (cxm + ax + 0.06, ty + 0.2, 1.1), gold, 0.02)
            for bx in (2.0, self.w - 2.0):   # estandartes na parede do fundo
                box('banner', C['BACK'], (bx - 0.35, self.N - T / 2 - 0.04, 1.2), (bx + 0.35, self.N - T / 2 - 0.01, WH - 0.4), red)
                box('bannerG', C['BACK'], (bx - 0.4, self.N - T / 2 - 0.06, WH - 0.45), (bx + 0.4, self.N - T / 2 - 0.01, WH - 0.35), gold)
        if s.get('chimney'):
            cx = self.Wx + 0.9; cy = self.N - 0.35
            cw = 0.55 if s.get('big_chimney') else 0.3
            box('chimney', C['ROOF'], (cx - cw, cy - cw, WH), (cx + cw, cy + cw, self.ridge_z + 0.9), M['stone'], 0.02)
            box('chimneyTop', C['ROOF'], (cx - cw - 0.06, cy - cw - 0.06, self.ridge_z + 0.9), (cx + cw + 0.06, cy + cw + 0.06, self.ridge_z + 1.0), M['stone'], 0.02)
        if s.get('awning'):
            x0, x1 = door[0] - 0.9, door[1] + 0.9
            bm = bmesh.new(); vs = [bm.verts.new(v) for v in ((x0, self.S - T / 2, 2.05), (x1, self.S - T / 2, 2.05), (x1, self.S - 1.3, 1.75), (x0, self.S - 1.3, 1.75))]
            bm.faces.new(vs); me = bpy.data.meshes.new('awn'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('awn', me); C['FRONT'].objects.link(o); me.materials.append(M['cloth'])
            o.modifiers.new('sol', 'SOLIDIFY').thickness = 0.03
            for x in (x0 + 0.05, x1 - 0.05): box('awnPost', C['FRONT'], (x - 0.04, self.S - 1.32, 0), (x + 0.04, self.S - 1.24, 1.76), M['beam'], low=C['FRONT_LOW'])

    def furnish(self, c, M, kind):
        """móveis de cada ofício, no chão (camada de fundo)"""
        iron = M['iron']; wood = M['trimx']; st = M['stone']
        glow = bpy.data.materials.new('Coals'); glow.use_nodes = True; bs = glow.node_tree.nodes['Principled BSDF']
        bs.inputs['Base Color'].default_value = (1, 0.35, 0.05, 1); bs.inputs['Emission Color'].default_value = (1, 0.35, 0.05, 1); bs.inputs['Emission Strength'].default_value = 6
        x0, x1, y0, y1 = self.Wx + self.T / 2, self.E - self.T / 2, self.S + self.T / 2, self.N - self.T / 2
        def barrel(x, y, r=0.28, h=0.75):
            bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(x, y, h / 2), vertices=16); o = bpy.context.active_object
            for cc in o.users_collection: cc.objects.unlink(o)
            c.objects.link(o); o.data.materials.append(M['trimy'])
            for z in (0.15, h - 0.15): box('hoop', c, (x - r - 0.01, y - r - 0.01, z - 0.03), (x + r + 0.01, y + r + 0.01, z + 0.03), iron)
        def table(x, y, w=1.2, d=0.7):
            box('top', c, (x - w / 2, y - d / 2, 0.7), (x + w / 2, y + d / 2, 0.78), wood, 0.02)
            for dx in (-w / 2 + 0.08, w / 2 - 0.08):
                for dy in (-d / 2 + 0.08, d / 2 - 0.08): box('leg', c, (x + dx - 0.04, y + dy - 0.04, 0), (x + dx + 0.04, y + dy + 0.04, 0.7), wood)
        def shelf(x, y, w=1.6, cols=((0.5, 0.2, 0.1), (0.2, 0.3, 0.5), (0.6, 0.55, 0.3))):
            box('shelf', c, (x - w / 2, y - 0.18, 0), (x + w / 2, y + 0.18, 2.0), wood, 0.02)
            for k, z in enumerate((0.45, 0.95, 1.45)):
                for i in range(6):
                    cx = x - w / 2 + 0.15 + i * (w - 0.3) / 5
                    box('good', c, (cx - 0.08, y - 0.24, z), (cx + 0.08, y - 0.12, z + 0.28), mat_flat('g%d%d' % (k, i), cols[(i + k) % len(cols)]))
        if kind == 'forge':
            # forja de pedra com brasas, fole, bigorna, tina de água, suporte de armas
            fx = x0 + 0.9; fy = y1 - 0.8
            box('hearth', c, (fx - 0.8, fy - 0.6, 0), (fx + 0.8, fy + 0.6, 0.85), st, 0.03)
            box('coals', c, (fx - 0.6, fy - 0.4, 0.85), (fx + 0.6, fy + 0.4, 0.92), glow)
            box('hood', c, (fx - 0.85, fy - 0.65, 1.9), (fx + 0.85, fy + 0.65, 2.2), st, 0.03)
            box('flue', c, (fx - 0.4, fy - 0.3, 2.2), (fx + 0.4, fy + 0.3, self.WH), st, 0.02)
            box('bellows', c, (fx + 0.85, fy - 0.3, 0.4), (fx + 1.3, fy + 0.3, 0.7), M['beam'], 0.05)
            ax, ay = x0 + 2.4, y0 + 1.6
            box('stump', c, (ax - 0.3, ay - 0.3, 0), (ax + 0.3, ay + 0.3, 0.55), M['trimy'], 0.04)
            box('anvil', c, (ax - 0.42, ay - 0.16, 0.55), (ax + 0.42, ay + 0.16, 0.85), iron, 0.03)
            box('horn', c, (ax + 0.42, ay - 0.08, 0.7), (ax + 0.7, ay + 0.08, 0.83), iron, 0.03)
            box('hammer', c, (ax - 0.2, ay - 0.03, 0.85), (ax + 0.25, ay + 0.03, 0.89), M['beam'])
            barrel(x1 - 0.5, y0 + 0.6, 0.35, 0.7)
            box('water', c, (x1 - 0.8, y0 + 0.3, 0.66), (x1 - 0.2, y0 + 0.9, 0.68), mat_flat('Water', (0.05, 0.1, 0.12), rough=0.1))
            rx = x1 - 1.6; ry = y1 - 0.15
            box('rack', c, (rx - 0.9, ry - 0.12, 0.2), (rx + 0.9, ry, 1.9), M['beam'])
            for i in range(5):
                bx = rx - 0.7 + i * 0.35; box('blade', c, (bx - 0.03, ry - 0.2, 0.5), (bx + 0.03, ry - 0.14, 1.75), mat_flat('Steel', (0.6, 0.62, 0.65), 0.9, 0.3))
                box('hilt', c, (bx - 0.1, ry - 0.21, 1.4), (bx + 0.1, ry - 0.13, 1.45), iron)
            box('shield', c, (x1 - 0.13, y0 + 1.6, 0.9), (x1 - 0.05, y0 + 2.4, 1.7), mat_flat('ShieldR', (0.45, 0.08, 0.06)))
        elif kind == 'tavern':
            box('counter', c, (x0 + 0.3, y1 - 1.3, 0), (x0 + 3.2, y1 - 0.8, 1.05), wood, 0.03)
            for i in range(4): barrel(x0 + 0.5 + i * 0.7, y1 - 0.35, 0.28, 0.8)
            for tx_, ty_ in ((x1 - 1.6, y0 + 1.2), (x1 - 1.6, y0 + 2.9), (x0 + 1.4, y0 + 1.3)):
                table(tx_, ty_, 1.3, 0.8)
                for dy in (-0.6, 0.6): box('bench', c, (tx_ - 0.6, ty_ + dy - 0.12, 0.42), (tx_ + 0.6, ty_ + dy + 0.12, 0.48), wood, 0.02)
                box('mug', c, (tx_ - 0.1, ty_ - 0.06, 0.78), (tx_ + 0.02, ty_ + 0.06, 0.92), M['trimy'])
            box('hearth', c, (x1 - 0.7, y1 - 1.0, 0), (x1 - 0.15, y1 - 0.1, 1.2), st, 0.03)
            box('fire', c, (x1 - 0.6, y1 - 0.9, 0.1), (x1 - 0.25, y1 - 0.2, 0.35), glow)
        elif kind == 'bank':
            box('counter', c, (x0 + 0.3, y0 + 2.0, 0), (x1 - 0.3, y0 + 2.4, 1.1), st, 0.03)
            box('grille', c, (x0 + 0.3, y0 + 2.15, 1.1), (x1 - 0.3, y0 + 2.25, 1.8), iron)
            for i in range(3): box('chest', c, (x0 + 0.5 + i * 1.1, y1 - 0.7, 0), (x0 + 1.3 + i * 1.1, y1 - 0.2, 0.55), wood, 0.03)
            box('vault', c, (x1 - 1.2, y1 - 0.16, 0), (x1 - 0.3, y1 - 0.05, 1.9), iron, 0.02)
        elif kind == 'mage':
            shelf((x0 + x1) / 2, y1 - 0.2, x1 - x0 - 0.4, ((0.3, 0.1, 0.4), (0.1, 0.2, 0.45), (0.5, 0.35, 0.15)))
            table((x0 + x1) / 2, y0 + 1.0, 1.0, 0.7)
            orb = mat_flat('Orb', (0.3, 0.5, 1)); orb.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.3, 0.5, 1, 1)
            orb.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 4
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=((x0 + x1) / 2, y0 + 1.0, 0.94)); o = bpy.context.active_object
            for cc in o.users_collection: cc.objects.unlink(o)
            c.objects.link(o); o.data.materials.append(orb)
        elif kind == 'shop':
            box('counter', c, (x0 + 0.3, y0 + 1.4, 0), (x1 - 0.3, y0 + 1.8, 1.0), wood, 0.03)
            shelf((x0 + x1) / 2, y1 - 0.2, x1 - x0 - 0.5)
            barrel(x1 - 0.4, y0 + 0.5, 0.25, 0.7); barrel(x0 + 0.4, y0 + 0.5, 0.25, 0.7)

    def wall(self, coll, low, axis, pos, a, b, holes, M):
        T, WH, kind = self.T, self.WH, self.s['wall']
        mat = M['wall' + axis]
        if kind == 'log':
            CH, z, n = 0.244, (0.0 if axis == 'x' else 0.122), 0
            if z > 0:
                for p, q in segs(a, b, holes, 0, z):
                    lo, hi = ((p, pos - T / 2, 0), (q, pos + T / 2, z)) if axis == 'x' else ((pos - T / 2, p, 0), (pos + T / 2, q, z))
                    box(f'log{n}', coll, lo, hi, mat, 0.035, low); n += 1
            while z < WH - 1e-4:
                z1 = min(z + CH, WH); jit = random.uniform(-0.03, 0.03)
                for p, q in segs(a - 0.17 + jit, b + 0.17 - jit, holes, z, z1):
                    t = T * random.uniform(0.92, 1.05)
                    lo, hi = ((p, pos - t / 2, z), (q, pos + t / 2, z1)) if axis == 'x' else ((pos - t / 2, p, z), (pos + t / 2, q, z1))
                    box(f'log{n}', coll, lo, hi, mat, 0.06, low); n += 1
                z = z1
            return
        # parede maciça: colunas entre as bordas dos vãos, cada coluna com os intervalos de altura livres
        cuts = sorted({a, b, *[x for h in holes for x in h[:2] if a < x < b]})
        for k in range(len(cuts) - 1):
            p, q = cuts[k], cuts[k + 1]; m = (p + q) / 2
            zs = [(0.0, WH)]
            for h0, h1, z0, z1 in holes:
                if h0 <= m <= h1:
                    nz = []
                    for u, v in zs:
                        if v <= z0 or u >= z1: nz.append((u, v)); continue
                        if u < z0: nz.append((u, z0))
                        if v > z1: nz.append((z1, v))
                    zs = nz
            for u, v in zs:
                lo, hi = ((p, pos - T / 2, u), (q, pos + T / 2, v)) if axis == 'x' else ((pos - T / 2, p, u), (pos + T / 2, q, v))
                box(f'w{axis}{k}', coll, lo, hi, mat, 0.01, low)
        # rodapé de pedra mais escura nas casas de pedra/adobe
        if kind in ('stone', 'adobe'):
            lo, hi = ((a, pos - T / 2 - 0.04, 0), (b, pos + T / 2 + 0.04, 0.22)) if axis == 'x' else ((pos - T / 2 - 0.04, a, 0), (pos + T / 2 + 0.04, b, 0.22))
            for p, q in segs(lo[0] if axis == 'x' else lo[1], hi[0] if axis == 'x' else hi[1], [h for h in holes if h[2] < 0.1], 0, 0.22):
                l2, h2 = ((p, lo[1], 0), (q, hi[1], 0.22)) if axis == 'x' else ((lo[0], p, 0), (hi[0], q, 0.22))
                box('plinth', coll, l2, h2, M['stone'] if kind == 'stone' else M['wall' + axis], 0.02, low)

    def frame(self, coll, low, axis, pos, h0, h1, z0, z1, M, sill=False):
        T, tw = self.T, 0.09; tm = M['trimx'] if axis == 'x' else M['trimy']
        if axis == 'x':
            box('fL', coll, (h0 - tw, pos - T / 2 - 0.03, z0), (h0, pos + T / 2 + 0.03, z1 + tw), tm, 0.012, low)
            box('fR', coll, (h1, pos - T / 2 - 0.03, z0), (h1 + tw, pos + T / 2 + 0.03, z1 + tw), tm, 0.012, low)
            box('fT', coll, (h0 - tw - 0.05, pos - T / 2 - 0.04, z1), (h1 + tw + 0.05, pos + T / 2 + 0.04, z1 + tw + 0.02), tm, 0.012)
            if sill: box('fB', coll, (h0 - tw, pos - T / 2 - 0.07, z0 - 0.07), (h1 + tw, pos + T / 2 + 0.03, z0), tm, 0.012)
        else:
            box('fL', coll, (pos - T / 2 - 0.03, h0 - tw, z0), (pos + T / 2 + 0.03, h0, z1 + tw), tm, 0.012, low)
            box('fR', coll, (pos - T / 2 - 0.03, h1, z0), (pos + T / 2 + 0.03, h1 + tw, z1 + tw), tm, 0.012, low)
            box('fT', coll, (pos - T / 2 - 0.04, h0 - tw - 0.05, z1), (pos + T / 2 + 0.04, h1 + tw + 0.05, z1 + tw + 0.02), tm, 0.012)
            if sill: box('fB', coll, (pos - T / 2 - 0.03, h0 - tw, z0 - 0.07), (pos + T / 2 + 0.07, h1 + tw, z0), tm, 0.012)

    def window(self, coll, axis, pos, h0, h1, z0, z1, M):
        T = self.T
        self.frame(coll, None, axis, pos, h0, h1, z0, z1, M, sill=True)
        if axis == 'x':
            box('wD', coll, (h0, pos + 0.02, z0), (h1, pos + T / 2, z1), M['dark'])
            box('wBar', coll, ((h0 + h1) / 2 - 0.02, pos - 0.02, z0), ((h0 + h1) / 2 + 0.02, pos + 0.02, z1), M['trimx'])
            if self.s['wall'] in ('timber', 'log'):
                box('shut', coll, (h0 - 0.42, pos - T / 2 - 0.07, z0), (h0 - 0.1, pos - T / 2 - 0.03, z1), M['trimx'], 0.01)
        else:
            box('wD', coll, (pos - T / 2, h0, z0), (pos - 0.02, h1, z1), M['dark'])
            box('wBar', coll, (pos - 0.02, (h0 + h1) / 2 - 0.02, z0), (pos + 0.02, (h0 + h1) / 2 + 0.02, z1), M['trimy'])

    def doors(self, C, M):
        d0, d1, _, dz = self.door; S = self.S
        box('thr', C['FRONT'], (d0 - 0.05, S - self.T / 2 - 0.06, 0), (d1 + 0.05, S + self.T / 2, 0.06), M['trimx'], 0.01, C['FRONT_LOW'])

        for coll, ang in ((C['DOOR_CLOSED'], 0), (C['DOOR_OPEN'], -80)):
            parts = []
            n = 4
            for i in range(n):
                x0 = d0 + 0.02 + i * (d1 - d0 - 0.04) / n
                parts.append(box('db', coll, (x0, S - 0.03, 0.04), (x0 + (d1 - d0 - 0.04) / n - 0.006, S + 0.03, dz - 0.02), M['trimx'], 0.01))
            for zz in (0.3, 1.3): parts.append(box('ds', coll, (d0 + 0.05, S - 0.07, zz), (d1 - 0.05, S - 0.03, zz + 0.07), M['iron']))
            parts.append(box('dr', coll, (d1 - 0.2, S - 0.09, 0.82), (d1 - 0.14, S - 0.03, 0.9), M['iron']))
            if ang:
                bpy.context.view_layer.update()   # sem isso matrix_world ainda é a identidade
                piv = Vector((d0 + 0.02, S, 0)); R = Matrix.Rotation(math.radians(ang), 4, 'Z')
                for o in parts:
                    if o: o.matrix_world = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv) @ o.matrix_world

    def timber(self, C, M, holesS, holesE):
        """enxaimel: vigas escuras por fora das paredes da frente (e do fundo, por dentro não precisa)"""
        WH, T = self.WH, self.T
        for axis, pos, a, b, holes, out in (('x', self.S, self.Wx - T / 2, self.E + T / 2, holesS, -1), ('y', self.E, self.S, self.N, holesE, 1),
                                            ('x', self.N, self.Wx - T / 2, self.E + T / 2, [], 1), ('y', self.Wx, self.S, self.N, [], -1)):
            coll = C['FRONT'] if (axis, out) in (('x', -1), ('y', 1)) else C['BACK']
            low = C['FRONT_LOW'] if coll == C['FRONT'] else None
            face = pos + out * (T / 2 + 0.015)

            def bb(name, p, q, z0, z1):
                if axis == 'x': box(name, coll, (p, face - 0.03, z0), (q, face + 0.03, z1), M['beam'], 0.01, low)
                else: box(name, coll, (face - 0.03, p, z0), (face + 0.03, q, z1), M['beam'], 0.01, low)
            for z0 in (0.0, 1.05, WH - 0.12):
                for p, q in segs(a, b, holes, z0, z0 + 0.12): bb('tH', p, q, z0, z0 + 0.12)
            x = a
            while x <= b + 1e-3:
                for p, q in segs(x - 0.06, x + 0.06, holes, 0, WH):
                    for u, v in ((0, 1.05), (1.17, WH - 0.12)):
                        if not any(h0 - 0.06 < (p + q) / 2 < h1 + 0.06 and not (v <= hz0 or u >= hz1) for h0, h1, hz0, hz1 in holes): bb('tV', p, q, u, v)
                x += 1.0

    def gable_roof(self, C, M):
        T, WH = self.T, self.WH
        ym = self.h / 2; slope = self.s.get('slope') or (0.62 if self.s['roof'] != 'thatch' else 0.75)
        run = ym - (self.S - T / 2); rz = WH + run * slope; self.ridge_z = rz
        ov = 0.45; x0, x1 = -ov + 0.1, self.w + ov - 0.1
        for name, ya, yb in (('rS', ym, self.S - T / 2 - ov), ('rN', ym, self.N + T / 2 + ov)):
            za = rz + 0.05; zb = WH - ov * slope
            bm = bmesh.new()
            vs = [bm.verts.new(v) for v in ((x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb))]
            bm.faces.new(vs); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
            for pl in me.polygons: pl.use_smooth = True
            o = bpy.data.objects.new(name, me); C['ROOF'].objects.link(o); me.materials.append(M['roof'])
            sub = o.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = 5; sub.render_levels = 5
            tx = bpy.data.textures.new(name + 'n', 'CLOUDS'); tx.noise_scale = 0.35
            dp = o.modifiers.new('disp', 'DISPLACE'); dp.texture = tx; dp.strength = 0.05 if self.s['roof'] in ('thatch', 'snow') else 0.015
            so = o.modifiers.new('sol', 'SOLIDIFY'); so.thickness = 0.22 if self.s['roof'] in ('thatch', 'snow') else 0.12; so.offset = 1.0
            # vedação embaixo do telhado para não vazar luz
            bm = bmesh.new(); vs = [bm.verts.new((v.co.x, v.co.y, v.co.z - 0.03)) for v in me.vertices[:4]] if False else None
        cap = box('ridge', C['ROOF'], (x0, ym - 0.12, rz - 0.02), (x1, ym + 0.12, rz + 0.16), M['roof'], 0.05)
        # empenas (triângulos) no material da parede: oeste no fundo, leste na frente
        for coll, x in ((C['BACK'], self.Wx), (C['FRONT'], self.E)):
            bm = bmesh.new(); y0, y1 = self.S - T / 2, self.N + T / 2
            prof = [(y0, WH - 0.01), (y1, WH - 0.01), (ym, rz)]
            A = [bm.verts.new((x - T / 2, y, z)) for y, z in prof]; B = [bm.verts.new((x + T / 2, y, z)) for y, z in prof]
            bm.faces.new(A); bm.faces.new(B[::-1])
            for i in range(3): bm.faces.new((A[i], A[(i + 1) % 3], B[(i + 1) % 3], B[i]))
            me = bpy.data.meshes.new('gable'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('gable', me); coll.objects.link(o)
            me.materials.append(M['wally'] if self.s['wall'] != 'timber' else M['wally'])

    def flat_roof(self, C, M):
        T, WH = self.T, self.WH; self.ridge_z = WH + 0.5
        x0, x1, y0, y1 = self.Wx - T / 2, self.E + T / 2, self.S - T / 2, self.N + T / 2
        box('slab', C['ROOF'], (x0, y0, WH), (x1, y1, WH + 0.16), M['wallx'], 0.02)
        for lo, hi, m in (((x0, y0, WH + 0.16), (x1, y0 + 0.22, WH + 0.5), M['wallx']), ((x0, y1 - 0.22, WH + 0.16), (x1, y1, WH + 0.5), M['wallx']),
                          ((x0, y0, WH + 0.16), (x0 + 0.22, y1, WH + 0.5), M['wally']), ((x1 - 0.22, y0, WH + 0.16), (x1, y1, WH + 0.5), M['wally'])):
            box('parapet', C['ROOF'], lo, hi, m, 0.03)
            if self.s.get('merlons'):
                ax = 0 if hi[0] - lo[0] > hi[1] - lo[1] else 1; L0, L1 = lo[ax], hi[ax]; k = L0
                while k < L1 - 0.2:
                    l2, h2 = list(lo), list(hi); l2[ax], h2[ax] = k, min(k + 0.35, L1); l2[2], h2[2] = WH + 0.5, WH + 0.85
                    box('merlon', C['ROOF'], l2, h2, m, 0.02); k += 0.7
        # vigas de palmeira saindo da parede da frente, logo abaixo do teto
        x = x0 + 0.5 if self.s['wall'] == 'adobe' else x1
        while x < x1 - 0.3:
            box('viga', C['FRONT'], (x - 0.06, y0 - 0.32, WH - 0.24), (x + 0.06, y0 + 0.1, WH - 0.12), M['beam'], 0.02); x += 0.85
        y = y0 + 0.5 if self.s['wall'] == 'adobe' else y1
        while y < y1 - 0.3:
            box('viga', C['FRONT'], (x1 - 0.1, y - 0.06, WH - 0.24), (x1 + 0.32, y + 0.06, WH - 0.12), M['beam'], 0.02); y += 0.85
        if self.s['wall'] == 'adobe':   # esteira no terraço
            box('mat', C['ROOF'], (x0 + 0.5, y0 + 0.5, WH + 0.16), (x0 + 1.6, y0 + 1.3, WH + 0.19), M['cloth'])
        if self.s.get('merlons'):        # torreões nos cantos
            for cx, cy in ((x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x0 + 0.5, y1 - 0.5), (x1 - 0.5, y1 - 0.5)):
                box('turret', C['ROOF'], (cx - 0.75, cy - 0.75, WH), (cx + 0.75, cy + 0.75, WH + 1.5), M['wallx'], 0.03)
                for ddx, ddy in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6), (0, -0.6), (0, 0.6), (-0.6, 0), (0.6, 0)):
                    box('tm', C['ROOF'], (cx + ddx - 0.15, cy + ddy - 0.15, WH + 1.5), (cx + ddx + 0.15, cy + ddy + 0.15, WH + 1.85), M['wallx'], 0.02)
            box('flagpole', C['ROOF'], (x1 - 0.55, y1 - 0.55, WH + 1.5), (x1 - 0.45, y1 - 0.45, WH + 3.6), M['beam'])
            box('flag', C['ROOF'], (x1 - 0.45, y1 - 0.52, WH + 2.8), (x1 + 0.6, y1 - 0.48, WH + 3.5), mat_noise('Flag', (0.35, 0.04, 0.04), (0.6, 0.1, 0.08), 6, 0.05))

    def meta(self):
        w, h = self.w, self.h
        walls = [[i, j] for j in range(h) for i in range(w) if i in (0, w - 1) or j in (0, h - 1)]
        door = [self.s['door'], h - 1]
        props = [[1, 1, 'bed_r0'], [w - 2, 1, 'chest_r2']]
        if w >= 6 and h >= 5: props.append([w // 2, h // 2, 'table_r1'])
        return {'version': 2, 'id': self.id, 'size': [w, h], 'walls': [x for x in walls if x != door], 'doors': [door],
                'props': props, 'interior': [[1, 1], [w - 2, h - 2]], 'biome': self.s['biome']}


def setup_render(s, w, h):
    def sun(name, energy, color, rot):
        l = bpy.data.lights.new(name, 'SUN'); l.energy = energy; l.color = color; l.angle = math.radians(3)
        o = bpy.data.objects.new(name, l); s.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
    sun('key', 3.2, (1.0, 0.93, 0.84), (40, 0, -150)); sun('fill', 0.6, (0.82, 0.86, 0.95), (60, 0, 40))
    wd = bpy.data.worlds.new('W'); s.world = wd; wd.use_nodes = True; nt = wd.node_tree; nt.nodes.clear()
    bg = nt.nodes.new('ShaderNodeBackground'); out = nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs[0].default_value = (0.55, 0.58, 0.62, 1); bg.inputs[1].default_value = 0.22
    W = int((w + h) * 96 + 360); H = int((w + h) * 48 + 900)
    TILE00 = Vector((0.5, h - 0.5, 0))
    # centro da planta no meio da imagem, um pouco abaixo (o telhado sobe)
    ci, cj = w / 2 - 0.5, h / 2 - 0.5
    cx, cy = W / 2, H - (w + h) * 48 / 2 - 160
    ANCHOR = [round(cx - (ci - cj) * 96), round(cy - (ci + cj) * 48)]
    cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Camera', cd); s.collection.objects.link(cam); s.camera = cam
    cd.type = 'ORTHO'; cd.sensor_fit = 'HORIZONTAL'; cd.ortho_scale = W / (192 / math.sqrt(2))
    cam.rotation_euler = (math.radians(60), 0, math.radians(45)); cam.location = (12 + w / 2, -12 + h / 2, 12)
    s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.render.threads_mode = 'AUTO'
    s.render.resolution_x = W; s.render.resolution_y = H; s.render.film_transparent = True
    s.cycles.samples = SAMP; s.cycles.use_denoising = True; s.cycles.max_bounces = 4
    s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'; s.view_settings.exposure = -0.2
    bpy.context.view_layer.update()
    p0 = world_to_camera_view(s, cam, TILE00); cd.shift_x = 1; bpy.context.view_layer.update(); px = world_to_camera_view(s, cam, TILE00)
    cd.shift_x = 0; cd.shift_y = 1; bpy.context.view_layer.update(); py = world_to_camera_view(s, cam, TILE00)
    cd.shift_x = (ANCHOR[0] / W - p0.x) / (px.x - p0.x); cd.shift_y = ((1 - ANCHOR[1] / H) - p0.y) / (py.y - p0.y)
    return ANCHOR


def render_pieces():
    """peças de muralha de 1 tile (vão para o atlas do mapa como objetos): reta ao longo de i, reta ao longo de j, torre"""
    out = os.path.join(ROOT, 'art', 'buildings', 'city', 'pieces'); os.makedirs(out, exist_ok=True)
    meta = {}
    for mat in ('stone', 'adobe'):
        for piece in ('wall_x', 'wall_y', 'tower'):
            s = new_scene(); coll = bpy.data.collections.new('P'); s.collection.children.link(coll)
            M = materials({'wall': mat, 'roof': 'flat'}); m = M['wallx']; H = 3.3
            def merl(x0, x1, y0, y1, z):
                box('m', coll, (x0, y0, z), (x1, y1, z + 0.38), m, 0.02)
            if piece == 'wall_x':
                box('w', coll, (-0.01, 0.15, 0), (1.01, 0.85, H), m, 0.01)
                box('pl', coll, (-0.01, 0.1, 0), (1.01, 0.9, 0.3), M['stone'] if mat == 'stone' else m, 0.02)
                for x in (0.05, 0.55): merl(x, x + 0.32, 0.15, 0.33, H); merl(x, x + 0.32, 0.67, 0.85, H)
            elif piece == 'wall_y':
                box('w', coll, (0.15, -0.01, 0), (0.85, 1.01, H), m, 0.01)
                box('pl', coll, (0.1, -0.01, 0), (0.9, 1.01, 0.3), M['stone'] if mat == 'stone' else m, 0.02)
                for y in (0.05, 0.55): merl(0.15, 0.33, y, y + 0.32, H); merl(0.67, 0.85, y, y + 0.32, H)
            else:
                T = 4.4
                box('t', coll, (-0.2, -0.2, 0), (1.2, 1.2, T), m, 0.02)
                box('tc', coll, (-0.28, -0.28, T - 0.25), (1.28, 1.28, T), m, 0.02)
                for k in range(4):
                    a = -0.28 + k * 0.43
                    merl(a, a + 0.26, -0.28, -0.1, T); merl(a, a + 0.26, 1.1, 1.28, T); merl(-0.28, -0.1, a, a + 0.26, T); merl(1.1, 1.28, a, a + 0.26, T)
                box('slit', coll, (0.45, -0.21, 2.2), (0.55, -0.19, 2.9), M['dark']); box('slit2', coll, (1.19, 0.45, 2.2), (1.21, 0.55, 2.9), M['dark'])
            anchor = setup_render(s, 1, 1)
            f = f'{mat}_{piece}.png'; s.render.filepath = os.path.join(out, f); bpy.ops.render.render(write_still=True)
            meta[f'{mat}_{piece}'] = {'file': f, 'anchor': anchor}
            print('PIECE', mat, piece, flush=True)
    json.dump(meta, open(os.path.join(out, 'pieces.json'), 'w'), indent=1)


def main():
    if ONLY == ['pieces']: return render_pieces()
    for hid, spec in HOUSES.items():
        if ONLY and hid not in ONLY: continue
        s = new_scene()
        LAYERS = ['BACK', 'FRONT', 'FRONT_LOW', 'ROOF', 'DOOR_CLOSED', 'DOOR_OPEN']
        C = {}
        for n in LAYERS:
            c = bpy.data.collections.new(n); s.collection.children.link(c); C[n] = c
        hs = House(hid, spec); M = materials(spec); hs.build(C, M)
        anchor = setup_render(s, hs.w, hs.h)
        out = os.path.join(ROOT, 'art', 'buildings', spec['biome'], hid); os.makedirs(os.path.join(out, 'props'), exist_ok=True)
        for f in os.listdir(PROPS_SRC): shutil.copy(os.path.join(PROPS_SRC, f), os.path.join(out, 'props', f))
        names = {'back': 'BACK', 'front': 'FRONT', 'front_low': 'FRONT_LOW', 'roof': 'ROOF', 'door_closed': 'DOOR_CLOSED', 'door_open': 'DOOR_OPEN'}
        for name, cn in names.items():
            if os.environ.get('LAYERS') and name not in os.environ['LAYERS'].split(','): continue
            for n in LAYERS: C[n].hide_render = (n != cn)
            s.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True); print('RENDER', hid, name, flush=True)
        meta = hs.meta(); meta['anchor'] = anchor; meta['layers'] = {k: k + '.png' for k in names}
        json.dump(meta, open(os.path.join(out, 'house.json'), 'w'), indent=1)
        if os.environ.get('PREVIEW'):
            for n in LAYERS: C[n].hide_render = n not in ('BACK', 'FRONT', 'ROOF', 'DOOR_CLOSED')
            s.render.filepath = os.path.join('/tmp/t', hid + '_prev.png'); bpy.ops.render.render(write_still=True)
        print('OK', hid, flush=True)


main()
