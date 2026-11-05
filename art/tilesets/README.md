# art/tilesets/

Dono: **Ludimus**.

Definição dos tilesets e, quando existirem, as folhas
empacotadas. A proposta de formato é um JSON por bioma,
`art/tilesets/<bioma>.json`, compatível com a tupla do
`CENARIO_DADOS` do TCoM:

`[folha, x, y, largura, altura, ancoraX, ancoraY]`

O esquema, as alternativas (texto do Flare e Tiled) e a
recomendação estão em `docs/ART_SPEC.md`. Enquanto o Claude não
aprovar, não há JSON de tileset nesta pasta.

Os PNG soltos continuam em `art/tiles/` e `art/props/`. A folha
é um passo posterior.
