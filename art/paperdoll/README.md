Relatório da entrega da fase 1, guardado aqui (veio de `PAPERDOLL_REPORT.md` na raiz do pacote). Os créditos foram para `CREDITOS.txt` na raiz do repositório; `CREDITOS_snippet.txt` não fica no repositório.

# PAPERDOLL_REPORT — phase 1

**Owner:** Ludimus (art/)  
**Spec:** ART_SPEC §10 (authoritative)  
**Date:** 2026-11-05 (America/Sao_Paulo)  
**Canvas:** 300×480 RGBA, transparent background, shared anchor (feet near bottom, CX≈150)

## Composition rules

1. **Body vs skin:** Engine uses **either** `body.png` **or** one of `skin_01.png`…`skin_03.png` as the body layer (not both).  
   - `body.png` = painted bald base with undertunic/hose/boots (default appearance).  
   - `skin_01` fair, `skin_02` medium, `skin_03` deep — same silhouette, skin pixels remapped.  
2. **Hair:** `hair_01.png`…`hair_06.png` stack **on top of** body/skin. Styles: short crop, bowl/monastic, medium parted, long/tied or bun, widow/braids (or beard for m hair_05), wild/gray.  
3. **Paint order (engine):** body → hair → legs → feet → torso → arms → hands → neck → cloak → head → weapon → shield.  
4. **Hueable** cloth/leather/enamel: `<item_id>.png` in **light gray with shading** (engine hues).  
5. **Non-hue** metal/wood/rivets/clasp: `<item_id>_fixed.png`.  
6. Filenames use `data/items/base.json` **`id`** field.

## Delivered file list

### Structure
- `art/paperdoll/m/`
- `art/paperdoll/f/`
- créditos em `CREDITOS.txt` (raiz)
- `art/_preview/paperdoll_*.png`
- `art/paperdoll/README.md` (este arquivo)

### Per-sex layers (all 300×480 RGBA)

| File | Role |
|---|---|
| body.png | Default bald painted base |
| skin_01.png … skin_03.png | Skin tone variants |
| hair_01.png … hair_06.png | Hairstyles |
| cloth_pants.png | Hueable legs |
| leather_boots.png | Hueable feet |
| cloth_shirt.png | Hueable torso/sleeves |
| studded_leather.png | Hueable leather torso (+ studded_leather_fixed.png rivets) |
| leather_gloves.png | Hueable hands |
| wool_cloak.png | Hueable cloak (+ wool_cloak_fixed.png clasp) |
| leather_hood.png | Hueable hood |
| loriga_fixed.png | Mail/chain torso |
| plate_torso_fixed.png | Plate torso |
| plate_arms_fixed.png | Plate arms |
| plate_gloves_fixed.png | Plate hands |
| plate_legs_fixed.png / chain_greaves_fixed.png | Plate/chain legs |
| plate_boots_fixed.png | Plate feet |
| nasal_helm_fixed.png | Nasal helm |
| longsword_fixed.png | Weapon |
| kite_shield_fixed.png | Kite shield |
| wooden_shield_fixed.png | Wooden round shield |

### Previews (single panel, dark background)
- `art/_preview/paperdoll_f_leather.png`
- `art/_preview/paperdoll_f_nude_hair.png`
- `art/_preview/paperdoll_f_plate.png`
- `art/_preview/paperdoll_f_shirt.png`
- `art/_preview/paperdoll_m_leather.png`
- `art/_preview/paperdoll_m_nude_hair.png`
- `art/_preview/paperdoll_m_plate.png`
- `art/_preview/paperdoll_m_shirt.png`

### Verification stacks (body+hair modular)
- `art/_preview/paperdoll_f_body_hair_stack.png`
- `art/_preview/paperdoll_m_body_hair_stack.png`

### Layer inventory (path, size, mode, bytes)

- `art/paperdoll/m/body.png` — 300×480 RGBA (99402 bytes)
- `art/paperdoll/m/chain_greaves_fixed.png` — 300×480 RGBA (39665 bytes)
- `art/paperdoll/m/cloth_pants.png` — 300×480 RGBA (28853 bytes)
- `art/paperdoll/m/cloth_shirt.png` — 300×480 RGBA (41474 bytes)
- `art/paperdoll/m/hair_01.png` — 300×480 RGBA (30204 bytes)
- `art/paperdoll/m/hair_02.png` — 300×480 RGBA (33032 bytes)
- `art/paperdoll/m/hair_03.png` — 300×480 RGBA (27996 bytes)
- `art/paperdoll/m/hair_04.png` — 300×480 RGBA (41747 bytes)
- `art/paperdoll/m/hair_05.png` — 300×480 RGBA (38726 bytes)
- `art/paperdoll/m/hair_06.png` — 300×480 RGBA (45252 bytes)
- `art/paperdoll/m/kite_shield_fixed.png` — 300×480 RGBA (19813 bytes)
- `art/paperdoll/m/leather_boots.png` — 300×480 RGBA (9848 bytes)
- `art/paperdoll/m/leather_gloves.png` — 300×480 RGBA (14657 bytes)
- `art/paperdoll/m/leather_hood.png` — 300×480 RGBA (32009 bytes)
- `art/paperdoll/m/longsword_fixed.png` — 300×480 RGBA (18556 bytes)
- `art/paperdoll/m/loriga_fixed.png` — 300×480 RGBA (89710 bytes)
- `art/paperdoll/m/nasal_helm_fixed.png` — 300×480 RGBA (60021 bytes)
- `art/paperdoll/m/plate_arms_fixed.png` — 300×480 RGBA (26574 bytes)
- `art/paperdoll/m/plate_boots_fixed.png` — 300×480 RGBA (11417 bytes)
- `art/paperdoll/m/plate_gloves_fixed.png` — 300×480 RGBA (18299 bytes)
- `art/paperdoll/m/plate_legs_fixed.png` — 300×480 RGBA (39665 bytes)
- `art/paperdoll/m/plate_torso_fixed.png` — 300×480 RGBA (89710 bytes)
- `art/paperdoll/m/skin_01.png` — 300×480 RGBA (105397 bytes)
- `art/paperdoll/m/skin_02.png` — 300×480 RGBA (104625 bytes)
- `art/paperdoll/m/skin_03.png` — 300×480 RGBA (99780 bytes)
- `art/paperdoll/m/studded_leather.png` — 300×480 RGBA (41004 bytes)
- `art/paperdoll/m/studded_leather_fixed.png` — 300×480 RGBA (824 bytes)
- `art/paperdoll/m/wooden_shield_fixed.png` — 300×480 RGBA (17460 bytes)
- `art/paperdoll/m/wool_cloak.png` — 300×480 RGBA (58111 bytes)
- `art/paperdoll/m/wool_cloak_fixed.png` — 300×480 RGBA (800 bytes)
- `art/paperdoll/f/body.png` — 300×480 RGBA (102255 bytes)
- `art/paperdoll/f/chain_greaves_fixed.png` — 300×480 RGBA (36583 bytes)
- `art/paperdoll/f/cloth_pants.png` — 300×480 RGBA (38086 bytes)
- `art/paperdoll/f/cloth_shirt.png` — 300×480 RGBA (32296 bytes)
- `art/paperdoll/f/hair_01.png` — 300×480 RGBA (37346 bytes)
- `art/paperdoll/f/hair_02.png` — 300×480 RGBA (34008 bytes)
- `art/paperdoll/f/hair_03.png` — 300×480 RGBA (27726 bytes)
- `art/paperdoll/f/hair_04.png` — 300×480 RGBA (40201 bytes)
- `art/paperdoll/f/hair_05.png` — 300×480 RGBA (48341 bytes)
- `art/paperdoll/f/hair_06.png` — 300×480 RGBA (41120 bytes)
- `art/paperdoll/f/kite_shield_fixed.png` — 300×480 RGBA (13841 bytes)
- `art/paperdoll/f/leather_boots.png` — 300×480 RGBA (8997 bytes)
- `art/paperdoll/f/leather_gloves.png` — 300×480 RGBA (11612 bytes)
- `art/paperdoll/f/leather_hood.png` — 300×480 RGBA (30935 bytes)
- `art/paperdoll/f/longsword_fixed.png` — 300×480 RGBA (28822 bytes)
- `art/paperdoll/f/loriga_fixed.png` — 300×480 RGBA (77310 bytes)
- `art/paperdoll/f/nasal_helm_fixed.png` — 300×480 RGBA (49735 bytes)
- `art/paperdoll/f/plate_arms_fixed.png` — 300×480 RGBA (7377 bytes)
- `art/paperdoll/f/plate_boots_fixed.png` — 300×480 RGBA (9626 bytes)
- `art/paperdoll/f/plate_gloves_fixed.png` — 300×480 RGBA (2658 bytes)
- `art/paperdoll/f/plate_legs_fixed.png` — 300×480 RGBA (36583 bytes)
- `art/paperdoll/f/plate_torso_fixed.png` — 300×480 RGBA (77310 bytes)
- `art/paperdoll/f/skin_01.png` — 300×480 RGBA (104402 bytes)
- `art/paperdoll/f/skin_02.png` — 300×480 RGBA (103433 bytes)
- `art/paperdoll/f/skin_03.png` — 300×480 RGBA (101205 bytes)
- `art/paperdoll/f/studded_leather.png` — 300×480 RGBA (49776 bytes)
- `art/paperdoll/f/studded_leather_fixed.png` — 300×480 RGBA (852 bytes)
- `art/paperdoll/f/wooden_shield_fixed.png` — 300×480 RGBA (16408 bytes)
- `art/paperdoll/f/wool_cloak.png` — 300×480 RGBA (61870 bytes)
- `art/paperdoll/f/wool_cloak_fixed.png` — 300×480 RGBA (800 bytes)

## Starter item coverage vs base.json equip slots

**Present (phase 1):** chain_greaves, cloth_pants, cloth_shirt, kite_shield, leather_boots, leather_gloves, leather_hood, longsword, loriga, nasal_helm, plate_arms, plate_boots, plate_gloves, plate_legs, plate_torso, studded_leather, wooden_shield, wool_cloak

**Still missing for phase 2** (equip ids in base.json without paperdoll layer yet):

- `axe` (slot=hand1)
- `battleaxe` (slot=hand1)
- `bedouin_robe` (slot=torso)
- `bow` (slot=hand1)
- `buckler` (slot=hand2)
- `cazagante` (slot=torso)
- `chain_boots` (slot=feet)
- `chain_coif` (slot=head)
- `chain_gloves` (slot=hands)
- `cloth_sandals` (slot=feet)
- `club` (slot=hand1)
- `crimson_cloak` (slot=cloak)
- `crossbow` (slot=hand1)
- `crusader_shield` (slot=hand2)
- `crusader_surcoat` (slot=torso)
- `dagger` (slot=hand1)
- `egyptian_gambeson` (slot=torso)
- `face_helm` (slot=head)
- `fishing_pole` (slot=hand1)
- `flanged_mace` (slot=hand1)
- `gambeson` (slot=torso)
- `gold_necklace` (slot=neck)
- `greathelm` (slot=head)
- `hand_axe` (slot=hand1)
- `hand_crossbow` (slot=hand1)
- `hatchet` (slot=hand1)
- `hauberk` (slot=torso)
- `heater_shield` (slot=hand2)
- `keffiyeh` (slot=head)
- `kettle_helm` (slot=head)
- `kris` (slot=hand1)
- `lamellar` (slot=torso)
- `lance` (slot=hand1)
- `leather_armor` (slot=torso)
- `longbow` (slot=hand1)
- `lorigao` (slot=torso)
- `mace` (slot=hand1)
- `mortar_pestle` (slot=hand1)
- `peasant_tunic` (slot=torso)
- `pickaxe` (slot=hand1)
- `pilgrim_cross` (slot=neck)
- `pilgrim_habit` (slot=torso)
- `quarterstaff` (slot=hand1)
- `relicary` (slot=neck)
- `round_shield` (slot=hand2)
- `scimitar` (slot=hand1)
- `sewing_kit` (slot=hand1)
- `shortsword` (slot=hand1)
- `shovel` (slot=hand1)
- `silver_necklace` (slot=neck)
- `skinning_knife` (slot=hand1)
- `smith_hammer` (slot=hand1)
- `spear` (slot=hand1)
- `staff` (slot=hand1)
- `sword` (slot=hand1)
- `tinker_tools` (slot=hand1)
- `travel_cloak` (slot=cloak)
- `turban` (slot=head)
- `turkish_cuirass` (slot=torso)
- `warhammer` (slot=hand1)

## Notes / known limits

- Bodies are original painted masters (sombrio medieval); no UO/EA assets.
- Hueable layers are light-gray shaded extracts shaped to the body silhouette.
- Full leather/plate **previews** are painted outfit composites matching the body pose (readability for Rodrigo review). Modular `_fixed` / hueable PNGs are region extracts from those outfits + body-contour masks — phase 2 can refine seam quality / female plate arms density.
- `studded_leather` maps to item id `studded_leather` (sprite_layer `m/jaque_couro` in data).
- Credits: `CREDITOS.txt` (CC0 original).

