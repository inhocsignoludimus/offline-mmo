# offline-mmo

MMO offline de um jogador, no estilo de Ultima Online. O mundo segue
sem outras pessoas na rede: os outros aventureiros são jogadores
simulados, com guildas, ofício e fala própria. O nome do jogo ainda
é provisório. O repositório guarda o nome técnico `offline-mmo`.

Estúdio **In Hoc Signo Ludimus**. Direção: **Rodrigo**, que aprova
cada pull request.

Este repositório está no esqueleto inicial. Há pastas, regras e as
especificações já revisadas pelo Claude. Ainda não há jogo jogável.

## O jogo

Um único mapa fixo, de cerca de **2000×2000 tiles**, dividido em
**8 biomas**:

| Id | O que é |
| --- | --- |
| `outremer` | Deserto da Terra Santa. |
| `plains` | Planície. |
| `forest` | Floresta. |
| `swamp` | Pântano. |
| `mountains` | Montanhas. |
| `north` | Norte. |
| `ruins` | Ruínas. |
| `coast` | Costa. |

Projeção isométrica 2:1, a mesma do Flare e de [A Cruz de Montgisard](https://github.com/inhocsignoludimus/The-Cross-of-Montgisard).
O tile de chão **no jogo** mede **96×48 pixels**. O PNG master mede
**192×96** (2×). O Ludimus entrega só o master; o build da engine
reduz para 1× e monta os atlas. O contrato está em `docs/ART_SPEC.md`
(versão 1, revisada pelo Claude).

Alvos de publicação: página **web**, pacote Android (**APK**) e
página na **itch.io**.

## De onde vem o que se reaproveita

O motor isométrico em JavaScript é o do TCoM, jogo do mesmo estúdio.
A escala de cenário deste jogo não é o tile de 64×32 do TCoM: o
Claude validou o 96×48 com mapas do Flare e os personagens do TCoM
por cima. O tileset que a engine lê é o `.txt` do Flare
(`tile=ID,x,y,w,h,ox,oy`). A âncora `ox,oy` é o centro do losango
de chão. Os mapas são do Tiled, salvos no `.txt` do Flare.

A arte livre de referência é a do Flare:

- [flare-game](https://github.com/flareteam/flare-game) — arte sob
  CC-BY-SA 3.0, com versões posteriores permitidas;
- [flare-game-art-src](https://github.com/flareteam/flare-game-art-src)
  — fontes Blender e a câmera que este jogo usa sem mudar o ângulo.
  Texturas em CC0 onde o repositório assim indica.

O código do motor Flare (GPL v3) não entra aqui. Cada arquivo
adaptado ganha autor, licença e link em `CREDITOS.txt`. Não entra
material do Ultima Online nem da EA.

## Quem faz o quê

Dois colaboradores de IA trabalham no repositório. O Rodrigo dirige
e aprova. Cada colaborador só edita as pastas dele e entrega por
pull request. **A divisão de pastas e esse fluxo de pull request
estão aprovados pelo Claude.**

`src/` na raiz é código. `art/src/` são os `.blend`. São pastas
diferentes, de donos diferentes.

| Pasta | Dono | O que mora aqui |
| --- | --- | --- |
| `src/` | Claude | Ponto de entrada do programa e a cola entre motor, interface e sistemas. |
| `engine/` | Claude | Projeção, câmera, mapa, desenho de tiles, redução do master 2× e atlas. |
| `ui/` | Claude | Interface: inventário, papel do personagem, chat na tela, janelas. |
| `systems/` | Claude | Regras de jogo: jogadores simulados, guildas, mundo. Lê `data/`; não edita `data/`. |
| `build/` | Claude | Reduz os masters, gera atlas, web, APK e o pacote da itch.io. |
| `art/tilesets/<bioma>/` | Ludimus | `<set>.png` e `<set>.txt` no formato do Flare. Master 192×96. |
| `art/buildings/<bioma>/<id>/` | Ludimus | Casa em peças (`floor`, `wall`, `wall_low`, `door`, `roof`, `props`) e `house.json`. |
| `art/props/<categoria>/` | Ludimus | Móveis e objetos soltos. Quatro rotações em `_r0`…`_r3` quando o objeto gira. |
| `art/maps/` | Ludimus | Mapas `<id>.txt` no formato do Flare. |
| `art/maps/src/` | Ludimus | Fontes Tiled (`.tmx`). |
| `art/src/` | Ludimus | `.blend` novos ou modificados. Os do Flare ficam como referência, fora daqui. |
| `art/_preview/` | Ludimus | Prévia `<id>.png` com a peça e um personagem do TCoM ao lado. |
| `data/lore/` | Ludimus | `biomes.json` e um Markdown longo por bioma. |
| `data/chat/` | Ludimus | `personalities.json` e `lines.json`. |
| `data/names/` | Ludimus | `players.json` e `guilds.json` (a guilda leva `tag`). |
| `data/items/` | Ludimus | `base.json` e `affixes.json`. |
| `data/magic/` | Ludimus | `spells.json` e `reagents.json`. Nomes e palavras de poder são nossos. |
| `docs/` | compartilhada | Especificações. `ART_SPEC.md` e `DATA_SCHEMA.md` já foram revisados pelo Claude. |

`CREDITOS.txt` fica na raiz e é mantido pelo Ludimus: é a ficha
pública do jogo, no mesmo espírito do TCoM.

`README.md`, `LICENSE` e `.gitignore` descrevem o acordo do
projeto. Mudam quando esse acordo muda, sempre em pull request
aprovado pelo Rodrigo.

## Fluxo de trabalho

A divisão de pastas e este fluxo estão aprovados pelo Claude.
O Rodrigo é quem aprova o merge.

1. O colaborador cria um ramo a partir de `main` e mexe só nas
   pastas dele. Precisou de uma mudança na pasta do outro: pede no
   pull request, e o dono da pasta faz a alteração.
2. A entrega é um pull request para `main`.
3. O que vira contrato do motor é o que está em `docs/ART_SPEC.md`
   e `docs/DATA_SCHEMA.md`. Os dois já passaram pela revisão do
   Claude. Mudança posterior nesses contratos volta para o Claude
   antes do merge.
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

A arte derivada do Flare fica em **CC-BY-SA 3.0**, e versões
posteriores dessa licença podem ser usadas. Texturas e modelos CC0
(ambientCG, Poly Haven, `flare-game-art-src`, Quaternius, KayKit)
podem entrar, com crédito. Ver `art/LICENSE` e `CREDITOS.txt`.

Não entram assets non-commercial, nem material do Ultima Online ou
da EA, nem arquivo sem autor, licença e link.

A licença dos textos em `data/` acompanha a decisão do Rodrigo
sobre o código e o conteúdo. `data/` não herda a licença de `art/`
só por estar ao lado.

## Documentos

- `docs/ART_SPEC.md` — grade, câmera, âncora, pastas e checklist.
  Versão 1, revisada pelo Claude.
- `docs/DATA_SCHEMA.md` — esquemas de chat, nomes, itens, magia,
  lore e `house.json`. Revisado pelo Claude.
- `CREDITOS.txt` — créditos e a regra de ouro de cada asset.
- `LICENSE` — notas de licença. O código continua em aberto.
