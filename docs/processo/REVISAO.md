# Roteiro de revisão pré-PR

> Executável por `/revisao`. Revisa o que está em curso: conformidade com o
> [PADRAO_OURO](../PADRAO_OURO.md) e as regras do projeto, mais os bugs.
> **Revisão é leitura.** Nada aqui corrige, commita ou toca em HML/PROD.
> **Sessão própria:** rode numa conversa nova e corrija os achados em outra. O que passa de uma
> para a outra é o relatório do §4.

O checklist **não** é redigido aqui: é o `§ Checklist de revisão` do PADRAO_OURO. Este roteiro
diz como executá-lo sobre um diff.

Argumento recebido (opcional): `$ARGUMENTS`.

---

## §0. Alvo e coleta

| Argumento | Alvo |
|---|---|
| *(vazio)* | Worktree não commitada |
| Uma branch (`main`…) | `git diff <base>...HEAD`, o recorte que o PR vai mostrar |
| Caminhos | Só esses arquivos |

```bash
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard   # git diff não mostra untracked: liste-os no relatório
```

Diga em uma linha o que vai revisar: arquivos alterados, novos e áreas tocadas.

---

## §1. Portões

Os de `docs/README.md § Parâmetros do processo`, **antes** da leitura, com a suíte rodando sob a
"Cobertura" dos Parâmetros. A medição do diff não reprova: diz quais linhas novas ou alteradas
nenhum teste executa, e o §2 decide o que vira achado. Rode também `scripts/verificar_docs.py`;
o achado em arquivo que o diff tocou entra.

Suíte vermelha não aborta: vai para o topo do relatório. Aviso de lint em arquivo tocado entra
inteiro se o projeto exige o arquivo limpo; senão, só o que o diff introduziu. Diga qual regra
aplicou. Guarde os números: eles fecham o relatório.

---

## §2. Conformidade

1. **O checklist do PADRAO_OURO, item a item**, contra o diff. Item com guarda automática que o
   §1 já provou é pulado, dizendo qual guarda.
2. **Regras do projeto que um diff viola calado:** as regras invioláveis do `CLAUDE.md`, o
   "Proibido" dos Parâmetros do processo, variável nova em todos os lugares exigidos
   (`docs/README.md § Configuração`), contrato mudado sem declarar.
3. **Docs acompanham a mudança:** item fechado riscado em PENDENCIAS; ADR, negócio ou README
   técnico atualizados se o diff os desmente; tetos respeitados; nenhuma referência por linha
   em doc perene.
4. **O que o diff deixou sem prova.** Linha que a cobertura do §1 deu como não executada vira
   achado `Importante` quando é regra de negócio, contrato ou caminho de erro. Em tela e
   código de ligação, só a contagem no cabeçalho. Correção de bug sem o teste que falharia
   sem ela também é achado.
5. **A função inteira.** A unidade de leitura é a função ou classe que o diff tocou, não a
   linha. Entra o defeito da mesma função de que a mudança depende ou que ela agrava. Entra
   também o que o diff introduz e o lint não pega: código comentado, comentário que narra
   histórico, citação por seção ou item.
6. <!-- opcional: paridade — para cada unidade gêmea, replicado / não se aplica (motivo) /
   faltando (vira achado). -->

**Filtro de ruído.** Descarte a dívida já registrada em PENDENCIAS (salvo se o diff a agravar),
o que está fora das funções tocadas, o que linter ou teste pegaria, e nitpick. Problema de fundo
da unidade, que não é desta mudança e já apareceu em revisão anterior, não se repete como achado:
anote "pede `/auditoria <unidade>`" ([AUDITORIA](AUDITORIA.md)). **Só reporte o que você
defenderia numa revisão de PR**; na dúvida, leia o código ao redor antes de escrever.

---

## §3. Bugs

No Claude Code, invoque a skill `code-review` (nível `high`, ou o que vier no argumento),
nomeando os untracked entre os alvos. Ela roda em segundo plano: siga com o §2, mas **não
escreva o §4 antes de ela voltar**. Sem ela, diga que a caça a bugs não entrou. Outros
ambientes: faça a leitura de correção à mão, arquivo a arquivo do diff.

---

## §4. Relatório

Gravado no caminho de "Relatório de revisão" dos Parâmetros do processo (gitignored), como
`REVISAO_<branch>_<AAAA-MM-DD>.md`:

1. **Cabeçalho:** alvo, sha do `HEAD`, contagem de arquivos, resultado dos portões e a cobertura
   do diff (N de M linhas; as não cobertas, por arquivo).
2. **Arquivos novos**, um a um.
3. **Achados** em `Crítico` e `Importante`: `arquivo:linha`, origem (item do checklist, regra,
   sem prova, paridade, `bug`), o que quebra e a correção sugerida. No fim, as unidades que
   pedem auditoria, se houver.
4. **Encerramento:** `Testes: N passed`.

Sem achado, uma linha dizendo isso. Na resposta: o caminho, a contagem por grupo e o fecho.

---

## §5. Limites

1. **Não corrige.** 2. **Não commita nem indexa.** 3. **Respeita o "Proibido".**
4. Ao terminar, `git status --short` está idêntico ao do §0.

A correção é outra sessão: ela lê o relatório e confere o sha contra o `HEAD` antes de corrigir.
