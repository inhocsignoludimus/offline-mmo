# data/items

`base.json` is the first-round gear kit for the Claude engine (weapons, armor, shields, clothing, jewelry, consumables, resources, tools, a few furniture/deed stubs).

## Icons and sprites

- `icon` prefers real keys from TCoM `ICONES_ITENS` in `jogo.js` (e.g. `espada_2`, `loriga`, `elmoNasal`, `broquel`). Consumables/resources/tools without a sheet cell keep a snake_case id; the engine falls back to a generic icon and can log the miss.
- `sprite_layer` uses real `CAMADAS_ANIM` keys (`m/longsword`, `m/lorigao`, `m/elmo_nasal`, …) via TCoM `VISUAL_ITEM` where possible. `null` means no wear layer yet — that is OK; the engine skips the overlay.

Missing art is expected for this handoff. Affixes live in a later `affixes.json`; reagents for spells may grow in `data/magic/`.
