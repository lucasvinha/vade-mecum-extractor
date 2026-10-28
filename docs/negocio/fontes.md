# Fontes — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O que se observou nas fontes reais e como cada leitor as transforma em `LinhaFonte`. Usado por
`fontes/html.py`, `fontes/pdf.py` e `segmentador.py`. Vizinhos: [parsing.md](parsing.md) (o que se
faz com as linhas) e [pipeline-e-perfis.md](pipeline-e-perfis.md).

Fontes analisadas: `DEL2848compilado_2.mht` (Planalto, salvo em 26/10/2026) e
`LEI_SECA_OJ26_Legislacao_Especial.17.10.pdf` (18 p.).

**Legenda de evidência:** **[Verificado]** = conferido nas fontes anexadas · **[Inferido]** =
dedução a partir das amostras, a confirmar na implementação.

## §1. O PDF é fonte já estruturada (D6)

O PDF é tratado como fonte **já estruturada**: montado no Word, com texto selecionável.

## §2. Leitura

- **RF01** — Aceitar como fonte: URL HTTP(S), arquivo `.htm`/`.html`, `.mht`/`.mhtml` e `.pdf`. O tipo é detectado pela extensão ou pelo conteúdo.
- **RF02** — Ao baixar por URL, salvar o HTML bruto em cache local com data e SHA-256, para reprodutibilidade.
- **RF03** — Em `.mht`, extrair a parte `text/html` principal (MIME `multipart/related`) e decodificar pelo charset declarado (H1).
- **RF04** — No HTML, colapsar espaços em branco e só então quebrar linhas em `<p>`, `<br>`, `<div>`, `<blockquote>`, `<tr>` (H3, H4).
- **RF05** — No PDF, extrair por coluna (P2), remover cabeçalho e número de página (P3) e mapear negrito e cor por caractere (P4).
- **RF06** — Rejeitar com mensagem clara um PDF sem camada de texto (OCR está fora de escopo).

## §3. HTML do Planalto (Código Penal)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| H1 | Codificação **windows-1252** declarada em `<meta>`. | [Verificado] | Decodificar pelo charset declarado e emitir UTF-8. |
| H2 | **Sem marcação semântica.** Só `<p>`, `<b>`/`<strong>`, `<font>`, `<a>`, `<span>`. Só existem 8 âncoras `name="art…"` em todo o documento. | [Verificado] | O parse é **por texto + regex**, não por DOM ou âncoras. |
| H3 | O código-fonte tem quebras de linha **no meio das frases** (ex.: `§` numa linha e `1º Se o agente…` na seguinte). As quebras reais são `<p>` e `<br>`. | [Verificado] | Colapsar espaços em branco **antes** de quebrar em blocos; quebrar só em `<p>`/`<br>`/`<div>`/`<blockquote>`. |
| H4 | Um mesmo `<p>` pode conter **vários artigos** separados por `<br>` (ex.: arts. 187, 189 e 191). | [Verificado] | A unidade de parse é a **linha lógica**, não o parágrafo HTML. |
| H5 | Títulos estruturais ficam em `<p align="CENTER"><strong>` (ex.: `TÍTULO I<br>DOS CRIMES CONTRA A PESSOA`). | [Verificado] | Centralizado + negrito + palavra-chave identifica um nível hierárquico. A linha seguinte é o nome do nível. |
| H6 | Rubricas ("Homicídio simples", "Caso de diminuição de pena") ficam em `<p align="left"><b>`, isoladas. Também aparecem **antes de parágrafos e incisos**, não só antes de artigos (ex.: "Homicídio contra menor de 14 anos" antes do inciso IX do art. 121, § 2º). | [Verificado] | Rubrica = bloco 100% negrito, não centralizado, sem padrão de dispositivo. Ela se liga ao **próximo dispositivo de qualquer nível**. |
| H7 | Rubricas podem carregar nota: `Feminicídio (Incluído pela Lei nº 14.994, de 2024)`. | [Verificado] | Separar a nota do texto da rubrica. |
| H8 | **`<strike>` não marca texto revogado.** As 6 ocorrências estão vazias (só envolvem `<br>` ou espaço). | [Verificado] | Ignorar `<strike>`. A revogação é identificada pela **nota**, não pela formatação. |
| H9 | Notas aparecem inline, entre parênteses, em geral como link: Incluído (610), Redação dada (480), Vigência (74), Revogado (47), Vide (34), Vetado (17). | [Verificado] | Extrair todas e classificar por tipo ([vigencia-e-notas.md](vigencia-e-notas.md)). |
| H10 | "Vigência" aparece **com e sem parênteses** (25 linhas terminam em `) Vigência`). | [Verificado] | O regex de notas deve aceitar as duas formas. |
| H11 | Variações de numeração: `Art. 1º -`, `Art. 10 -`, `Art. 121.`, `Art 187.` (sem ponto), `§ 2°` (grau), `§ 4o` (letra "o"), `§ 2o-A`, `§ 2º-B.` | [Verificado] | Normalizar `º`/`°`/`o` como ordinal; aceitar `Art` com ou sem ponto e `-`, `–` ou `.` como separador. |
| H12 | Sufixos de **dois níveis**: `Art. 359-M-A`, `Art. 359-M-B`. | [Verificado] | O identificador e a ordenação suportam sufixo composto ([recorte-e-cli.md](recorte-e-cli.md)). |
| H13 | Travessão (`–`) e hífen (`-`) se alternam: `VII – contra:` / `I - mediante…` / `Pena – reclusão`. | [Verificado] | Tratar os dois como o mesmo separador. |
| H14 | A linha `Pena -` **não fecha** o dispositivo. No art. 121, § 2º, há uma pena depois do inciso V, os incisos VII–X continuam no mesmo § 2º e a pena se repete no final. | [Verificado] | A pena é um nó **posicional** dentro do pai. O parser não deve encerrar o § ao encontrar `Pena`. |
| H15 | Falso positivo de revogação: `Art. 88 - Revogado o livramento, não poderá ser novamente concedido…` é texto **vigente**. | [Verificado] | Só é revogado o dispositivo cujo conteúdo, tirando as notas, está **vazio** ou é exatamente `Revogado.`/`Revogados.`. |
| H16 | Rubrica que fica **órfã** quando o dispositivo seguinte é revogado (ex.: "Feminicídio" antes do inciso VI revogado do art. 121, § 2º). | [Verificado] | Descartar a rubrica junto com o dispositivo revogado. |
| H17 | Cabeçalho da página (Presidência, "Vide" gerais, ementa, preâmbulo) e rodapé (local/data, assinaturas, "Este texto não substitui o publicado no DOU…"). | [Verificado] | Guardar preâmbulo e rodapé em `metadados`, fora da árvore de artigos. |
| H18 | Títulos estruturais com nota: `TÍTULO I / DA APLICAÇÃO DA LEI PENAL / (Redação dada…)`; `CAPÍTULO IV / (Incluído…) / DOS CRIMES…` (a nota pode vir **antes** do nome). | [Verificado] | O nome do nível é a próxima linha que não é nota. |
| H19 | Numeração-base do CP sem lacunas (1 a 361) e último artigo `Art. 361 - Este Código entrará em vigor…`. | [Verificado] | Usar como critério de aceite (A1, no [PADRAO_OURO](../PADRAO_OURO.md)). |

## §4. PDF montado (Legislação Especial)

| # | Característica | Evidência | Consequência |
|---|---|---|---|
| P1 | Gerado por "Microsoft: Print To PDF" a partir do Word. Texto selecionável. | [Verificado] | `pdfplumber` resolve; não precisa de OCR. |
| P2 | **Duas colunas.** A extração padrão intercala as colunas. | [Verificado] | Recortar cada página em duas colunas (esquerda, depois direita) antes de extrair linhas. Detectar a divisória ou usar a metade da largura, configurável. |
| P3 | Cabeçalho de página `LEGISLAÇÃO ESPECIAL` e número de página (fonte F1, 12 pt). | [Verificado] | Remover por fonte/tamanho/posição. |
| P4 | Rótulos em **negrito** (`Art. 1º`, `§ 1º`, `I -`, `a)`, `Parágrafo único`); corpo em fonte regular. Os nomes de fonte são genéricos (`CIDFont+F3` = negrito, `CIDFont+F4` = regular). | [Verificado] | O negrito vem do **mapeamento de fonte por documento**, não do nome. Rótulo em negrito no início da linha é sinal forte de novo dispositivo. |
| P5 | **Várias normas num só PDF**: NSCGJ Tomo I, Lei 6.830/80, Res. CNJ 354/2020, Lei SP 11.608/03. Cada norma começa com título em azul-escuro sublinhado, ementa em vermelho-escuro e preâmbulo. | [Verificado] | Segmentar o PDF em **documentos** antes do parse. A saída tem uma base por norma ([modelo-de-dados.md](modelo-de-dados.md)). |
| P6 | O PDF já é um **recorte**: a numeração tem lacunas (NSCGJ pula de 4 para 33, 49, 105…). | [Verificado] | Não acusar lacuna no modo PDF; acusar só **numeração fora de ordem**. |
| P7 | Artigos **parciais**: o edital pede "196, inciso XX", e o PDF traz só o inciso XX do art. 196. | [Verificado] | Modelo aceita artigo sem caput ou com incisos esparsos (`parcial: true`). |
| P8 | Hierarquia **incompleta**: o bloco dos arts. 994 e seguintes aparece sob "DOS OFICIAIS DE JUSTIÇA / Seção I", sem a linha "CAPÍTULO VII". | [Verificado] | Campos de hierarquia são opcionais. Título sem palavra-chave vira `rotulo_livre`. |
| P9 | Lei estadual usa `Artigo 1° -` em vez de `Art. 1º`. | [Verificado] | O perfil define os prefixos aceitos (`Art.`, `Artigo`). |
| P10 | Notas da NSCGJ usam outro vocabulário e cor azul: `(Alterado pelo Provimento CG Nº 33/2024)`, `(Acrescentado pelo…)`, `(Revogado pelo…)`. | [Verificado] | O vocabulário de notas é configurável por perfil. A cor serve como sinal auxiliar. |
| P11 | Revogação em faixa: `Art. 1.054 a Art. 1091. Revogados.` | [Verificado] | Reconhecer e registrar a faixa como revogada (relatório), sem gerar artigos. |
| P12 | Revogação sem parênteses: `Artigo 10 - Revogado.`; `I – Revogado. (Revogado pelo Provimento CG Nº 03/2026)`. | [Verificado] | Mesma regra do H15. |
| P13 | Números com separador de milhar: `Art. 1.247`, `1.091-A`. | [Verificado] | Normalizar `1.091` → 1091 no número; manter o rótulo original para exibição. |
| P14 | Linhas terminadas em hífen são palavras compostas (`apresentar-`/`se`, `e-`/`mail`, `devolvê-`/`lo`), não hifenização tipográfica. | [Inferido, 6 amostras] | Ao juntar linhas, manter o hífen e não inserir espaço. |
| P15 | `Parágrafo único.` **no meio da linha**, colado ao caput (Res. CNJ 354, art. 8º). | [Verificado] | Não quebrar automaticamente. Gerar **aviso** no relatório para revisão manual. |
| P16 | Marcador `(NR)` (nova redação). | [Verificado, 1 ocorrência] | Tratar como nota do tipo `redacao`. |

Os IDs P1–P16 desta tabela são características do PDF; as pendências P1–P7 de
[PENDENCIAS.md](../PENDENCIAS.md) são outra série.

## §5. Armadilhas e limites conhecidos

- `<strike>` e atributos de estilo não dizem nada sobre vigência (H8); o leitor não deve depender
  deles, só de negrito e alinhamento.
- O layout do Planalto muda: HTML antigo do FrontPage convive com trechos novos em
  `<p style="text-align: justify">`.
