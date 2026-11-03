# Prompt — vade mecum de uma matéria, do zero, por qualquer IA

Cole este arquivo como primeira mensagem numa IA com acesso ao terminal na raiz do repositório.
Ele conduz as três etapas ([ADR-005](../decisoes/ADR-005-vade-mecum-em-tres-etapas.md)): pergunta
o que falta, roda a CLI e só escreve a curadoria. O detalhe da Etapa 3 está em
[INSTRUCOES.md](INSTRUCOES.md); este prompt não o repete.

---

Você vai gerar o vade mecum de estudo de **uma matéria** de um edital de concurso usando a CLI
`python -m vademecum`. Você **usa** a aplicação: não altera código, perfil, base nem recorte.
Texto legal nunca sai da sua memória; sai sempre do recorte.

## Passo 0 — Entrevista

Leia `claude/topicos-oj2026.json` (ou o arquivo de tópicos que o operador indicar) e pergunte ao
operador, numa mensagem só, o que não der para tirar dele. Proponha a resposta provável de cada
pergunta e espere a confirmação.

| # | Pergunta | De onde vem o padrão |
|---|---|---|
| 1 | Qual **edital** e qual o arquivo de tópicos? Qual o id curto (`oj26`)? | `edital` do arquivo de tópicos; id = pasta em `dados/recortes/` |
| 2 | Qual **matéria**? | `materias[].id`; mostre a lista com `nome` e `tipo: "lei"` |
| 3 | Quais **leis** entram e qual a **fonte** de cada uma? | `grupos[].norma` da matéria; fonte `.mht` em `dados/fontes/<norma>/` |
| 4 | Qual a **data de corte** da legislação no edital? | o edital; sem ela, pergunte: é o que vai nos avisos da capa |
| 5 | Qual a **data de hoje** (`gerado_em` da capa)? | o sistema; confirme |
| 6 | Qual a **banca**? Há pegadinhas ou artigos que o operador quer destacar? | vai para as atenções e os quadros |

Respostas fixas: o recorte é o do arquivo de tópicos (não pergunte artigo por artigo) e o estilo é
o de [estilo.md](estilo.md).

## Passo 1 — Base de cada lei (Etapa 1)

Para cada `norma` da matéria sem `dados/bases/<norma>/base.json`:

```bash
python -m vademecum extrair --fonte dados/fontes/<norma>/<arquivo> --perfil <norma> --saida dados/bases/<norma>/base.json
```

- `--fonte`: o arquivo do passo 0; `--perfil`: o perfil da lei, em `src/vademecum/perfis/`;
  `--saida`: a base. O relatório sai ao lado, em `base.relatorio.json`.
- Esperado: código 0, sem nada impresso. Código 2 com `perfil inexistente: '<norma>'`: **pare**
  e diga ao operador que a lei ainda não tem perfil. Não rode com o perfil `padrao` para
  contornar: a base sairia com `norma.id = "padrao"` e o recorte não a reconheceria.
- A base de `dados/` sai do `.mht`, que guarda a data da captura; o teste de sincronia não
  aceita `.htm`. Só há `.htm`? Peça ao operador que abra a lei no Planalto e salve com Ctrl+S
  como "Página da Web, arquivo único (.mht)". Enquanto isso, as etapas podem rodar do `.htm`
  numa pasta temporária, só como prévia: nada dela entra em `dados/`.
- Abra o relatório e conte as entradas por `tipo`. `aviso` e `nota_outra` não impedem nada,
  mas resuma ao operador os que caem nos artigos do edital.

## Passo 2 — Recorte do edital (Etapa 2)

Para cada `norma`, sem `dados/recortes/<edital>/<materia>/<norma>.json`:

```bash
python -m vademecum recortar --base dados/bases/<norma>/base.json --topicos claude/topicos-oj2026.json --materia <materia> --saida dados/recortes/<edital>/<materia>/<norma>.json
```

- `--topicos` e `--materia` dizem quais artigos o edital cobra; `--saida` é o recorte, com o
  relatório ao lado.
- Esperado: código 0. Confira se o número de artigos do recorte bate com o `n` dos itens da
  matéria; diferença vem nos `aviso` do relatório (artigo inexistente, faixa revogada).

## Passo 3 — Curadoria e HTML (Etapa 3)

Leia [INSTRUCOES.md](INSTRUCOES.md) inteiro e siga-o. Os avisos da capa levam, no mínimo:

- a data de corte do passo 4 da entrevista e as leis do relatório com ano igual ou posterior a ela,
  a conferir;
- os artigos com letra fora da faixa do edital e os revogados dentro dela;
- a data de captura de cada fonte, que o `renderizar` já põe: não repita.

Rode `renderizar` e `conferir` até os dois saírem 0. Erro de curadoria se corrige na curadoria;
divergência no `conferir` é defeito do programa: relate, não edite o HTML.

## Passo 4 — Entrega

Mostre ao operador, nesta ordem:

1. as respostas da entrevista;
2. a saída da última execução de `renderizar` e de `conferir`;
3. o que ficou de fora ou ficou duvidoso (avisos do relatório, leis recentes a conferir);
4. o caminho do HTML, com o pedido de abrir no navegador, imprimir com Ctrl+P → "Salvar como
   PDF" sem cabeçalhos do navegador, gravar o PDF ao lado e conferir capa, cores e rodapé.

Não faça commit: o commit é do operador.
