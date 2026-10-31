# vade-mecum-extractor

Parser genérico que converte legislação bruta (HTML do Planalto, `.mht`, PDF com texto) em base
JSON hierárquica e gera recortes de artigos; o JSON é o contrato lido pela Etapa 2.

**Comece por [docs/README.md](../docs/README.md)**: stack, contratos, testes, lint, commits,
mapa do código e `§ Parâmetros do processo`. Este arquivo só guarda o que é regra inviolável e o
que é específico do Claude.

## Regras invioláveis
- **Parser genérico (ADR-002):** nada de `if norma == "cp"`; diferença entre normas vai para o
  perfil `.toml`.
- **Nenhuma perda silenciosa (RNF04):** todo texto entra na árvore ou no relatório, com `origem`.
- **Determinismo (RNF03):** JSON com chaves ordenadas, sem timestamp dentro de `artigos`.
- **Windows sem WSL (RNF02):** `pathlib` e `encoding="utf-8"` explícito em toda leitura e escrita.
- Texto legal é **literal** (inclusive "alguem", "conseqüências"); não se corrige ortografia.
- **Regex só muda com teste**, com o caso real que motivou a mudança.
- **Snapshot de regressão** só é regravado com a justificativa no corpo da mensagem do commit.
- Regra citada em código, teste ou commit usa o ID (`# H15`, `test_a2_...`, `ADR-001`).
- Siga o [PADRAO_OURO](../docs/PADRAO_OURO.md).

## Comandos
- Testes: `pytest` (só aceite: `pytest -m aceite`)
- Lint: `ruff check . && ruff format --check .`
- Rodar local: `python -m vademecum extrair --fonte <fonte> --perfil cp --saida dados/cp/base.json`

## Fluxo
Mudança que vale mais de um commit começa por `/spec`, nunca pela implementação inteira.
`/spec` → `/fase` (uma por vez; para e espera o commit) → `/revisao` → `/regressao`, quando
couber. Módulo herdado ou antes de refatorar: `/auditoria <módulo>`.
Defeito (teste vermelho, traceback, achado de revisão ou regressão):
skill `depuracao-sistematica`, causa raiz antes da correção.
Contradição com regra de negócio ou ADR: registre em PENDENCIAS e pergunte; não decida sozinho.
Roteiros em [docs/processo/](../docs/processo/README.md).

## Específico do Claude
- **Commit e push ao fim de cada fase, sem pedir autorização:** com os portões verdes, o Claude
  faz `git commit -F` com a mensagem do FASE §4 e `git push` na branch da sessão. Neste projeto,
  isso prevalece sobre o FASE §4.5 e §5.1 ("Não commita e não faz push"). Seguem valendo o
  §5.2 (não avança para a fase seguinte) e o §5.4 (não reescreve histórico).
- `.claude/CLAUDE.md` e `.claude/commands/` são versionados; os comandos só carregam os roteiros
  de `docs/processo/`. `settings.local.json` é pessoal e fica fora do git.
