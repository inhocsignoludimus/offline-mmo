# BUILDINGS.md — catálogo de construções

A vila do protótipo usa uma cabana só, repetida, e por isso o lugar parece falso. A regra daqui em diante: **nenhuma cidade usa o mesmo modelo duas vezes lado a lado**. Uma cidade pequena tem pelo menos 5 modelos diferentes.

A variedade sai de três coisas, da mais barata para a mais cara:

1. **Arredores (engine + props):** cada casa ganha um conjunto de props do lado de fora, escolhido pelo ofício dela: barris, caixotes, lenha empilhada, carroça, horta, varal, placa, bigorna, poço, cerca. A mesma cabana com uma horta e um varal parece outra casa que a mesma cabana com lenha e um machado.
2. **Variações do mesmo modelo (Blender):** troca de material e de detalhe no mesmo `.blend`: cor da madeira, telha de madeira, palha ou ardósia, chaminé sim ou não, janela com veneziana, alpendre. Cada variação é uma casa com o seu `house.json` (`plains_cabin_01a`, `01b`...).
3. **Modelos novos (Blender):** plantas, tamanhos e silhuetas diferentes. Os itens abaixo.

## Primeira rodada: planície (`plains`)

| id | Planta (tiles) | O que é | Base |
|---|---|---|---|
| `plains_cabin_01` | 5×4 | cabana de troncos, 1 cômodo | `cabin.blend` do Flare (em andamento) |
| `plains_cabin_02` | 4×4 | cabana menor, telhado de palha, alpendre | variação da 01 |
| `plains_house_01` | 6×5 | casa de enxaimel, 2 andares (o 2º só por fora) | `medieval_building_tiles.blend` do Flare |
| `plains_house_02` | 7×4 | casa de pedra na base e enxaimel em cima, chaminé | `medieval_building_tiles.blend` |
| `plains_smithy_01` | 6×5 | ferraria com metade aberta (alpendre com forja) | modelo novo |
| `plains_tavern_01` | 8×6 | taverna, telhado alto, placa pendurada | `medieval_building_tiles.blend` |
| `plains_barn_01` | 7×5 | celeiro/armazém, portão largo | modelo novo |
| `plains_chapel_01` | 5×8 | capela de pedra com sineira | modelo novo |

Isso dá uma vila com o banco, a ferraria, a taverna, a capela, as casas e o celeiro, todos diferentes.

## Outros biomas (rodadas seguintes)

- **`outremer`:** casas de pedra caiada com terraço plano, arenito, tendas redondas e listradas, muralha com torres. O TCoM já tem esse kit em Blender (o kit de paredes de Acre e Jafa, as tendas e as carroças), então dá para re-renderizar na escala nova (tile 96×48) em vez de modelar do zero.
- **`north`:** casa longa de madeira com telhado de grama.
- **`swamp`:** palafita.
- **`coast`:** casa de pescador e armazém do porto.
- **`ruins`:** as mesmas casas da planície, quebradas: sem telhado e com as paredes no meio da altura.

## Regras para todo modelo

- Seguem a seção 5 do `ART_SPEC.md`: camadas `back`, `front`, `front_low`, `roof` e `door_*`, com uma âncora só.
- Porta com pelo menos 1,2× a altura do personagem.
- Silhueta diferente vale mais que textura diferente: varie a altura do telhado, a planta e o que sai da casa (chaminé, alpendre, torre).
- Mesma luz, câmera e paleta da cabana `plains_cabin_01`, para a vila não parecer feita de pedaços de jogos diferentes.

## O que a engine faz (Claude)

- Coloca os props de arredores por ofício da casa, a partir de uma lista no `house.json` ou de conjuntos prontos.
- Varia de leve o tom do `roof` de cada casa (±8% de brilho e matiz), para o mesmo modelo não ficar idêntico ao vizinho.
- Na geração do mapa, nunca põe o mesmo `id` em duas casas vizinhas.
