# build/

Dono: **Claude**.

Scripts para reduzir os masters 2× (192×96) ao runtime 96×48,
montar os atlas e gerar os três alvos de publicação: página web,
APK Android e pacote da itch.io. A escala está em `docs/ART_SPEC.md`.

O que esta pasta versiona é o script. APK, zip e a pasta de saída
(`dist/`, `out/`) ficam de fora do Git (`.gitignore` na raiz).

Só o Claude edita esta pasta. Pull request; o Rodrigo aprova.

## Efeitos e ferramentas (depois do import_dev_assets)
- `python3 build/import_powers.py --flare <flare-game>` — sprites de magia/habilidade do Flare (CC-BY-SA) → `engine/dev_assets/powers/`
- `python3 build/make_tools.py` — cria `m/cajado`, `m/bastao` e `m/picareta` a partir da lança e do machado do TCoM. Rodar de novo sempre que `import_dev_assets.py` regravar `layers.json`.
- `python3 build/make_icons.py --flare <flare-game>` — ícones dos itens que faltavam (TCoM + Flare, com tinta por material) acrescentados em `engine/dev_assets/tcom/icons.webp`.
- `SAMP=16 python3.11 art/src/gen_houses_bpy.py [ids]` — casas por parâmetro no Blender (pip install bpy no Python 3.11): enxaimel, pedra, toras com neve, adobe, capela. Depois `python3 build/import_art.py --flare <flare> --only houses`.
