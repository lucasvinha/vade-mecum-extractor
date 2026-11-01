# Spec — M3: parser do CP, notas e `extrair`

> Decisão que executa: regras de [negocio/parsing.md](../../negocio/parsing.md),
> [negocio/fontes.md](../../negocio/fontes.md) e ADR-002, completadas na entrevista de 2026-11-01
> (registradas na fase 1). Itens: PENDENCIAS #7 (M3), #16 e #18.
> Escrita em 2026-11-01 contra `b1ef044`, branch `m2-leitor-html`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

O pipeline para no leitor: `cli.py:42` levanta `NotImplementedError` e nenhuma linha vira árvore.
Medido nas 2.397 linhas que `ler_html` + `normalizar` tiram de `dados/cp/del2848compilado.mht`:

- Quase toda linha termina em nota (`(Redação dada pela Lei nº 7.209, de 1984)`); 95 rubricas têm
  só o nome em negrito e a nota fora dele (`Lugar do crime (Redação dada…)`, `html:p#35`), e a H6
  ("bloco 100% negrito") não as vê. Sem `notas.py`, o parser não separa nota de texto.
- 10 rubricas sem negrito nenhum (`Feminicídio (Incluído pela Lei nº 14.994, de 2024)`, `p#615`;
  `Sabotagem`, `Golpe de Estado`, `p#2332`–`p#2378`) seriam coladas ao dispositivo anterior.
- `III perda ou inutilização do membro…;` (`p#684`, art. 129, § 2º) não tem hífen, e
  `Pena: detenção…` (`p#2032`, art. 319-A; `p#2258`) usa dois-pontos: os regex de partida falham.
- 20 notas presas a nível (`CAPÍTULO IV` / `(Incluído…)` / `DOS CRIMES…`, `p#2374`–`p#2377`),
  nível sem negrito (`p#2374`), nome de nível em duas linhas (`p#919`–`p#920`), 4 linhas
  `(VETADO) (Incluído…)` sem rótulo (`p#2367`, `p#2372`, `p#2383`, `p#2388`) e o rodapé
  `Rio de Janeiro, 7 de dezembro de 1940;…` (`p#2393`) logo depois do art. 361.
- Item 16: RF19 (`negocio/modelo-de-dados.md`) manda `origem` para o JSON; `modelo.py:138` não.
- Item 18: 55 tachados só por `text-decoration: line-through` (CPC 35, Lei 8.429 16, Lei 13.146 4)
  passam como vigentes; `fontes/html.py:131` só olha a tag. No CPC, art. 63, o § 1º antigo
  (tachado por CSS) e o novo saem os dois.

## Estado final

- `python -m vademecum extrair --fonte dados/cp/del2848compilado.mht --perfil cp --saida
  dados/cp/base.json` grava a base e `dados/cp/base.relatorio.json`; erro de entrada sai com 2.
- Passam A1 (fonte inteira de `dados/`, pulado com motivo se faltar), A4, A6, A7, A8 e a parte
  estrutural de A2 e A3: § 2º do art. 121 com inciso VII e alíneas a e b, duas penas posicionais;
  § 2º-D com pena própria.
- `texto` sai sem nota; toda nota está em `notas`, classificada (RF12).
- Nenhuma linha do CP fica fora da árvore, dos `metadados` ou do relatório (RNF04).
- O CSS `line-through` conta como tachado (H8 revista); RF19 diz que `origem` não vai ao JSON.

## Fora do escopo, de propósito

- **Filtro de vigência** (ADR-001, RF14–RF16): no M3, `Art. 189. (Revogado…)`, `§ 7º (Revogado…)`
  e `Art. 359-Q. (VETADO).` entram na árvore com `texto` vazio e a nota. Sai no M4, com a parte
  "ausente" de A2, A3 e A5 e a rubrica órfã (H16). Exceção: a linha `(VETADO)` sem rótulo (abaixo).
- **Validador V1–V7** e motivo estruturado do descarte: M4. O M3 registra `nao_classificada`.
- **Snapshot de regressão:** M4, quando a saída para de mudar com a vigência.
- **URL, PDF, `--perfil-auto`, `--saida-dir`:** M7 e M8; aqui levantam `ErroFonte` (código 2).
- **Perfis de outras normas:** M6. A fase 2 mexe no leitor do CPC e da Lei 8.429 só pelo item 18.
- **Item numérico** (`1.`, `2.`): M8.

## Contrato

- **CLI:** `extrair` passa a funcionar para `.htm`/`.mht`; grava `<saida>` e
  `<saida sem .json>.relatorio.json` ao lado (`base.json` → `base.relatorio.json`).
- **Base:** esquema por tipo já definido em `modelo.py`, sem chave nova. Nota da rubrica entra em
  `notas` do dispositivo a que a rubrica se liga, antes das notas dele. `norma.id` = `id` do perfil.
- **Relatório:** passa a existir em disco no M3, com `descarte` (tachado H8; `(VETADO)` sem
  rótulo), `aviso` (tachado parcial; nota de nível; rubrica sem dispositivo seguinte),
  `nao_classificada` (V7) e `nota_outra`. Sem campo novo em `EntradaRelatorio`.
- **Perfil:** `padrao.toml` ganha as chaves reais (abaixo) e nasce `cp.toml`.
- **Consumidores:** a Etapa 2 ainda não lê nada; base do M2 não existe. Nenhuma base perde validade.

### Regras fixadas na entrevista (a fase 1 as escreve em `negocio/`)

| Regra | Decisão |
|---|---|
| H6 + H7 (rubrica) | Rubrica é: (a) linha 100% negrito, não centralizada, sem padrão de dispositivo; ou (b) linha com `rotulo_negrito` sem padrão de dispositivo e seguida de dispositivo; ou (c), se o perfil ligar `rubrica.sem_negrito`, linha não centralizada, sem padrão de dispositivo, cujo resto sem notas não termina em `.`, `;`, `:` ou `,`, seguida de dispositivo. A nota dela vai para `notas` do dispositivo seguinte. Rubrica sem dispositivo seguinte (vem nível ou fim) → `aviso` |
| H5 + H18 (nível) | Centralizada + palavra-chave do perfil, sem diferenciar maiúsculas (`SEÇÃO I`); negrito não é exigido (`p#2374`). Nome = linhas centralizadas seguintes que não são nota nem nível, unidas por espaço (`p#919`–`p#920`). Centralizada em negrito sem palavra-chave depois de artigo → `rotulo_livre` (`DISPOSIÇÕES FINAIS`, P8). `local` = `"<rótulo> — <nome>"`; nível novo zera os de baixo. Nota de nível → `aviso` com a origem |
| RF11 (linha só de nota) | As notas vão para o elemento corrente. Se começa por `(VETADO)` e não há rótulo → `descarte` (RF14), nunca vira nota de outro |
| H17 (cabeçalho e rodapé) | Cabeçalho = linhas antes do primeiro nível ou artigo → `metadados.preambulo`. `norma.titulo` = 1ª linha centralizada do cabeçalho que começa por tipo de norma (`DECRETO-LEI`, `LEI`…); `norma.ementa` = linha logo antes da fórmula `O PRESIDENTE DA REPÚBLICA`. Rodapé começa na linha que casa `rodape.inicio` do perfil (local e data: `Rio de Janeiro, 7 de dezembro de 1940;`, `Brasília, …`) → `metadados.rodape` |
| H8 (tachado) | `text-decoration` com `line-through` no `style` de qualquer ancestral conta como `<strike>` (inclui `none line-through`, Lei 8.429) |
| RF19 | `origem` fica no `No` em memória e em toda entrada do relatório; não entra no JSON da base |

Chaves do perfil: `artigo.prefixos`, `hierarquia.niveis`, `dispositivos.rubrica`,
`dispositivos.pena`, `rubrica.sem_negrito`, `rodape.inicio`, `validacao.lacunas`, `notas.<tipo>`.

## Fases

Todas: portões `ruff check . && ruff format --check . && pytest`. Teste com linha real do CP
(texto copiado de `dados/`, ou fixture). Regra citada pelo ID no teste e no comentário.

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | Registra as decisões: H5, H6, H7, H8, H17, H18 em `negocio/fontes.md`; RF11 em `negocio/parsing.md`; RF19 em `negocio/modelo-de-dados.md`; chaves novas em `negocio/pipeline-e-perfis.md`; `(VETADO)` sem rótulo em `negocio/vigencia-e-notas.md`; PENDENCIAS: `notas.py` sai do M4 para o M3, risca o 16 | 5 docs | `scripts/verificar_docs.py` sai 0; tabela "Regras fixadas" acima toda transcrita | Opus | 2026-11-01, `9e441f2` |
| 2 | Leitor: tachado pelo CSS (item 18). `fontes/html.py:131` passa a ver `line-through` no `style` do ancestral. Enxertos novos `cpc_art63.htm` e `lei8429_art17.htm`, recortados em bytes de `dados/` | `fontes/html.py`, 2 fixtures, `tests/unit/test_fontes_html.py`, PENDENCIAS (risca 18) | § 1º antigo do CPC, art. 63, vira `descarte` e o novo fica; Lei 8.429, art. 17, § 3º vira `descarte`; os tachados por tag seguem iguais | Sonnet | 2026-11-01, `12a1e6b` |
| 3 | `perfil.py`: `carregar_perfil(nome) -> Perfil` (dataclass frozen), merge `padrao.toml` + específico, chave desconhecida é erro; preenche `padrao.toml`; cria `cp.toml` (`id = "cp"`, `rubrica.sem_negrito = true`) | `perfil.py`, 2 `.toml`, `tests/unit/test_perfil.py` | `carregar_perfil("cp")` traz as chaves da lista acima; perfil inexistente → `ErroFonte` | Sonnet | 2026-11-01, `485aafc` |
| 4 | `notas.py`: `extrair_notas(texto, perfil, origem, relatorio) -> (texto_limpo, tuple[Nota, ...])` (RF12, H9, H10, P16); `norma`, `ano`, `data` só quando o texto traz a data inteira; parêntese com `Lei nº` não classificado → `nota_outra` | `notas.py`, `tests/unit/test_notas.py`, `negocio/parsing.md` (regex de nota, se mudar) | Casos reais: `(Redação dada pela Lei nº 7.209, de 11.7.1984)`, `… (Vigência)`, `… Vigência` sem parênteses, `(Incluído dada pela Lei nº 12.720, de 2012)` (`p#1828`), `(Incluído pela Lei 12.550. de 2011)` (`p#1970`); `(quatorze)` fica no texto | Sonnet | 2026-11-01, `599b9a0` |
| 5 | `parser.py`, dispositivos: `analisar(linhas, perfil, relatorio)` monta artigo › § / parágrafo único › inciso › alínea, pena posicional (H14) e continuação (RF11), com `id` de `modelo.py` e notas de `notas.py`. Regex: inciso aceita romano + espaço + minúscula (`p#684`); pena aceita `-` ou `:` (`p#2032`) | `parser.py`, `tests/unit/test_parser.py`, `negocio/parsing.md` (tabela) | Art. 121 caput, § 2º com I–X, VII com alíneas a e b, duas penas; § 2º-D com pena própria; `III perda…` é inciso III; `Pena:` é pena; texto literal | Opus | 2026-11-01, `268764f` |
| 6 | `parser.py`, rubricas e linhas só de nota: regras H6/H7 da tabela, `(VETADO)` sem rótulo → `descarte` | `parser.py`, `tests/unit/test_parser.py` | `Lugar do crime` liga ao art. 6º com a nota em `notas`; `Feminicídio` (`p#615`) liga ao art. 121-A; `Sabotagem` ao 359-R; `III perda…;` não é rubrica; as 4 linhas `(VETADO)` são `descarte` | Opus | 2026-11-01, `21de4a0` |
| 7 | `parser.py`, hierarquia: `local` de cada artigo (RF07, H5, H18, P8) | `parser.py`, `tests/unit/test_parser.py` | Art. 121 em `PARTE ESPECIAL` / `TÍTULO I — DOS CRIMES CONTRA A PESSOA` / `CAPÍTULO I — DOS CRIMES CONTRA A VIDA`; nome de duas linhas unido; `CAPÍTULO IV` sem negrito reconhecido; nota de nível → `aviso`; art. 360 com `rotulo_livre = "DISPOSIÇÕES FINAIS"` | Opus | 2026-11-01, `1beb872` |
| 8 | `parser.py`, cabeçalho e rodapé: devolve `Norma` parcial + `Metadados` (H17) | `parser.py`, `tests/unit/test_parser.py` | `titulo = "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940"`, `ementa = "Código Penal."`; rodapé de `Rio de Janeiro…` até `*`; art. 361 sem texto do rodapé | Opus | 2026-11-01, `4241d75` |
| 9 | `cli.py`, `extrair`: `ler_html` → `normalizar` → `analisar` → `Base`; grava base e relatório com `para_json`, `encoding="utf-8"`, `newline="\n"`; `ErroFonte` → stderr e código 2; URL/`.pdf`/`--perfil-auto`/`--saida-dir` → `ErroFonte` | `cli.py`, `tests/unit/test_cli.py` | Fixture `cp_enxertos.mht` → dois arquivos em `tmp_path`, byte a byte iguais em duas execuções (RNF03); arquivo inexistente → 2 | Sonnet | |
| 10 | Aceite: enxerto `cp_parser.htm` (cabeçalho e arts. 1–3, 88, 129, 359-I ao fim e rodapé, em bytes de `dados/cp/del2848compilado.htm`); A1, A2 e A3 (parte estrutural), A4, A6, A7 | 1 fixture, 5 `tests/aceite/test_a0N_*.py` | `pytest -m aceite` verde; A1 pulado com motivo sem `dados/`; com `dados/`, A1 passa e o CP inteiro roda em menos de 10 s (RNF05, meta) | Sonnet | |
| 11 | Fechamento: risca o M3 (item 7) em PENDENCIAS, atualiza "Agora" e o texto do M4 (sem `notas.py`); ajusta `docs/README.md` (Mapa do código, se a assinatura mudou); apaga esta spec | docs | `verificar_docs.py` sai 0; conferência manual do relatório do CP inteiro: nenhuma `nao_classificada` sem explicação | Sonnet | |

## Em aberto

- Nenhuma pergunta bloqueia fase.
- Para a spec do M4: no relatório do CP real, conferir se o `descarte` do `(VETADO)` sem rótulo
  precisa do motivo estruturado do RF16, e se o `aviso` da nota de nível basta à Etapa 2.
