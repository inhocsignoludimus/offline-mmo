# engine/

Dono: **Claude**.

Motor isométrico reaproveitado de A Cruz de Montgisard, na escala
aprovada em `docs/ART_SPEC.md`:

- projeção 2:1;
- tile de runtime **96×48**;
- master **192×96**, reduzido no build;
- tileset no `.txt` do Flare (`tile=ID,x,y,w,h,ox,oy`), com a
  âncora no centro do losango;
- mapas em `art/maps/<id>.txt`.

Repositório de origem, do mesmo estúdio:

https://github.com/inhocsignoludimus/The-Cross-of-Montgisard

O código do motor Flare (GPL v3) não entra nesta pasta. A arte
do Flare, quando for adaptada, mora em `art/` e nos créditos.

Os dados que esta engine lê estão especificados em
`docs/DATA_SCHEMA.md`.

Só o Claude edita esta pasta. Pull request; o Rodrigo aprova.
