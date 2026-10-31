# Spec — M2: leitor HTML e normalizador

> Decisão que executa: H8 revista (o tachado sai da linha) e H1 sem charset declarado (operador,
> 2026-10-31); aplica o ADR-001 no leitor.
> Item: PENDENCIAS #6.
> Escrita em 2026-10-31 contra `ef01737`, branch `m2-leitor-html`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema

Não há leitor de fonte nem normalizador: `src/vademecum/fontes/` só tem o `__init__.py`, e o
pipeline não tem entrada. A fonte real é `dados/cp/del2848compilado.mht` (salvo pelo Chrome/Edge,
"Saved by Blink", em 26/10/2026; 769 KB, fora do git). O que se viu nela:

- Parte `text/html` com `Content-Transfer-Encoding: binary` e **sem charset no MIME**; o charset
  só aparece no `<meta http-equiv>` (`windows-1252`, H1). Há uma segunda parte, `image/gif`.
- Cabeçalho `Date: Mon, 26 Oct 2026 02:03:12 GMT` e `Snapshot-Content-Location` com a URL.
- O ordinal vem em tag: `§ 4<sup>o</sup>`, `§ 1<sup><u>o</u></sup>` (105 `<sup>`). Extrair o
  texto pondo espaço entre as tags gera `4 o` e quebra a H11.
- Recuo com `&nbsp;` antes de cada dispositivo; quebra de linha no meio do rótulo
  (`Art\n187.`, `§ \n\t2°-D.`), o que confirma a H3.
- `<b>` vazios em volta de blocos (`<b>\n\n</b><p …>`), e rótulo só em negrito no HTML também
  (`Parágrafo único</strong> - A homologação…`).
- 6 `<strike>`, todos vazios (`<br>` ou espaço). Nas outras normas do Planalto o tachado traz a
  redação antiga: 3 com texto no CPP, 43 no CPC e 83 na Lei 8.429 (H8 revista).
- O `.htm` que vem do Planalto não declara charset (H1). No `.mht`, quem declara é o `<meta>`
  que o navegador põe ao salvar.
- Travessão `–` em 141 rótulos (`I – aplicada pena…`), ao lado de `Pena - reclusão` (H13).
- `§ 2°` com sinal de grau só no art. 78 (`§ 2° Se o condenado houver reparado o dano`); no
  art. 121, `§ 2o-A`, `§ 4o`, `§ 6o`, `§ 7o` e `§ 2º-B.` (A8, H11).

## Estado final

- `ler_html(caminho, relatorio)` lê `.mht`/`.mhtml` e `.htm`/`.html` locais e devolve as linhas
  lógicas do art. 121 da fixture na ordem do texto, uma por bloco ou `<br>` (H3, H4), com
  `negrito`, `rotulo_negrito` e `centralizado` corretos (H5, H6).
- `normalizar(linhas, prefixos_artigo)` deixa `§ 4º`, `§ 2º`, `§ 2º-A` e `VII -` no rótulo do
  início da linha; o resto do texto fica literal.
- `tests/aceite/test_a08_ordinais.py` passa sobre a fixture (leitor + normalizador).
- A linha toda tachada sai da saída e vira `descarte` no relatório; o tachado parcial fica e
  gera `aviso`. Ambos com `origem` (H8).
- Portões verdes.

## Fora do escopo, de propósito

- **Preâmbulo e rodapé em `metadados` (H17):** saber onde termina o preâmbulo depende do
  `Art. 1`, que é do parser. Fica no M3 (operador, 2026-10-31).
- **Título e ementa da norma:** o `<title>` é `DEL2848compilado`, não o título. Saem do parser
  (M3).
- **URL com cache (RF02, A14):** M7. O Planalto recusa cliente que não é navegador; isso
  vai para a spec do M7.
- **Separação de notas e junção de continuação (RF11, P14):** `notas.py` no M4, junção no
  parser (M3) e no PDF (M8). O normalizador do M2 faz só ordinal e travessão.
- **`perfil.py`:** M3. O normalizador recebe os prefixos de artigo por parâmetro; no M3 a CLI
  passa os do perfil (ADR-002).
- **Subcomando `extrair`:** M3. A CLI não muda nesta spec.
- **Cor no HTML:** `cor` fica `None`; nenhuma regra H* usa cor no HTML.

## Contrato

| Eixo | O que muda |
|---|---|
| Consumidores | Nenhum ainda: o `extrair` só chega no M3. Etapa 2 não é afetada |
| Esquema do JSON | Não muda. `LinhaFonte` não muda (`modelo.py:87`) |
| Relatório | Novas origens de `descarte` e `aviso`: o tachado (os tipos já existem, `modelo.py:185`) |
| CLI | Não muda |
| Compatibilidade | Sem snapshot (o primeiro é do M4); nenhuma base gerada perde validade |
| Fontes | `dados/cp/` (`.mht` e `.htm`), `dados/lei8429/` e `dados/cpp/` geram as fixtures; nada depende de rede |
| Decisão | H8 revista e H1 com default; aplica o ADR-001; não contradiz o ADR-002 |

Decisões que a spec fixa, para as fases não decidirem:

- **`FonteLida`** em `modelo.py`, `frozen=True, slots=True`: `linhas: tuple[LinhaFonte, ...]`,
  `tipo_fonte: str` (`"html"`), `fonte: str`, `capturado_em: str`, `sha256: str`. São os campos
  de `Norma` (`modelo.py:145`) que vêm da captura; o parser completa o resto no M3.
- **`fonte`:** `Snapshot-Content-Location` do `.mht`; no `.htm` local, o caminho como foi
  passado (`str(caminho)`).
- **`capturado_em`:** ISO `AAAA-MM-DDTHH:MM:SSZ` em UTC. No `.mht`, o cabeçalho `Date`; no
  `.htm`, o `mtime` do arquivo. `.mht` sem `Date` cai no `mtime`.
- **`sha256`:** dos bytes da parte HTML (no `.htm`, do arquivo), antes de decodificar.
- **Charset:** parâmetro `charset` do MIME; senão, `<meta>` (`http-equiv` ou `charset=`);
  senão, `windows-1252` (H1: é o caso de todo `.htm` do Planalto). Decodificação estrita:
  byte inválido é `ErroFonte`, nunca `replace` (RNF04). Os 10 `.htm` de `dados/` passam no
  windows-1252 estrito. Arquivo inexistente, `.mht` sem parte `text/html` e extensão
  desconhecida também são `ErroFonte`.
- **Texto da linha:** os nós de texto de um bloco são concatenados **sem separador** (o
  `4<sup>o</sup>` vira `4o`); depois, todo espaço em branco (inclusive `\xa0`) vira um espaço
  só, e as pontas são aparadas (RF04). Linha vazia depois disso não é emitida.
- **Quebra de linha:** abertura e fechamento de `<p>`, `<div>`, `<blockquote>`, `<tr>`,
  `<center>`, `<h1>`–`<h6>` e `<li>`, e cada `<br>` (RF04). Texto fora de bloco também vira
  linha. `<script>`, `<style>` e `<head>` não são texto da norma e não são lidos.
- **Bytes antes do lxml** (achado na fase 2, operador, 2026-10-31): `&#128;`–`&#159;` viram
  o caractere do windows-1252 (regra do HTML5; o libxml2 dava U+0096 em 61 travessões do CP), e
  `</body>`/`</html>` saem (o libxml2 parava no `</html>` solto após o preâmbulo do CC). Com
  isso, o `.htm` do CP dá as mesmas 2397 linhas do `.mht`.
- **Flags:** `negrito` = todo caractere visível da linha está dentro de `<b>`/`<strong>`;
  `rotulo_negrito` = a linha começa em negrito e não é toda negrito; `centralizado` = algum
  ancestral de bloco tem `align="center"` (qualquer caixa), `text-align: center` no `style`,
  ou é `<center>`. `<b>` só com espaço não conta.
- **`origem`:** `html:p#<n>`, com `n` = posição da linha lógica (1, 2, 3…) no documento,
  contando as que saem pela H8. Assim, a saída pode ter lacunas, e a `origem` do descarte
  aponta o lugar exato. O formato é o de `negocio/pipeline-e-perfis`.
- **Tachado (H8):** texto dentro de `<strike>`, `<s>` ou `<del>`. Para cada linha lógica, o
  "resto" é o texto fora do tachado, já com o espaço colapsado:
  - tachado só com espaço: nada muda (CP);
  - resto vazio ou só notas, ou seja, uma ou mais `(…)`, cada uma com `.` opcional: a linha
    **sai inteira** e o leitor registra um `descarte` com a `origem` e o texto completo da
    linha, tachado e nota juntos (`Art. 4° Os agentes… (Revogado pela Lei nº 14.230, de 2021)`).
    A nota não pode ficar sozinha, senão o parser a cola no dispositivo anterior;
  - qualquer outro resto: a linha fica literal, com o tachado, e o leitor registra um `aviso`
    com a `origem` e o trecho tachado. Apagar o trecho adulteraria o CPP, art. 336.
- **Normalizador:** função pura `normalizar(linhas, prefixos_artigo) -> tuple[LinhaFonte, ...]`,
  via `dataclasses.replace`, sem perfil e sem relatório. Só no rótulo do início da linha:
  ordinal `o`/`°` → `º` logo depois do número do artigo (com `prefixos_artigo`) e do `§`; o
  separador `–` → `-` logo depois do rótulo de artigo, `§`, `Parágrafo único`, inciso romano e
  `Pena`. O corpo não muda: `art. 121, § 2o` no meio do texto fica como está.

## Fases

| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| 1 | Fixture real + leitor `.mht`: texto, quebra e `origem` | `modelo.py`, `fontes/html.py`, `tests/unit/test_fontes_html.py`, `tests/fixtures/html/cp_enxertos.mht`, `tests/fixtures/README.md` | portões verdes; linhas do art. 121 na ordem; `4<sup>o</sup>` vira `§ 4o`; `Art\n187.` vira `Art 187.`; os três artigos do `<p>` dos arts. 187–191 saem em linhas separadas (H4); byte inválido levanta `ErroFonte` | Sonnet | 2026-10-31, `b894418` |
| 2 | Leitor `.htm`/`.html` local | `fontes/html.py`, teste, `tests/fixtures/html/cp_art78.htm` | portões verdes; mesmas linhas do `.mht` para o mesmo trecho; sem charset declarado, lê em windows-1252 (H1); `capturado_em` pelo `mtime`; extensão desconhecida levanta `ErroFonte` | Sonnet | |
| 3 | Flags de negrito e centralizado | `fontes/html.py`, teste | portões verdes; `TÍTULO I` e `DOS CRIMES CONTRA A PESSOA` centralizados (H5); `Homicídio simples` com `negrito` (H6); `Parágrafo único</strong> - …` com `rotulo_negrito`; `<b>` vazio não marca a linha seguinte | Sonnet | |
| 4 | Tachado (H8): descarte ou aviso | `fontes/html.py`, teste, `tests/fixtures/html/lei8429_tachado.htm`, `tests/fixtures/html/cpp_art336.htm` | portões verdes; os 6 `<strike>` vazios do CP não mudam nada; na Lei 8.429, `Art. 4°…(Revogado…)` e o inciso IV antigo do art. 9º saem como `descarte` com `origem`, e o IV novo fica; no CPP, o art. 336, parágrafo único, fica literal e gera um `aviso` | Opus | |
| 5 | Normalizador: ordinal e travessão no rótulo + aceite A8 | `normalizador.py`, `tests/unit/test_normalizador.py`, `tests/aceite/test_a08_ordinais.py` | portões verdes; `§ 4o` → `§ 4º`, `§ 2°` → `§ 2º` (art. 78), `§ 2o-A` → `§ 2º-A`, `VII – contra:` → `VII - contra:`; `art. 121, § 2o` no corpo fica igual; `Artigo 1°` com o prefixo passado | Sonnet | |
| 6 | Fechamento | `docs/PENDENCIAS.md`, `docs/README.md`, `docs/negocio/pipeline-e-perfis.md`, `docs/negocio/fontes.md`, esta spec | — | Sonnet | |

Notas por fase, para o `/fase` não precisar de outro documento:

- **Fase 1.** A fixture é um `.mht` real recortado do `dados/cp/del2848compilado.mht`: o
  cabeçalho MIME original (com `Date` e `Snapshot-Content-Location`), uma parte `text/html` com
  o `<head>` original e só os trechos da fonte, em ordem: títulos `TÍTULO I`/`CAPÍTULO I` antes
  do art. 121, o art. 78 (`§ 2°`), o art. 121 inteiro (até antes do `Art. 122`) e o `<p>` dos
  arts. 187–191. Os bytes ficam em **windows-1252**: é isso que prova a H1. A parte `image/gif`
  sai. O script de recorte fica no scratchpad, fora do git. O `tests/fixtures/README.md` diz que
  as fixtures HTML estão em UTF-8: corrigir para "no charset original da fonte". Origem e data
  da captura no topo da parte HTML, em comentário `<!-- -->`. O art. 121 tem ~29 KB; a fixture
  inteira fica abaixo de 60 KB (exceção de tamanho declarada: fixture real). Parser:
  `BeautifulSoup(conteudo, "lxml", from_encoding=charset)`, com bytes e nunca com `str`: com
  `str`, o `<meta charset>` faz o libxml2 trocar de codificação no meio do texto, e o CP inteiro
  vira mojibake e para no art. 266. A decodificação estrita roda antes, só para validar. O
  `.mht` é lido com
  `email.message_from_bytes(..., policy=email.policy.default)` e
  `get_payload(decode=True)`. I/O com `pathlib`; os bytes são lidos com `read_bytes()`.
- **Fase 2.** A fixture `.htm` é o trecho do art. 78 recortado em bytes de
  `dados/cp/del2848compilado.htm`, a página como o Planalto serve, sem charset declarado. O
  teste compara com as linhas do mesmo trecho no `.mht`.
- **Fase 4.** As duas fixtures são bytes recortados das fontes reais, sem charset declarado,
  como na fase 2. `lei8429_tachado.htm`, de `dados/lei8429/l8429.htm`: os `<p>` do art. 4º e
  do art. 9º, IV (o antigo, tachado, e o novo). `cpp_art336.htm`, de
  `dados/cpp/del3689compilado.htm`: o `<p>` do parágrafo único do art. 336. O regex de "só
  notas" é testado com as duas notas reais: `(Revogado pela Lei nº 14.230, de 2021)` e
  `(Redação dada pela Lei nº 12.403, de 2011).`.
- **Fase 5.** Os casos vêm das linhas reais da fixture (art. 121 e art. 78), passadas pelo
  leitor. `Artigo 1°` é da Lei SP 11.608 (P9, PDF do M8): sem fixture HTML, o teste usa a
  `LinhaFonte` com o texto literal da P9 e diz isso. O ordinal só muda colado ao número
  (`4o`, `2°`, `2o-A`); `Art. 10 -` e `Art. 121.` não mudam.
- **Fase 6.** Riscar o item 6 com data e sha; "Agora" aponta o M3. `pipeline-e-perfis`
  ganha o formato de `origem` do HTML. No README técnico, o Mapa do código mostra a saída
  `FonteLida` e a assinatura do normalizador. Na spec do M7, registrar a recusa do Planalto a
  cliente sem User-Agent de navegador.

## Em aberto

Nada. O tachado nas outras normas foi conferido e decidido em 2026-10-31 (H8).
