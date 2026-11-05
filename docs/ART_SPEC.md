# Especificação de arte

**RASCUNHO – Claude revisa e aprova**

Proposta de valores para a arte isométrica do MMO offline (nome do
jogo ainda provisório). Os números abaixo são proposta de trabalho,
não contrato do motor. O que o TCoM e o Flare já fazem está citado
como fato; o que este jogo deve adotar está marcado como proposta.
As perguntas que travam a produção em escala estão no final.

Dono da pasta de arte: Ludimus. Dono do motor que vai ler essa arte:
Claude. Aprovação do pull request: Rodrigo.

## Projeção e tile na tela

Proposta:

- Projeção isométrica de jogo, razão **2:1**. O losango do chão é
  duas vezes mais largo do que alto. Não é a isométrica de
  engenharia (ângulos de 30° entre eixos iguais), porque essa não
  cai em pixel inteiro.
- Tile de chão na tela: **64×32 pixels**.
- É o mesmo par de constantes de A Cruz de Montgisard, em
  `js/jogo.js`:

  - `TILE_LARGURA = 64`
  - `TILE_ALTURA = 32`

Referência do motor:

https://github.com/inhocsignoludimus/The-Cross-of-Montgisard

## Escala em metros

No TCoM o mundo é medido em metros e desenhado em pixels. Fato do
código atual de `js/jogo.js`:

- `METROS_POR_TILE = 2` (cada tile são 2×2 metros de chão);
- `PX_POR_METRO = (TILE_LARGURA / 2) / (METROS_POR_TILE * √½)`,
  cerca de 22,6 px por metro na horizontal da tela;
- `PX_ALTURA_POR_METRO = PX_POR_METRO * cos(30°)`, cerca de 19,6 px
  por metro de altura. A altura aparece um pouco achatada, de
  propósito.

Proposta: herdar esses três números. Um mapa de cerca de 2000×2000
tiles, a 2 m o tile, tem cerca de 4 km de lado.

Pergunta para o Claude: o mapa deste jogo continua em 2×2 metros
por tile?

## Resolução de render

O chão do Flare em resolução alta ocupa **192×96** pixels, isto é,
**3×** o tile de tela 64×32. O repositório
[flare-game-art-src](https://github.com/flareteam/flare-game-art-src)
descreve as fontes em `art_src_hd` como um alvo de 3× em relação à
arte original. Exemplo real de chão no tileset de pradaria do
flare-game (`mods/fantasycore/tilesetdefs/tileset_grassland.txt`):

```
tile=16,1061,2698,192,96,96,48
```

Largura 192, altura 96, deslocamento (offset) 96, 48.

No TCoM a folha também nasce maior do que o pixel da tela. O campo
`escala` de `CENARIO_DADOS` vale `2.0` nas áreas atuais. Na hora de
desenhar, a fatia é dividida por essa escala. Há ainda a folha
`_m`, pela metade, para o celular (`FONTE_CENARIO = 0.5`): as
coordenadas do JSON continuam as da folha cheia.

Proposta:

- O Ludimus entrega o PNG na resolução de render **3×** (chão
  192×96; objeto alto no mesmo fator, com a altura que o modelo
  pedir).
- O JSON do tileset grava `escala: 3`, no mesmo papel do `escala`
  do `CENARIO_DADOS`: o motor divide largura, altura e âncora por
  3 e cai em 64×32 na tela.
- O arquivo solto não é reduzido no Blender. Reduzir no export
  jogaria fora o detalhe se uma tela de alta densidade passar a
  usar a folha cheia.

Perguntas para o Claude: quem reduz (motor na hora de desenhar, ou
um passo de empacote em `build/`)? Qual filtro (vizinho mais
próximo, bilinear, outro)? O jogo precisa do par folha cheia /
folha `_m`, como o TCoM?

O chão deste mapa é um carimbo repetível por bioma (2000×2000
tiles). É outra organização em relação ao chão do TCoM, que usa
imagens grandes `chao_i_j.webp` já achatadas por área. Proposta:
tile de chão repetível, mais peças de transição entre biomas.
Confirmar com o Claude antes de fechar o formato da folha.

Sangria: o artigo do Clint Bellanger sobre tiles isométricos no
Blender recomenda o losango um fio maior do que o quadro, para não
abrir fresta entre tiles vizinhos. Proposta: 1 pixel de sangria
além do losango 192×96, combinada com o motor para o Claude dizer
se o tileset inclui essa margem ou se o motor sobrepõe os tiles.

Artigo (câmera e sangria, não é o arquivo do repositório HD):

https://clintbellanger.net/articles/isometric_tiles/

## Âncora

Proposta: a âncora é o **vértice sul do losango** (bottom-center of
the diamond). Em um chão 192×96 que preenche o quadro, esse ponto
é o pixel **(96, 96)**, meio da borda de baixo. A coordenada é
sempre medida do canto superior esquerdo do PNG.

```
           norte
        +---------+
       /           \
      /             \
     +     centro    +
      \             /
       \           /
        +----S----+
           sul
     S = bottom-center do losango
```

Em um prop alto (árvore, muro, tenda) a âncora continua nesse
ponto do **losango do chão onde o objeto pisa**, não no centro da
imagem e não no rodapé do PNG se o sprite passar do vértice sul.
Os pixels acima do losango são o volume do objeto.

Há dois fatos que não batem com essa proposta. Por isso a âncora
está em aberto para o Claude, no fim do documento:

- No TCoM, o comentário de `js/jogo.js` diz que a âncora é o
  **centro do tile no chão**, em pixels da folha. O desenho faz
  `cx - ancoraX / escala`, `cy - ancoraY / escala`. A tupla da
  fatia é `[folha, x, y, largura, altura, ancoraX, ancoraY]`.
- No chão 192×96 do Flare, o offset publicado é **(96, 48)**, o
  centro da imagem, que num losango justo é o centro do losango,
  não o vértice sul.

Para um chão que preenche o quadro, os dois pontos se calculam
sem renderizar de novo: centro `(largura/2, altura/2)`, vértice
sul `(largura/2, altura)`. Trocar a convenção, nesse caso, é
trocar número no JSON. Para props, a âncora precisa ser marcada no
render, então a convenção tem de estar fechada antes da leva
grande.

## Câmera

Proposta, **a confirmar contra a câmera dos `.blend` em
flare-game-art-src**:

- Câmera **ortográfica** (sem perspectiva: o que está longe não
  encolhe).
- Ângulos no espírito do Flare: cerca de **30° de elevação** e
  **45° de rotação** em torno da vertical.

O que dá para citar sem abrir o `.blend` deste projeto:

- Clint Bellanger, em "Isometric Tiles Introduction" e "Isometric
  Tiles in Blender", descreve a isométrica de jogo como girar a
  câmera 45° para o lado e cerca de 30° para baixo. No Blender,
  a rotação que ele publica para o losango 2:1 é Euler
  **X = 60°, Y = 0°, Z = 45°**. A isométrica de engenharia seria
  cerca de X = 54,736°, e as arestas não caem no pixel 2:1.
  https://clintbellanger.net/articles/isometric_intro/
  https://clintbellanger.net/articles/isometric_tiles/
- O README de flare-game-art-src diz que os `.blend` em
  `art_src_hd` renderizam com **EEVEE** e miram 3×. Este jogo
  renderiza com **Cycles na CPU**. A câmera pode ser a mesma e o
  motor de render outro; isso só vale se alguém abrir o arquivo
  e ler a rotação.

Ninguém, neste rascunho, abriu um `.blend` do flare-game-art-src
para copiar o Euler. Até o Claude confirmar, o Ludimus não trata
(60, 0, 45) como número já aprovado. Trata como a hipótese que
produz o losango 2:1 no artigo do autor do tileset.

Escala ortográfica, distância e resolução de saída precisam fazer
o plano de 2×2 metros cair no quadro 192×96 (mais a sangria, se
ela for aprovada). Esses dois números (escala ortográfica e
posição da câmera) ficam anotados no `.blend` de referência quando
a câmera for confirmada, para os biomas não divergirem.

## Luz e render

Proposta:

- Renderizador: **Blender Cycles**, dispositivo **CPU**. Sem
  depender de GPU. O mesmo em todos os biomas.
- Um sol só, estável, vindo de **cima e da esquerda** na imagem
  final, de modo que a sombra caia para baixo e para a direita.
  A direção não muda de bioma para bioma: tiles de biomas
  diferentes precisam sentar lado a lado sem dois sóis.
- Uma luz de preenchimento fraca, ou o fundo do mundo um pouco
  acima de zero, para a face oposta ao sol não ir a preto. A
  intensidade é pergunta aberta; a existência de um preenchimento
  único e compartilhado é a proposta.
- Saída: **PNG com alfa**. Alfa reto (não premultiplicado), em
  sRGB. O fundo do render é transparente.
- O TCoM já registra, no `CREDITOS.txt` dele, personagens
  renderizados com Cycles no Blender 5. Proposta: a mesma versão
  maior do Blender para o cenário, assim que o Claude e o Rodrigo
  confirmarem o número exato.

A paleta (areia, grama, pedra, neve) **pode diferir por bioma**.
Isso o Rodrigo já decidiu. A direção do sol não entra nessa
liberdade.

## Pastas, formato e nome

| Caminho | Conteúdo |
| --- | --- |
| `art/tiles/<bioma>/` | Chão, borda, água e transição. |
| `art/props/<bioma>/` | Objeto ou criatura que ocupa o tile e sobe acima do losango. |
| `art/blend/<bioma>/` | `.blend` de origem. O `.blend1` fica de fora do Git (`.gitignore`). |
| `art/tilesets/` | JSON do tileset e, depois, a folha empacotada se o Claude quiser folha. |

Nome de arquivo, só ASCII, minúsculas, underscores, sem acento:

```
art/tiles/<bioma>/<tipo>_<nome>_<variante>.png
```

Exemplos da proposta (os ids de bioma ainda não estão fechados):

```
art/tiles/deserto/chao_areia_00.png
art/tiles/deserto/transicao_areia_pradaria_02.png
art/props/pradaria/arvore_carvalho_00.png
art/props/pradaria/criatura_guarda_s_00.png
```

- `<bioma>` é o id da pasta, não o nome bonito.
- `<tipo>` descreve a classe da peça: `chao`, `transicao`,
  `agua`, `parede`, `arvore`, `criatura`, `tenda`, e a lista
  cresce no JSON em vez de crescer numa lista informal.
- `<nome>` distingue peças do mesmo tipo.
- `<variante>` é dois dígitos, `_00`, `_01`, para variação visual
  do mesmo tile. Em animação, o quadro também é dois dígitos, e a
  direção entra antes dele: `<tipo>_<nome>_<direcao>_<quadro>.png`.

O PNG solto é a entrega do Ludimus. A folha (`folha0.webp` e
irmãs, no estilo do TCoM) é um passo posterior. Proposta: o
Claude empacota, porque o empacote depende do motor; o JSON tem
de nascer já com os campos da fatia, mesmo enquanto `fatia` ainda
for nula.

## Tileset

Três formatos possíveis. A recomendação é o terceiro.

### 1. Texto do Flare

Uma linha por tile:

```
tile=<id>,<x>,<y>,<largura>,<altura>,<offsetX>,<offsetY>
```

É o formato de `tileset_grassland.txt`. Lê-se fácil e já descreve
a folha do Flare. O offset do Flare é o dialeto do motor Flare, e
a animação mora em outra linha (`animation=`). Este jogo não vai
embarcar o motor Flare. Adotar o `.txt` obrigaria o Claude a
traduzir offset e animação para a tupla do `CENARIO_DADOS`.

### 2. Tiled

Mapa e tileset em `.tmx` / `.tsx`. Serve como editor para pintar
o mapa de 2000×2000, se o Claude quiser essa ferramenta. Não serve
como formato que o motor lê: o TCoM não lê TMX, e o JSON abaixo
já carrega o recorte. Um export Tiled pode nascer depois, a partir
do JSON, sem ser a fonte de verdade.

### 3. JSON próprio, compatível com `CENARIO_DADOS` (recomendado)

O motor que vamos reutilizar já consome, por área:

```json
{
  "escala": 2.0,
  "folhas": 1,
  "fatias": {
    "coluna,linha": [0, 0, 0, 241, 454, 100.0, 439.0]
  }
}
```

A tupla é `[folha, x, y, largura, altura, ancoraX, ancoraY]`.

Proposta: um arquivo por bioma em `art/tilesets/<bioma>.json`,
com a lista de PNG que o Ludimus entrega e, no mesmo objeto, o
campo `fatia` nessa ordem. Enquanto a folha não existe, `fatia`
é `null` e `arquivo` aponta para o PNG. Quando a folha existir,
`fatia` deixa de ser nula e o motor lê a tupla como já lê o
TCoM. Um gerador pode, a partir deste JSON, emitir o objeto
`CENARIO_DADOS` sem reinterpretar offset do Flare.

Exemplo de chão 3× com a âncora proposta no vértice sul. Os
números de âncora mudam se o Claude escolher o centro do tile:

```json
{
  "versao": 1,
  "bioma": "pradaria",
  "projecao": "isometrica-2-1",
  "tile_tela": { "largura": 64, "altura": 32 },
  "metros_por_tile": 2,
  "escala": 3,
  "ancora_convencao": "vertice-sul",
  "folhas": [],
  "tiles": [
    {
      "id": "chao_grama_00",
      "tipo": "chao",
      "arquivo": "art/tiles/pradaria/chao_grama_00.png",
      "largura": 192,
      "altura": 96,
      "ancoraX": 96,
      "ancoraY": 96,
      "fatia": null
    }
  ]
}
```

`fatia`, quando a folha existir, repete largura, altura e âncora
na ordem do TCoM. `folhas` continua na raiz do arquivo; `fatia`
continua dentro do tile:

```json
{
  "folhas": ["art/tilesets/pradaria/folha0.webp"],
  "tiles": [
    {
      "id": "chao_grama_00",
      "fatia": [0, 0, 0, 192, 96, 96, 96]
    }
  ]
}
```

Quadro de animação, no mesmo arquivo, com direção e ordem do
quadro. A âncora do exemplo é ilustrativa: num prop ela não é a
base da imagem inteira, é o ponto do losango combinado com o
Claude.

```json
{
  "id": "criatura_guarda_s_00",
  "tipo": "criatura",
  "arquivo": "art/props/pradaria/criatura_guarda_s_00.png",
  "direcao": "s",
  "quadro": 0,
  "largura": 192,
  "altura": 288,
  "ancoraX": 96,
  "ancoraY": 260,
  "fatia": null
}
```

Campos obrigatórios na proposta: `versao`, `bioma`, `projecao`,
`tile_tela`, `metros_por_tile`, `escala`, `ancora_convencao`,
`folhas`, `tiles`. Dentro de cada tile: `id`, `tipo`, `arquivo`,
`largura`, `altura`, `ancoraX`, `ancoraY`, `fatia`. Direção e
quadro só entram quando a peça é animada.

`id` é único dentro do bioma, em minúsculas, `[a-z0-9_]+`.

## Direções

Proposta para criatura, projétil e objeto animado: **8 direções**.

É o número do Ultima Online e o número da maior parte das
animações de personagem do Flare. Dezesseis direções cabem no
mesmo esquema de nome (`<direcao>` mais longo) se o Claude quiser
a volta mais macia; custam o dobro de quadros.

Ids propostos, no sentido horário a partir do norte:

| Id | Direção na tela |
| --- | --- |
| `n` | norte |
| `ne` | nordeste |
| `e` | leste |
| `se` | sudeste |
| `s` | sul |
| `so` | sudoeste |
| `o` | oeste |
| `no` | noroeste |

`e` aqui é leste; `o` é oeste. A ordem dos índices numéricos, se
o motor preferir número em vez de sigla, fica com o Claude. O
arquivo leva a sigla, que não depende dessa ordem.

O tempo de cada quadro (milissegundos) é dado do motor, não do
PNG. Se precisar viver no JSON, entra num campo `duracao_ms` que
o Claude ainda não pediu. Não está no exemplo de propósito.

## Biomas e paleta

O mapa tem 8 biomas. A mistura pedida é deserto da Terra Santa
com biomas medievais no estilo do Flare. A paleta de cada bioma
pode ser a sua. A luz, não.

Proposta de ids de pasta, para o Claude e o Rodrigo fecharem
antes de criar as pastas e o lore:

| Id | Papel na proposta |
| --- | --- |
| `deserto` | Dunas e solo árido. |
| `oasis` | Água, palmeira, cultivo irrigado. |
| `costa` | Litoral árido. |
| `colinas` | Relevo seco e pedra. |
| `pradaria` | Grassland no estilo do Flare. |
| `floresta` | Bosque temperado. |
| `neve` | Planície nevada, no espírito do snowplains do rubberduck. |
| `pantano` | Solo úmido, em contraste com o deserto. |

Cavernas e masmorras não estão nessa lista. Se forem bioma, um
dos oito acima sai. Se forem interior (outro mapa, ou um andar),
não gastam um id de bioma do mapa de superfície. Pergunta aberta.

Transição entre biomas vizinhos é tile de `art/tiles/`, com os
dois ids no nome (`transicao_areia_pradaria_00`), no bioma de
quem "recebe" a borda ou numa pasta `art/tiles/transicao/`. A
segunda opção foge de `<bioma>` no caminho. Proposta: o arquivo
mora no bioma de origem e o JSON marca `bioma_destino`. A
confirmar.

## Perguntas em aberto para o Claude

1. Âncora: vértice sul do losango, como nesta proposta, ou o
   centro do tile no chão, como o comentário de `js/jogo.js` do
   TCoM e o offset `(96, 48)` do chão 192×96 do Flare?
2. A câmera dos `.blend` em `art_src_hd` (flare-game-art-src) é a
   Euler `(60°, 0°, 45°)` do artigo do Clint Bellanger? Confirmar
   no arquivo. Este projeto renderiza com Cycles na CPU; aqueles
   arquivos usam EEVEE. A câmera pode ser copiada mesmo assim?
3. Entregar PNG 3× com `escala: 3`, ou gravar já em 64×32? Quem
   reduz, e com qual filtro? Precisamos da folha `_m`?
4. Chão em tile repetível (esta proposta) ou folha grande já
   achatada, como `chao_i_j` no TCoM?
5. O JSON desta página, com `fatia` nula até o empacote e tupla
   `[folha, x, y, largura, altura, ancoraX, ancoraY]` depois,
   serve como fonte de verdade? Algum campo a mais é obrigatório
   para o motor (`chao` com `x0`, `y0`, `tam`, `nx`, `ny`, por
   exemplo)?
6. Oito ou dezesseis direções? As siglas `n, ne, e, se, s, so,
   o, no` servem, ou o motor quer índice numérico com uma ordem
   já usada no TCoM?
7. Azimute e altura exatos do sol, e a intensidade do
   preenchimento, para a sombra coincidir com a arte do Flare que
   viermos a adaptar. A paleta por bioma já está decidida pelo
   Rodrigo; a direção da luz, nesta proposta, é uma só.
8. Os oito ids de bioma desta página fecham? Caverna é bioma de
   superfície ou interior?
9. PNG com alfa reto, sRGB, é o que o motor espera?
10. Folha final em `.webp`, como o TCoM, ou o motor lê o PNG
    solto na primeira versão jogável?
11. `METROS_POR_TILE = 2` permanece, inclusive para o mapa de
    cerca de 2000×2000?
12. A sangria de 1 pixel entra no PNG e no `largura`/`altura` do
    JSON, ou o motor sobrepõe os tiles e o quadro fica justo em
    192×96?
13. Versão do Blender: fixar a mesma do TCoM (Cycles no Blender 5,
    segundo o `CREDITOS.txt` daquele jogo)?
