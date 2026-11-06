# data/chat/

Dono: **Ludimus**.

Falas dos jogadores simulados.

- `personalities.json` — `novato`, `farmador`, `pvper` (agora focado em PvE/boss),
  `comerciante`, `roleplayer`, `troll`, com as probabilidades
  `typo`, `caps` e `emoji`.
- `lines.json` — frases com personalidade (`p`), contexto (`ctx`)
  e canal (`ch`).

Quem sorteia e aplica erro de digitação é a engine, em
`systems/`. O esquema está em `docs/DATA_SCHEMA.md`.

Sem PvP: contextos `pk_warning` e `kill_other` removidos; novos `hunt`, `boss_spawn`, `loot_drop`, `trade`.
