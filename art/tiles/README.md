# art/tiles/

Dono: **Ludimus**.

Tiles de chão, borda, água e transição entre biomas, em PNG com
alfa. Um diretório por bioma, no padrão de
`docs/ART_SPEC.md`:

```
art/tiles/<bioma>/<tipo>_<nome>_<variante>.png
```

As pastas dos biomas nascem quando os ids forem aprovados. Até
lá este diretório fica só com este texto.

Render proposto: Cycles na CPU, chão em 192×96 (3× o tile de tela
64×32). A âncora proposta é o vértice sul do losango. Os dois
números ainda esperam o Claude.
