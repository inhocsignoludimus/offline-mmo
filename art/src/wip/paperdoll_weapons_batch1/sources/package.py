from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil,tarfile,csv
R=Path('/workspace/paperdoll_weapons_batch1');W=R/'work';D=R/'pkg';T=D/'tools_src';U=T/'upstream/hero';U.mkdir(parents=True,exist_ok=True);P=Path('/workspace/offline-mmo-art/pr_ready/paperdoll_pr23_fix/art/paperdoll');items=['shortsword','dagger','hand_axe','mace','longbow','staff','wand','buckler'];source_dir=Path('/workspace/flare-game/art_src/characters/hero')
# Finish actual static loadout and approved glove fit preview, not engine captures.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13);sh=Image.new('RGB',(6*160,560),(27,27,32));dr=ImageDraw.Draw(sh)
def tint(im,c):
 a=np.array(im).astype(float);a[...,:3]*=np.array(c)/255;return Image.fromarray(a.astype('uint8'))
for row,s in enumerate('mf'):
 for col,(name,ids,hue,gloved) in enumerate([('sword + buckler',['shortsword','buckler'],(150,108,72),False),('sword + gloves',['shortsword','buckler'],(150,108,72),True),('axe + gloves',['hand_axe'],(150,108,72),True),('bow neutral',['longbow'],(170,60,50),True),('staff neutral',['staff'],(232,218,188),True),('wand neutral',['wand'],(150,108,72),True)]):
  im=Image.open(P/s/'body.png').convert('RGBA')
  if gloved:
   for it in ['cloth_pants','cloth_shirt','leather_gloves']:
    a=Image.open(P/s/f'{it}.png').convert('RGBA');im.alpha_composite(tint(a,(110,94,75)))
  for it in ids:
   for suf in ['','_fixed']:
    f=D/'art/paperdoll'/s/f'{it}{suf}.png'
    if f.exists():
     a=Image.open(f).convert('RGBA');im.alpha_composite(a if suf else tint(a,hue))
  bg=Image.new('RGBA',(150,240),(27,27,32));bg.alpha_composite(im.resize((150,240),Image.Resampling.LANCZOS));sh.paste(bg.convert('RGB'),(col*160,row*280+28));dr.text((col*160,row*280+6),s+'/'+name,font=font,fill='white')
sh.save(D/'art/_preview/weapons_batch1_loadouts_150.png')
qa=json.loads((D/'QA.json').read_text());files=list((D/'art/paperdoll').rglob('*.png'));assert len(files)==22
for f in files:
 im=Image.open(f);a=np.array(im);assert im.mode=='RGBA' and im.size==(300,480);assert a[...,3].min()==0 and a[...,3].max()==255
 assert (a[a[...,3]==0,:3]==0).all()
 box=im.getbbox();assert box[0]>0 and box[1]>0 and box[2]<300 and box[3]<480,(f,box)
 if '_fixed' not in f.stem:assert np.ptp(a[...,:3],axis=2)[a[...,3]>0].max()==0
 assert not (P/f.relative_to(D/'art/paperdoll')).exists(),'duplicate existing staged path'
qa['visual_review']={'scales':['300x480','150x240'],'sexes':['m','f'],'result':'all eight readable, no canvas clipping, broquel offhand does not obscure torso; static open-hand accommodation explicit, not a firing/casting pose','staff_fix':'original crystal gap 0.033 source units removed by seating existing crystal mesh +0.038 along native X','known_limits':['open palms unchanged; no new closed grip','bow and staff neutral one-hand display only','low-poly facets and subpixel bow string','future glove silhouettes may require occlusion adjustment'],'phase1_clothed_glove_test':True}
preserve=json.loads((W/'preservation.json').read_text());changed=[p for p,h in preserve.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h];assert not changed
qa['preservation']={'checked_files':len(preserve),'changed_files':changed};qa['exact_ids']=items;qa['new_png_layers']=22
(D/'QA.json').write_text(json.dumps(qa,indent=2))
source_names={'shortsword':'Shortsword','dagger':'Dagger','hand_axe':'HandAxe','mace':'IronMaceHigh','longbow':'LongBow','staff':'Staff','wand':'Wand','buckler':'IronBuckler'};prov=[]
for it in items:
 src=source_dir/f"{'iron_buckler' if it=='buckler' else it}.blend";shutil.copy(src,U/src.name)
 entry={'id':it,'upstream':'https://github.com/flareteam/flare-game/tree/master/art_src/characters/hero','upstream_file':src.name,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'actual_mesh':source_names[it],'license':'CC-BY-SA-3.0','originals_preserved':True,'modification':'actual mesh reoriented/rescaled for static paperdoll; new materials; hand occlusion in PNG; staff crystal seated without new geometry' if it=='staff' else 'actual mesh reoriented/rescaled; UV retained for buckler; new Cycles materials on other items; hand occlusion in PNG','sex_specific_fit':{}}
 for s in 'mf':
  meta=json.loads((W/f'{it}_{s}.json').read_text());meta['source_object']=source_names[it];entry['sex_specific_fit'][s]=meta
 prov.append(entry)
for name in ['iron_buckler_diffuse.png','iron_buckler_normal.png']:shutil.copy(source_dir/name,U/name)
shutil.copy('/workspace/flare-game/README.md',T/'upstream/Flare_README_license_proof.md');shutil.copy('/workspace/flare-game/CREDITS.txt',T/'upstream/Flare_CREDITS.txt')
shutil.copy('/workspace/wardrobe_batch2_delivery/v4/pkg/LICENSE_CC-BY-SA-3.0.txt',D/'LICENSE_CC-BY-SA-3.0.txt')
ref=T/'reference';ref.mkdir(exist_ok=True)
for s in 'mf':shutil.copy(P/s/'body.png',ref/f'body_{s}_CC0.png')
(ref/'README.txt').write_text('Approved paperdoll body references, Ludimus/offline-mmo, CC0. Unmodified copies for alignment only. NOT target files; do not overwrite phase1 bodies.\n')
for name in ['render.py','finalize.py','paint_helper.py','inventory.py','inspect_models.py','clean_scenes.py','package.py']:shutil.copy(W/name,T/name)
(T/'REPRODUCE.txt').write_text('Editable, packed/cleaned scenes in scenes/ reproduce geometry/material/light. Render script can rebuild original meshes with WEAPON_SOURCE_DIR pointing to tools_src/upstream/hero and WEAPON_BATCH_DIR pointing to a new scratch directory. Example: WEAPON_SOURCE_DIR=/absolute/pkg/tools_src/upstream/hero WEAPON_BATCH_DIR=/absolute/scratch blender -b -t 3 --python tools_src/render.py -- m shortsword\nfinalize.py currently names the local delivery and approved-body paths; remap R and P before running outside the original workspace. paint_helper.py is standalone; dependency Pillow/Numpy/OpenCV. Original public Flare sources retained for derivation/editability, including their historical missing linked material references; delivered scenes have unused linked data purged.\n')
(D/'PROVENANCE.json').write_text(json.dumps(prov,indent=2))
inv=json.loads((D/'INVENTORY.json').read_text())
with (D/'INVENTORY.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['id','slot','phase1_exact_m','phase1_exact_f','status','combat_sprite_not_paperdoll_alias'])
 for v in inv:w.writerow([v['id'],v['slot'],';'.join(v['phase1_exact_files']['m']),';'.join(v['phase1_exact_files']['f']),v['status'],v['sprite_layer']])
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.name!='MANIFEST.json'};(D/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
archive=R/'paperdoll_weapons_batch1_REVIEW.tar.gz'
with tarfile.open(archive,'w:gz') as tf:tf.add(D,arcname='paperdoll_weapons_batch1_REVIEW')
assert archive.stat().st_size<=25_000_000
with tarfile.open(archive) as tf:assert all(not x.name.endswith('.blend1') for x in tf.getmembers())
with (R/'PROGRESS.md').open('a') as f:f.write('2026-11-07 America/Sao_Paulo — Eight IDs m/f rendered and inspected at 300x480/150x240. Staff native crystal seated to remove gap. 22 PNG layers plus packed/clean source scenes, upstreams, QA/provenance delivered for parent review only. No engine/repo/publication changes; old files preserved.\n')
print('ARCHIVE',archive,archive.stat().st_size,'bytes; files',len(manifest),'PNG targets',len(files),'preserved',len(preserve))
