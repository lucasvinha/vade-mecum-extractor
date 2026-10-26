# Roteiro da spec — como uma mudança vira fases

> Executável por `/spec`. Produz **um** arquivo: a spec, em [specs/](specs/).
> **Spec é conversa e escrita.** Nada aqui implementa, cria branch ou commita.
> Implementar é o [FASE](FASE.md).

O problema que este roteiro resolve: mudança especificada num documento grande e implementada de
uma vez só. A worktree cresce, a revisão fica cara e reverter um pedaço é desfazer trinta arquivos
à mão. A spec existe para **fatiar antes**, quando fatiar ainda é barato.

Argumento recebido (opcional): `$ARGUMENTS`.

---

## §0. Quando existe spec

| Situação | O que fazer |
|---|---|
| Correção de uma linha, ajuste de texto, renomeação local | Commit direto. Spec aqui é cerimônia |
| Mudança que vale mais de um commit | Spec |
| Mexe em contrato (ver Parâmetros do processo, "Contrato e consumidores") | Spec |
| Cai num dos "Gatilhos de spec" dos Parâmetros do processo | Spec |

Na dúvida, pergunte ao operador antes de abrir a entrevista. **Spec que não fatia nada não
precisava existir.**

---

## §1. Leitura antes da primeira pergunta

Obrigatória, e declarada: antes de perguntar qualquer coisa, diga em uma linha o que leu.

1. O [README técnico](../../docs/README.md), em especial `§ Parâmetros do processo`, e o
   [CLAUDE.md](../CLAUDE.md) do projeto.
2. O item de [PENDENCIAS](../../docs/PENDENCIAS.md), **pelo número**. Não achou? Ou a spec nasce de um
   item novo, ou o operador confirma que a mudança não estava na fila. Diga qual dos dois.
3. As regras do PRD (`docs/Prd.md`) e a spec técnica do assunto.
4. O código afetado e as fixtures reais que cobrem o caso.

**Proibido perguntar o que o código responde.** A entrevista existe para o que só o operador
sabe: a intenção, a evidência, o limite e o risco.

---

## §2. A entrevista

Rodadas curtas, no máximo quatro perguntas por rodada, com `AskUserQuestion` e opções concretas
sempre que houver. **Entre uma rodada e a seguinte, confirme a resposta no código.** Divergência
achada volta como pergunta, com o `arquivo:linha` na mão.

**Toda pergunta traz a sua recomendação**, primeira opção, marcada "(Recomendado)", com o
motivo. **Pergunte primeiro o que decide as outras:** o eixo 8 e o 3 costumam vir antes.

| # | Eixo | O que tem de sair da resposta |
|---|---|---|
| 1 | **Problema** | O defeito ou a necessidade em uma frase, **com evidência**: trecho real da norma, `arquivo:linha`, saída do relatório. Sem evidência, a spec não nasce |
| 2 | **Estado final** | Como se prova que acabou. Observável (caso de aceite A*, snapshot) |
| 3 | **Fronteira** | O que fica de fora, de propósito, e por quê |
| 4 | **Consumidores** | Quem lê a saída? O esquema do JSON e a CLI mudam? A Etapa 2 é afetada? |
| 5 | **Contrato** | O que muda de comportamento visível: esquema do JSON, relatório, opção da CLI, código de saída |
| 6 | **Compatibilidade** | Snapshot que muda, base já gerada que perde validade |
| 7 | **Fontes** | Qual fixture real prova o caso? Depende de fonte que não está no repositório (T1)? |
| 8 | **Decisão** | Contradiz ou completa o PRD? Se sim, **o PRD §12 vem primeiro** e a spec o executa |

Nenhum eixo é opcional: o que não se aplica é dito na spec, não omitido.
**Spec não decide, spec executa decisão.**

---

## §3. O que não se resolveu

Pergunta sem resposta **não** trava a spec. Vira a seção `## Em aberto`, dizendo quem pode
responder e o que está parado, e bloqueia **só a fase que depende dela**.

---

## §4. O molde

Arquivo: `.claude/processo/specs/<slug>.md`. **Teto: 200 linhas.** Passou disso, são duas specs.

```markdown
# Spec — <título>

> Decisão que executa: Prd §N / pendência P0N — ou "nenhuma decisão nova". Item: PENDENCIAS #N.
> Escrita em <AAAA-MM-DD> contra `<sha>`, branch `<branch>`.
> Fechada a última fase, este arquivo é apagado (o git preserva).

## Problema
## Estado final
## Fora do escopo, de propósito
## Contrato
## Fases
## Em aberto
```

**A spec não vira diário.** O que sobrevive à execução vai para o PRD, a spec técnica ou o
README técnico; o resto morre com o arquivo.

---

## §5. Fatiamento em fases

1. **Fase = um commit revertível sozinho.**
2. **Portões verdes ao fim de cada fase.**
3. **Um assunto por fase.** Se a mensagem de commit precisa de um "e", são duas fases.
4. **Ordem aditivo → consumidores → remoção.** Cada fase deixa o sistema de pé.
5. **Mudança de contrato incompatível** (esquema do JSON, CLI) tem fase própria.
6. **Teto de ~10 arquivos ou ~200 linhas de diff**, salvo exceção declarada (renomeação
   mecânica, fixture grande).
7. **Teste e documentação vão na fase que os gera.** A última fase é sempre a de fechamento:
   risca o item em PENDENCIAS, atualiza "Agora", ajusta PRD, spec técnica e `revisao.md` e
   **apaga a spec**.
8. Fase que depende de uma pergunta do §3 nasce marcada **bloqueada**.
9. **A spec basta a cada fase.** O `/fase` lê só a spec, os arquivos da fase e o CLAUDE.md.
   O que a fase precisa a mais (`arquivo:linha`, regra do PRD) está citado na linha dela.
10. **Regex só muda com teste.** Fase que altera padrão (PRD §8) traz o caso real na mesma fase.
11. **Snapshot** só é regravado em fase própria ou com justificativa em `revisao.md`.
12. **Norma nova** entra por perfil `.toml` (D2); fase que precisaria de `if norma == ...` no
    parser volta para a spec.

```markdown
| # | Fase | Toca | Aceite | Modelo | Feito |
|---|---|---|---|---|---|
| ~~1~~ | ~~Função nova + teste~~ | 2 arquivos | portões verdes; nenhum chamador ainda | Sonnet | **2026-09-23 `abc1234`** |
| 2 | Parser e perfil | 3 arquivos | portões verdes; A3 passando | Sonnet | |
| 3 | Fechamento | docs | — | Sonnet | |
```

Fase feita é riscada com `~~…~~` e fecho em negrito com data e sha, nunca `- [x]`.
O **Aceite** é frase verificável. O **Modelo** é a família recomendada: **Opus** quando a fase
decide algo que a spec não fixou (ver "Fase pede Opus quando" nos Parâmetros do processo);
**Sonnet** quando só executa. Na dúvida, Opus. Quem troca de modelo é o operador.

---

## §6. Limites

1. **Não escreve código.**
2. **Não cria branch, não indexa, não commita.** Ao terminar, `git status --short` tem
   exatamente um arquivo a mais: a spec.
3. **Respeita o "Proibido" dos Parâmetros do processo.**
4. **Não decide pelo PRD.** Contradição ou lacuna vai para `docs/Prd.md` §12, ou para "Em aberto".
