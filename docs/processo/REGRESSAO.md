# Roteiro de regressão

> Executável por `/regressao`. Prova que o comportamento observável que não devia mudar não
> mudou, e que o que devia mudar mudou como a spec disse. **Não corrige nada.**
> Como roda neste projeto: "Regressão" dos Parâmetros do processo, em `docs/README.md`.

Argumento recebido (opcional): `$ARGUMENTS` (a base de comparação; padrão, a branch principal).

---

## §0. Planejar (sessão curta, só leitura)

```bash
git diff <base>...HEAD --stat
git log --oneline <base>..HEAD
```

Cruze os arquivos com a lista de cenários do projeto (caminho nos Parâmetros do processo) e
entregue no chat:

1. **Os cenários** que o diff exige, cada um com o motivo em uma linha.
2. **O insumo** de cada um (processo, usuário, registro de exemplo) que o operador separa antes.
3. **Os blocos**, se a lista passar de ~15 chamadas ou de um assunto: um bloco por sessão, com o
   relatório do anterior como entrada. Regressão grande se fatia como spec.

---

## §1. Portão de entrada

- Worktree limpa, na branch a testar ("Untracked tolerados" dos Parâmetros não contam).
- As fontes brutas de cada cenário em `dados/` (fora do git). Faltou uma, o cenário sai como
  **não executado**; não baixe nada sem o operador pedir.
- Nada de escrita fora da pasta de relatórios; snapshot versionado não se regrava aqui.

---

## §2. Executar — snapshot e antes/depois da base

1. **Snapshot:** `pytest -m regressao` na branch. Falha é **regressão** até a spec dizer que a
   mudança era esperada.
2. **Antes/depois:** na **base**, gere a base de cada cenário com
   `python -m vademecum extrair --fonte <fonte> --perfil <perfil> --saida <pasta de relatórios>/antes/<cenario>.json`;
   na **branch**, o mesmo em `.../depois/<cenario>.json`.
3. Compare os pares ignorando o que varia por natureza (`capturado_em`, `sha256` de fonte baixada).
   A saída é determinística, então qualquer outra diferença conta. Diferença esperada pela spec →
   **esperado**. Qualquer outra → **regressão**.

Script de comparação fica em `scripts/` e é reaproveitado entre execuções.

---

## §3. Relatório

`RELATORIO_regressao_<branch>_<AAAA-MM-DD>.md` na pasta de relatórios (gitignored):

1. Base e branch com sha, ambiente usado, bloco executado.
2. Uma linha por cenário: **ok** / **esperado** (cita a spec) / **regressão** (o diff do JSON,
   resumido) / **não executado** (o insumo que faltou).
3. O que o próximo bloco precisa saber.

---

## §4. Limites

1. **Não corrige.** Regressão achada vira item para outra sessão.
2. **Respeita o "Proibido"**: nada de DML, nada de automação contra ambiente não permitido.
3. **Não commita.** Os artefatos ficam na pasta de relatórios, fora do git.
