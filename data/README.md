# data/

Dono: **Ludimus**.

Texto e catálogos do jogo, no esquema de `docs/DATA_SCHEMA.md`,
já revisado pelo Claude. JSON UTF-8. Cada arquivo é um objeto com
`"version": 1`. Ids em `snake_case`, únicos dentro do arquivo.
Texto que o jogador lê vem em `pt` e `en`.

O Claude lê estes arquivos a partir de `systems/` e `ui/`. Não
edita esta árvore.

A planta do mundo contínuo está em `world_layout.json`,
`zones.json` (`regions`), `invasions.json`, `contracts.json` e
`portals.json`. O texto está em `docs/WORLD_DESIGN.md`.

A licença deste texto ainda não foi escolhida (ver `LICENSE` na
raiz). Não herda a CC-BY-SA de `art/`.

Nomes de magia e palavras de poder são nossos. Não copiar os do
Ultima Online.
