# Fechamento — paperdoll armas / escudos
2026-11-07 · America/Sao_Paulo (UTC-3)

## Pode publicar agora (importação pelo cloud)
- Somente `production/art/paperdoll/{m,f}/buckler_fixed.png`: 2 PNGs novos, 300×480 RGBA. Broquel estático na mão esquerda, sem problema de empunhadura visível porque a face do escudo cobre a mão.
- Acrescentar `production/CREDITOS_PRODUCTION_snippet.txt`; Flare derivado CC-BY-SA 3.0, não CC0. Prova, créditos e fontes acompanham o pacote.
- Preservar os antigos longsword, wooden_shield e kite_shield; esta entrega não substitui nem reaprova esses arquivos. Preservar fase 1, batch2v4 e seus arquivos históricos. A publicação das quatro peças batch2v4 segue o pacote e a aprovação próprios; o hauberk continua adiado.

## NÃO publicar como arma acabada
- shortsword, dagger, hand_axe, mace, longbow, staff, wand: **WIP**, somente em `wip/art/_wip/paperdoll_weapons_batch1/`.
- Não importar as armas do antigo `paperdoll_weapons_batch1_REVIEW.tar.gz` nos caminhos runtime. Esse arquivo foi preservado como histórico, não é o pacote de produção deste fechamento.
- Não havia um processo de correção rodando. O último estado real continuava com mãos abertas. A comparação limitada entre o recorte antigo de mão aberta e os cabos 3D integrais mostrou que corrigir só a oclusão não fecha os dedos: a empunhadura convincente ainda NÃO está resolvida. Reconstituí os cabos completos no namespace WIP para não obrigar a reconstruir pixels depois.
- Fontes 3D, materiais, UVs, renders, referências abertas e metadados foram organizados em WIP. Nenhum placeholder de arma novo e nenhuma alteração no corpo aprovado.

## Todos os 9 IDs de escudo estão mapeados, sem fingir nove artes prontas
`SHIELD_VISUAL_MAPPING.json` / `.md` enumera cada ID do base.json.
- Exatos: wooden_shield e kite_shield já existentes; buckler novo.
- Seis referências aproximadas, DESATIVADAS por padrão: heater_shield → kite; round_shield → wooden; crusader_shield → kite sem cruz; tower_shield → kite (não tem a altura correta); oval_shield → wooden (não tem formato oval próprio); pavise → wooden (não tem silhueta/apoio de pavise).
- O JSON é manifesto de handoff, NÃO configuração aplicada à engine. Não ativar silenciosamente esses seis fallbacks nem anunciar que têm arte própria. Os IDs não foram alterados.

## O que falta na engine e na arte para as sete armas
1. O compositor precisa suportar substituição LOCAL da mão aberta por uma pose fechada, sem substituir o PNG do corpo inteiro. Uma máscara sozinha não transforma palma aberta em punho: **faltam patches de mão fechada desenhados/renderizados**.
2. Ordem sugerida: base/roupas → arma traseira/cabo integral → patch de mão/dedos fechados → detalhes frontais quando necessários → escudo. Suprimir os dedos abertos originais na região de substituição para evitar mãos duplicadas.
3. Escolher apenas UM patch: pele correspondente à skin, OU a luva equipada. Luvas de couro/malha/placa precisam da própria pose fechada; não pintar pele em cima de luva. Os arquivos `OPEN_*REFERENCE*` são guias da pose antiga, NÃO máscaras finais de empunhadura.
4. Após patches reais: validar âncoras m `[48,237]` / f `[35,216]`, testar todos os cabos/guardas com corpo e luvas em 150×240, cores e alpha. As sete armas continuam WIP até esse teste.
5. Arco/cajado atuais são exibição neutra; não representam tiro, cast ou apoio de duas mãos. Uma pose nova de duas mãos precisa de arte/integração próprias; não deformar automaticamente a base aprovada.

## Validações realizadas e limites
Camadas originais: Cycles 96 + denoiser, CPU 3 threads. Broquel conferido m/f em 300×480 e 150×240. Arquivo REVIEW anterior e 236 arquivos-fonte/anteriores conferidos por SHA-256, sem alterações. Nenhuma alteração de repo/engine, clone, push, PR, merge, publicação ou teste na engine foi feita por este executor. O cloud recebe pacote production separado para importar o que é utilizável, sem novo ciclo de revisão cosmética.
