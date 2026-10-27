# Formato JSON de questões (questoes-oj/1) e painel de estudo

> **Para que serve este arquivo:** é o contrato entre o extrator de questões (parte do projeto do vade mecum) e o painel **Estudo OJ 2026**. Se o formato mudar, mude aqui e na validação do painel ao mesmo tempo.

- **Painel:** https://claude.ai/artifact/RWiMPK8Xr4uw4ALscyaxcr (criado em 27.10.2026)
- **Tópicos:** `claude/topicos-oj2026.json` (schema `topicos-oj/1`). São 163 itens: um por capítulo da lei nas matérias de direito e um por tópico do edital nas demais. Os ids são estáveis (`pc:citacao`, `penal:particular`…).

## Arquivo de entrada

```json
{
  "schema": "questoes-oj/1",
  "questoes": [
    {
      "id": "vunesp-2024-tjsp-oj-q26",
      "materia": "proc-civil",
      "topico": "pc:citacao",
      "fonte": { "banca": "VUNESP", "ano": 2024, "orgao": "TJSP",
                 "cargo": "Oficial de Justiça", "numero": 26, "arquivo": "prova-2024.pdf" },
      "texto_base": null,
      "enunciado": "…",
      "alternativas": [ { "letra": "A", "texto": "…" } ],
      "gabarito": "B",
      "anulada": false,
      "imagem": false,
      "comentario": null
    }
  ]
}
```

| Campo | Obrigatório | Regra |
|---|---|---|
| `materia` | sim | `penal`, `proc-penal`, `proc-civil`, `constitucional`, `administrativo`, `civil`, `leg-especial`, `portugues`, `atualidades`, `matematica`, `raciocinio`, `informatica` |
| `enunciado` | sim | texto não vazio |
| `alternativas` | sim | 2 a 6 itens. Aceita `[{letra, texto}]`, lista de strings (as letras A, B… são atribuídas) ou objeto `{"A": "…"}` |
| `gabarito` | sim | letra de uma alternativa, ou `null` com `anulada: true` |
| `id` | não | sem `id`, o painel gera um a partir de `fonte.banca`, `fonte.ano`, `fonte.orgao`, `fonte.cargo` e `fonte.numero`. Se não houver id nem esses campos, a questão é rejeitada |
| `topico` | não | id de `topicos-oj2026.json` da mesma matéria. Se for inválido, a questão entra sem tópico (com aviso) |
| `texto_base`, `comentario` | não | texto |
| `imagem` | não | `true` quando a questão depende de figura que não foi extraída |

- O arquivo pode ser o objeto acima ou só a lista. Limite: 2.000 questões por arquivo.
- **Reimportar é seguro.** Questão com o mesmo id tem o conteúdo atualizado. Respostas, motivo e observação são mantidos. O tópico só é trocado se o arquivo trouxer um.

## O que o painel acrescenta a cada questão no banco

`respostas` (lista só de anexar: `{data, marcou, certo}`), `motivo` (lei-seca, interpretacao, desatencao, pegadinha, desatualizada, nao-sabia), `obs`, `importado_em`.

A situação é calculada, não gravada:

- **nova:** nunca respondida.
- **rever:** errou na última resposta.
- **em revisão:** acertou a última, mas já errou antes.
- **dominada:** acertou sem nunca errar, ou acertou as duas últimas.

## Outras coleções do banco

- `estado/{topico}`: `{l: 0–4 leituras, v: aula assistida, obs}`. Sobrescrito.
- `tentativas/{auto}`: `{topico, materia, data, feitas, acertos, origem, criado}`. Só anexa. O percentual não é gravado; é calculado do histórico.
- `notas/{materia}`: `{texto}`.

O acesso ao banco é restrito a quem tem nível de edição no painel (dono e editores).

## Pontos de atenção para o extrator

- A VUNESP publica o gabarito em documento separado da prova. O extrator precisa juntar os dois e usar o **gabarito definitivo**, já com as anulações.
- Questões de NSCGJ de 2023 e 2024 podem ter gabarito superado pela redação atual das Normas. Para essas, use o motivo `desatualizada`.
- Material comercial (NEAF, cadernos de questões) não deve ir para um painel compartilhado.
