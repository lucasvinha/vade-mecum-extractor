# Fixtures

Enxertos **reais** das fontes, de poucas páginas, nunca o arquivo inteiro (ver
`docs/PADRAO_OURO.md`). A fonte inteira e as extrações geradas ficam em `dados/` (ADR-005).

- `html/` — trechos do HTML do Planalto (ex.: `cp_enxertos.mht`), recortados em bytes e no
  charset original da fonte (windows-1252 no Planalto, H1).
- `pdf/` — PDFs pequenos recortados do original (ex.: `nscgj_art196.pdf`, duas páginas de questões).
- `snapshots/` — bases JSON geradas dos enxertos, versionadas para o teste de regressão.

Nome do arquivo = `<norma>_<trecho>.<ext>`. Registre a origem (arquivo e data de captura)
no topo do arquivo quando o formato permitir comentário.
