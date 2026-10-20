# Montco — Prospecção B2B assistida

Fluxo de prospecção com **n8n + Google Sheets + Claude (API Anthropic)** e **aprovação humana obrigatória**.
Nenhum workflow envia e-mail: o sistema prepara, valida e coloca rascunhos numa fila; você revisa e envia manualmente.

## Conteúdo
| Caminho | Função |
|---|---|
| `workflows/*.json` | Fluxos n8n exportáveis (01 importação, 02 qualificação+rascunho, 03 revisão+funil, 04 dashboard+exportação) |
| `src/lib/` | Lógica testável: CSV, deduplicação, score, supressão, funil, validador de e-mail, métricas |
| `src/prompts/` | Prompts de qualificação e e-mail (regras anti-invenção) |
| `sheets/` | Esquema e CSVs de cabeçalho das abas |
| `scripts/build-workflows.js` | Gera os JSON a partir de `src/` (`npm run build`) |
| `data/exemplo_leads.csv` | Empresas **fictícias** para teste |
| `docs/` | Configuração, LGPD, pontuação |

## Execução rápida
```bash
npm test          # 33 testes, sem rede, empresas fictícias
npm run build     # regenera workflows/*.json
```
Depois siga `docs/setup.md`.

## Status honesto
Testado: lógica (`src/lib`), execução simulada dos Code nodes e validade estrutural dos JSON.
**Não testado**: execução real no n8n, Google Sheets e API Anthropic (sem instância nem credenciais neste ambiente). Importe, vincule credenciais e rode primeiro com o CSV de exemplo.
