# ENGINE.md — engine v0

Dono: **Claude**. Este é o primeiro protótipo jogável. A vila provisória usa o mapa Lochport do Flare e vai até a cabana do Ludimus chegar.

## Como rodar

```
python3 build/import_dev_assets.py --flare <flare-game> --tcom <tcom> --map lochport --out engine/dev_assets   # só uma vez (~15 min)
python3 build/build.py          # gera dist/
python3 -m http.server -d dist  # ou abrir dist/index.html direto (file://)
```

O build cria `dist/game.js`. Esse arquivo junta os scripts com todos os JSON de `data/` e de `engine/dev_assets` embutidos. Por isso o jogo roda por `file://` no APK, sem fetch. O `dist/` não vai para o git.

## Arquivos

| Arquivo | O que faz |
| --- | --- |
| `engine/iso.js` | Projeção 2:1 com tile de 96×48, câmera e as 8 direções do TCoM. |
| `engine/map.js` | Mapa em tiles. O chão é pré-desenhado em pedaços de 16×16, há colisão (camada `collision` do Flare: diferente de 0 bloqueia) e A* em 8 direções sem cortar quina. |
| `engine/actor.js` | Personagem em camadas do TCoM. A ordem por direção é a mesma do TCoM; animações stance, run, swing, hit e die. |
| `engine/render.js` | Chão, objetos do mapa e personagens ordenados por x+y. Desenha também os nomes e as falas em balão. |
| `ui/gumps.js` | Janelas arrastáveis no estilo do UO: Status, Paperdoll, Mochila, Diário/chat, Mapa e Jogadores. A posição de cada uma fica salva no navegador. |
| `systems/chat.js` | Monta as falas: frase de `data/chat` + placeholders + erros de digitação, CAIXA ALTA e emoticons conforme a personalidade. |
| `systems/sim.js` | Jogadores simulados: login e logout, passeio pela cidade, treino, falas locais e globais, respostas ao jogador, convite de guilda, guerras e raids. |
| `src/main.js` | Criação do personagem, entrada, itens e equipamento, laço do jogo. |

## Controles

- Clique para andar. Segurando o clique, o personagem segue o cursor.
- Clique num jogador para ver o nome e a guilda dele e preparar um sussurro.
- Enter abre o chat.
- Atalhos de janela: S, P, B, J, O, M.
- Comandos: `/g` (global), `/w Nome` (sussurro), `/gu` (guilda), `/aceitar` e `/sair` (guilda), `/quem`.

## Pendências de dados (Ludimus)

- `data/items/base.json`: até ele chegar, a engine usa a tabela provisória `ITENS_DEV` de `src/main.js`.
- Lista de chefes para `{boss}`: até ela chegar, a engine usa a lista provisória `Chat.DEV.boss`.
- Ícones de skills e um `skills.json`.

## Próximos passos

1. Casas por dentro. A cabana `plains_cabin_01` vai ter teto escondido e as paredes da frente trocadas por `wall_low`.
2. Monstros e combate.
3. Mapa grande em pedaços e biomas.
4. Builds para web, APK e itch.io.
