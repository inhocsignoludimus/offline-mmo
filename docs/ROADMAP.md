# ROADMAP.md — o que falta e quem faz

Regra de sempre:
- **Ludimus:** arte (`art/`), lore e todos os dados em `data/` (o *quê*).
- **Claude:** engine, sistemas, interface e builds (o *como*).
- **Rodrigo:** decide e aprova.

Cada fase só começa quando os dados da anterior estão no `main`.

## Fase 1 — Combate e monstros (base de quase tudo o que vem depois)

**Claude**
- Combate no estilo do UO: modo de guerra, ataque automático, alcance por arma, armadura, aparar golpes, flechas e virotes.
- IA dos monstros:
  - rondar, perseguir, fugir com pouca vida;
  - atacar à distância e lançar magia (os monstros usam o `spells.json`).
- Spawns por região, com tempo de reaparecimento.
- Morte e ressurreição:
  - o monstro morto deixa um cadáver com loot;
  - o jogador morto vira fantasma, como no UO, e volta no curandeiro ou com a magia de ressurreição.
- Os jogadores simulados passam a lutar de verdade: caçam, morrem, pedem ajuda e participam de PK.
- Importar os monstros do Flare (CC-BY-SA) para a escala nova, do mesmo jeito que foi feito com o TCoM:
  - antlion, formigas, goblins, hobgoblins, esqueletos (guerreiro, arqueiro, mago), zumbis;
  - minotauro, wyverns (fogo, ar, água, adulta), necromante e os chefes.

**Ludimus**
- `data/monsters.json`: vida, dano, resistências, skills, magias, velocidade, comportamento, bioma, tabela de loot e ouro.
- Arte nova, em ordem: lobo, urso, javali, aranha gigante, escorpião, rato, caranguejo gigante e grifo. Os outros da lista `NEW_MONSTER_IDS.md` vêm depois.
- **Dragões em 5 degraus:** filhote, jovem, adulto, ancião e **alfa**.
  - Um modelo só, com um rig só. O que muda de degrau para degrau é o tamanho, os chifres, as placas, as cicatrizes, a cor e a aura.
  - O filhote e o jovem podem sair das wyverns do Flare.
  - Do adulto em diante, o modelo é novo no Blender.
  - Variações por elemento: fogo (Outremer), gelo (Norte), pântano (veneno) e tempestade (Montanhas).
  - O alfa é chefe de evento, com nome próprio.

## Fase 2 — Mundo grande e cidades

**Claude**
- Mapa em pedaços (chunks) de 64×64. Só o que está perto é carregado, o que permite um mundo de 2000×2000.
- Gerador do mundo:
  - os 8 biomas saem de ruído, com estradas e rios;
  - cidades, dungeons e pontos de interesse são **carimbados** a partir de arquivos prontos.
- Transição de bioma, música e luz de dia e de noite por região.

**Ludimus**
- Tilesets por bioma: chão, bordas, árvores, rochas e água.
- Cidades montadas no **Tiled**, salvas como `.txt` do Flare (formato do `ART_SPEC.md`).
  - Primeiro, 1 cidade por bioma: as capitais do `biomes.json`.
  - Depois, as vilas.
- As casas do `BUILDINGS.md`, por bioma.
- Lugares de dungeon: cripta, mina, caverna e templo em ruínas.

## Fase 3 — NPCs, comércio e banco

**Claude**
- Janelas de comprar e vender, no estilo do UO.
- Banco, com o baú do banco.
- Curandeiro (ressurreição), guarda da cidade e treinador de skill (paga para subir até 30).
- **Jogadores simulados que vendem:** bancas de "player vendor" na praça, preço que varia com a oferta, e anúncios WTS/WTB no chat que correspondem a itens que existem de verdade nas bancas.

**Ludimus**
- `data/npcs/vendors.json`: tipos de loja (ferreiro, alfaiate, mago, alquimista, açougueiro, estalajadeiro, carpinteiro, arqueiro, banqueiro) e o estoque de cada uma.
- Falas de NPC e nomes por cidade.
- Arte dos NPCs: na maioria, combinações de camadas do TCoM, sem modelo novo.

## Fase 4 — Itens, raridades e melhoria

Proposta (Rodrigo decide):

- **Raridade:** usar as 5 faixas do TCoM, que já funcionam e combinam com o estilo Diablo pedido:
  - **comum** (branco);
  - **refinado** (azul): 1 a 2 afixos;
  - **raro** (amarelo): 3 a 4 afixos e nome sorteado;
  - **conjunto** (verde): peças com bônus ao juntar;
  - **lendário/único** (laranja): item fixo com nome e efeito próprio.
- **Quantidades-alvo:**
  - 111 → ~250 bases;
  - ~60 afixos (prefixo e sufixo);
  - ~12 conjuntos de 3 a 5 peças;
  - ~40 únicos, um ou mais por chefe.
- **Melhoria, sem grind pesado:**
  - **Ofício:** quem tem a skill alta faz itens **excepcionais**.
  - **Materiais coloridos, como no UO:** cobre, bronze, prata, ouro e ferro-negro na mineração; couros e madeiras especiais. Cada material dá bônus próprios.
  - **Aprimorar:** gastar material para subir um item de faixa, com chance que cresce com a skill. Falhar gasta o material, mas não quebra o item.
  - **Reforjar afixos:** trocar 1 afixo por ouro e gema.
  - **Desgaste:** durabilidade leve, com conserto no ferreiro.

**Claude:** gerador de loot por faixa, afixos aplicados ao combate, ofício (fazer, aprimorar, reforjar), cor do nome por raridade e comparação de item no tooltip.

**Ludimus:** `affixes.json`, `sets.json`, `uniques.json`, mais bases em `base.json`, receitas de ofício (`data/crafting/*.json`), materiais e ícones.

## Fase 5 — Eventos, portais e chefes

**Claude**
- Agenda de eventos do mundo:
  - um chefe aparece num lugar, com aviso no global ("o Rei Formiga surgiu nas Dunas de Qasr");
  - o evento tem tempo limite;
  - os jogadores simulados e as guildas vão até lá, disputam o chefe e saqueiam;
  - há ranking de dano e recompensa.
- Invasões de cidade e guerra de guildas valendo território.
- **Portais:**
  - portais fixos entre as cidades, que mudam de destino com a fase da lua, como no UO;
  - runas para marcar um lugar e voltar a ele (magias de Marcar, Retornar e Portal);
  - portais de dungeon.

**Ludimus**
- `data/events.json`: chefe, lugar, horário ou intervalo, falas e recompensas.
- `data/portals.json`.
- Arte do portal e das runas.
- Os chefes: dragão alfa, Rei Formiga e os outros 16 do `bosses.json`.

## Fase 6 — Casas do jogador (como no After Light)

**Claude**
- **Escritura:** coloca uma casa pronta, das casas em camadas, onde couber, com prévia verde ou vermelha.
- **Modo construção, como no After Light:**
  - piso, paredes, portas, janelas, cercas, portão com tranca e móveis, tile a tile, com custo em material;
  - telhado gerado sozinho.
- Itens trancados na casa, baús seguros, lista de amigos, placa com o nome da casa e marcador no mapa.

**Ludimus**
- Kit modular de construção **por tile**, em madeira, pedra e enxaimel:
  - parede reta, quina, janela, porta e meia-parede (`front_low`);
  - piso e telhados modulares.
- Para casa feita pelo jogador, a peça por tile é o certo: as paredes são retas e simples, e a emenda que atrapalhou na cabana grande quase não aparece.
- Móveis como props soltos.

## Ordem sugerida

1. Combate e monstros.
2. Itens e loot. Os monstros já soltam loot com as faixas.
3. NPCs e comércio.
4. Segunda cidade e portal entre as duas. É o começo do mundo grande.
5. Eventos e chefes, com os dragões.
6. Casas do jogador.
7. Resto do mundo: biomas e cidades.
