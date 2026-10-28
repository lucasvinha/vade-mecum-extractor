# vade-mecum-extractor

Parser genérico que converte legislação bruta (HTML do Planalto, `.mht`, PDF com texto) em
**base JSON hierárquica** (artigo › parágrafo › inciso › alínea) e gera **recortes** de artigos.
Etapa 1 de 2; a Etapa 2 (material de estudo) está fora de escopo.

## Documentos de referência (leia antes de mudar comportamento)

| Arquivo | Papel |
|---|---|
| `docs/Prd.md` | Requisitos: **o quê** e **por quê**. Fonte da verdade para regras (H*, P*, RF*, D*, A*). |
| `docs/README.md` | README técnico: **como** (stack, contratos, mapa do código, Parâmetros do processo). |
| `docs/PENDENCIAS.md` | Fila e fases de implementação (1–7), com critério de saída. |
| `docs/processo/REVISAO.md` | Roteiro de `/revisao`. |
| `docs/processo/SPEC.md`, `FASE.md` | Roteiros de `/spec` e `/fase`. |

Ao citar uma regra em código, teste ou commit, use o ID do PRD (ex.: `# H15`, `test_a2_...`).

## Comandos

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # ambiente
ruff check . && ruff format --check .                 # lint + formato (obrigatório antes de commit)
pytest                                                # testes
pytest -m aceite                                      # só casos de aceite A1–A14
python -m vademecum extrair --fonte <fonte> --perfil cp --saida dados/cp/base.json
python -m vademecum recortar --base dados/cp/base.json --artigos "121-130" --saida dados/cp/r.json
```

## Estrutura

```
src/vademecum/        pacote (layout src); módulos listados em docs/README.md § Mapa do código
  fontes/             leitores HTML/PDF → list[LinhaFonte]
  perfis/*.toml       regras por norma (D2) — nunca lógica específica de norma no parser
tests/                pytest; fixtures/ = trechos reais, snapshots/ = regressão
docs/                 PRD e decisões
dados/                fontes brutas e saídas geradas (não versionado)
```

## Regras do projeto

- **Python 3.12**, ruff (config em `pyproject.toml`), pytest. Sem dependência nova sem registrar em `docs/README.md § Stack`.
- **Identificadores em português**, alinhados ao vocabulário do PRD (`LinhaFonte`, `artigo`, `rubrica`, `nota`).
- **Parser genérico (D2):** nada de `if norma == "cp"`. Diferenças vão para o perfil `.toml`.
- **Nenhuma perda silenciosa (RNF04):** todo texto entra na árvore ou no relatório, com `origem`.
- **Determinismo (RNF03):** JSON com chaves ordenadas, sem timestamp dentro de `artigos`.
- **Windows sem WSL (RNF02):** `pathlib`, `encoding="utf-8"` explícito em toda leitura/escrita.
- **Regex só muda com teste:** toda alteração de padrão (PRD §8) vem com o caso real que a motivou.
- **Snapshot de regressão** só é regravado com justificativa registrada em `REVISAO.md`.
- Texto legal é **literal** (inclusive "alguem", "conseqüências"); não corrigir ortografia.

## Fluxo de trabalho

1. Ler a fase atual em `docs/PENDENCIAS.md` ("Agora"); trabalhar só no escopo dela.
2. Teste primeiro, com fixture real, citando o ID do PRD.
3. `ruff check . && ruff format --check . && pytest` verdes antes de commit.
4. Ao fechar uma fase: preencher o log em `REVISAO.md` e avançar `PENDENCIAS.md`.
5. Descobriu algo que contradiz o PRD? Registrar em `docs/Prd.md` §12 (pendências) e perguntar — não decidir sozinho.
