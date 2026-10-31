# Padrão-ouro do módulo do pipeline

Como um módulo novo de `src/vademecum/` deve ser, e como se reescreve um trecho antigo. O código
ainda é um esqueleto (a fila de implementação está em [PENDENCIAS.md](PENDENCIAS.md)); o primeiro
módulo que passar na revisão vira a referência viva. Em divergência com o código de referência,
**vale o código**, e este documento é corrigido.

## §1. Anatomia

Um módulo é uma etapa do pipeline ([negocio/pipeline-e-perfis.md](negocio/pipeline-e-perfis.md)).

| Camada | Arquivo | Papel |
|---|---|---|
| Etapa | `src/vademecum/<modulo>.py` | Função pura: dados + `Perfil` + `Relatorio` → dados novos |
| Fonte | `src/vademecum/fontes/<tipo>.py` | Único lugar, com `cli.py`, que faz I/O; devolve `list[LinhaFonte]` |
| Perfil | `src/vademecum/perfis/<norma>.toml` | Tudo o que varia por norma (ADR-002) |
| Teste de unidade | `tests/unit/test_<modulo>.py` | Regras do módulo com linhas reais |
| Teste de aceite | `tests/aceite/test_a<NN>_<nome>.py` | Um caso A* de ponta a ponta |
| Fixture | `tests/fixtures/<tipo>/<norma>_<trecho>.<ext>` | Trecho real da fonte, nunca o arquivo inteiro |

Dependências só apontam para a direita do pipeline, nunca para trás
([docs/README.md § Mapa do código](README.md#mapa-do-código)).

## §2. Nomenclatura

Identificadores em português, no vocabulário das regras de negócio (`LinhaFonte`, `artigo`,
`rubrica`, `nota`, `chave_ordenacao`). Regra citada em código ou teste usa o ID: `# H15`,
`test_a2_feminicidio_descartado`.

## §3. Contrato de entrada e saída

- Etapa não lê nem escreve arquivo; recebe e devolve dados (ver `docs/README.md § Contratos`).
- O esquema da saída é o de [negocio/modelo-de-dados.md](negocio/modelo-de-dados.md); mudar campo
  é mudança de contrato e pede spec.
- O texto legal é **literal**, inclusive grafias antigas ("alguem", "conseqüências"); não se
  corrige ortografia.

## §4. Erros e relatório

- Erro de entrada levanta `ErroFonte` com mensagem para o usuário; a CLI devolve código 2.
- Todo texto que não entra na árvore vai para o `Relatorio`, tipado e com `origem` (RNF04).

## §5. Requisitos não funcionais

- **RNF01** — Python 3.12. Dependências: `requests`, `beautifulsoup4`, `lxml`, `pdfplumber`. Desenvolvimento: `pytest`, `pytest-cov`, `ruff` (lint e formatação; configuração em `pyproject.toml`).
- **RNF02** — Rodar em Windows sem WSL (caminhos via `pathlib`, saída UTF-8 explícita).
- **RNF03** — Determinismo: mesma fonte e mesmo perfil geram JSON idêntico, byte a byte (chaves ordenadas, sem timestamp dentro de `artigos`).
- **RNF04** — Nenhuma perda silenciosa: todo texto da fonte entra na árvore ou aparece no relatório.
- **RNF05** — Desempenho: base do CP em menos de 10 s numa máquina comum. É meta, não requisito rígido.

## §6. Validação e testes exigidos

### Regras do validador

- **V1** — Numeração em ordem crescente pela chave de ordenação ([negocio/recorte-e-cli.md](negocio/recorte-e-cli.md)) (sempre).
- **V2** — Sem lacunas na numeração-base (só em perfil de norma integral).
- **V3** — Nenhum `id` duplicado.
- **V4** — Nenhum filho fora de ordem lógica (inciso depois de inciso maior no mesmo pai gera aviso).
- **V5** — Nenhum texto vazio em dispositivo vigente.
- **V6** — Nenhuma nota `outra` sem registro no relatório.
- **V7** — Linhas não classificadas (nem dispositivo, nem continuação reconhecida) aparecem no relatório com `origem`.

### Casos de aceite (com as fontes anexadas)

| # | Entrada | Resultado esperado |
|---|---|---|
| A1 | CP, base completa | Artigos 1 a 361 sem lacuna de numeração-base; último = art. 361; rodapé fora da árvore. |
| A2 | CP, art. 121, § 2º | Incisos I–V e VII–X; **VI ausente** (revogado); rubrica "Feminicídio" do VI descartada; VII com alíneas a e b; duas penas posicionais. |
| A3 | CP, art. 121 | § 2º-A e § 7º ausentes; § 2º-B, § 2º-C e § 2º-D presentes; § 2º-D com pena própria. |
| A4 | CP, art. 88 | **Presente** ("Revogado o livramento…" é texto vigente). |
| A5 | CP, arts. 187–196 | Ausentes (revogados); registrados no relatório. |
| A6 | CP, art. 359-M-A e 359-M-B | Presentes, ordenados após 359-M e antes de 359-N. |
| A7 | CP, art. 2º | Parágrafo único reconhecido (`Parágrafo único -`). |
| A8 | CP, `§ 4o` e `§ 2°` | Rotulados como `§ 4º` e `§ 2º`. |
| A9 | PDF | 4 normas segmentadas: NSCGJ Tomo I, Lei 6.830/1980, Res. CNJ 354/2020, Lei 11.608/2003. |
| A10 | PDF, NSCGJ | Nenhum aviso de lacuna; art. 196 com `parcial: true` contendo só o inciso XX; arts. 1.054–1.091 registrados como faixa revogada. |
| A11 | PDF, Lei 11.608 | `Artigo 1°` reconhecido; artigos 10 e 11 ausentes (revogados). |
| A12 | PDF, Res. CNJ 354, art. 8º | Aviso de "Parágrafo único" no meio da linha (P15). |
| A13 | Recorte `121-130` | Contém 121, 121-A, 121-B, 122…130 vigentes; não contém 130-A. |
| A14 | Leitura de `.mht` e da URL da mesma página | Bases idênticas, exceto `metadados`. |

### Testes

- `pytest` com fixtures de **trechos reais** das fontes (não o arquivo inteiro), um teste por caso de aceite.
- No git entram só **enxertos**: poucas páginas reais da fonte (o art. 121 do CP, duas páginas de questões). A fonte inteira e toda extração gerada ficam em `dados/`, fora do git, porque o repositório é público.
- Caso que exige a fonte inteira (A1) lê de `dados/` e é pulado, com o motivo, quando ela não está lá.
- Teste de regressão: a base gerada dos enxertos é comparada com um snapshot JSON versionado. Qualquer mudança no parser que altere o snapshot precisa ser revisada, e o commit que o regrava traz a justificativa no corpo. A base completa é comparada antes e depois, localmente, pelo `/regressao`.
- Regex só muda com o caso real que motivou a mudança, no mesmo commit.

## §7. Checklist de revisão

O `/revisao` percorre esta lista contra o diff. Item com guarda automática na suíte diz qual.

**Qualidade**
- [ ] `ruff check .` e `ruff format --check .` sem erros. Guarda: portões.
- [ ] `pytest` verde; nenhum teste pulado sem motivo declarado. Guarda: portões.

**Requisitos**
- [ ] Cada regra nova cita o ID (H*, P*, RF*, V*, A*, ADR-NNN) no teste ou comentário.
- [ ] Mudança de regex acompanhada do caso real que a motivou.
- [ ] Nenhuma lógica específica de norma fora de `perfis/*.toml` (ADR-002).

**Invariantes**
- [ ] Nenhuma perda silenciosa: texto descartado ou não classificado vai ao relatório com `origem` (RNF04).
- [ ] Saída determinística: chaves ordenadas, sem timestamp em `artigos` (RNF03).
- [ ] I/O com `pathlib` e `encoding="utf-8"` explícito (RNF02). Guarda parcial: ruff `PTH`.
- [ ] Texto legal preservado literalmente.

**Regressão**
- [ ] Snapshot alterado? A justificativa está no corpo da mensagem do commit que o regrava.

**Documentação**
- [ ] Comentário e docstring citam documento pelo nome ("ver ADR-002", "ver negocio/parsing"),
      nunca por seção, linha ou item; spec nunca é citada no código. Guarda:
      `scripts/verificar_docs.py`, para ADR inexistente e seção ou item por número.
- [ ] Documentos dentro dos tetos de `docs/README.md § Regras de manutenção`.
