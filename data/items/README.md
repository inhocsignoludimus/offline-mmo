# data/items

`base.json` is the gear catalog (weapons, armor, shields, clothing, jewelry, consumables, resources, tools, furniture and deeds). Rarity bands and rare-name parts live in `rarity.json`; rolled mods in `affixes.json`; green sets in `sets.json`; orange uniques in `uniques.json`. Dye and material colors are `data/hues.json`. Spell reagents stay in `data/magic/reagents.json`.

## Icons and sprites

- `icon` prefers real keys from TCoM `ICONES_ITENS` in `jogo.js` (e.g. `espada_2`, `loriga`, `elmoNasal`, `broquel`). Consumables/resources/tools without a sheet cell keep a snake_case id; the engine falls back to a generic icon and can log the miss.
- `sprite_layer` uses real `CAMADAS_ANIM` keys (`m/longsword`, `m/lorigao`, `m/elmo_nasal`, …) via TCoM `VISUAL_ITEM` where possible. `null` means no wear layer yet — that is OK; the engine skips the overlay.

Missing art is expected. New bases use a snake_case `icon` (the engine falls back to a generic) and a real TCoM `sprite_layer`, or `null` when no layer exists yet.
