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

- `mundo` — mapa contínuo (Lochport + Bosque da Vila + trilha leste).
  Os primeiros 98 tiles de largura são a fatia anterior, intacta.
- `bosque_da_vila` — peça modular da região de caça (sem exits);
  já embutida em `mundo`. Não foi alargada.
- `trilha_leste` — peça modular da continuação a leste, embutida em
  `mundo` a partir do tile local `(98, 12)`.
- `estrada_norte` — peça à parte, ao norte de `mundo.txt`. O arquivo
  antigo não muda de tamanho. A origem legada é `[32, -72]`; o portão
  em `(41, 0)` continua no mesmo tile. Ver `docs/HANDOFF_ESTRADA_NORTE.md`.

Regiões e spawns: `data/zones.json` (`world.map`, `origin`,
`chunks[].rect` em coordenadas do mapa único).

O retângulo noroeste de 98×60 (Lochport + Bosque da Vila) entra no
mapa alvo de 2048×2048 no tile `[768, 1408]`. `mundo.txt` agora mede
146×60: as 48 colunas novas são a trilha leste, a partir de x=98.
A planta grossa é `data/world_layout.json`. Não regenerar as
primeiras 98 colunas. Ver `docs/WORLD_DESIGN.md` e
`docs/HANDOFF_TRILHA_LESTE.md`.

Ver `docs/ART_SPEC.md` e `docs/DATA_SCHEMA.md`.
