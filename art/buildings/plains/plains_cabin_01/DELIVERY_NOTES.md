# plains_cabin_01 — entrega LARGE LAYERS / house.json v2

## Entrega
Cabana Flare coerente em planta retangular **5 x 4**, sem recorte modular de paredes por tile. As seis camadas usam exatamente o mesmo canvas **1560 x 1040 px** e a mesma ancora **`[720, 760]`**, o centro do losango do tile `[0,0]` no master 192 x 96. `house.json` contem apenas o contrato version 2, com uma porta sul em `[2,3]`, colisao por tile e interior `[[1,1],[3,2]]`.

- `back.png`: paredes de fundo, piso interno e rodape fixo.
- `front.png`: paredes da frente em altura total, vao/janela e lintel, sem a folha da porta.
- `front_low.png`: mesma parede frontal cortada a **20%** da altura.
- `roof.png`: telhado original Flare com substrato opaco continuo.
- `door_closed.png` / `door_open.png`: apenas a folha, na mesma ancora da casa.
- `props/bed_r0..r3.png`, `chest_r0..r3.png`, `table_r0..r3.png`: mobiliario separado, 384 x 420 px, ancora de trabalho `[192,300]`.
- Editavel: `art/src/plains_cabin_01.blend`, com colecoes nomeadas por camada.
- Previas: `art/_preview/plains_cabin_01.png`, `plains_cabin_01_cutaway.png` e `plains_cabin_01_door_open.png`.

## Escala medida
Referencia TCoM stance direcao 4, sete camadas, ampliacao exata 2x nearest-neighbor: **167 px** de altura visivel. Folha `door_closed.png`: **234 px** de altura visivel. Razao **1.4012x**, minimo exigido 200.4 px: **APROVADO**. Parede nominal 2.22 unidades; folha 1.543 unidades mais o lintel. A medida usa bounding boxes alfa dos masters, nao estimativa de cena.

## Correcoes Claude
1. Telhado: os pontos amarelos foram eliminados com substrato continuo opaco sob as telhas. Verificacao final de componentes transparentes fechados: **0 pixels**. Pequenos desgastes entre telhas aparecem como madeira escura opaca, nao como ceu/luz.
2. Janela: recesso escuro, material nao emissivo; Lamp.002 interna zerada. Nenhuma iluminacao noturna embutida.
3. Porta: 234 px / personagem 167 px = 1.4012x. Frente conserva lintel acima da folha.

## Render e validacao
Blender 4.5.15 LTS, Cycles CPU, 64 amostras na casa, Standard, RGBA 8-bit, fundo transparente e camera ortografica 60/0/45. O HDR quebrado foi removido da arvore do mundo e substituido por preenchimento neutro; as luzes superiores esquerdas do Flare foram mantidas. Todos os masters de casa tem tamanho/modo identicos, props sem magenta, house.json parseado e previas compostas a partir das camadas reais.

Observacao de cutaway: a parede lateral ininterrupta original pertence a `back`; a frente com porta/janela e a que baixa para `front_low`. Isso preserva os meshes completos do Flare e evita fragmentar suas emendas. O bau usa materiais Cycles madeira/ferro validos, sem os antigos outputs magenta.

## Arquivo para CloudAgent
`/workspace/offline-mmo-art/plains_cabin_01_layers.tar.gz` contem a pasta version 2, o blend, as previas e estas notas. Nenhum push ao GitHub foi feito.

## Reproducao
`work/render_layers.py` monta/renderiza as camadas e props; `work/seal_roof_continuous.py` aplica o substrato final; `work/assemble_layers.py` monta as previas e grava `work/scale_report.json`; `work/validate_delivery.py` executa os asserts finais.
