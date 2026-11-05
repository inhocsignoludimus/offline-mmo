# offline-mmo

MMO offline de um jogador, no estilo de Ultima Online. O mundo segue
sem outras pessoas na rede: os outros aventureiros são jogadores
simulados, com guildas, ofício e fala própria. O nome do jogo ainda
é provisório. O repositório guarda o nome técnico `offline-mmo`.

Estúdio **In Hoc Signo Ludimus**. Direção: **Rodrigo**, que aprova
cada pull request.

Este repositório está no esqueleto inicial. Há pastas, regras e
rascunhos de especificação. Ainda não há jogo jogável.

## O jogo

Um único mapa fixo, de cerca de **2000×2000 tiles**, dividido em
**8 biomas**. Os biomas misturam o deserto da Terra Santa com
biomas medievais no estilo do [Flare](https://flarerpg.org)
(pradaria, floresta, neve e vizinhança). A lista fechada dos oito
nomes ainda é proposta; está em `docs/ART_SPEC.md`.

O tile de chão na tela mede **64×32 pixels**, projeção isométrica
2:1, a mesma de [A Cruz de Montgisard](https://github.com/inhocsignoludimus/The-Cross-of-Montgisard)
(`TILE_LARGURA = 64`, `TILE_ALTURA = 32` em `js/jogo.js`). O mundo
é medido em metros reais e convertido para pixels. No TCoM, cada
tile são 2×2 metros.

Alvos de publicação: página **web**, pacote Android (**APK**) e
página na **itch.io**.

## De onde vem o que se reaproveita

O motor isométrico em JavaScript é o do TCoM, jogo do mesmo estúdio.
As folhas de cenário de lá ficam em `assets/cenario/<área>/folha*.webp`
e são recortadas pela tabela `CENARIO_DADOS` (folha, x, y, largura,
altura, âncora). A especificação de tileset deste jogo propõe um
JSON compatível com essa tabela. O contrato ainda é rascunho: o
Claude revisa antes de virar regra do motor.

A arte livre de referência é a do Flare:

- [flare-game](https://github.com/flareteam/flare-game) — arte sob
  CC-BY-SA 3.0, com versões posteriores permitidas;
- [flare-game-art-src](https://github.com/flareteam/flare-game-art-src)
  — fontes Blender; texturas em CC0 onde o repositório assim indica.

O código do motor Flare (GPL v3) não entra aqui. Cada arquivo
adaptado ganha autor, licença e link em `CREDITOS.txt`.

## Quem faz o quê

Dois colaboradores de IA trabalham no repositório. O Rodrigo dirige
e aprova. Cada colaborador só edita as pastas dele e entrega por
pull request.

| Pasta | Dono | O que mora aqui |
| --- | --- | --- |
| `src/` | Claude | Ponto de entrada do programa e a cola entre motor, interface e sistemas. |
| `engine/` | Claude | Projeção, câmera, mapa, desenho de tiles e a escala metros → pixels. |
| `ui/` | Claude | Interface: inventário, papel do personagem, chat na tela, janelas. |
| `systems/` | Claude | Regras de jogo: jogadores simulados, guildas, mundo. Lê `data/`; não edita `data/`. |
| `build/` | Claude | Scripts para gerar a web, o APK e o pacote da itch.io. |
| `art/tiles/` | Ludimus | Tiles de chão e de transição, por bioma, em PNG. |
| `art/props/` | Ludimus | Objetos e criaturas renderizados (o que passa da altura do losango). |
| `art/blend/` | Ludimus | Fontes Blender. Render em Cycles, na CPU. |
| `art/tilesets/` | Ludimus | Definição dos tilesets (JSON) e, quando existirem, as folhas empacotadas. |
| `data/lore/` | Ludimus | Lore por bioma, em Markdown. |
| `data/chat/` | Ludimus | Dicionário de falas dos jogadores simulados. |
| `data/names/` | Ludimus | Nomes de jogadores e de guildas, com sigla. |
| `data/items/` | Ludimus | Itens, prefixos, sufixos, feitiços e reagentes. |
| `docs/` | compartilhada | Especificações. Rascunho até o Claude revisar a parte técnica e o Rodrigo aprovar. |

`CREDITOS.txt` fica na raiz e é mantido pelo Ludimus: é a ficha
pública do jogo, no mesmo espírito do TCoM.

`README.md`, `LICENSE` e `.gitignore` descrevem o acordo do
projeto. Mudam quando esse acordo muda, sempre em pull request
aprovado pelo Rodrigo.

## Fluxo de trabalho

1. O colaborador cria um ramo a partir de `main` e mexe só nas
   pastas dele. Precisou de uma mudança na pasta do outro: pede no
   pull request, e o dono da pasta faz a alteração.
2. A entrega é um pull request para `main`.
3. O Claude revisa o que vira contrato do motor. Os rascunhos
   `docs/ART_SPEC.md` e `docs/DATA_SPEC.md` estão marcados para
   essa revisão.
4. O Rodrigo aprova. Sem a aprovação dele, o pull request não é
   mergeado. Colaborador não aprova o próprio trabalho no lugar
   do Rodrigo.

O esqueleto inicial (a árvore inteira de uma vez) é a exceção
combinada para o repositório nascer. A regra das pastas vale a
partir daí.

## Licenças

A licença do **código** está pendente. O Rodrigo escolhe. Até lá,
o código não está publicado sob MIT, GPL nem qualquer outra
licença livre. O detalhe está em `LICENSE`.

A pasta **`art/`** é distribuída sob **CC-BY-SA 4.0**, compatível
com a arte do Flare (CC-BY-SA 3.0 ou posterior). Ver `art/LICENSE`
e `CREDITOS.txt`.

Não entram assets non-commercial, nem arquivo sem autor, licença
e link.

A licença dos textos em `data/` acompanha a decisão do Rodrigo
sobre o código e o conteúdo. `data/` não herda a CC-BY-SA só por
estar ao lado de `art/`.

## Documentos

- `docs/ART_SPEC.md` — projeção, câmera, nome de arquivo, tileset.
  Rascunho para o Claude revisar e aprovar.
- `docs/DATA_SPEC.md` — esquemas de chat, nomes, itens e lore.
  Rascunho para o Claude revisar e aprovar.
- `CREDITOS.txt` — créditos e a regra de ouro de cada asset.
- `LICENSE` — notas de licença. O código continua em aberto.
