# Spec — Renderização do vade mecum: curadoria em JSON e `renderizar` determinístico

> Decisão que executa: ADR-006 (decidido pelo operador nesta entrevista, escrito na fase 1;
> emenda o ADR-005). Item: PENDENCIAS #20 (novo, aberto na fase 1).
> Escrita em 2026-11-02 contra `f40f101`, branch `melhora-render-vade-mecum`. Revista no mesmo
> dia contra `d29654b`, com os anexos do protótipo, que tinham chegado cifrados, já lidos.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

O piloto `dados/vade-mecum/oj26/penal.html` (commit `9e88c15`) ficou aquém da amostra de 22 e
23/10 (`docs/etapa3/estilo.md` e `docs/etapa3/referencia-visual.pdf`):

- 38 `<mark>` de uma cor só, sem a função do trecho. O caput do art. 312 não grifa nem o verbo
  ("Apropriar-se") nem o sujeito ("funcionário público").
- A pena sai em preto, com a fonte do texto, sem a caixa "PENA" da referência.
- Uma coluna só (o CSS não tem `column`), sem selos nos rótulos e sem a hierarquia azul dos títulos.
- 7 quadros, contra 6 + 11 entre a referência e o `estilo.md`. As penas dos quadros são digitadas
  sem conferência (o `conferir` não olha anotações, `negocio/vade-mecum.md`).
- O script que gerou o piloto não está no repositório. Cada geração reinventa o estilo, e o
  ADR-005 deixa layout e anotações misturados no HTML que a LLM escreve.

A referência, porém, não é gabarito cego. Ela é a saída do protótipo (`render_html.py` pelo
Chromium, num Linux: as fontes saíram Liberation Serif e Sans), cujo CSS está em
`docs/etapa3/prototipo.css`. O plano do protótipo (`PLANO-vademecum-legis.md`, fora do git)
registra seis defeitos dela, que o `renderizar` não repete:

1. Sumário sem número de página: o Chromium não implementa `target-counter()`.
2. Cerca de 1/4 de página em branco no pé das pp. 13 a 15. Causa provável, segundo o plano:
   `column-fill` e `column-span: all`.
3. Capa com cabeçalho e número de página: o `to_pdf.py` desenhava os do Chromium em toda página.
4. Página 3 do sumário com duas linhas (mesma causa do 2).
5. Justificação em coluna estreita abre rios (pp. 4 e 15).
6. Notas legislativas dominam a página: 15 repetições de "(Redação dada pela Lei nº 7.209…)" no
   art. 7º. Para o plano, é o defeito mais grave para o estudo. O recorte tem 221 notas, 204
   delas de redação ou inclusão.

## Estado final

- `python -m vademecum renderizar` gera `dados/vade-mecum/oj26/penal.html` a partir dos tópicos,
  do recorte `cp.json` (com o relatório) e de `dados/curadoria/oj26/penal.json`, e sai 0.
- `conferir` sai 0 sobre esse HTML, e o teste de sincronia o regera byte a byte.
- Grifos em 5 categorias, com legenda; pena em caixa âmbar; notas compactas; duas colunas na
  impressão; quadros em largura total, com cada pena ancorada e conferida numericamente.
- O PDF salvo do navegador não tem os defeitos 2 a 6. O operador o compara com
  `referencia-visual.pdf` e aprova.
- `docs/etapa3/INSTRUCOES.md` manda a LLM escrever só a curadoria, nunca o HTML.

## Fora do escopo, de propósito

- Diagramas em SVG (arts. 129, 109, 7º, 117 e 107): item novo #21, que depende do `renderizar`.
- Flashcards em PDF separado: item novo #22, outro produto que reusa a curadoria.
- Correções de extração (`estilo.md`, seção de correções): item novo #23. A spec só mexe na
  renderização. `extrair`, `recortar` e `conferir` não mudam.
- Outras matérias: dependem dos perfis do M7. A spec prova o estilo só em `penal`.
- Número de página no sumário (defeito 1): o PDF sai do navegador, que não tem
  `target-counter()`, e o sumário fica com links. As duas passadas com `pypdf` do plano pedem
  dependência nova e motor de PDF próprio.
- Opção `--notas` com três modos (plano do protótipo): o compacto é fixo, e o detalhe de cada
  nota continua na base (operador, na revisão).
- Matriz Word editável (`render_docx.py` do protótipo): fora, sem item (operador, na revisão).

## Contrato

**Inalterado:** esquema da base e do recorte, relatório, `conferir` e o contrato `data-*` do HTML
(`negocio/vade-mecum.md`). O `renderizar` produz o mesmo contrato que a LLM produzia.

**Novo: subcomando `renderizar`** (fase 4):

```bash
python -m vademecum renderizar --topicos claude/topicos-oj2026.json --materia penal \
  --recorte dados/recortes/oj26/penal/cp.json --curadoria dados/curadoria/oj26/penal.json \
  --saida dados/vade-mecum/oj26/penal.html
```

- `--recorte` é repetível, um por norma. O relatório é lido ao lado (`<norma>.relatorio.json`,
  como o `_relatorio_de` de `src/vademecum/cli.py`).
- `--curadoria` é opcional: sem ela, sai só o texto legal (útil para a fase 5).
- Sai 0 e grava o HTML; avisos (teto de grifo) vão para o stderr, e o código continua 0.
  Sai 1 com erro de curadoria, uma linha por erro, **sem gravar o HTML**. Sai 2 com erro de
  entrada (`ErroFonte`).

**Novo: `dados/curadoria/<edital>/<materia>.json`**, esquema `curadoria-vm/1`:

```json
{"schema": "curadoria-vm/1", "edital": "oj26", "materia": "penal", "gerado_em": "2026-11-02",
 "avisos_capa": ["..."],
 "dispositivos": {"cp:art312": {"marcas": [{"trecho": "Apropriar-se", "cat": "verbo"}],
                                "atencao": ["..."]}},
 "quadros": [{"depois_de": "cp:art314", "titulo": "Peculato e figuras próximas",
              "colunas": ["Dispositivo", "Verbo nuclear", "Elemento distintivo", "Pena"],
              "linhas": [["Art. 312 — Peculato", "apropriar-se", "tem a posse",
                          {"pena": "cp:art312.pena1", "texto": "reclusão, 2 a 12 anos, e multa"}],
                         ["Art. 304 — Uso de documento falso", "fazer uso", "não falsifica",
                          {"pena": "cp:art304.pena1"}]],
              "nota": "..."}]}
```

- Chave `<norma>:<id>` porque a matéria pode ter mais de uma norma.
- `cat`: `verbo` (amarelo), `sujeito` (verde), `especializante` (ciano), `quantidade`
  (magenta) e `condicao` (cinza claro: subsidiariedade e procedibilidade). O vermelho sai da
  paleta, porque a pena tem a caixa âmbar da referência (operador, nesta entrevista).
- **Marca:** o trecho é procurado no `texto` do nó depois de normalizar ambos para NFC. Deve
  aparecer uma vez só e não pode sobrepor outra marca. Vira `<mark class="hl-<cat>">` dentro do
  `data-campo="texto"`, o que não muda o texto conferido.
- **Erro (sai 1):** id inexistente no recorte, trecho não encontrado, ambíguo ou sobreposto,
  `cat` fora da lista, pena divergente ou, com `texto`, não interpretável.
- **Aviso (sai 0):** marcas acima de ~15% dos caracteres do artigo (pena fora da conta).
- **Pena no quadro:** a célula `{"pena", "texto"}` declara a âncora, uma pena por célula.
  Espécie, mínimo, máximo, unidade e multa do `texto` têm de bater com os da pena do recorte.
  "dois", "2" e "2 (dois)" valem o mesmo. A multa é ausente, cumulativa ("e multa", "além da
  multa") ou alternativa ("ou multa"), e "e" × "ou" conta.
- **Pena literal:** a célula `{"pena"}`, sem `texto`, sai com o texto da pena do recorte, sem
  conferência. É a saída para a pena que o interpretador não entende (duas faixas no 299 e no
  305, remissão no 304): com `texto`, ela é erro.
- `gerado_em` vem da curadoria, nunca do relógio (RNF03), e é a data da capa.

**Sem dependência nova:** `html.escape`, `unicodedata` e `importlib.resources` da stdlib. O CSS
fica em `src/vademecum/estilo/vade-mecum.css` e entra embutido no `<style>`, porque o HTML
continua sendo um arquivo só, sem recurso externo (INSTRUCOES).

**Compatibilidade:** nenhum snapshot muda. `penal.html` é regravado nas fases 8 e 9, com a
justificativa no corpo do commit. O `penal.pdf` fica defasado entre a fase 8 e a 9, quando o
operador salva o novo.

## Regras de layout

Fonte: `referencia-visual.pdf` e o CSS que a gerou (`docs/etapa3/prototipo.css`), sem os
defeitos 1 a 6. Detalhe em `docs/etapa3/estilo.md`.

- **Capa:** norma, "VADE MECUM", matéria, edital, avisos de uso (os `avisos_capa`, mais a data
  de captura do recorte e a nota de conferência) e assinatura, sem cabeçalho nem número de
  página (defeito 3). A nota de conferência diz que o texto legal foi conferido contra o recorte
  e que as notas vêm da fonte, sem verificação independente. Depois vêm o sumário e a legenda
  "Como ler os destaques", com uma amostra de cada cor e o aviso de que quadros e atenções são
  material de apoio, não texto de lei.
- **Sumário:** grupos › itens › `Art. N — rubrica`, em duas colunas, em links. Sem a página
  quase vazia da p. 3 da referência (defeito 4).
- **Hierarquia:** grupo e título em azul, centralizados. Rubrica em linha própria, com barra
  laranja à esquerda. `Art. N.` em azul e negrito. Rótulos de §, inciso e alínea em selo, com o
  texto do rótulo literal. Recuo por nível.
- **Pena:** caixa âmbar com o rótulo "PENA" (fora do `data-campo`), logo depois do dispositivo,
  na ordem dos `filhos`.
- **Notas (compacto, defeito 6):** as de `redacao` e `inclusao` do artigo e dos filhos viram uma
  linha "Alterações: Lei nº 7.209/1984 · Lei 12.550/2011" no fim do artigo: a `norma` como está
  na base (a 12.550 vem sem "nº", como na fonte) e o `ano`, cada par uma vez, por ano e, no
  mesmo ano, na ordem em que aparece. As demais (`remissao`, `vigencia`) ficam coladas ao
  dispositivo, com a `bruto`, em cinza e corpo menor, uma vez por nó.
- **Revogados:** cada `descarte` do relatório vira uma linha com a etiqueta `REVOGADO` e a nota,
  sem `data-id`. Fica sob o pai, na ordem do rótulo. Se o pai não está no recorte, fica na
  posição do artigo.
- **Saltos:** entre artigos seguidos da mesma norma, quando a numeração-base avança com buraco,
  inclusive na troca de grupo, onde a linha fecha o grupo anterior (o "arts. 155 a 292" da
  referência). Quando recua, não há salto. Se o artigo seguinte tem letra, o número-base dele
  entra no buraco: 308 → 311-A dá "arts. 309 a 311" (o 311 está fora do edital; a referência
  imprimiu "309 a 310"). Um artigo só sai "art. X — fora do edital" (a referência imprimiu
  "arts. 306 a 306"). Artigo com letra logo depois do anterior (121-A e 121-B, 337-A a 337-P)
  não entra no salto: fica nos avisos da capa (seção de capa do `estilo.md`).
- **Ordem e remissão:** seguem a seção "Organização" do INSTRUCOES. A ordem é a dos tópicos, a
  `nota` do item vira aviso, o selo `oj` aparece, e o artigo coberto por dois itens fica no
  primeiro, com remissão sem `data-id` no segundo (faixa pelo ADR-004).
- **Quadro:** largura total (`column-span: all`), logo depois do nó `depois_de`, com cabeçalho
  azul-escuro e a nota embaixo. Quebra entre linhas, com o cabeçalho repetido e
  `break-inside: avoid` só na linha: o quadro inteiro indivisível é suspeito do defeito 2.
  **Atenção:** aside depois do dispositivo.
- **Impressão:** A4, duas colunas com fio, rodapé `@page` do INSTRUCOES e
  `print-color-adjust: exact`. Sem `break-inside: avoid` no artigo inteiro (lição do piloto).
  Texto alinhado à esquerda, com `lang="pt-BR"` e `hyphens: auto` (defeito 5). Fontes do
  Windows primeiro (Georgia no corpo, Segoe UI nos rótulos), com fallback genérico.

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | ADR-006 e docs da decisão | ADR-006 (novo), ADR-005 (Histórico), `docs/README.md` (três etapas, linha "Fora", mapa), README raiz se citar a LLM no HTML, `negocio/vade-mecum.md` (seção Curadoria com o esquema acima), `docs/etapa3/estilo.md` (pena âmbar, 5 categorias, notas compactas, saltos com o 311, defeitos 1 a 6 como lições; tira SVG, flashcards e correções, que viram itens), `docs/etapa3/referencia-visual.pdf`, PENDENCIAS (#20 em curso; #21–#23) | portões verdes; `python scripts/verificar_docs.py` sai 0 | Opus || 2026-11-02 `a251f82` |
| 2 | `curadoria.py`: leitura e validação do `curadoria-vm/1`, marcas (NFC, único, sem sobreposição), teto e pena resumida × literal | `src/vademecum/curadoria.py`, `tests/unit/test_curadoria.py`, mapa do código | portões verdes; testes com penas reais do CP: 312 ("dois a doze anos"), 316 ("2 (dois) a 12 (doze)"), 121 § 2º-D ("20 (vinte) a 40 (quarenta)"), 129 ("três meses a um ano"), 320 ("quinze dias a um mês, ou multa") e 321 p.u. ("além da multa"); a do 299 (duas faixas) é erro com `texto` e passa sem ele | Sonnet || 2026-11-02 `9884d7e` |
| 3 | `render.py`: texto legal sem curadoria (capa, sumário, grupos, itens, artigos com `data-*`, pena, notas compactas, revogados, saltos, remissão, avisos do relatório) e CSS mínimo | `src/vademecum/render.py`, `tests/unit/test_render.py`, mapa do código; ~250 linhas (exceção: módulo novo com teste) | portões verdes; render do `tests/fixtures/snapshots/cp_enxertos.json` com tópicos de teste → `conferir` devolve `()`; salto testado na troca de grupo, no recuo (sem salto) e em 308 → 311-A | Opus || 2026-11-02 `7f9c58c` |
| 4 | Subcomando `renderizar` | `src/vademecum/cli.py`, `tests/unit/test_cli.py`, `negocio/vade-mecum.md` (seção da CLI) | portões verdes; códigos 0, 1 e 2 testados; não regrava nada em `dados/` | Sonnet || 2026-11-02 `9954cb9` |
| 5 | CSS da referência | `src/vademecum/estilo/vade-mecum.css` (novo, a partir de `docs/etapa3/prototipo.css`, que esta fase apaga), `render.py` (embute o CSS), `pyproject.toml` só se o hatchling não levar o `.css` | portões verdes; o operador renderiza o penal sem curadoria numa pasta temporária, salva o PDF e compara com `referencia-visual.pdf`: sem os defeitos 2 a 5, com a fonte diferente como esperado | Opus || 2026-11-02 `1a8c5eb` |
| 6 | Curadoria no render: marcas, atenção, quadros, legenda, avisos de capa, rótulo de apoio, erros (sai 1) e aviso de teto | `render.py`, `test_render.py`, `test_cli.py` | portões verdes; trecho ausente sai 1 sem gravar; pena divergente sai 1; pena literal sai sem conferência; teto só avisa | Sonnet || 2026-11-02 `68072f0` |
| 7 | Etapa 3 no fluxo novo | `docs/etapa3/INSTRUCOES.md` (a LLM escreve a curadoria, roda `renderizar` e `conferir`), `.claude/skills/vade-mecum/SKILL.md` | portões verdes; `verificar_docs` sai 0 | Sonnet || 2026-11-02 `e2701d1` |
| 8 | Curadoria do CP: marcas e atenções | `dados/curadoria/oj26/penal.json` (novo), `penal.html` regravado, `tests/regressao/test_dados_versionados.py` (regera o vade mecum); exceção: arquivo de dados grande | portões verdes; `renderizar` sai 0; `conferir` sai 0; os 27 "Atenção" do piloto migrados; os 12 saltos (13–99, 122–128, 130–149, 151–153, 155–292, 306, 309–311, 318, 334–335, 338, 348–356, 358); `avisos_capa` sem o do inciso III do art. 129, § 2º (o recorte o traz), e com as Leis 15.358, 15.438 e 15.455, de 2026, a conferir contra o corte de 19/10/2026 | Opus | |
| 9 | Curadoria do CP: quadros | `penal.json`, `penal.html`, `penal.pdf` (o operador salva), `docs/etapa3/quadros-prototipo.json` (os 6 quadros da referência em texto, base desta fase, que o apaga) | portões verdes; os 6 quadros da referência mais os do `estilo.md` que couberem, todas as penas ancoradas; `depois_de` pela tabela do `estilo.md`, não pela `ancora` do protótipo (o primeiro artigo); 321 p.u. em linha própria; título "quatro tipos" da vantagem indevida revisto (o quadro tem cinco); rodapé do 109 sem o "CONFERIR" (o art. 115 do recorte traz a Lei 15.160/2025); o operador aprova o PDF | Opus | |
| 10 | Fechamento | PENDENCIAS (risca #20, atualiza "Agora"), ADR-006 se algo mudou, docs afetados; apaga esta spec | `verificar_docs` sai 0; portões verdes | Sonnet | |

## Em aberto

- **Os 4 quadros [Provável] da Parte Geral** citados no `estilo.md`: a referência e o protótipo
  (`quadros-prototipo.json` e a matriz `.docx`) trazem só o do art. 109. A fase 9 decide entre
  os candidatos do `estilo.md` (103 × 104 × 105–106; 110 § 1º × 117), sem bloquear.
