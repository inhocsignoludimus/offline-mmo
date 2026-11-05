# art/tilesets/

Dono: **Ludimus**.

Um diretório por bioma. Dentro dele, o par `<set>.png` e
`<set>.txt` no formato de tileset do Flare, que a engine já lê:

```
[tileset]
img=art/tilesets/plains/plains_walls.png
tile=ID,x,y,w,h,ox,oy
```

`ox,oy` é a distância do canto superior esquerdo do recorte até o
centro do losango de chão. O PNG master do chão é 192×96 (2× o
runtime de 96×48). O build da engine reduz e gera os atlas.

O id do tile não muda depois de entregue. Peça nova ganha id no
fim; id antigo não é reaproveitado.

Biomas: `outremer`, `plains`, `forest`, `swamp`, `mountains`,
`north`, `ruins`, `coast`. Ver `docs/ART_SPEC.md`.
