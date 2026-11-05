# art/

Dono: **Ludimus**.

Arte do jogo, no contrato de `docs/ART_SPEC.md` (versão 1, revista
pelo Claude). A arte derivada do Flare fica em CC-BY-SA 3.0, com
versões posteriores permitidas (`LICENSE` aqui ao lado). Todo
arquivo novo ganha autor, licença e link em `CREDITOS.txt` no
mesmo pull request.

```
art/
  tilesets/<bioma>/          <set>.png e <set>.txt
  buildings/<bioma>/<id>/    peças da casa e house.json
  props/<categoria>/         <id>.png e rotações _r0.._r3
  maps/<id>.txt              mapa no formato do Flare
  maps/src/<id>.tmx          fonte editável do Tiled
  src/                       .blend novos ou modificados
  _preview/<id>.png          prévia com personagem do TCoM
```

Biomas: `outremer`, `plains`, `forest`, `swamp`, `mountains`,
`north`, `ruins`, `coast`.

O chão no master é 192×96. O runtime é 96×48; quem reduz é o
build da engine. A âncora `ox,oy` é o centro do losango.

`art/src/` são arquivos Blender. O código do jogo está em `src/`
na raiz, pasta do Claude.

Só o Ludimus edita esta árvore. Mudança entra por pull request;
o Rodrigo aprova.
