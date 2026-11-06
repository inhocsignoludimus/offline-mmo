# Monstros — lote 1

Entrega de arte no mesmo desenho dos PRs do dragão (#21 filhote,
#22 jovem): `art/monsters/<id>/<id>.png` + `<id>.json` no formato
CAMADAS_ANIM, `art/_preview/<id>.png` e `art/src/<id>.blend`.

Os créditos (autor, título, URL, licença e o que mudou) estão no
`CREDITOS.txt` da raiz. Não há `CREDITOS_snippet.txt` por criatura.

## Quadros (8 direções: SW W NW N NE E SE S)

| id | escala vs humano de 140 px | stance | run | swing | hit | die | atlas |
|---|---|---|---|---|---|---|---|
| rat | 0,3× (≈42 px) | 6 back_forth | 8 looped | 7 play_once | 3 play_once | 8 play_once | 862×2728 |
| boar | 0,6× (≈84 px) | 6 | 8 | 7 | 3 | 8 | 1459×4512 |
| giant_spider | 0,7× (≈98 px) | 6 | 8 | 7 | 3 | 8 | 1658×3927 |
| scorpion | 0,5× (≈70 px) | 6 | 8 | 7 | 3 | 8 | 985×3314 |

Sem `cast` e sem `special`.

## Compromissos

- **boar:** a fonte só tinha walk e attack. Idle (respiração), hit (recuo) e die (tombo de lado) foram animados à mão.
- **giant_spider e scorpion:** o hit é um recuo animado à mão. Os sprites saem em **CC-BY-SA 4.0** (compartilha-igual), porque os modelos de GuieA_7 são CC-BY-SA 4.0.
- **scorpion:** o osso do olho foi reduzido a 0,55×.
- **giant_spider:** a altura opaca do corpo fica cerca de 88 px contra o alvo de 98 px (pernas finas abaixo do limiar de alfa). O recorte geral permanece perto do alvo.

## Fontes `.blend`

Cada mesh em `art/src/` fica abaixo de 10 MB e entra no repositório, como o `.blend` do filhote no PR #21:

| arquivo | tamanho |
|---|---|
| `art/src/rat.blend` | 6,7 MB |
| `art/src/boar.blend` | 2,4 MB |
| `art/src/scorpion.blend` | 1,5 MB |
| `art/src/giant_spider.blend` | 1,1 MB |

## Look

Câmera e luz do teste (mundo verde-escuro, sol 2.6, Standard, Cycles, shadow catcher). Visual escuro, sóbrio, no espírito de um MMO isométrico. Sem assets do Ultima Online ou da EA.
