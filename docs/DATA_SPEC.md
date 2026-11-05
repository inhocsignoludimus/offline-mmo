# Especificação de dados

**RASCUNHO – Claude revisa e aprova**

Proposta de JSON para as falas, os nomes, os itens e o lore do
MMO offline (nome do jogo ainda provisório). O Ludimus escreve o
conteúdo nas pastas `data/`. O Claude faz o motor ler. Até a
aprovação, estes esquemas não são contrato: uma amostra pequena
serve para a revisão; o dicionário inteiro espera o ok.

A licença desses textos ainda não foi escolhida. Não estão sob
CC-BY-SA 4.0. Ver `LICENSE`.

## Texto em dois idiomas

Proposta para todo texto que o jogador lê:

```json
{ "pt": "Texto em português do Brasil.", "en": "Text in English." }
```

As duas chaves são obrigatórias e não vazias. O jogo de origem
(TCoM) é escrito em português e traduz a tela para o inglês; aqui
a proposta é carregar os dois idiomas no próprio dado, porque
fala de jogador simulado e nome de guilda não passam bem por uma
tradução automática feita só na hora de desenhar.

Não há terceira língua neste esquema (`versao` sobe se houver).

Nome próprio de jogador simulado é a exceção: uma string só,
igual nos dois idiomas. Está na seção de nomes.

## `data/chat/`

Falas dos jogadores simulados, por personalidade. Não é diálogo
de missão. É o dicionário que o sistema sorteia quando um
simulado fala no chat.

Personalidades fechadas nesta proposta:

| Id | Quem fala |
| --- | --- |
| `novato` | Acabou de chegar, pede informação, erra o nome da coisa. |
| `farmador` | Fala de coleta, rota e estoque. |
| `pvper` | Fala de combate entre jogadores, caça e fama. |
| `troll` | Provoca, exagera, não sustenta a conversa. |
| `comerciante` | Compra, vende, anuncia preço. |
| `roleplayer` | Fala em personagem, trata o mundo como lugar. |

Contextos fechados nesta proposta. Uma frase pode ter mais de um.

| Id | Quando o sistema pode sorteá-la |
| --- | --- |
| `saudacao` | Encontro, chegada à cidade. |
| `despedida` | Saída. |
| `ocioso` | Parado, sem outro gancho. |
| `combate` | Luta em curso. |
| `morte` | Alguém caiu, ou o próprio simulado caiu. |
| `comercio` | Banca, preço, item à venda. |
| `guilda` | Tag, recrutamento, rivalidade de guilda. |
| `exploracao` | Caminho, bioma, descoberta. |
| `ajuda` | Pedido ou oferta de ajuda. |
| `provocacao` | Desafio, insulto leve, farpa. |

Arquivo proposto: `data/chat/frases.json`.

```json
{
  "versao": 1,
  "frases": [
    {
      "id": "novato.saudacao.01",
      "personalidade": "novato",
      "contextos": ["saudacao", "exploracao"],
      "peso": 1,
      "texto": {
        "pt": "Oi. É a primeira vez que eu saio da estrada principal.",
        "en": "Hi. This is my first time off the main road."
      }
    }
  ]
}
```

Regras da proposta:

- `id` único, `[a-z0-9.]+`, no padrão
  `<personalidade>.<contexto principal>.<número>`.
- `personalidade` é uma das seis.
- `contextos` tem pelo menos um id da tabela, sem repetir.
- `peso` é inteiro ≥ 1. O sistema sorteia com peso. Peso ausente
  não é permitido neste rascunho: quem escreve declara `1`.
- `texto.pt` e `texto.en` não vazios.
- Marcador opcional, escrito exatamente assim, para o motor
  substituir: `{nome}` (quem fala), `{guilda}` (sigla da guilda),
  `{bioma}` (nome do bioma no idioma da tela). Fora dessa lista,
  chaves `{...}` não entram na frase. Se o marcador estiver na
  frase, os dois idiomas o incluem.

O que este JSON não guarda: intervalo mínimo entre repetições,
memória do que já foi dito, relação entre dois simulados. Isso é
sistema, pasta do Claude.

## `data/names/`

Nomes prontos para o gerador de jogadores simulados e para as
guildas. A proposta é uma lista fechada que o sistema consome,
não um gerador de sílabas. Se o Claude quiser sílabas, isso é
outro arquivo e outra aprovação.

Arquivo proposto: `data/names/nomes.json`.

```json
{
  "versao": 1,
  "jogadores": [
    {
      "id": "aldric",
      "nome": "Aldric",
      "personalidade": "novato"
    }
  ],
  "guildas": [
    {
      "id": "ordem_da_lanterna",
      "nome": {
        "pt": "Ordem da Lanterna",
        "en": "Order of the Lantern"
      },
      "sigla": "ODL"
    }
  ]
}
```

Regras da proposta:

- `jogadores[].nome` é o nome na tela, uma string, sem tradução.
  Não leva a sigla da guilda dentro do nome.
- `jogadores[].personalidade` usa as mesmas seis ids do chat, para
  o sistema amarrar voz e nome. Um nome pode ser sorteado só
  dentro da própria personalidade.
- `guildas[].nome` é texto bilíngue.
- `guildas[].sigla` é a tag, de 2 a 4 caracteres, só `A`–`Z` e
  `0`–`9`, única no arquivo. Na tela o sistema pode mostrar
  `[ODL]`. O JSON não inclui os colchetes.
- `id` de jogador e de guilda: `[a-z0-9_]+`, único na sua lista.

Números de população (quantos simulados, quantas guildas no mapa)
não moram aqui.

## `data/items/`

Catálogo de linguagem dos itens: nome, descrição, prefixos,
sufixos, feitiços e reagentes. Sem dano, peso, preço ou duração.
Esses números são sistema; quando existirem, o Claude acrescenta
um bloco e sobe `versao`.

Arquivo proposto: `data/items/catalogo.json`, com cinco listas no
mesmo documento para o motor carregar um esquema só.

A ordem das palavras muda com o idioma ("espada afiada" e "sharp
longsword" não encaixam no mesmo molde). Por isso o afixo não
guarda um adjetivo solto: guarda um `modelo` com o marcador
`{base}`.

```json
{
  "versao": 1,
  "itens": [
    {
      "id": "espada_longa",
      "nome": { "pt": "espada longa", "en": "longsword" },
      "descricao": {
        "pt": "Lâmina reta, de uma mão, comum nas estradas.",
        "en": "A straight one-handed blade, common on the roads."
      }
    }
  ],
  "prefixos": [
    {
      "id": "afiada",
      "modelo": {
        "pt": "{base} afiada",
        "en": "sharp {base}"
      }
    }
  ],
  "sufixos": [
    {
      "id": "das_chamas",
      "modelo": {
        "pt": "{base} das chamas",
        "en": "{base} of flames"
      }
    }
  ],
  "feiticos": [
    {
      "id": "bola_de_fogo",
      "nome": { "pt": "Bola de fogo", "en": "Fireball" },
      "descricao": {
        "pt": "Um globo de fogo lançado à distância.",
        "en": "A globe of fire thrown from a distance."
      },
      "reagentes": ["enxofre"]
    }
  ],
  "reagentes": [
    {
      "id": "enxofre",
      "nome": { "pt": "Enxofre", "en": "Sulfurous ash" },
      "descricao": {
        "pt": "Pó amarelo, queimado nos círculos.",
        "en": "A yellow powder, burned in the circles."
      }
    }
  ]
}
```

Regras da proposta:

- Todo `id` é único dentro da sua lista, `[a-z0-9_]+`.
- `itens[].nome` é o nome comum, minúsculo no português quando for
  nome comum. O sistema capitaliza o início da linha se a janela
  precisar. Nome próprio de artefato, se um dia existir, vem com
  a capitalização já certa nos dois idiomas.
- `prefixos` e `sufixos` não sabem em quais itens podem cair. A
  compatibilidade (lâmina aceita "afiada", poção não aceita) é
  regra de sistema, ou um campo futuro que o Claude nomeia.
- O nome mágico é a aplicação do `modelo` do prefixo e depois do
  sufixo, cada um recebendo a frase já montada no lugar de
  `{base}`. Exemplo em português: modelo do prefixo sobre "espada
  longa" produz "espada longa afiada"; o sufixo sobre esse
  resultado produz "espada longa afiada das chamas". Os dois
  `modelo` precisam ser escritos para aceitar uma `{base}` que já
  contém outras palavras.
- `feiticos[].reagentes` lista ids que existem em `reagentes`.
  Pode ser lista vazia se o feitiço não gastar reagente. A
  quantidade gasta não está neste esquema.
- Um reagente não aponta de volta para os feitiços. O motor acha
  o uso pela lista do feitiço.
- Descrição é uma frase ou duas, sem regra de jogo escondida em
  número ("causa 12 de dano" não entra na descrição enquanto o
  dano não existir no sistema).

## `data/lore/`

Um bioma, dois arquivos Markdown irmãos: o corpo em português do
Brasil e a tradução em inglês. O índice é JSON para o motor achar
o arquivo sem varrer a pasta.

`data/lore/indice.json`:

```json
{
  "versao": 1,
  "biomas": [
    {
      "id": "deserto",
      "nome": { "pt": "Deserto", "en": "Desert" },
      "pt": "deserto.md",
      "en": "deserto.en.md"
    }
  ]
}
```

`data/lore/deserto.md`:

```markdown
# Deserto

Texto corrido em português do Brasil. Sem front matter: o índice
já tem o id e o nome. Parágrafos curtos, do ponto de vista de
quem anda no bioma. Sem estatística de jogo.
```

`data/lore/deserto.en.md` repete a mesma estrutura, com o título
em inglês (`# Desert`).

Regras da proposta:

- `id` igual ao id de pasta em `art/tiles/<bioma>/` e ao campo
  `bioma` do tileset. A lista dos oito ainda é a proposta de
  `docs/ART_SPEC.md` (`deserto`, `oasis`, `costa`, `colinas`,
  `pradaria`, `floresta`, `neve`, `pantano`). Nenhum `.md` entra
  antes de o Claude e o Rodrigo fecharem esses ids.
- O índice lista só bioma que já tem os dois arquivos.
- Markdown simples: título, parágrafos, ênfase. Sem HTML. Sem
  imagem (a arte mora em `art/`).
- O lore não contradiz uma fala de `data/chat/` de propósito. Os
  dois podem ter voz diferente: o lore é o lugar, a fala é a
  pessoa.

## O que fica de fora deste rascunho

Mapa (qual tile em qual coordenada), atributos de combate, preço,
receita de ofício e estado dos jogadores simulados. São sistema e
formato do jogo salvo, pastas do Claude, quando ele os especificar.

## Perguntas em aberto para o Claude

1. Um `frases.json` só, como nesta proposta, ou um arquivo por
   personalidade em `data/chat/<personalidade>.json`?
2. A lista de `contextos` fecha nestes dez, ou o motor precisa de
   outros ganchos (`cidade`, `masmorra`, `grupo`) já na versão 1?
3. `peso` no JSON é o bastante para o sorteio? O intervalo mínimo
   entre repetições e a regra de não repetir a última frase ficam
   só no sistema?
4. Os marcadores `{nome}`, `{guilda}` e `{bioma}` são os três que
   o motor vai substituir?
5. Nomes de jogador como lista fechada, sem gerador de sílabas,
   servem para a população simulada que o sistema pretende?
6. Sigla de guilda entre 2 e 4 caracteres `[A-Z0-9]` serve? A
   exibição com colchetes (`[ODL]`) é da UI?
7. Prefixos e sufixos via `modelo` com `{base}` resolvem a ordem
   das palavras em português e em inglês? O motor aplica prefixo
   e depois sufixo, como descrito?
8. Compatibilidade afixo×item mora no sistema ou volta para este
   catálogo num campo que o Claude nomeia?
9. Feitiços e reagentes no mesmo `catalogo.json`, ou arquivos
   irmãos `feiticos.json` e `reagentes.json`?
10. Lore em dois Markdown (`bioma.md` e `bioma.en.md`) mais
    `indice.json` serve, ou o motor prefere um JSON com o texto
    dentro?
11. `versao: 1` inteiro em cada arquivo é o sinal de quebra de
    esquema que o carregador deve exigir?
