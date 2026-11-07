# WORLD DESIGN — Aelória

Desenho do mundo contínuo para o Claude implementar **um módulo de cada vez**.
O Rodrigo aprova o merge. Este arquivo não é código de engine.

Prévia da grelha: `docs/world_layout.png`.

## Como ler

Cada módulo abaixo fecha sozinho: objetivo, arquivos, regras, e o que fica de fora.
O módulo 0 é a planta. Os outros não mudam a planta, só leem.

Não editar `engine/` nem `engine/dev_assets/`. Não regenerar `art/maps/mundo.txt`.

## Contrato que não muda

- Um jogador, com os outros aventureiros simulados. PvE. Sem dano entre jogadores.
- Guerra de guilda é corrida de dano em chefe (`contest: guild_damage`), não cerco de gente.
- Isométrico 2:1. Tile de jogo **96×48**. Master **192×96**. Os personagens são as camadas do TCoM por cima desse tile. Tileset em `art/tilesets/<bioma>/`, no `.txt` do Flare.
- Combate e magia nas teclas 1–9. Skills sobem com o uso, teto 100 cada e 700 no total. Casual: sem grind para morar, caçar ou abrir o mapa.
- Construção só com as peças de `data/building.json`. Custo em `logs`, `stone` ou `iron_ingot`. Árvore dá `logs`. Rocha dá `stone` e, por chance, minério (`data/gathering.json`).
- Oito biomas de `data/lore/biomes.json`. Cidades com os ids de lá.
- Inspiração estrutural apenas: hubs espalhados, bioma legível, estrada entre eles, perigo que cresce ao afastar da capital. Nomes, forma de continente e lugares de outros jogos não entram. O continente é **Aelória**.

## O que já existe e fica

A fatia jogável de hoje é `art/maps/mundo.txt`, **98×60** tiles.

| Zona | Papel | origin local | size | No mapa de 2048 |
| --- | --- | --- | --- | --- |
| `lochport` | Porto do Trigo. O mapa do Flare é o carimbo visual. O id da zona não muda. | `[0, 0]` | `[50, 60]` | tile `[768, 1408]`, célula `(12, 22)` |
| `bosque_da_vila` | Caça inicial a leste da vila. Chunks `entrada`, `cripta`, `clareira_do_fundo` com os mesmos `rect`. | `[50, 12]` | `[48, 36]` | tile `[818, 1420]` |

`data/zones.json` → `world.size` continua `[98, 60]`. O alvo de 2048×2048 está em `world.design_size` e em `data/world_layout.json`. A origem local dos chunks não se soma ao carimbo dentro do JSON antigo: quem for pintar o mapa grande usa `world_origin`.

Os quatro eventos do bosque (`chefe_goblin_entrada`, `guardiao_cripta_bosque`, `wyvern_clareira`, `serpe_de_fogo_clareira`) continuam nessa fatia.

---

## Módulo 0 — Planta do mapa

**Objetivo.** Carregar o mundo como uma grelha grossa e carimbar a fatia de hoje em cima, sem troca de área.

**Arquivos.** `data/world_layout.json`, `data/zones.json` (`world` e as duas zonas antigas), `docs/world_layout.png`.

**Planta.**

| | |
| --- | --- |
| Mapa | `mundo` |
| Células | 32×32 |
| Cada célula | 64×64 tiles |
| Mundo alvo | 2048×2048 tiles |
| Chunk de engine | 64×64, o mesmo tamanho da célula |
| Eixo | `(0,0)` no noroeste. Y cresce para o sul. |
| Tile de uma célula `(x, y)` | `(x*64, y*64)` |

Cada célula traz `biome`, `zone`, `level` (nível de monstro), `danger` (1–5), `build`, `invasion`, `road`, `river`, `water`, `resources`, `monsters`. Cidade, chefe, casa de guilda e vaga de simulado são campos opcionais.

`zone`: `city`, `frontier`, `open`, `dangerous`, `boss`.
Água é `biome: coast`, `water: true`, `build: nao`. Não é um nono bioma.

**Geografia, em uma frase.** O Mar de San Marco fecha o oeste e o sul. O Norte Gelado ocupa o topo. A serra de Pedralta corta o meio. O Bosque Sombrio fica a oeste da serra, as Planícies no miolo sul, o Miasma no delta, as Ruínas a leste da serra, Outremer na cunha sudeste, a Costa Levantina na orla.

**Rios** (`rivers[]`): Fiorde Pálido, Rio da Coroa (da serra, por Aurélia e Porto do Trigo, até Acre), Braço do Brejo, Uede de Qasr (seco, até o oásis).

**Estradas** (`roads[]`): Estrada do Gelo, Trilha das Folhas, Estrada Real, Caminho do Selo, Rota das Caravanas, Via Litorânea, e um ramal por vila. A lista de células já está no JSON.

**Masmorras.** Ainda não decididas. Se existirem, são exceção vertical: um tile de entrada, volta no mesmo tile. O mapa de cima não troca de área. Entradas candidatas: `cripta_familia`, `formigueiro` (Rei Formiga), boca da `mina_ferro`. A cripta do Bosque da Vila é superfície, já desenhada, não é essa exceção.

**Fora deste módulo.** Lote, invasão, loot raro, portais, pedidos do quadro. Só a planta e o carimbo.

**Pronto quando.** Dá para perguntar a célula de um tile, saber o bioma e a zona, e a fatia 98×60 continua nos mesmos `origin`/`rect`.

---

## Módulo 1 — Zoneamento de construção

**Objetivo.** Onde o jogador e os simulados podem erguer base, sem encher o mapa e sem punir quem sai.

**Arquivos.** `zones.json` → `regions[]` e o bloco `housing` de `world_layout.json`. A célula manda no detalhe; a região é o pacote (uma fronteira, um aberto, um chefe).

### O que cada zona permite

| zone | build | danger | invasion | Lote |
| --- | --- | --- | --- | --- |
| `city` | `proibido` | 1 | não | não |
| `frontier` | `fronteira` | 1 | não | sim, pequeno |
| `open` | `aberta` | 2–3 | sim | sim, médio, depois de abrir |
| `dangerous` | `aberta` | 4 | sim | sim, maior, depois do aberto |
| `boss` | `nao` | 5 | não | não. A arena é do chefe. |
| água | `nao` | 1 | não | não |
| Bosque da Vila | `nao` | 2 (clareira 3) | não | não. É caça desenhada. |

A faixa de fronteira é **uma célula** (64 tiles) em volta de cada povoado seguro, mais a estrada que esteja a até 2 células dele. Vila não amansa o bioma: dois passos depois da faixa, o nível segue a distância até a **capital**.

Outremer não tem região `outremer_dangerous`. A areia funda é a coluna de chefes na borda leste (`build: nao`). O pântano tem uma célula perigosa só; o resto do brejo é aberto invadível.

### Abrir terreno (qualquer uma das condições)

| Região | Como abre |
| --- | --- |
| Cidade, fronteira de Aurélia, fronteira de Porto do Trigo, Bosque da Vila, mar | já abertos |
| Outra fronteira | visitar a cidade uma vez (`unlock.kind: visit`) |
| `<bioma>_open` | limpar o `camp` **ou** qualquer skill de `skill_any` a 35 **ou** 15 de reputação na capital |
| `<bioma>_dangerous` | o aberto desse bioma já aberto, **e** então o camp fundo **ou** skill 50 **ou** 40 de reputação |

`skill_any` é espada, maça, machado, esgrima, arco, luta, magia ou táticas. Um caminho só já chega. O acampamento é um grupo curto, não um farm.

### Anti-saturação

Um personagem, **um lote** no mundo inteiro. Mudar de lugar devolve o lote na hora. A banca da cidade não gasta esse lote.

| Zona | Pegada máxima | Distância mínima entre lotes |
| --- | --- | --- |
| fronteira | 12×12 | 10 tiles |
| aberto | 20×20 | 16 |
| perigoso | 28×28 | 14 |

Sete dias sem o dono: aviso. Catorze: a casa vira entulho por 24 horas e o conteúdo vai para o **banco**. Simulado não decai enquanto o nome estiver em `data/names/players.json`.

### Onde os simulados moram

Há 100 nomes e 20 guildas. A grelha marca `sim_slots`: 99 vagas no total. A casa de guilda já está dentro desse número (`guild_hall` na mesma célula). Não criar casa além da soma de `sim_slots`.

A vaga fica na fronteira, de preferência na estrada. Duas vagas de aberto por bioma, na estrada, e uma de perigoso quando o bioma tem essa zona. Quem não tem vaga mora na cidade: usa banco, quadro e caça, sem casinha.

Casa de guilda fica **fora** do muro, na fronteira do povoado do tema. Três guildas de caos acampam no aberto ou no perigoso, não dentro da faixa segura: Corsários do Golfo na costa, Cabala do Osso e Skull Collectors nas ruínas. A tag está na célula.

**Fora deste módulo.** Composição da horda, preço de recurso raro, fase da lua.

**Pronto quando.** Não se constrói na cidade, na água, na arena e no Bosque da Vila. A fronteira de Porto do Trigo aceita um lote no primeiro minuto, sem invasão. Um segundo lote é recusado. Base abandonada devolve o baú ao banco.

---

## Módulo 2 — Biomas e ciclo de recurso

**Objetivo.** Cada bioma tem cara, caça e material. O comum fica perto da cidade. O raro só fora da zona segura.

**Arquivos.** `world_layout.json` (`rows`, `resource_rules`, `bosses`), `zones.json` `regions`, `gathering.json` (não mudar as receitas; a zona filtra).

### Biomas

Tile igual em todos: runtime 96×48, master 192×96, âncora no centro do losango. Pasta `art/tilesets/<id>/`.

| id | Nome | Onde na grelha | Perto da cidade | Raro, só em aberto / perigoso / chefe | Caça que já existe | Nível típico | Chefe (célula) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `plains` | Planícies Verdes | miolo sul | `logs`, `stone`, `iron_ore`, `copper_ore` | `silver_ore`, `leather_hide` | goblin, goblin_runner, goblin_spearman, goblin_elite, skeleton, skeleton_archer, wyvern | fronteira 1; aberto 4–10; perigoso 12–18 | Chefe Goblin `(10,19)` nv 6; Matilha Cinzenta `(17,23)` nv 8 |
| `forest` | Bosque Sombrio | oeste da serra | os mesmos | `silver_ore`, `oak_logs`, `leather_hide` | goblin, goblin_runner, goblin_shaman, goblin_elite, skeleton | igual, +0 | Aranha `(3,9)` nv 10; Coração `(4,7)` nv 14; Urso Negro `(11,16)` nv 12 |
| `mountains` | Pedra Alta | espinha norte–sul | os mesmos | `silver_ore`, `gold_ore`, `blackiron_ore`, `cedar_logs` | goblin, goblin_elite, hobgoblin, hobgoblin_archer, skeleton, skeleton_knight, boulder, minotaur, wyvern_air | +1 | Minotauro `(20,10)` nv 15; Elemental `(20,12)` nv 14; Serpe da Crista `(18,6)` nv 18 |
| `north` | Norte Gelado | faixa de cima | os mesmos | `silver_ore`, `fur_bundle`, `gold_ore` | frozen_zombie, antlion_freezer, skeleton_mage_ice, wyvern_air | +2 | Gigante do Gelo `(25,1)` nv 16; Jarl Morto `(7,1)` nv 14 |
| `swamp` | Pântano de Miasma | delta | os mesmos | `silver_ore`, `saltpeter`, `myrrh` | zombie_rotting, zombie, zombie_dark, antlion_hatchling, antlion, skeleton, wyvern_water | +1 | Senhor do Pântano `(24,24)` nv 14; Sombra `(24,21)` nv 12 |
| `outremer` | Outremer | cunha sudeste | os mesmos | `silver_ore`, `gold_ore`, `myrrh`, `incense` | antlion_hatchling, fire_ant, antlion_spitter, antlion, antlion_armored, skeleton, skeleton_mage_fire, wyvern_fire | +2. Sem faixa `dangerous`: a borda leste é chefe | Rei Formiga `(30,27)` nv 16; Serpe de Fogo `(30,25)` nv 16; Fantasma Cruzado `(30,22)` nv 12 |
| `ruins` | Ruínas Antigas | leste da serra | os mesmos | `silver_ore`, `blackiron_ore`, `gold_ore`, `quicklime` | skeleton, skeleton_knight, skeleton_mage, zombie, zombie_ghost, zombie_dark, necromancer, minotaur, boulder | +2 | Necromante Caduco `(26,10)` nv 16; Guardião da Cripta `(29,11)` nv 14 |
| `coast` | Costa Levantina | orla oeste e sul | os mesmos | `silver_ore`, `saltpeter`, `cedar_logs` | goblin, skeleton, skeleton_archer, wyvern_water, wyvern_air | +0 | Corsário Vermelho `(9,28)` nv 12; Caranguejo Colossal `(27,29)` nv 14 |

Cidade e fronteira **suprimem** todo raro, inclusive o `silver_ore` que `gathering.json` hoje sorteia em qualquer rocha. Rocha na faixa segura: `stone` + `iron_ore` + `copper_ore`. Prata e o que está em `rare_not_in_gathering_yet` só nascem com `zone` aberto, perigoso ou chefe.

O Bosque da Vila é aberto de nível 4, mas é caça inicial: recurso só comum, sem lote.

`wyrm_hide` entra no raro da célula de serpe (fogo, ar, crista), não no campo inteiro.

### O que a coleta já faz e o que é pedido

Já sai do nó: `logs`, `stone`, `iron_ore`, `copper_ore`, `silver_ore`.
Forja: 2 minérios → 1 lingote, como está.

Existem como item ou reagente e **ainda não têm nó**. Não inventar chance na rocha segura. São pedido de nó ou drop, só fora da faixa segura:

| id | Uso | Onde |
| --- | --- | --- |
| `gold_ore` | raro de serra, norte, deserto, ruína | nó de rocha fundo, ou drop |
| `blackiron_ore` | serra e ruína | idem |
| `oak_logs` | bosque fundo | árvore variante |
| `cedar_logs` | serra e costa | árvore variante |
| `fur_bundle` | norte | drop de caça |
| `leather_hide` | planície, bosque, matilha | drop |
| `wyrm_hide` | serpe | drop de chefe |
| `incense`, `myrrh` | deserto, fé, brejo | nó ou drop; o mago da cidade também vende reagente |
| `saltpeter`, `quicklime` | brejo, costa, ruína | nó ou drop |

### Chefes e o monstro que ainda falta

A célula de chefe usa só ids que já estão em `monsters.json`. O campo `requested_monster` é o modelo que a ficha de `bosses.json` pede e que **não** entra no spawn até existir.

| Chefe | Monstro da ficha | Na célula hoje | Pedido |
| --- | --- | --- | --- |
| Rei Formiga | `antlion` | antlion, antlion_armored, fire_ant | — |
| Serpe de Fogo | `wyvern_fire` | wyvern_fire, antlion_armored | — |
| Fantasma Cruzado | `crusader_ghost` | skeleton_knight, skeleton_mage_fire | `crusader_ghost` |
| Chefe Goblin | `goblin` | goblin_elite, goblin_spearman | — |
| Matilha Cinzenta | `wolf` | goblin_elite, skeleton | `wolf` |
| Aranha da Clareira | `spider_giant` | goblin_shaman, goblin | `spider_giant` |
| Coração do Bosque | `treant` | goblin_elite, skeleton | `treant` |
| Urso Negro | `dire_bear` | goblin_elite, goblin_shaman | `dire_bear` |
| Senhor do Pântano | `bog_lurker` | zombie_dark, antlion, wyvern_water | `bog_lurker` |
| Sombra do Miasma | `zombie_rotting` | zombie_dark, zombie | — (o corpo do evento é `zombie_dark`) |
| Minotauro do Pico | `minotaur` | minotaur, hobgoblin, boulder | — |
| Elemental de Pedra | `rock_elemental` | boulder, hobgoblin_archer | `rock_elemental` |
| Gigante do Gelo | `frost_giant` | antlion_freezer, skeleton_mage_ice, wyvern_air | `frost_giant` |
| Jarl Morto | `wight` | frozen_zombie, skeleton_mage_ice | `wight` |
| Necromante Caduco | `necromancer_apprentice` | necromancer, skeleton_mage | — |
| Guardião da Cripta | `skeleton_knight` | skeleton_knight_boss, skeleton_mage | — |
| Corsário Vermelho | `sea_raider` | skeleton_archer, goblin, wyvern_water | `sea_raider` |
| Caranguejo Colossal | `crab_giant` | wyvern_water, skeleton | `crab_giant` |
| Serpe da Crista | `wyvern_air_boss` (não está em `bosses.json`; é monstro) | wyvern_air_boss, wyvern_air | — |

Eventos novos, todos `guild_damage`, apontam para `place.region`: `rei_formiga_dunas`, `serpe_de_fogo_dunas`, `minotauro_passo`, `necromante_cidadela`, `guardiao_cripta_familiar`, `sombra_torre_miasma`, `chefe_goblin_seara`, `serpe_da_crista`. Os quatro do bosque não se movem.

Lista de ids de bioma que a lore cita e que ainda não são monstro: `jackal`, `hyena`, `sand_scorpion`, `ghazi`, `boar`, `bandit`, `plague_rat`, `croc`, `mosquito_swarm`, `mountain_goat`, `griffon`, `ice_wolf`, `shade`, `cultist`, `golem_ruin`, `siren`, `sharkman`, mais os da coluna Pedido. Não spawnar esses ids.

**Fora deste módulo.** Não ligar invasão nem mudar `gathering.json` além do filtro de zona descrito aqui.

**Pronto quando.** Na fronteira a rocha não dá prata. No aberto do bioma, o raro da tabela pode cair. Chefe sem modelo usa o stand-in e não um id vazio.

---

## Módulo 3 — Invasões de base

**Objetivo.** Horda do bioma bate em base que foi para longe. A fronteira nunca. Quem está offline não perde a casa.

**Arquivo.** `data/invasions.json`. Peças de `building.json`. Não há `tower_stone` ainda.

### Quando sai

- Zona `open` ou `dangerous`, `build: aberta`, pelo menos 4 peças de parede ou portão.
- Relógio: minutos **online do dono**, não o tempo em que ele está fora.
- Uma horda ativa por base. Não dispara no meio de um evento de chefe.
- Prefere a base mais longe da capital.
- Cidade, fronteira, água, arena e Bosque da Vila: nunca.
- Casa de simulado: racha, o chat usa `raid_call`, e o simulado conserta. Sem prejuízo de verdade.

### Tamanho, aviso, ritmo

| danger | zona | cabeças | aviso | a cada (min online) |
| --- | --- | --- | --- | --- |
| 2 | open | 4–7 | 180 s | 480–720 |
| 3 | open | 8–12 | 120 s | 240–420 |
| 4 | dangerous | 12–18 | 90 s | 150–240 |

A composição está em `hordes[]`, um perfil por bioma e danger, só com monstros que existem. `size` é o total; `composition` é o peso.

Alvos, nesta ordem: portão, porta, parede, cerca, baú que não seja o baú da casa. O marco do lote e o baú da casa são imunes. Banco e o que está equipado também.

### O que se perde

| danger | paredes no máximo | baús saqueados |
| --- | --- | --- |
| 2 | 20% | 0 |
| 3 | 30% | 1, e não é o baú da casa |
| 4 | 45% | 1, idem |

Offline: não saqueia baú. No máximo 15% das paredes racham. O `stone` ou os `logs` do conserto aparecem no banco.

### Defesa

| Peça | Existe | Função |
| --- | --- | --- |
| `fence_wood`, `wall_wood` | sim | atraso |
| `fence_stone`, `wall_stone` | sim | muro de verdade |
| `gate_iron`, `door_iron` | sim | gargalo |
| `tower_stone` | **não** | pedido. Enquanto não existe, uma sala 1×1 de `wall_stone` com `gate_iron` conta como reduto. |

Recompensa de quem defende (jogador presente): ouro baixo e um punhado de `logs`, `stone` e, no danger alto, `iron_ingot`, mais uma chance de `bandage`, `heal_potion`, `cure_potion` ou `greater_bandage`. Não é melhor que um chefe. Não vale farmar horda.

**Fora deste módulo.** Não mudar o zoneamento nem o catálogo de cidades.

**Pronto quando.** Base na fronteira de Porto do Trigo passa horas sem horda. Base no perigoso avisa, racha muro e para no teto. Logout no meio não esvazia o baú da casa.

---

## Módulo 4 — Cidades, portais e o elo com a base

**Objetivo.** Uma capital viva por bioma, serviços iguais no essencial, ofício diferente, e a base do jogador vendendo para essa cidade sem PvP.

**Arquivos.** `zones.json` regiões `city_*`, `data/portals.json`, `data/contracts.json`, `data/events.json`, `data/npcs/vendors.json` (só ler).

### Capitais

A capital de ruína **viva** é o Templo do Selo. A Cidadela Quebrada é o ninho do necromante, arena, não banco. Folhaverde, Lodoalto e Acre não têm `type: capital` na lore; mesmo assim são o hub do bioma (cidade, cidade e porto). Porto do Trigo não é a capital das planícies — Aurélia é — mas é o começo do jogo e por isso tem o serviço completo.

| Hub | Célula | Ofício | Serviço completo |
| --- | --- | --- | --- |
| Gelomarca | 20,3 | honra e caça | sim |
| Pedralta | 18,10 | forja e minério | sim |
| Folhaverde | 7,13 | madeira, erva, arco | sim |
| Aurélia | 14,18 | coroa e comércio | sim |
| Porto do Trigo | 12,22 | porto fluvial, grão. Carimbo Lochport. | sim |
| Lodoalto | 22,20 | peixe, veneno, reagente | sim |
| Templo do Selo | 27,14 | fé e selo contra a necromancia | sim |
| Aelia Sancta | 28,23 | fé e caravana | sim |
| San Marco | 5,27 | arsenal e porto da república | sim |
| Acre Livre | 16,27 | bazar | sim |

Serviço completo: `bank`, `healer`, `trainer` (sobe skill até 30, como no roadmap), `contract_board`, `moon_portal`, `stall_market`, e os nove vendedores de `vendors.json` (`ferreiro`, `alfaiate`, `mago`, `alquimista`, `acougueiro`, `estalajadeiro`, `carpinteiro`, `arqueiro`, `banqueiro`).

Vilas, castelos e mosteiros são cidade (`build: proibido`) com um recorte: curandeiro, um ofício, às vezes treinador. O quadro de contratos e o banco ficam nas dez linhas de cima. Mina do Ferro não tem banco; o lingote desce a estrada até Pedralta ou segue de envio.

Cova do Corsário, Torre Miasma e Cidadela Quebrada não são cidades seguras.

### Portais da lua

Só `kind: moon`, no mesmo mapa. Três destinos por pedra. A rede das oito capitais é simétrica: cada par que aparece numa pedra aparece na volta.

Pedras locais, para a viagem curta não depender da fase: Porto do Trigo, Acre Livre, Castelo Montgisard, Oásis de Qasr, Mosteiro do Musgo. As fases estão em `portals.json`. A estrada continua o caminho que não muda com a lua.

### Quadro, envio e banca

`data/contracts.json`. Cada pedido é um item só, quantidade até 30, ouro modesto, 1 a 3 de reputação naquela cidade. Não cumprir não pune. Dá para mandar da mochila ou do baú da base.

O envio chega. Cidade mais próxima da base: sem taxa. Outra cidade: 5 a 15 de ouro. Nada se perde no caminho, mesmo offline.

A banca é o `deed_market_stall`, uma por jogador, na praça `stall_market`, e **não** conta como lote. Cidade não é invadida, então o estoque da banca é seguro. Simulados compram e vendem; o chat WTS/WTB fala de item que está mesmo na banca.

Reputação é um número por cidade. 15 abre o caminho de reputação do aberto; 40, o do perigoso. Oito entregas de 2 já passam dos 15. O acampamento e a skill continuam sendo os outros caminhos.

**Fora deste módulo.** Não rebalancear horda nem mover a fatia Lochport.

**Pronto quando.** As oito capitais e Porto do Trigo e Acre têm banco, curandeiro, treinador e portal. Um lote na fronteira entrega `logs` no quadro de Aurélia e o ouro cai. A banca não deixa o jogador sem o lote de moradia.

---

## Pedidos novos (não spawnar, não craftar ainda)

Monstros: ver a coluna Pedido do módulo 2 e a lista extra no fim desse módulo. Arte em `data/lore/NEW_MONSTER_IDS.md`.

Peça: `tower_stone` (e, se couber no mesmo kit, a variante de madeira). Até lá o reduto é sala de pedra com portão de ferro.

Nós: `gold_ore`, `blackiron_ore`, `oak_logs`, `cedar_logs` fora da zona segura. O resto raro pode ser drop.

Masmorra: não decidida. Não abrir segundo mapa.

## Validar

```
python3 build/check_data.py
```

Confere id de item, monstro, chefe, cidade, skill, peça, tag de guilda, cobertura das 1024 células, fatia Lochport/Bosque intacta, raro fora da zona segura, invasão só em aberto/perigoso, portal `moon` com cidade que existe, e a ausência de topónimos de outros MMOs nesses JSON.

A grelha é gerada por `python3 build/gen_world_layout.py`. O JSON é o que a engine lê. `contracts.json` é escrito à mão e o gerador não mexe nele.
