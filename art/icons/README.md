# art/icons/

Ícones 128×128 RGBA (fundo transparente), estilo pintado sombrio alinhado ao atlas TCoM.

```
skills/<id>.png       38 skills
spells/scroll_c1..c8  pergaminho tingido por círculo de magia
reagents/<id>.png     incense, saltpeter, myrrh, quicklime
items/<id>.png        poções, 37 itens que eram snake_case, ferramentas
resources/<id>.png    logs, ores (iron/copper/silver/gold), ingots (iron/copper/silver/gold)
sheet.webp + sheet.json   atlas empacotado (também em engine/dev_assets/tcom/)
```

A engine lê `engine/dev_assets/tcom/icons.webp` + `icons.json` (`tam`, `w`, `h`, `mapa`).
`ui/gumps.js` usa `meta.w` / `meta.h` para o `background-size`.
