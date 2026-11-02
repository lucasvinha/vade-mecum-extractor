# Vade Mecum Penal — especificação de estilo (amostra feita no projeto OJ TJSP 2026)

> **Para que serve:** registrar a camada visual aplicada ao vade mecum anotado do Código Penal (sessões de 22 e 23/10/2026), para que o projeto `vade-mecum-extractor` reproduza no HTML → PDF o que hoje falta: regras de estilo, marca-texto conceitual e quadros comparativos.
>
> **Origem:** a amostra foi feita sobre o `.docx` (python-docx, edição por *run*). O arquivo de referência é `VadeMecum-CodigoPenal-TJSP-OJ-2026-ANOTADO.docx`. Abaixo, cada regra vem adaptada para HTML/CSS.

---

## 1. Princípio inegociável — fidelidade ao texto legal

- **Nenhuma palavra do texto legal é alterada.** A intervenção é só de formatação. A VUNESP cobra a literalidade, e paráfrase treina o raciocínio certo com as palavras erradas.
- A numeração do próprio Código vira **hierarquia visual**. Nada de reescrever a lei em bullets. Se um dia houver versão parafraseada, ela será outro documento.
- Quadros, diagramas e cards são **curadoria**, não lei. No PDF, isso aparece rotulado ("material de apoio elaborado para estudo — não é texto de lei").
- **Camadas separadas:** a curadoria fica em `dados/curadoria/<slug>.json`, com `ancora` apontando para o `id` do dispositivo, e nunca entra no `diploma.json`. Se a lei for capturada de novo, a curadoria se religa pelos ids.

## 2. Layout da página

| Elemento | Regra |
|---|---|
| Página | A4, **duas colunas** com fio separador (decisão de 22/10) |
| Quadros comparativos | **largura total** (`column-span: all`), no fluxo, logo depois do último artigo comparado |
| Títulos / Capítulos / Seções | centralizados, **azul**, aparecem mesmo quando o edital cobra só parte do título |
| Rubrica (nome do crime) | **negrito**, em linha própria, antes do artigo. É por ela que a VUNESP referencia o dispositivo |
| `Art. N` | negrito no início do caput |
| Caput | nível 0 |
| §§ | recuo 1 |
| Incisos | recuo 2 |
| Alíneas | recuo 3 |
| **Pena** (preceito secundário) | **vermelho escuro (#9C0006), recuada, em linha própria**, separada do preceito primário |
| Notas legislativas | cinza, corpo reduzido |
| Saltos do edital | marcador "· · · arts. X a Y — fora do edital · · ·" |
| Revogados dentro da faixa | mantidos com a redação do compilado ("Revogado pela Lei …"), para não parecer omissão |

**"Arte nos enumeradores"** (pedido original): na amostra, isso foi feito só com hierarquia de recuo. No HTML, os rótulos (`§ 1º`, `I`, `a`) podem virar uma marca visual discreta, como selo ou cor de rótulo, desde que o texto do rótulo continue literal.

## 3. Marca-texto conceitual — paleta semântica (6 categorias)

A cor marca a **função do trecho** no tipo penal, e não um grau genérico de "importância".

| Código | Cor | Categoria | Exemplos | Por que separar |
|---|---|---|---|---|
| `y` | **Amarelo** | conduta nuclear (verbo do tipo) | *Apropriar-se*, *Exigir*, *Solicitar ou receber* | é o que a banca troca na pegadinha |
| `g` | **Verde** | sujeito / qualidade exigida | *funcionário público*, *o médico*, *Diretor de Penitenciária* | quem pode praticar |
| `c` | **Ciano** | elemento especializante | *de que tem a guarda em razão do cargo*, *por erro de outrem*, *vantagem indevida* | o detalhe que separa o tipo do vizinho |
| `m` | **Magenta** | prazos, frações e quantidades | *um terço até a metade*, *sexta parte*, *6 meses* | alvo clássico de prova |
| `l` | **Cinza claro** | subsidiariedade e procedibilidade | *se o fato não constitui crime mais grave*, *somente se procede mediante representação* | muda o enquadramento ou a ação penal |
| — | **Vermelho (fonte)** | pena | preceito secundário inteiro | leitura rápida da sanção |

**Regras de aplicação:**
- **Teto de cerca de 15% da mancha de texto por artigo.** Grifo que cobre tudo não destaca nada. Na amostra, o 313-A e o 316 §1º passaram do ponto, e esses casos devem ficar mais enxutos.
- Densidade escolhida em 22/10: **o nível da amostra** (verbo + sujeito + especializante + condicionantes).
- No Word havia o limite de 15 cores de `w:highlight`. **Em HTML esse limite não existe**, mas a semântica de 6 categorias continua sendo o teto: mais do que isso deixa de funcionar.
- Uso permitido: material de estudo em casa. A vedação de marca-texto do edital vale só para o caderno de prova.
- **Legenda obrigatória** no início ("Como ler os destaques"), com uma amostra de cada cor e a descrição da categoria.

### Como as marcações eram declaradas (formato a reaproveitar)

```python
D('Art. 314 -', [('Extraviar', 'y'), ('sonegá-lo ou inutilizá-lo', 'y'),
                 ('de que tem a guarda em razão do cargo', 'c'),
                 ('se o fato não constitui crime mais grave', 'l')])
```

Para o JSON de curadoria, proposta equivalente:

```json
{"ancora": "art314", "marcas": [
  {"trecho": "Extraviar", "cat": "verbo"},
  {"trecho": "de que tem a guarda em razão do cargo", "cat": "especializante"},
  {"trecho": "se o fato não constitui crime mais grave", "cat": "subsidiariedade"}
]}
```

- O casamento é por **substring exata** no `texto` do nó, depois de normalizar para **Unicode NFC**. A amostra quebrou com acentos NFD.
- Trecho não encontrado deve **gerar aviso, nunca falhar em silêncio**. A amostra gerava uma lista `AVISOS` ao final.
- No CSS, cada categoria vira uma classe (`.hl-verbo`, `.hl-sujeito`, `.hl-espec`, `.hl-quant`, `.hl-subsid`, `.pena`), com `-webkit-print-color-adjust: exact` para as cores saírem no PDF.

## 4. Quadros comparativos

**Gatilho:** dois ou mais tipos que a banca historicamente confunde.
**Formato:** título "▸ QUADRO COMPARATIVO — …" em azul, tabela com cabeçalho e uma **nota de rodapé** com a distinção-chave. Negrito marca o elemento que diferencia.

A amostra completa tinha **15 quadros**. Recuperei 11 do histórico:

| # | Quadro | Âncora (depois de) | Colunas | Nota-chave |
|---|---|---|---|---|
| 1 | Peculato e figuras próximas — 312, §1º, §2º, 313, 313-A, 313-B, 314 | art. 314/315 | Tipo · Conduta · O que separa · Pena | 313-A é o único com fim especial (vantagem/dano); 313-B se contenta com modificação não autorizada |
| 2 | Verbo nuclear — 316 × 317 × 333 × 332 × 357 | art. 317 §2º | Tipo · Verbo · Quem pratica · Observação | EXIGIR (concussão) × SOLICITAR/RECEBER/ACEITAR (passiva) × OFERECER/PROMETER (ativa, particular) |
| 3 | Omissões do dever funcional — 319 × 319-A × 320 × 321 × 323 × 324 | Cap. I | — | prevaricação × condescendência × advocacia administrativa |
| 4 | Violação de domicílio — quando a entrada **não** é crime (art. 150) | art. 150 §5º | Situação · Permitida? · Base | de dia + formalidades legais = cumprimento de mandado (§3º, I); conceito de "casa" (§§4º–5º) |
| 5 | Falsidades documentais — 296 × 297 × 298 × 299 × 300 × 304 | art. 305 | Tipo · Conduta · Objeto · Pena | material (forma) × ideológica (conteúdo) |
| 6 | Identidade e documento alheio — 307 × 308 × 304 | art. 311-A | Tipo · Conduta · Há doc. falso? · Pena | 307/308 expressamente subsidiários |
| 7 | Supressão/extravio de documento — 305 × 314 × 337 | art. 337 | Tipo · Quem pratica · Relação com o doc · Pena | nota sobre o 336 (edital/selo), comum no cumprimento de mandado |
| 8 | Resistência × desobediência × desacato — 329 × 330 × 331 | art. 331 | Tipo · Conduta · Meio · Pena | há violência/ameaça? Resistência §1º (ato não se executa) e §2º (concurso com a violência) |
| 9 | Imputações e declarações falsas — 339 × 340 × 341 × 342 | art. 343 | Tipo · O que faz · Contra quem · Pena | só o 342 admite retratação (§2º); 343 = suborno |
| 10 | Homicídio qualificado × causas de aumento × §2º-D | art. 121 | — | — |
| 11 | Lesão corporal por resultado (§§1º a 3º) | art. 129 | — | grave × gravíssima × seguida de morte |

**Os outros 4** não apareceram no histórico que consegui recuperar. [Provável] São os da Parte Geral, entregues no bloco 1 (arts. 1º–12, 100–120). Para recuperá-los, abra o `.docx` ANOTADO.

**Candidatos previstos e ainda não feitos:**
- decadência (103) × renúncia (104) × perdão (105–106);
- prescrição retroativa × intercorrente (110 §1º × 117);
- art. 327 (conceito de funcionário público).

> ⚠️ As penas digitadas dentro dos quadros são **curadoria escrita à mão**, não texto extraído. Antes de reaproveitar, confira cada uma contra o `recorte_oj26.json`, de preferência com um teste automático que compare o quadro com o nó `pena` da âncora. Em especial, o art. 129 §9º e as penas alteradas pelas leis de 2024–2026.

## 5. Planejado e ainda não implementado (sessão de 22/10)

- **Diagramas em SVG inline**, largura total, até uma página, na ordem de retorno:
  - art. 129 (gradação das lesões);
  - art. 109 (tabela de prazos);
  - art. 7º (extraterritorialidade como árvore de decisão);
  - art. 117 (linha do tempo das interrupções);
  - art. 107 (causas de extinção agrupadas).
- **Flashcards** em arquivo separado `<slug>-cards.pdf`:
  - grade 2×4 em A4, impressão frente e verso;
  - frente: rubrica + verbo nuclear; verso: pena + elemento distintivo;
  - cerca de 55 cartões (Parte Especial com preceito secundário);
  - **não entram no corpo do vade mecum**.

## 6. Capa e avisos de leitura

1. **Artigos com letra incluídos:** 313-A, 313-B e 319-A (dentro das faixas). Total de 90 artigos.
2. **Artigos com letra fora:**
   - 121-A e 121-B, incluindo o feminicídio, que saiu do 121 §2º, VI pela Lei 14.994/2024;
   - 154-A e 154-B;
   - 337-A a 337-P;
   - 359-A a 359-U.

   Ficam fora porque vêm depois do último número da faixa, que é a leitura literal do edital.
3. **Saltos e revogados:** como descrito na seção 2.
4. **Selo de data da compilação:** o texto foi capturado em 26/10/2026, e o edital considera a legislação até 19/10/2026.
5. **Legenda de cores** (seção 3) e o aviso de que os quadros são material de apoio.

## 7. Correções de extração já identificadas (verificar no extrator novo)

**Da amostra (fonte PDF → docx):**
- art. 129 §2º, III sumido;
- rubrica do art. 109 reduzida a "o";
- "§" sem ordinal (109, 110, 121, 129, 311-A);
- parágrafos colados: 7º, I, a; 107, IX; 114, II; 296, II;
- acentos em NFD.

**Do `recorte_oj26.json` (fonte HTML Planalto, análise de 02/11):**
- notas duplicadas em 12 nós (6º–11, 121 §2º IX, 298 p.ú.…);
- "Vigência" e "(Vigência)" misturados;
- ordinal "1o" em 6 trechos;
- pena por remissão no art. 304;
- "Detenção" com maiúscula no 326;
- "Capítulo V" em caixa baixa.
