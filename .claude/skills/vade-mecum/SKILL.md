---
name: vade-mecum
description: Gera o vade mecum em HTML de uma matéria do edital (Etapa 3) a partir dos recortes, confere o texto legal com o `conferir` até sair 0 e pede o PDF ao operador. Use quando o operador pedir o vade mecum, o material de estudo ou o HTML de uma matéria (`/vade-mecum penal`).
---

# Vade mecum — carregador

As instruções vivem em `docs/etapa3/INSTRUCOES.md`, neutras de LLM. Esta skill só as liga ao
Claude Code. Os caminhos valem a partir da raiz do repositório.

Argumento: o `id` da matéria em `claude/topicos-oj2026.json` (ex.: `penal`).

1. **Etapas 1 e 2, só se faltar arquivo.** Para cada `norma` dos grupos da matéria:
   - sem `dados/bases/<norma>/base.json`, rode
     `python -m vademecum extrair --fonte dados/fontes/<norma>/<arquivo>.mht --perfil <norma> --saida dados/bases/<norma>/base.json`;
   - sem `dados/recortes/oj26/<materia>/<norma>.json`, rode
     `python -m vademecum recortar --base dados/bases/<norma>/base.json --topicos claude/topicos-oj2026.json --materia <materia> --saida dados/recortes/oj26/<materia>/<norma>.json`.

   Norma sem fonte `.mht` ou sem perfil: pare e diga ao operador qual falta (perfis no M7).
2. **Leia `docs/etapa3/INSTRUCOES.md` inteiro e siga-o**, inclusive o laço do `conferir`.
3. Não termine com o `conferir` saindo diferente de 0. Ao fim, mostre a última execução dele e
   peça ao operador que abra o HTML no navegador, salve o PDF ao lado e confira capa e rodapé.
4. Não commita: o commit é do operador, ou da fase que chamou a skill.
