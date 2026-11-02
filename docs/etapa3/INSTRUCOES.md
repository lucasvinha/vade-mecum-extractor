# Etapa 3 — instruções para gerar o vade mecum de uma matéria

Executável por qualquer LLM. Gera o material de estudo de **uma matéria** do edital a partir dos
recortes das etapas 1 e 2 ([ADR-005](../decisoes/ADR-005-vade-mecum-em-tres-etapas.md)).
A LLM escreve **só a curadoria**, em JSON: marcas, pontos de atenção, quadros comparativos e
avisos da capa. O HTML sai do `renderizar`, determinístico, que copia o texto legal do recorte e
aplica o estilo; o `conferir` prova que o texto legal é o do recorte
([ADR-006](../decisoes/ADR-006-curadoria-em-json-e-render-deterministico.md)).

Argumento: o `id` da matéria em `claude/topicos-oj2026.json` (ex.: `penal`). Os caminhos valem a
partir da raiz do repositório. `<edital>` é `oj26`.

## 1. Entradas e saída

| Arquivo | O que tem |
|---|---|
| `claude/topicos-oj2026.json` | a matéria: grupos (cada um com a `norma`) e itens (`rubrica`, `arts`, `nota`, `oj`), no esquema `topicos-oj/2` de [negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md) |
| `dados/recortes/<edital>/<materia>/<norma>.json` | os artigos de cada norma da matéria, na árvore de [negocio/modelo-de-dados.md](../negocio/modelo-de-dados.md): é daqui que saem os `id` e os trechos |
| `dados/recortes/<edital>/<materia>/<norma>.relatorio.json` | os `descarte` (revogados e vetados) e os `aviso` do recorte |
| `docs/etapa3/estilo.md` | o que cada cor marca, o teto de grifo, os quadros já previstos e os avisos de capa |
| **`dados/curadoria/<edital>/<materia>.json`** | **a saída da LLM**, no esquema `curadoria-vm/1` de [negocio/vade-mecum.md](../negocio/vade-mecum.md) |

Falta o recorte de uma norma da matéria? Gere-o antes (etapas 1 e 2, em
[negocio/recorte-e-cli.md](../negocio/recorte-e-cli.md)). Texto legal nunca entra na curadoria
nem é escrito de memória.

## 2. O que o `renderizar` já faz (não repita na curadoria)

- A ordem dos tópicos do edital, as seções por item, a `nota` do item, o selo `oj` e a remissão
  do artigo coberto por dois itens ([ADR-004](../decisoes/ADR-004-faixa-inclui-artigos-com-letra.md)).
- Capa, sumário em links, legenda das cores, rodapé de página, duas colunas na impressão.
- A pena em caixa âmbar, as notas de redação e inclusão na linha "Alterações", os revogados do
  relatório entre os irmãos, os saltos "fora do edital" e os `aviso` do relatório.
- A data de captura do recorte e a nota de conferência nos avisos da capa.

## 3. Como escrever a curadoria

O esquema e as regras de erro estão em [negocio/vade-mecum.md](../negocio/vade-mecum.md); o
critério de estudo, no [estilo.md](estilo.md). A chave de tudo é `<norma>:<id>`, com o `id` do nó
no recorte (`cp:art312`, `cp:art121.p2.i1`, `cp:art312.pena1`).

- **`gerado_em`:** a data de hoje, `AAAA-MM-DD`, informada pelo operador ou pelo sistema. É a
  data da capa; o `renderizar` não lê o relógio.
- **Marcas** (`dispositivos.<chave>.marcas`): `{"trecho", "cat"}`, com `cat` entre `verbo`,
  `sujeito`, `especializante`, `quantidade` e `condicao`.
  - O `trecho` é copiado do `texto` do nó, sem mudar uma letra, e tem de aparecer **uma vez só**
    nele. Repetido no mesmo nó? Estenda o trecho até ficar único.
  - Duas marcas do mesmo nó não se sobrepõem. A pena não é marca: já tem caixa própria.
  - Teto de ~15% dos caracteres do artigo: acima disso, o `renderizar` avisa. Enxugue.
- **Atenção** (`dispositivos.<chave>.atencao`): lista de textos curtos, cada um vira um aside
  logo depois do nó. Pegadinha de prova, redação recente (nota `redacao` ou `inclusao` dos
  últimos anos), artigo `parcial: true`, destino de dispositivo revogado quando for certo (o
  feminicídio virou o art. 121-A).
- **Quadros** (`quadros`): onde a banca confunde figuras vizinhas (tabela do `estilo.md`).
  - `depois_de` é o nó depois do qual o quadro sai, em geral o último artigo comparado.
  - Cada linha tem uma célula por coluna. A célula de pena é `{"pena": "<chave da pena>",
    "texto": "reclusão, 2 a 12 anos, e multa"}`: o `renderizar` confere espécie, faixa, unidade
    e multa contra o recorte. A pena com duas faixas ou por remissão (arts. 299, 304 e 305 do
    CP) vai sem `texto`, e sai literal do recorte.
  - Uma pena por célula: figuras com penas diferentes ocupam linhas diferentes.
- **`avisos_capa`:** o que o leitor precisa saber antes de estudar: artigos com letra que ficam
  fora da faixa do edital, leis recentes a conferir contra a data de corte do edital, limites
  conhecidos do recorte.

## 4. Gerar e conferir

1. Grave a curadoria em `dados/curadoria/<edital>/<materia>.json`, em UTF-8.
2. Gere o HTML, com um `--recorte` por norma da matéria:

   ```bash
   python -m vademecum renderizar --topicos claude/topicos-oj2026.json --materia penal \
     --recorte dados/recortes/oj26/penal/cp.json --curadoria dados/curadoria/oj26/penal.json \
     --saida dados/vade-mecum/oj26/penal.html
   ```

   - `--topicos` e `--materia` escolhem a matéria; `--recorte` aponta o recorte de uma norma e
     se repete para cada norma; `--curadoria` é o JSON do passo 1; `--saida`, o HTML.
   - Retorno esperado: código 0 e o HTML gravado. O aviso de teto (`aviso: cp:art313-A: marcas
     cobrem 22% do artigo…`) sai no stderr e não impede a gravação: enxugue as marcas e rode de
     novo.
   - Código 1: uma linha por erro de curadoria (`cp:art312: trecho não encontrado: '…'`,
     `quadro 2, linha 3: cp:art316.pena1: pena divergente: …`), e o HTML **não** é gravado.
     Corrija a curadoria, nunca o recorte, e rode de novo até sair 0.
   - Código 2: erro de entrada (arquivo ausente, JSON inválido, matéria inexistente).
3. Confira o texto legal do HTML:

   ```bash
   python -m vademecum conferir --recorte dados/recortes/oj26/penal/cp.json --html dados/vade-mecum/oj26/penal.html
   ```

   - `--recorte` repete-se por norma, como no passo 2; `--html` é o HTML gerado.
   - Retorno esperado: nada impresso e código 0. Como o texto legal vem do `renderizar`, uma
     divergência aqui é defeito do programa: relate, não edite o HTML à mão.
4. Entregue ao operador o caminho do HTML. Ele abre no navegador, imprime com Ctrl+P → "Salvar
   como PDF", sem os cabeçalhos e rodapés do navegador, grava
   `dados/vade-mecum/<edital>/<materia>.pdf` ao lado e confere capa, cores e rodapé.
