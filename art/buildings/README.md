# art/buildings/

Dono: **Ludimus**.

Construções em que se entra. Cada casa é uma pasta
`art/buildings/<bioma>/<id>/`, com peças separadas na mesma grade:

| Peça | O que é |
| --- | --- |
| `floor` | Chão interno, tile a tile. |
| `wall` | Uma peça de parede por tile, com as variações da spec. |
| `wall_low` | A mesma parede cortada na altura do rodapé. |
| `door` | Aberta e fechada, nas duas orientações. |
| `roof` | Uma imagem por construção, `<casa>_roof.png`. |
| `props` | Móveis soltos desta casa. |
| `house.json` | Peças por posição, porta e área interna. O esquema está em `docs/DATA_SCHEMA.md`. |
| `pieces.txt` | Tileset das peças, no formato do Flare. |

Biomas: `outremer`, `plains`, `forest`, `swamp`, `mountains`,
`north`, `ruins`, `coast`. A pasta `<id>` nasce com a primeira
casa daquele bioma.

Ver `docs/ART_SPEC.md`.
