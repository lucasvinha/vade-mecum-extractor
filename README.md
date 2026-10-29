# vade-mecum-extractor

Converte legislação bruta (HTML do Planalto, `.mht` salvo, PDF com texto) em uma base JSON
hierárquica — artigo › parágrafo › inciso › alínea, com rubricas, penas e notas — e gera
recortes de artigos a partir dela. A base é lida pela Etapa 2 (material de estudo).

A documentação técnica começa em [docs/README.md](docs/README.md): arquitetura, stack,
contratos, testes e o mapa do código. Este arquivo só diz por onde entrar.

## Subir local em 5 minutos

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
pytest
```

- `uv venv --python 3.12` cria o ambiente virtual `.venv` com Python 3.12. Retorno: o caminho do `.venv`.
- `uv pip install -e ".[dev]"` instala o pacote em modo editável (`-e`) com as dependências de
  desenvolvimento (`[dev]`). Retorno: a lista de pacotes instalados.
- `pytest` roda a suíte. Retorno: `N passed`.

Sem `uv`: `python -m venv .venv` e `pip install -e ".[dev]"`. Uso da CLI e detalhes:
[docs/negocio/recorte-e-cli.md](docs/negocio/recorte-e-cli.md).

## Quero…

| Fazer | Comece por |
|---|---|
| Entender como o sistema é montado | [docs/README.md](docs/README.md) |
| Entender uma regra de negócio | [docs/negocio/](docs/negocio/) |
| Saber por que algo é assim | [docs/decisoes/](docs/decisoes/) |
| Corrigir algo pequeno (um commit) | [PADRAO_OURO](docs/PADRAO_OURO.md) e commit direto; ver [processo](docs/processo/README.md) |
| Criar um módulo ou mudar algo maior | [docs/processo/README.md](docs/processo/README.md): spec → fases |
| Revisar antes do PR | [docs/processo/REVISAO.md](docs/processo/REVISAO.md) |
| Auditar um módulo inteiro (herdado, ou antes de refatorar) | [docs/processo/AUDITORIA.md](docs/processo/AUDITORIA.md) |
| Saber o que falta fazer | [docs/PENDENCIAS.md](docs/PENDENCIAS.md) |

## Licença

MIT.
