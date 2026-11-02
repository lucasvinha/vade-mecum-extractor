# Etapa 3 — instruções para gerar o vade mecum de uma matéria

Executável por qualquer LLM. Gera o HTML do material de estudo de **uma matéria** do edital a
partir dos recortes das etapas 1 e 2 ([ADR-005](../decisoes/ADR-005-vade-mecum-em-tres-etapas.md)).
O texto legal é copiado **sem nenhuma alteração** e conferido pelo `conferir`; a contribuição da
LLM está na organização e nas anotações.

Argumento: o `id` da matéria em `claude/topicos-oj2026.json` (ex.: `penal`). Os caminhos valem a
partir da raiz do repositório. `<edital>` é `oj26`.

## 1. Entradas

| Arquivo | O que tem |
|---|---|
| `claude/topicos-oj2026.json` | a matéria: grupos (cada um com a `norma`) e itens (`rubrica`, `arts`, `nota`, `oj`), no esquema `topicos-oj/2` de [negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md) |
| `dados/recortes/<edital>/<materia>/<norma>.json` | os artigos de cada norma da matéria, na árvore de [negocio/modelo-de-dados.md](../negocio/modelo-de-dados.md) |
| `dados/recortes/<edital>/<materia>/<norma>.relatorio.json` | os `descarte` (revogados e vetados dos artigos recortados) e os `aviso` do recorte |

Falta o recorte de uma norma da matéria? Gere-o antes (etapas 1 e 2, em
[negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md)); não escreva texto legal de memória.

## 2. Organização

- **Ordem dos tópicos do edital**, não a da norma: um bloco por grupo, na ordem do arquivo, e
  dentro dele uma seção por item.
- Título da seção: a `rubrica` do item. A `nota` do item vira um aviso logo abaixo do título.
  Item com `oj: true` ganha um selo "cobrado para Oficial de Justiça".
- Artigos de cada item: os do recorte cobertos pela expressão `arts` do item, pela regra de
  faixa do [ADR-004](../decisoes/ADR-004-faixa-inclui-artigos-com-letra.md) (`121 a 130` inclui
  121-A e 121-B, não 130-A). Item sem `arts` vira só o título e a nota.
- **Todo artigo do recorte aparece uma vez só.** Coberto por dois itens, ele fica no primeiro, e
  o segundo traz uma remissão ("ver art. 121, acima") sem `data-id`.
- Em cada artigo, os filhos seguem a ordem do JSON (`filhos`), com as penas intercaladas.
- A localização do artigo (`local`: parte, título, capítulo) vai numa linha discreta só quando
  muda, e no começo de cada item.

## 3. Contrato do texto legal

O contrato completo está em [negocio/vade-mecum.md](../negocio/vade-mecum.md). Em resumo:

```html
<section data-norma="cp">
  <div class="artigo" data-id="art121">
    <h4 data-campo="rubrica">Homicídio simples</h4>
    <p><strong data-campo="rotulo">Art. 121</strong> <span data-campo="texto">Matar alguem:</span></p>
    <div class="pena" data-id="art121.pena1">
      <p><span class="rotulo-pena">Pena –</span> <span data-campo="texto">reclusão, de seis a vinte anos.</span></p>
    </div>
  </div>
</section>
```

- `data-norma` é o `norma.id` do recorte; `data-id`, o `id` do nó; `data-campo`, um de
  `rotulo`, `rubrica` e `texto`, só quando o nó tem o campo.
- Copie o texto do campo **byte a byte**: "alguem", "conseqüências" e "futil" ficam como estão.
  Não corrija ortografia, não atualize valores, não troque aspas nem traços.
- **Podendo rodar código, gere o texto legal por script**, lendo o JSON do recorte, e escreva à
  mão só as anotações. No piloto (90 artigos do CP), o script saiu com o `conferir` em 0 na
  primeira execução; copiar à mão é onde a LLM erra.
- Realce dentro do campo só com marcação que não muda o texto (`<mark>`, `<strong>`, `<em>`).
- Anotação, quadro, remissão e o "Pena –" nunca levam `data-id` nem `data-campo`.

## 4. Anotações de estudo

- **Realces:** núcleo do tipo, elementares, prazos, quantidades e exceções ("salvo", "exceto").
- **Quadros comparativos** onde o edital põe figuras vizinhas lado a lado: tipo simples ×
  qualificado × privilegiado, penas de crimes próximos, prazos que confundem.
- **Pontos de atenção:** pegadinhas de prova, dispositivo com redação recente (nota `redacao` ou
  `inclusao` dos últimos anos), artigo `parcial: true`.
- **Vigência:** as notas de cada nó (`notas`, com `tipo`, `norma` e `ano`) viram uma linha
  discreta abaixo do dispositivo, ex.: "Redação dada pela Lei nº 15.134, de 2025". A fonte às
  vezes repete a mesma nota no nó: mostre uma vez.
- **Descartes:** os `descarte` do relatório viram um aviso no artigo deles ("§ 2º, VI revogado
  pela Lei nº 14.994, de 2024"). O relatório não diz para onde o dispositivo foi (P4): cite o
  destino só quando ele for certo, como anotação (o feminicídio virou o art. 121-A).
- Os `aviso` do relatório do recorte (item sem artigo, trecho abaixo do artigo ignorado) viram
  uma nota na seção do item. Não esconda nenhum.

## 5. Capa, rodapé e impressão

- **Capa** (primeira página): nome da matéria, edital (`edital` do arquivo dos tópicos), data
  da geração e a assinatura **"Lucas Vinha Teixeira · github.com/lucasvinha"**.
- **Sumário** com os grupos e os itens, em links para as seções.
- **Rodapé** de toda página impressa: a assinatura, o link do repositório
  (`github.com/lucasvinha/vade-mecum-extractor`) e o número da página.
- Um arquivo só, sem recurso externo: CSS no `<style>`, sem script e sem fonte da web.
- CSS de impressão, para o PDF sair do navegador (Ctrl+P, "Salvar como PDF", sem cabeçalhos e
  rodapés do navegador). O artigo inteiro **não** leva `break-inside: avoid`: no piloto, os
  artigos longos (7, 293, 297) deixavam meia página em branco.

```css
@page {
  size: A4;
  margin: 18mm 16mm 20mm;
  @bottom-left { content: "Lucas Vinha Teixeira · github.com/lucasvinha"; font-size: 8pt; }
  @bottom-right { content: "github.com/lucasvinha/vade-mecum-extractor · p. " counter(page); font-size: 8pt; }
}
@page :first { @bottom-left { content: none; } @bottom-right { content: none; } }
.capa, nav { break-after: page; }
.grupo { break-before: page; }
table, aside, .inciso, .alinea, .pena { break-inside: avoid-page; }
h2, h3, h4 { break-after: avoid-page; }
```

## 6. Saída e conferência

1. Grave `dados/vade-mecum/<edital>/<materia>.html`, em UTF-8.
2. Rode o `conferir`, com um `--recorte` por norma da matéria:

   ```bash
   python -m vademecum conferir --recorte dados/recortes/oj26/penal/cp.json --html dados/vade-mecum/oj26/penal.html
   ```

   - `--recorte` aponta o recorte de uma norma; repita a opção para cada norma da matéria.
   - `--html` aponta o vade mecum gerado.
   - Retorno esperado: nada impresso e código 0. Com divergência, uma linha por problema
     (`cp:art121.p2.i2: campo texto divergente: …`) e código 1.

3. Corrija cada linha **no HTML**, copiando de novo do recorte, e rode outra vez até sair 0.
   Divergência nunca se resolve mexendo no recorte.
4. Entregue ao operador o caminho do HTML. Ele abre no navegador, salva
   `dados/vade-mecum/<edital>/<materia>.pdf` ao lado e confere capa e rodapé.
