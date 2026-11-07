# Paperdoll — fase 1, correção v5 e armadura v3

Dono: **Ludimus** (`art/`). Contrato: `docs/ART_SPEC.md`, seção 10.
Tela **300×480** RGBA, fundo transparente, a mesma âncora em todas as camadas.
A engine reduz para 150×240. Isto é paperdoll estático. Não é sprite de combate.

Rodrigo aprovou as prévias pendentes em 2026-11-06: fullplate e templário v3, luvas em cinza médio, botas e manto de tecido do Blender v5 («Estão legais, pode seguir com tudo»).

A v5 entrou primeiro. A armadura v3 entrou depois e **substitui** `plate_{legs,boots,torso,arms,gloves}_fixed.png`. O pacote de entrega não foi copiado para a raiz: QA e folhas ficam em `art/paperdoll/qa/`.

## Ordem de pintura

corpo → cabelo → pernas → pés → tronco → braços → mãos → pescoço → manto → cabeça → arma → escudo

Para um item com as duas camadas, a engine pinta `<id>.png` (recebe hue) e depois `<id>_fixed.png` (não recebe hue).

## Camadas

35 arquivos por sexo.

| Arquivo | Papel | Licença |
|---|---|---|
| `body`, `skin_01`…`03` | Corpo com roupa de baixo, pés descalços. A engine usa **ou** `body` **ou** uma pele. | CC0 |
| `hair_01`…`06` | Cabelo, por cima do corpo | CC0 |
| `cloth_pants`, `leather_boots`, `cloth_shirt`, `studded_leather`, `leather_gloves`, `leather_hood`, `wool_cloak` | Pano e couro que recebem cor, cinza puro | CC0 |
| `studded_leather_fixed`, `wool_cloak_fixed` | Rebites e fecho | CC0 |
| `loriga_fixed`, `chain_greaves_fixed`, `nasal_helm_fixed`, `longsword_fixed`, `kite_shield_fixed`, `wooden_shield_fixed` | Malha, arma, madeira | CC0 |
| `plate_{legs,boots,torso,arms,gloves,gorget}_fixed` | Placa por slot | CC-BY-SA 3.0 |
| `greathelm_fixed` | Elmo fechado arredondado, mapeado no id `greathelm` | CC-BY-SA 3.0 |
| `templar_cuirass` | Sobreveste de lã, hueable | CC-BY-SA 3.0 |
| `templar_cuirass_fixed` | Aço visível e cruz vermelha, sem hue | CC-BY-SA 3.0 |
| `templar_mantle` | Manto hueable, já recortado atrás do corpo | CC-BY-SA 3.0 |

Os nomes de item são os `id` de `data/items/base.json`. Corpo, pele e cabelo seguem a seção 10, não um id de item.

## Mapa dos itens

O esquema não tem campo de paperdoll. O arquivo é o contrato: `art/paperdoll/<m|f>/<id>.png` e, quando existe, `<id>_fixed.png`. `sprite_layer` continua sendo a camada isométrica do TCoM. Este trabalho não troca `sprite_layer` e não cria sprite de combate.

| Camada | id | slot |
|---|---|---|
| `plate_legs_fixed` | `plate_legs` | legs |
| `plate_boots_fixed` | `plate_boots` | feet |
| `plate_torso_fixed` | `plate_torso` | torso |
| `plate_arms_fixed` | `plate_arms` | arms |
| `plate_gloves_fixed` | `plate_gloves` | hands |
| `plate_gorget_fixed` | `plate_gorget` | neck |
| `greathelm_fixed` | `greathelm` | head |
| `templar_cuirass` + `templar_cuirass_fixed` | `templar_cuirass` | torso |
| `templar_mantle` | `templar_mantle` (item novo) | cloak |

`templar_cuirass` e `plate_torso` são **alternativas do mesmo slot torso**. A couraça templária já traz o aço dela em `templar_cuirass_fixed`. Não desenhar os dois ao mesmo tempo.

`templar_mantle` não existia. Entrou em `data/items/base.json` como roupa, slot `cloak`, material `cloth`, `sprite_layer` null. Não está em loot nem em vendedor. O ícone `templar_mantle` ainda não está na folha; a engine cai no genérico.

`greathelm_fixed` é aproximação: elmo fechado, arredondado, com viseira e frestas. Não é um grande elmo de topo chato. `face_helm` continua sem paperdoll.

O cordão do manto está na sobreveste (`templar_cuirass`), não em `templar_mantle`.

## O que a v5 mudou (CC0)

- `body` e `skin_*`: só roupa de baixo. Sem túnica longa, sem calça até o tornozelo, sem bota.
- Sete hueables repintados no cinza do corpo. Luvas e botas revistas. Manto v5 é simulação de tecido no Blender 4.5 (80 quadros, Cycles 128 amostras, holdout do `body.png`), reduzido de 600×960 para 300×480.
- Luvas depois clareadas por curva monotônica. Média sRGB dos pixels com alpha > 128: **0,560** nos dois sexos. Alpha idêntico ao de antes. Registro em `qa/QA_gloves_medium.json`. `qa/QA_V5.json` é a passagem do manto, anterior a esse clareamento.

## Armadura v3 (CC-BY-SA 3.0)

Derivada de `plate_armor.blend` do herói e da heroína do Flare (Clint Bellanger). A variante templária usa como referência visual `assets/personagens/m/armadura_templario.webp` de A Cruz de Montgisard. Crédito fechado em `CREDITOS.txt`. Não misturar com o bloco CC0.

Intenção do templário: manto atrás, corpo, placa, sobreveste, cruz. Na ordem da engine isso vira: pernas, pés, `templar_cuirass` + `templar_cuirass_fixed`, braços, mãos, gorjal, `templar_mantle`, elmo.

## QA desta importação (fora da engine)

Conferido aqui com Pillow, empilhando os PNGs. **Não** é teste da engine, nem do hue dela, nem do downscale dela.

- 70 peças (35 por sexo), todas 300×480 RGBA.
- Hueables com croma 0 (`max(R,G,B)−min(R,G,B)`), inclusive `templar_cuirass` e `templar_mantle`. A cruz em `templar_cuirass_fixed` é vermelha de propósito.
- Empilhar na ordem da engine reproduz `art/_preview/paperdoll_{m,f}_fullplate_v3.png` e `paperdoll_{m,f}_templar_v3.png` com diferença 0 nos pixels opacos. Por isso nenhuma máscara foi editada: fechar uma fresta mudaria a prévia aprovada.
- `templar_mantle` não tem pixel com alpha > 40 por cima do `body` (já vem recortado). Na ordem da engine, a interseção com `plate_arms_fixed` é 86 px (m) e 48 px (f), na borda da espaldeira. Com a armadura completa a prévia aprovada já inclui isso. Sem a placa nos braços, ou com outra ordem, essa borda precisa de teste.
- Redução local para 150×240 (filtro box, não o da engine): cruz, manto e elmo continuam legíveis. Frestas escuras na virilha, no cotovelo interno e sob a espaldeira continuam visíveis. O `qa/QA_armor_v3.json` mede o stack contra o render conjunto anterior (média absoluta ~2,6–3,2/255, cerca de 900–1200 px acima de 48). Essas frestas são sombra de contato de slot renderizado sozinho. Ficam como limitação.
- `paperdoll_{m,f}_plate.png` do pacote v5 ainda era o composto antigo (malha furada, luvas brancas, pés descalços). Foi refeito com os slots v3 sobre o fundo `(18,16,20)` das outras prévias de conjunto. A prévia aprovada, transparente, continua em `paperdoll_{m,f}_fullplate_v3.png`.

## Limitações que continuam

- Paperdoll estático. Nada foi validado na engine, a 150×240 nem com hue de verdade.
- Um slot sozinho fica limpo. A sombra de contato entre peças não é a do render conjunto.
- Espaldeira larga contra o manto: a borda citada acima.
- `greathelm` é aproximação, documentada na tabela.
- Salto da bota v4, na vista frontal, é um bloco escuro saindo pela sola.
- O manto de lã v5 usa proxy de profundidade do alpha, não anatomia 3D. A barra é pouco assimétrica. O forro só aparece nas backfaces.
- Hueables de roupa (menos o manto v5) são pintura 2D sobre o corpo, mais limpa que o corpo pintado.
- `body.png` tem frestas transparentes na costura da roupa de baixo.
- Cabelos podem ter resto de recorte de fundo.
- Itens ainda sem paperdoll: `REMAINING.txt` (152 ids). `greathelm`, `plate_gorget` e `templar_cuirass` saíram dessa lista porque entraram na v3.

## Onde está o quê

- Peças: `art/paperdoll/m/`, `art/paperdoll/f/`
- Prévias de conjunto: `art/_preview/paperdoll_*.png`
- QA numérico: `art/paperdoll/qa/QA_V5.json`, `QA_gloves_medium.json`, `QA_armor_v3.json`
- Folhas da v5 aprovada (manto, luvas, conjunto): `art/paperdoll/qa/paperdoll_fix_sheet_v5.png`, `paperdoll_fix_sheet_v5_full.png`, `paperdoll_v5_cloak_closeup.png`, `paperdoll_gloves_medium_hue_range.png`
- Folhas da armadura: `art/_preview/paperdoll_fullplate_v3_compare.png`, `paperdoll_fullplate_v3_detail.png`, `paperdoll_armor_v3_slot_split_qa.png`
