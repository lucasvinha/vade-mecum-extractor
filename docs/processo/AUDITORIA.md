# Roteiro de auditoria de módulo

> Executável por `/auditoria`. Lê **uma unidade inteira** (a unidade do
> [PADRAO_OURO](../PADRAO_OURO.md): módulo, rota, tela ou job) e mede a distância entre o código
> e o padrão. A [REVISAO](REVISAO.md) olha o que um diff mudou; esta olha o que ninguém muda há
> tempo, onde a dívida se acumula sem passar por revisão nenhuma.
> **Auditoria é leitura.** Nada aqui corrige, commita ou toca em HML/PROD.
> **Sessão própria.** O que sai daqui é o relatório do §6 e, com o sim do operador, um item em
> PENDENCIAS. A correção nasce depois: commit direto para o achado isolado, `/spec` para o resto.

Argumento recebido: `$ARGUMENTS` (o caminho da unidade; vazio, pergunte qual).

---

## §0. Quando rodar

- Antes de uma spec que refatora ou reescreve a unidade: a spec parte do relatório.
- Ao herdar ou retomar uma unidade escrita antes deste processo.
- Quando a revisão pede (`pede /auditoria`): o mesmo problema de fundo voltou na unidade.
- Periodicamente, na unidade mais alterada do período (`git log --since=<data> --name-only`).

---

## §1. Alvo e medição

O alvo é a unidade, os arquivos que só ela usa e os testes dela. Arquivo compartilhado entra
pelo que a unidade chama, não inteiro. **Liste o alvo antes de ler.**

Meça e guarde os números para o cabeçalho do §6:

1. **Portões** de `docs/README.md § Parâmetros do processo`, com o lint sobre o alvo inteiro.
2. **Cobertura por arquivo** do alvo ("Cobertura" dos Parâmetros), e as funções que nenhum
   teste executa.
3. **Tamanho:** linhas por arquivo; funções acima de ~60 linhas.
4. **Idade:** `git blame --line-porcelain <arquivo>`, resumido por mês. Código anterior ao
   processo pede mais atenção no §3 do que código que já passou por revisão.
5. **Varredura:** `scripts/verificar_docs.py`, filtrada pelo alvo.

---

## §2. Conformidade

1. **O `§ Checklist de revisão` do PADRAO_OURO, item a item, contra a unidade inteira**, não
   contra um diff. Item com guarda automática que o §1 provou é pulado, dizendo qual guarda.
2. **A anatomia** (`§ Anatomia` do PADRAO_OURO): cada arquivo cumpre o papel declarado, e só ele.
3. **Regras invioláveis** do `CLAUDE.md` e o "Proibido" dos Parâmetros.
4. <!-- opcional: paridade — a unidade contra as gêmeas: o que uma tem e a outra devia ter, sem
   apagar a diferença legítima de negócio. -->

---

## §3. Qualidade

O que a revisão de diff não vê, porque se acumula devagar:

| Eixo | O que procurar |
|---|---|
| Coesão | Arquivo ou função com mais de um papel (tela, regra, persistência e integração juntas) |
| Código morto | Função, constante ou ramo sem chamador (procure pelo nome); código comentado; ramo inalcançável |
| Comentários | Histórico ("antes era…"); citação por seção, item ou linha; nome que não existe mais; docstring fora do lugar; texto que o código desmente |
| Legibilidade | Nome opaco, número mágico, convenção implícita (sufixo em nome de campo, parse por posição) |
| Duplicação | O mesmo bloco em dois lugares da unidade, ou dela com a gêmea |
| Testes | Regra de negócio sem teste; teste que confere o fonte e não o comportamento |
| Segurança e dados | Credencial ou dado pessoal gravado ou logado sem máscara; dado real em código ou teste |

---

## §4. Bugs

No Claude Code, invoque a skill `code-review` (nível `high`, ou o do argumento) sobre os caminhos
do alvo. Ela roda em segundo plano: siga com o §3 e o §5, mas **não escreva o §6 antes de ela
voltar**. Sem ela, diga que a caça a bugs não entrou.

Suspeita que dá para provar, prove: teste descartável **fora do repositório**, numa pasta
temporária, apagado ao fim. Cada achado sai **confirmado** (e como) ou **plausível** (e o que
faltou para confirmar).

---

## §5. Documentação contra o código

O que a unidade cita e o que a cita: `negocio/`, ADRs, o PADRAO_OURO (a referência viva ainda é
verdade?) e o README técnico. Divergência é achado; vale o código.

---

## §6. Relatório

Gravado no caminho de "Relatório de auditoria" dos Parâmetros do processo (gitignored), como
`AUDITORIA_<unidade>_<AAAA-MM-DD>.md`:

1. **Cabeçalho:** alvo, sha do `HEAD`, portões, cobertura por arquivo, tamanho e idade.
2. **Achados** em `Crítico`, `Importante` e `Melhoria`: `arquivo:linha`, eixo (checklist, regra,
   §3, `bug`, docs), confirmado ou plausível, o que quebra e a correção sugerida.
3. **Já registrado:** achado que um item aberto de PENDENCIAS cobre aponta o item e não vira
   item novo.
4. **Item proposto para PENDENCIAS**, pronto para colar: título, achados agrupados e o caminho.
   Achado de segurança confirmado vira item próprio, à frente dos outros.
5. **Encerramento:** `Testes: N passed`.

Na resposta: o caminho, a contagem por grupo, o fecho e a pergunta (`AskUserQuestion`) sobre
registrar o item proposto.

---

## §7. Limites

1. **Não corrige.** 2. **Não commita nem indexa.** 3. **Respeita o "Proibido".**
4. Escreve o relatório e, com o sim do operador, o item em PENDENCIAS. Nada mais: ao terminar,
   o `git status --short` só difere do inicial por esse item.
