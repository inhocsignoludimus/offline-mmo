# ART_SPEC — offline-mmo (título provisório)

Versão 1 — revisada pela engine (Claude). Rascunho original: Ludimus.
Validado em teste: mapas do Flare (`black_oak_city`, `family_crypt`, `fort_amir`) renderizados na escala abaixo, com os personagens do TCoM por cima. As portas ficaram um pouco mais altas que o personagem, e as paredes da cripta passaram da cabeça.

---

## 1. Grade e escala

| Item | Valor |
|---|---|
| Projeção | isométrica 2:1 (dimétrica), igual ao Flare e ao TCoM |
| **Tile do jogo (runtime)** | **96 × 48 px** (losango do chão) |
| **Tile no PNG master** | **192 × 96 px**, ou seja, 2× o runtime. É o tamanho que os scripts do `flare-game-art-src` já geram |
| Entrega | só os masters (2×). O build da engine reduz para 1× e gera os atlas |
| Personagem humano (1,8 m) | ~78 px de altura no runtime, ~156 px no master |
| Porta | altura útil ≥ 1,15× o personagem, cerca de 180 px no master |
| Parede inteira | cerca de 1,6–2× o personagem, de 250 a 310 px de altura visível no master |

> Por que 96×48: o tile de 64×32 do TCoM deixava casas e portas pequenas demais em volta dos personagens. O cenário do Flare a ½ da resolução nativa casa com os personagens do TCoM a 1:1.

## 2. Câmera e render (Blender)

* Use **os scripts e a câmera dos `.blend` do `flare-game-art-src` sem mudar ângulo nem escala**. Assim tudo bate com o Flare e com os personagens.
  * Câmera **ortográfica**, rotação **X = 60°, Y = 0°, Z = 45°** (elevação de 30°, que dá a proporção 2:1).
  * 1 tile do Flare = 1 quadrado de chão do `.blend`, renderizado a 192×96 no master.
* **Cycles** (sem GPU), view transform **Standard** (não use Filmic nem AgX: muda contraste e cor em relação ao Flare e ao TCoM).
* Luz: a mesma do Flare, vinda **de cima, pela esquerda** (noroeste da tela). Sol suave, mais um preenchimento fraco. Sem neblina e sem bloom.
* Fundo **transparente** (Film → Transparent). PNG **RGBA 8 bits, alfa direto**, sem halo escuro nas bordas.
* Paleta: deserto/Terra Santa puxando para o calcário quente do TCoM. Os outros biomas seguem o Flare. **Não** escureça a arte na renderização: noite, tochas e masmorra escura são feitas pela iluminação dinâmica da engine.
* Sombras de contato e AO leves podem ir na peça. Sombra longa de construção vai numa **peça separada** (`*_shadow.png`), para a engine escurecê-la ou apagá-la à noite.

## 3. Âncora e definição dos tiles

Formato: **o `.txt` de tileset do Flare**, que a engine já lê:

```
[tileset]
img=art/tilesets/plains/plains_walls.png
tile=ID,x,y,w,h,ox,oy
```

* `x,y,w,h`: recorte no PNG.
* `ox,oy`: a distância do canto superior esquerdo do recorte até o **centro do losango de chão** onde a peça está. É a âncora.
* Mantenha a numeração de IDs estável depois de entregue. Para criar peças novas, acrescente IDs no fim; nunca reaproveite um ID.
* Mapas: **Tiled**, salvos no formato `.txt` do Flare, como os de `flare-game/mods/*/maps` (camadas `background`, `object` e `collision`). Os arquivos `.tmx` editáveis vão junto, em `art/maps/src/`.

## 4. Direções

* Personagens e monstros: **8 direções**, como no TCoM (comigo).
* Móveis e objetos que dá para girar (cama, mesa, baú, cadeira, estante, bancada): **4 rotações** (frentes para N, L, S e O), porque o jogador decora a casa girando os itens, como no UO.
* Portas: 2 orientações (parede que corre NE–SO e NO–SE), cada uma **aberta e fechada**.

## 5. Construções em que se entra (obrigatório)

Toda construção precisa poder ser aberta. Cada casa é renderizada **inteira** no Blender e entregue em **camadas grandes**, não em peças por tile. Todas as camadas da casa têm **o mesmo tamanho de imagem e a mesma âncora**: `ox, oy` é o ponto, dentro da imagem, onde fica o centro do losango do tile de origem da casa (o canto norte da planta, `[0,0]` no `house.json`), na escala do master (192×96).

| Camada | Arquivo | O que é |
|---|---|---|
| `back` | `back.png` | paredes do fundo (as faces voltadas para longe da câmera), chão interno e tudo o que é fixo por dentro |
| `front` | `front.png` | as paredes da frente inteiras (as duas faces voltadas para a câmera), **sem** a porta |
| `front_low` | `front_low.png` | as mesmas paredes da frente cortadas no rodapé (cerca de 20% da altura). A engine troca `front` por esta quando o jogador está dentro |
| `roof` | `roof.png` | o telhado, sozinho. A engine esconde quando o jogador entra |
| `door_closed` / `door_open` | `door_closed.png`, `door_open.png` | só a folha da porta, com a mesma âncora da casa |
| `props` | `props/<id>_r0..r3.png` | móveis soltos, um por tile, em 4 rotações (âncora própria, como qualquer objeto) |

* O telhado não pode ter frestas: um pixel de céu ou de luz interna atravessando as telhas aparece como brilho no jogo. Janela sem luz acesa por dentro (a luz da casa é da engine).
* A porta tem de ter **pelo menos 1,2× a altura do personagem** (personagem de pé ≈ 140 px no master, 70 px no jogo). Parede da frente da mesma altura da porta mais o lintel.
* A colisão continua **por tile** no `house.json` (ver o `DATA_SCHEMA.md`): parede ocupa o tile inteiro, como no Flare e no After Light.
* **Profundidade:** a engine ordena as camadas pela planta da casa (o retângulo `size`), não por um valor fixo. Quem está fora do lado da câmera (x maior que a parede da frente leste ou y maior que a parede da frente sul) é desenhado por cima de `front`; quem está dentro ou atrás fica por baixo. Por isso a casa é **retangular** em planta. Casas em L ou com anexo vêm como duas casas encostadas, cada uma com o seu `house.json`.
* Os materiais seguem: madeira (cabana), enxaimel (`medieval_building_tiles`), pedra (castelo e muralha), arenito (Terra Santa) e barro/adobe (vilas do deserto).

## 6. Nomes e pastas

```
art/
  tilesets/<bioma>/<set>.png + <set>.txt
  buildings/<bioma>/<id>/  (floor, wall, wall_low, door, roof, props, house.json)
  props/<categoria>/<id>.png (+ _r0.._r3 para as rotações)
  maps/<id>.txt  (+ src/<id>.tmx)
  src/<...>.blend (só os .blend novos ou modificados; os do Flare ficam como referência)
```

* Nomes em `snake_case`, minúsculos, sem acento.
* Biomas: `outremer` (deserto), `plains`, `forest`, `swamp`, `mountains`, `north`, `ruins`, `coast`.

## 7. Checklist de entrega por peça

1. O personagem de referência (o herói do Flare, ou uma camada do TCoM) foi colocado ao lado no Blender para conferir a escala.
2. Fundo transparente, sem halo.
3. A âncora `ox,oy` aponta para o centro do losango.
4. Construções: tem `wall_low` e `roof` separados.
5. Linha no `CREDITOS.txt` (autor, licença, link e o que foi modificado).
6. Uma prévia de conferência: `art/_preview/<id>.png`, com a peça montada e um personagem do TCoM ao lado.

## 8. Licenças

* A arte derivada do Flare fica em **CC-BY-SA 3.0** (pode usar versões posteriores). Texturas CC0 (ambientCG, Poly Haven, `flare-game-art-src`) e modelos CC0 (Quaternius, KayKit) podem entrar, sempre registrados no `CREDITOS.txt`.
* Não usar nada marcado como "non-commercial", nem nenhum material do Ultima Online ou da EA.
