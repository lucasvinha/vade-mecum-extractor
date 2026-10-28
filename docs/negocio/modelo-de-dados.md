# Modelo de dados — regras de negócio

**O que o sistema decide**, não como o código faz isso. A arquitetura está no
[PADRAO_OURO](../PADRAO_OURO.md) e as decisões em [decisoes/](../decisoes/). As âncoras são
nomes de função ou de módulo. Em divergência com o código, **vale o código**.

O formato da base e do recorte: é o contrato do projeto, lido pela Etapa 2. Usado por `modelo.py`
e `segmentador.py`. A serialização (chaves ordenadas, `null` em campo ausente) está em
[docs/README.md § Contratos](../README.md#contratos). Vizinhos:
[vigencia-e-notas.md](vigencia-e-notas.md) (o objeto nota) e [recorte-e-cli.md](recorte-e-cli.md).

## §1. Formato canônico (D5)

Formato canônico de saída: **JSON hierárquico**, UTF-8. CSV é rejeitado porque achata a árvore de dispositivos.

## §2. Saída

- **RF13** — Segmentar PDF multi-norma e identificar cada norma por título, número e data (P5).
- **RF17** — Gerar base completa em JSON e relatório de extração em JSON ou Markdown.
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
    {"id": "art121.pena1", "tipo": "pena", "texto": "reclusão, de seis a vinte anos."},
    {"id": "art121.p2", "tipo": "paragrafo", "rotulo": "§ 2º",
     "rubrica": "Homicídio qualificado",
     "texto": "Se o homicídio é cometido:", "notas": [],
     "filhos": [
       {"id": "art121.p2.i7", "tipo": "inciso", "rotulo": "VII", "texto": "contra:",
        "notas": [{"tipo": "redacao", "norma": "Lei nº 15.134", "ano": 2025, "data": null,
                   "bruto": "(Redação dada pela Lei nº 15.134, de 2025)"}],
        "filhos": [{"id": "art121.p2.i7.a", "tipo": "alinea", "rotulo": "a", "texto": "autoridade ou agente…"}]}
     ]}
  ]
}
```

- `id` é estável e derivado do rótulo: `art121`, `art121-A`, `art359-M-A`, `art121.p2-B`, `art121.pu` (parágrafo único), `.i7`, `.a`.
- `filhos` preserva a **ordem do texto**. Penas e dispositivos ficam intercalados, como na lei (H14).
- O texto vem **literal**, inclusive grafias antigas ("alguem", "conseqüências"). Normalizar ortografia é decisão da Etapa 2.

## §5. Armadilhas e limites conhecidos

- `parcial: true` marca artigo que a fonte traz incompleto (P7); não é erro.
- Campos de `local` são opcionais (P8): hierarquia ausente sai como `null`.
