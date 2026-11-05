# art/blend/

Dono: **Ludimus**.

Fontes Blender do cenário, um diretório por bioma. O render é
Cycles, na CPU, com o mesmo sol em todos os arquivos: luz de cima
e da esquerda na imagem final.

O `.blend` entra no Git. Cópias `*.blend1` e semelhantes ficam de
fora (`.gitignore` na raiz).

A câmera ortográfica e os ângulos (cerca de 30° de elevação e 45°
de rotação, a confirmar no flare-game-art-src) estão propostos em
`docs/ART_SPEC.md`. Um `.blend` de referência, com a câmera já
aprovada, passa a ser o modelo dos outros quando o Claude fechar
o Euler.
