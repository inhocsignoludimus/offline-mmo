#!/usr/bin/env python3
"""Regressão do check_house.

    python3 build/test_check_house.py

O rodapé (front_low) mede-se por coluna, acima da linha da fachada.
A fórmula antiga (topo do desenho contra a quina sul) soma a subida
isométrica da planta e rejeita um rodapé de 20% numa frente larga.
"""
import os, sys, json, tempfile, unittest
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_house as ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _line_y(p, q, x):
    t = (x - p[0]) / (q[0] - p[0])
    return p[1] + t * (q[1] - p[1])


def _facades(ax, ay, w, dpt):
    c = ch._corners(ax, ay, w, dpt)
    return (('sul', c['oeste'], c['sul']), ('leste', c['leste'], c['sul']))


def paint_walls(front, low, anchor, size, height, frac, inset=0, gable_east=False,
                south_only_low=False, east_frac=None):
    ax, ay = anchor
    w, dpt = size
    df, dl = ImageDraw.Draw(front), ImageDraw.Draw(low)
    for name, p, q in _facades(ax, ay, w, dpt):
        x0, x1 = int(min(p[0], q[0])), int(max(p[0], q[0]))
        span = max(1, (x1 - x0) / 2)
        mid = (x0 + x1) / 2
        use = frac if name == 'sul' or east_frac is None else east_frac
        for x in range(x0, x1 + 1):
            yg = _line_y(p, q, x)
            hgt = height
            if gable_east and name == 'leste':
                t = 1 - abs(x - mid) / span
                hgt = height + int(max(0, t) * 180)
            y_base = int(yg - inset)
            df.line([(x, int(yg - inset - hgt)), (x, y_base)], fill=(200, 160, 120, 255))
            if south_only_low and name != 'sul':
                continue
            dl.line([(x, int(yg - inset - height * use)), (x, y_base)], fill=(180, 140, 100, 255))


def paint_back(back, anchor, size):
    ax, ay = anchor
    w, dpt = size
    d = ImageDraw.Draw(back)
    for j in range(dpt):
        for i in range(w):
            cx, cy = ch.tile_center(ax, ay, i, j)
            d.polygon(ch.diamond(cx, cy), fill=(120, 90, 60, 255))


def paint_door(door, x, y0, y1):
    ImageDraw.Draw(door).line([(x, y0), (x, y1)], fill=(90, 60, 40, 255))


def legacy_south_corner_ratio(front, low, anchor, size):
    """A fórmula antiga: (quina sul − topo global) da low sobre o da front."""
    ax, ay = anchor
    w, dpt = size
    floor_y = ch.tile_center(ax, ay, w - 1, dpt - 1)[1] + ch.TH // 2

    def above(im):
        bb = im.split()[3].point(lambda v: 255 if v > 32 else 0).getbbox()
        return floor_y - bb[1]

    return above(low) / above(front)


class SillGeometry(unittest.TestCase):
    def setUp(self):
        self.anchor = (500, 450)
        self.size = (5, 4)
        self.wh = (1600, 1400)

    def _pair(self, **kw):
        front = Image.new('RGBA', self.wh, (0, 0, 0, 0))
        low = Image.new('RGBA', self.wh, (0, 0, 0, 0))
        paint_walls(front, low, self.anchor, self.size, 300, kw.pop('frac'), **kw)
        return front, low

    def _ratio(self, frac, **kw):
        front, low = self._pair(frac=frac, **kw)
        st = ch.facade_sill(front, low, self.anchor, self.size)
        return st

    def test_twenty_percent_reads_about_twenty(self):
        st = self._ratio(0.20)
        self.assertAlmostEqual(st['sul']['med_ratio'], 0.20, delta=0.03)
        self.assertAlmostEqual(st['leste']['med_ratio'], 0.20, delta=0.03)
        self.assertEqual(ch.sill_problems(st), [])

    def test_thirty_percent_passes(self):
        self.assertEqual(ch.sill_problems(self._ratio(0.30)), [])

    def test_forty_five_percent_fails(self):
        probs = ch.sill_problems(self._ratio(0.45))
        self.assertTrue(any('alta demais' in p and 'sul' in p for p in probs))

    def test_fifty_five_percent_fails_both_facades(self):
        probs = ch.sill_problems(self._ratio(0.55))
        self.assertTrue(any('alta demais' in p and 'sul' in p for p in probs))
        self.assertTrue(any('alta demais' in p and 'leste' in p for p in probs))

    def test_legacy_formula_false_fails_a_full_width_sill(self):
        front, low = self._pair(frac=0.20)
        old = legacy_south_corner_ratio(front, low, self.anchor, self.size)
        self.assertGreater(old, 0.45)
        self.assertEqual(ch.sill_problems(ch.facade_sill(front, low, self.anchor, self.size)), [])

    def test_stub_near_the_door_does_not_cover_the_facades(self):
        st = self._ratio(0.20, south_only_low=True)
        # o toco ainda cobre a sul inteira neste desenho; a leste fica sem rodapé
        probs = ch.sill_problems(st)
        self.assertTrue(any('não cobre' in p and 'leste' in p for p in probs))

    def test_partial_south_coverage_fails(self):
        front, low = self._pair(frac=0.20)
        # apaga o rodapé na metade oeste da fachada sul
        c = ch._corners(*self.anchor, *self.size)
        x_cut = int((c['oeste'][0] + c['sul'][0]) / 2)
        px = low.load()
        w, h = low.size
        for y in range(h):
            for x in range(x_cut):
                px[x, y] = (0, 0, 0, 0)
        st = ch.facade_sill(front, low, self.anchor, self.size)
        self.assertLess(st['sul']['cov'], ch.SILL_MIN_COVER)
        self.assertTrue(any('não cobre' in p and 'sul' in p for p in ch.sill_problems(st)))

    def test_gable_does_not_hide_a_tall_sill(self):
        st = self._ratio(0.55, gable_east=True)
        self.assertTrue(any('alta demais' in p and 'sul' in p for p in ch.sill_problems(st)))

    def test_gable_with_a_low_sill_passes(self):
        self.assertEqual(ch.sill_problems(self._ratio(0.20, gable_east=True)), [])

    def test_porch_below_the_facade_does_not_inflate_the_ratio(self):
        front, low = self._pair(frac=0.20)
        # deque 70 px ao sul da linha da fachada, nas duas camadas
        c = ch._corners(*self.anchor, *self.size)
        p, q = c['oeste'], c['sul']
        df, dl = ImageDraw.Draw(front), ImageDraw.Draw(low)
        for x in range(int(p[0]), int(q[0]) + 1):
            yg = _line_y(p, q, x)
            df.line([(x, int(yg)), (x, int(yg + 70))], fill=(140, 110, 80, 255))
            dl.line([(x, int(yg)), (x, int(yg + 70))], fill=(140, 110, 80, 255))
        st = ch.facade_sill(front, low, self.anchor, self.size)
        self.assertAlmostEqual(st['sul']['med_ratio'], 0.20, delta=0.04)
        self.assertEqual(ch.sill_problems(st), [])

    def test_inset_log_face_twenty_percent_passes_and_forty_fails(self):
        # a face do tronco fica 27 px para dentro da linha da planta
        ok = ch.sill_problems(self._ratio(0.20, inset=27))
        bad = ch.sill_problems(self._ratio(0.40, inset=27))
        self.assertEqual(ok, [])
        self.assertTrue(any('alta demais' in p for p in bad))


class WholeHouse(unittest.TestCase):
    def _house(self, dest, frac=0.22, anchor=(500, 450), size=(5, 4), wh=(1600, 1400),
               door_h=200, back='foot', stray=False, clip=False):
        os.makedirs(dest, exist_ok=True)
        layers = {}
        for name in ('back', 'front', 'front_low', 'roof', 'door_closed', 'door_open'):
            layers[name] = Image.new('RGBA', wh, (0, 0, 0, 0))
        paint_walls(layers['front'], layers['front_low'], anchor, size, 300, frac)
        if back == 'foot':
            paint_back(layers['back'], anchor, size)
        elif back == 'mismatch':
            ImageDraw.Draw(layers['back']).rectangle([40, 40, 80, 80], fill=(120, 90, 60, 255))
        # telhado acima da planta, longe da borda
        ImageDraw.Draw(layers['roof']).rectangle([anchor[0] - 40, 80, anchor[0] + 80, 160], fill=(90, 50, 40, 255))
        c = ch._corners(*anchor, *size)
        door_x = int((c['oeste'][0] + c['sul'][0]) / 2)
        door_y1 = int(c['sul'][1]) - 30
        paint_door(layers['door_closed'], door_x, door_y1 - door_h, door_y1)
        paint_door(layers['door_open'], door_x + 30, door_y1 - door_h, door_y1)
        if stray:
            ImageDraw.Draw(layers['front']).rectangle([20, wh[1] - 40, 40, wh[1] - 20], fill=(255, 0, 0, 255))
        if clip:
            ImageDraw.Draw(layers['roof']).point((0, 80), fill=(255, 0, 0, 255))
            ImageDraw.Draw(layers['roof']).point((1, 80), fill=(255, 0, 0, 255))
        for name, im in layers.items():
            im.save(os.path.join(dest, name + '.png'))
        house = {
            'version': 2, 'id': 'synth', 'size': list(size), 'anchor': list(anchor),
            'layers': {k: k + '.png' for k in layers},
            'walls': [], 'doors': [[1, size[1] - 1]], 'props': [], 'interior': [[1, 1], [2, 2]],
        }
        with open(os.path.join(dest, 'house.json'), 'w', encoding='utf-8') as f:
            json.dump(house, f)
        return dest

    def _probs(self, **kw):
        with tempfile.TemporaryDirectory() as d:
            self._house(d, **kw)
            probs, info, _, _ = ch.evaluate(d)
        return probs

    def test_good_house_passes(self):
        self.assertEqual(self._probs(), [])

    def test_tall_sill_fails(self):
        probs = self._probs(frac=0.55)
        self.assertTrue(any('alta demais' in p for p in probs))

    def test_short_door_fails(self):
        probs = self._probs(door_h=80)
        self.assertTrue(any('porta menor' in p for p in probs))

    def test_stray_pixels_fail(self):
        probs = self._probs(stray=True)
        self.assertTrue(any('fora da planta' in p for p in probs))

    def test_clipping_fails(self):
        probs = self._probs(clip=True)
        self.assertTrue(any('encosta na borda' in p for p in probs))

    def test_footprint_mismatch_fails(self):
        probs = self._probs(back='mismatch')
        self.assertTrue(any('não bate com a planta' in p for p in probs))

    def test_anchor_outside_fails(self):
        probs = self._probs(anchor=(40, 40), wh=(1600, 1400))
        self.assertTrue(any('quina' in p and 'fora da imagem' in p for p in probs))

    def test_missing_layer_fails(self):
        with tempfile.TemporaryDirectory() as d:
            self._house(d)
            h = json.load(open(os.path.join(d, 'house.json'), encoding='utf-8'))
            del h['layers']['front_low']
            json.dump(h, open(os.path.join(d, 'house.json'), 'w', encoding='utf-8'))
            os.remove(os.path.join(d, 'front_low.png'))
            probs, _, _, _ = ch.evaluate(d)
        self.assertTrue(any('falta a camada front_low' in p for p in probs))


class DeliveredCabins(unittest.TestCase):
    def test_plains_cabin_01_and_02_pass(self):
        for rel in ('art/buildings/plains/plains_cabin_01',
                    'art/buildings/plains/plains_cabin_02'):
            folder = os.path.join(ROOT, rel)
            self.assertTrue(os.path.isdir(folder), folder)
            probs, info, _, _ = ch.evaluate(folder)
            self.assertEqual(probs, [], '\n'.join(info + probs))


if __name__ == '__main__':
    unittest.main()
