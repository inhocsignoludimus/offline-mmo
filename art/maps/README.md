# art/maps/

Dono: **Ludimus**.

O mundo é um **mapa único e contínuo** (estilo After Light). Não há
troca de área nem `intermap`/exits entre mapas.

## Fonte

- Runtime / entrega: `art/maps/<id>.txt` no formato Flare
  (camadas `background`, `object`, `collision`).
- Fonte editável Tiled: `art/maps/src/<id>.tmx`.
- `engine/dev_assets/flare/*.json` é **gerado** pelos scripts de
  build do Claude. **Não editar à mão.**

## Checkout irmão do Flare (TMX)

Os `.tmx` referenciam o tileset grassland do Flare neste caminho
relativo a `art/maps/src/`:

```
../../../../flare-game/mods/fantasycore/images/tilesets/tileset_grassland.png
```

Ou seja, o repositório `flare-game` deve ficar como **irmão** do
checkout `offline-mmo`:

```
<pai>/
  offline-mmo/
  flare-game/
```

O `.txt` Flare usa `tileset=tilesetdefs/tileset_grassland.txt`
resolvido dentro do `flare-game` pelos scripts de import.

## Mapas

- `mundo` — mapa contínuo atual (Lochport + Bosque da Vila a leste,
  ligados por estrada, sem exits).
- `bosque_da_vila` — peça modular da região de caça (sem exits);
  já embutida em `mundo`.

Regiões e spawns: `data/zones.json` (`world.map`, `origin`,
`chunks[].rect` em coordenadas do mapa único).

`mundo.txt` é a fatia de 98×60 (Lochport + Bosque da Vila). Ela
entra no mapa alvo de 2048×2048 no tile `[768, 1408]`. A planta
grossa é `data/world_layout.json`. Não regenerar esta fatia por
cima: o desenho novo carimba em volta. Ver `docs/WORLD_DESIGN.md`.

Ver `docs/ART_SPEC.md` e `docs/DATA_SCHEMA.md`.
