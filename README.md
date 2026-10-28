# vade-mecum-extractor

Converte legislação bruta (HTML do Planalto, `.mht` salvo, PDF com texto) em uma base JSON
hierárquica — artigo › parágrafo › inciso › alínea, com rubricas, penas e notas — e gera
recortes de artigos a partir dela.

Documentação técnica: [`docs/README.md`](docs/README.md).

## Instalação

Requer Python 3.12.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
```

Sem `uv`: `python -m venv .venv` e `pip install -e ".[dev]"`.

## Uso

```bash
python -m vademecum extrair --fonte caminho/ou/url --perfil cp --saida dados/cp/base.json
python -m vademecum recortar --base dados/cp/base.json --artigos "121-130; 311-A" --saida dados/cp/recorte.json
```

## Desenvolvimento

```bash
ruff check . && ruff format --check .
pytest
```

Fases e status: [`docs/PENDENCIAS.md`](docs/PENDENCIAS.md).

## Licença

MIT.
