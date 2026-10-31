# Modelo de dados — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O formato da base e do recorte: é o contrato do projeto, lido pela Etapa 2. Usado por `modelo.py`
e `segmentador.py`. A serialização (chaves ordenadas, bytes estáveis) está em
[docs/README.md § Contratos](../README.md#contratos). Vizinhos:
[vigencia-e-notas.md](vigencia-e-notas.md) (o objeto nota) e [recorte-e-cli.md](recorte-e-cli.md).

## §1. Formato canônico (D5)

Formato canônico de saída: **JSON hierárquico**, UTF-8. CSV é rejeitado porque achata a árvore de dispositivos.

## §2. Saída

- **RF13** — Segmentar PDF multi-norma e identificar cada norma por título, número e data (P5).
- **RF17** — Gerar base completa em JSON e relatório de extração em JSON (`base.relatorio.json`, [recorte-e-cli.md](recorte-e-cli.md)).
- **RF19** — Cada nó guarda `origem` ([pipeline-e-perfis.md](pipeline-e-perfis.md)), para depurar o parser.

## §3. Envelope

```json
{
  "schema_version": "1.0",
  "norma": {
    "id": "cp",
    "titulo": "DECRETO-LEI No 2.848, DE 7 DE DEZEMBRO DE 1940",
    "ementa": "Código Penal.",
    "tipo_fonte": "html",
    "fonte": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
    "capturado_em": "2026-10-26T02:03:12Z",
    "sha256": "…",
    "perfil": "cp"
  },
  "metadados": {"preambulo": "…", "rodape": "…"},
  "recorte": null,
  "artigos": [ ]
}
```

- `metadados` guarda o que fica fora da árvore de artigos (H17). É a única parte que pode diferir entre leituras da mesma página por `.mht` e por URL (A14).
- PDF multi-norma: o comando gera **um arquivo por norma**, com o mesmo envelope.
- No recorte, `"recorte": {"expressao": "121-130; 311-A", "origem": "base_cp.json"}`.

## §4. Nós (exemplo real — art. 121, trecho)

**Esquema estável por tipo.** Cada objeto tem um conjunto fixo de chaves. Dentro dele, opcional
ausente sai como `null` e lista vazia como `[]`; chave de outro tipo não aparece.

| Objeto | Chaves |
|---|---|
| `artigo` | `id` `tipo` `rotulo` `numero` `sufixo` `rubrica` `local` `texto` `notas` `parcial` `filhos` |
| `paragrafo`, `inciso`, `alinea`, `item` | `id` `tipo` `rotulo` `rubrica` `texto` `notas` `filhos` |
| `pena` | `id` `tipo` `texto` `notas` |
| nota (em `notas`) | `tipo` `norma` `ano` `data` `bruto` |
| `local` (só no artigo) | `parte` `livro` `titulo` `capitulo` `secao` `subsecao` `rotulo_livre` |

```json
{
  "id": "art121",
  "tipo": "artigo",
  "rotulo": "Art. 121",
  "numero": 121,
  "sufixo": [],
  "rubrica": "Homicídio simples",
  "local": {"parte": "PARTE ESPECIAL", "livro": null,
            "titulo": "TÍTULO I — DOS CRIMES CONTRA A PESSOA",
            "capitulo": "CAPÍTULO I — DOS CRIMES CONTRA A VIDA",
            "secao": null, "subsecao": null, "rotulo_livre": null},
  "texto": "Matar alguem:",
  "notas": [],
  "parcial": false,
  "filhos": [
    {"id": "art121.pena1", "tipo": "pena", "texto": "reclusão, de seis a vinte anos.",
     "notas": []},
    {"id": "art121.p2", "tipo": "paragrafo", "rotulo": "§ 2º",
     "rubrica": "Homicídio qualificado",
     "texto": "Se o homicídio é cometido:", "notas": [],
     "filhos": [
       {"id": "art121.p2.i7", "tipo": "inciso", "rotulo": "VII", "rubrica": null,
        "texto": "contra:",
        "notas": [{"tipo": "redacao", "norma": "Lei nº 15.134", "ano": 2025, "data": null,
                   "bruto": "(Redação dada pela Lei nº 15.134, de 2025)"}],
        "filhos": [{"id": "art121.p2.i7.a", "tipo": "alinea", "rotulo": "a", "rubrica": null,
                    "texto": "autoridade ou agente…", "notas": [], "filhos": []}]}
     ]}
  ]
}
```

- A ordem das chaves no exemplo é a de leitura; o arquivo sai com as chaves ordenadas (RNF03).
- `numero` é inteiro, sem separador de milhar; `rotulo` guarda a grafia da fonte (P13):
  `Art. 1.091-A` vira `numero: 1091`, `sufixo: ["A"]`.
- `sufixo` é a lista das letras, na ordem do rótulo (H11, H12): `[]`, `["A"]`, `["M", "A"]`.
- `id` é estável e derivado do rótulo, com o número normalizado (P13): `art121`, `art121-A`,
  `art359-M-A`, `art1091-A`. O `id` do filho é o do pai seguido do segmento: `.p2`, `.p2-B`,
  `.pu` (parágrafo único), `.i7` (inciso romano em inteiro), `.a` (alínea), `.pena1`, `.pena2`
  (contadas entre as penas do mesmo pai, a partir de 1). Ex.: `art121.p2.i7.a`. O `id` do item
  numérico fica para o marco do PDF (M8).
- Nota: `data` é texto ISO `AAAA-MM-DD`, ou `null` quando a fonte só traz o ano; o texto
  original da nota fica em `bruto` ([vigencia-e-notas.md](vigencia-e-notas.md)).
- `filhos` preserva a **ordem do texto**. Penas e dispositivos ficam intercalados, como na lei (H14).
- O texto vem **literal**, inclusive grafias antigas ("alguem", "conseqüências"). Normalizar ortografia é decisão da Etapa 2.

## §5. Armadilhas e limites conhecidos

- `parcial: true` marca artigo que a fonte traz incompleto (P7); não é erro.
- Campos de `local` são opcionais (P8): hierarquia ausente sai como `null`.
