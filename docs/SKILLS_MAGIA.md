# SKILLS_MAGIA.md — skills sem classe e magia (versão casual do UO)

## Skills

- **Não há classe.** Como no UO e no começo do TCoM, você melhora qualquer skill usando: cura com bandagem, luta com espada, pesca pescando.
- **O começo é só um kit.** São 14 começos (Guerreiro, Mago, Ferreiro, Bardo…) mais o "Do seu jeito", em que você escolhe 3 skills que começam em 50, 30 e 20. Cada começo dá as primeiras skills e o equipamento; nada impede um ferreiro de virar mago.
- **Tetos:** 100 por skill e 700 no total, como no UO.
- **Teto total:** quando chega nele, uma skill só sobe se outra estiver marcada para baixar. Na janela de Skills, cada skill tem três estados: ▲ subir, ▼ baixar e ■ travada.
- **Casual, sem grind:** a chance de subir é alta e os passos são grandes no começo. Abaixo de 30 a skill sobe 1,0 por vez; abaixo de 60, 0,5; abaixo de 85, 0,2; daí até 100, 0,1. Ações difíceis ensinam mais. A meta é chegar ao 100 em horas de jogo, não em semanas.
- **Código:** `systems/skills.js`. `Skills.use(id, dif)` treina a skill, e `Skills.check(id, dificuldade)` testa o sucesso e também treina.

## Magia

- **8 círculos e cerca de 64 magias,** na mesma estrutura do UO: cura, dano, buff, debuff, invocação, teletransporte, campos e revelação.
- **Os nomes e as palavras de poder são nossos** (DATA_SCHEMA): nada copiado do UO.
- **Livro único:** você já começa com o livro de magias. Não há caça de pergaminho. Cada círculo abre pela skill **Magia**:

  | Círculo | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|
  | Magia mínima | 0 | 10 | 20 | 30 | 45 | 60 | 75 | 90 |

- **Reagentes simplificados:** os 8 reagentes do UO viram 4, e cada magia usa no máximo 2 tipos. Os do 1º e do 2º círculo não usam reagente. Reagente é barato, vendido pelo mago da cidade e cai de monstro.
- **Mana:** cada círculo custa 4, 6, 9, 11, 14, 20, 40 e 50 de mana. A mana volta mais rápido com Meditação.
- **Falha:** uma magia pode falhar quando a sua Magia está perto do mínimo do círculo, e para de falhar 20 pontos acima dele. Falhar não gasta reagente, só metade da mana.
- **Lançar:** pelo livro ou pela barra de atalhos (1 a 9). Magia com alvo pede um clique no alvo.
- **Dados:** `data/magic/spells.json` e `data/magic/reagents.json` (Ludimus), no formato do `DATA_SCHEMA.md`. **Código:** `systems/magic.js` (Claude).
