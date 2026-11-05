# art/props/

Dono: **Ludimus**.

Objetos e criaturas que ocupam o tile e passam da altura do
losango: árvore, muro, tenda, guarda. PNG com alfa, um diretório
por bioma.

```
art/props/<bioma>/<tipo>_<nome>_<variante>.png
```

Peça animada leva direção e quadro no nome
(`criatura_guarda_s_00.png`). A proposta é de 8 direções; 16
continua em aberto em `docs/ART_SPEC.md`.

A âncora é o ponto do losango onde o objeto pisa, não o rodapé
da imagem. O ponto exato (vértice sul ou centro do tile) o Claude
fecha.
