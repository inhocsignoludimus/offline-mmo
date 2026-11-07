from pathlib import Path
import json,hashlib
R=Path('/workspace/paperdoll_weapons_batch1');items=json.load(open('/workspace/offline-mmo/data/items/base.json'))['items'];P=Path('/workspace/offline-mmo-art/pr_ready/paperdoll_pr23_fix/art/paperdoll');chosen=['shortsword','dagger','hand_axe','mace','longbow','staff','wand','buckler'];out=[]
for it in items:
 if it['type'] not in ['weapon','shield']:continue
 iid=it['id'];present={s:[str(f.relative_to(P)) for f in (P/s).glob(iid+'*.png') if f.stem in [iid,iid+'_fixed']] for s in 'mf'}
 out.append({'id':iid,'type':it['type'],'slot':it.get('slot'),'sprite_layer':it.get('sprite_layer'),'phase1_exact_files':present,'status':'existing_exact_do_not_duplicate' if all(present.values()) else 'chosen_this_batch' if iid in chosen else 'missing_exact_NOT_in_this_batch'})
(R/'pkg/INVENTORY.json').write_text(json.dumps(out,indent=2))
roots=[P,Path('/workspace/wardrobe_batch2_delivery/v4'),Path('/workspace/armor_delivery_v3')]
preserve={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in root.rglob('*') if p.is_file()}
for n in chosen:
 p=Path('/workspace/flare-game/art_src/characters/hero')/(('iron_buckler' if n=='buckler' else n)+'.blend');preserve[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
p=Path('/workspace/offline-mmo/data/items/base.json');preserve[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'work/preservation.json').write_text(json.dumps(preserve,indent=1))
print('EXISTING EXACT',[o['id'] for o in out if o['status'].startswith('existing')]);print('CHOSEN',chosen);print('preservation files',len(preserve))
(R/'PROGRESS.md').write_text('2026-11-07 America/Sao_Paulo — Local weapon batch started. Eight missing exact IDs: '+', '.join(chosen)+'. Existing exact phase1 longsword/kite_shield/wooden_shield preserved. Static only; no body deformation, repo edit or publication.\n')
