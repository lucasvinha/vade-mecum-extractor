# Roteiro da fase — implementar uma fatia e parar

> Executável por `/fase`. Executa **uma** fase da spec ativa (o [SPEC](SPEC.md) diz como ela
> nasce). **Uma fase, um commit, e para.** O operador revisa e commita; só então vem a próxima.

Argumento recebido (opcional): `$ARGUMENTS`.

---

## §0. Alvo

| Argumento | Alvo |
|---|---|
| *(vazio)* | A spec de [specs/](specs/) com fase em aberto. Havendo mais de uma, a que já tem fase feita; empate, pergunte |
| Caminho de uma spec | Essa spec, primeira fase em aberto |
| Um número | Essa fase da spec ativa, só com a anterior fechada ou com o operador dizendo por quê |

Sem spec, não há o que executar: diga isso e proponha o `/spec`.

---

## §1. Portão de entrada

**Leitura, e só ela.** A spec foi escrita para bastar (SPEC §5.9). Leia:

1. A spec ativa, inteira.
2. Os arquivos da coluna "Toca" e os `arquivo:linha` que a spec cita para esta fase.
3. O [CLAUDE.md](../CLAUDE.md) do projeto e `docs/README.md § Parâmetros do processo`.
4. O PRD (`docs/Prd.md`) ou a spec técnica **só na regra que a linha da fase citar** (ID H*, P*, RF*…).

Se faltar contexto, o defeito é da spec: complete-a em vez de sair lendo a documentação.

```bash
git status --short                                                 # worktree limpa
git log --oneline --grep "de .claude/processo/specs/<slug>.md"     # fases que já entraram
git ls-files --others --exclude-standard                           # untracked que sobraram
```

O `--grep` casa com o corpo que o §4 põe em todo commit de fase.

- **Worktree suja** com sobra de fase anterior → **pare e diga o que está pendurado.** Os
  "Untracked tolerados" dos Parâmetros do processo não contam: diga que os ignorou.
- **Fase aberta na spec mas presente no `git log`** → risque-a primeiro, com data e sha.
- **Fase bloqueada** → pare e mostre a pergunta em aberto.
- **Modelo** da fase diferente do desta sessão → antes de ler código, pergunte com
  `AskUserQuestion`: parar para o operador rodar `/model <recomendado>` e chamar `/fase` de novo
  (recomendado), ou seguir no modelo atual.
- Diga em uma linha: **qual fase, em qual modelo, quais arquivos, qual é o aceite.**

---

## §2. Implementação

**Só esta fase.** Nada da seguinte, mesmo que sejam três linhas. Vale o CLAUDE.md do projeto
(parser genérico, nenhuma perda silenciosa, determinismo, texto legal literal).

Se a fase revelar que a spec está errada, **pare, relate e corrija a spec.** Se contradisser o PRD,
registre em `docs/Prd.md` §12 e pergunte: não decida sozinho.

---

## §3. Portões

Os de `docs/README.md § Parâmetros do processo`, a partir da raiz.

- **Vermelho não fecha a fase.** No Claude Code, invoque a skill `depuracao-sistematica` com o
  teste e a saída; em outro ambiente, ache a causa raiz antes de mudar o código. A entrega
  continua a do §4. Causa no que esta fase escreveu: a correção entra na fase. Vermelho também
  no `HEAD` limpo: a falha é anterior, não se corrige aqui e vai para a entrega como anterior.
- Aviso de lint em arquivo que a fase editou se corrige no arquivo inteiro. Diga qual regra aplicou.
- Diff sem código: rode a suíte assim mesmo.
- Caiu na "Conferência manual" dos parâmetros: faça e mostre o resultado.
- **Regra do PRD citada:** cada regra que a fase tocou aparece pelo ID no teste ou no comentário, e
  mudança de regex traz o caso real que a motivou. Faltando, volta para esta fase.

---

## §4. Entrega

1. **O diff:** `git diff --stat` mais os untracked nomeados um a um.
2. **O aceite, item a item**, com a evidência.
3. **Estourou o teto** (~10 arquivos / ~200 linhas)? Diga e proponha o corte das próximas.
4. **A mensagem de commit** em `$(git rev-parse --git-dir)/COMMIT_SUGERIDO.txt`, em
   Conventional Commits com os escopos do README técnico, e o corpo citando a fase:

   ```
   <tipo>(<escopo>): <descrição>

   Fase N de .claude/processo/specs/<slug>.md.
   ```

5. **O comando** para o operador revisar:

   ```bash
   git commit -e -F "$(git rev-parse --git-dir)/COMMIT_SUGERIDO.txt"
   ```
6. **A linha de fecho:** `Testes: N passed`, ou `Testes: N falharam (test_x, test_y)`.

Não risque a fase agora: ela se fecha no §1 da próxima execução, quando o commit existir.

---

## §5. Limites

1. **Não commita e não faz push.** `git add` só para montar a mensagem.
2. **Não avança para a fase seguinte.**
3. **Respeita o "Proibido" dos Parâmetros do processo.**
4. **Não reescreve histórico:** nada de `reset`, `rebase`, `amend` ou `stash` sem pedido.
