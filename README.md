# Montco — Prospecção B2B assistida

App local pronto para rodar (Node 22+, **sem instalar dependências**), com aprovação humana obrigatória: ele nunca envia e-mail.

## Rodar em 3 comandos
```bash
cp .env.example .env                    # preencha ANTHROPIC_API_KEY e ANTHROPIC_MODEL
export $(grep -v '^#' .env | xargs)     # ou defina as variáveis no seu shell
npm start                               # abre em http://localhost:3000
```
Só para ver o fluxo sem chave: `npm run demo` (IA **simulada**, banco em memória, aviso visível na tela).

Uso: Config (preencha "funcionalidades existentes" e remetente) → Leads (importe `data/exemplo_leads.csv` ou o seu) → abrir lead → *Pesquisar e qualificar* → Fila de revisão (aprovar/editar/rejeitar) → *Copiar e-mail* e enviar você mesmo → *Marquei como enviado* → registrar resposta/etapas → Dashboard. Exportação CSV/JSON em *Exportar*. Dados em `data/montco.sqlite`.

Pesquisa: o app lê apenas o site oficial cadastrado (1 GET) e os trechos de fontes que você colar na coluna `fonte_trecho` do CSV. Sem texto de fonte, nada é gerado.

## Status honesto
Testado aqui (39 testes + execução real do servidor e da interface no navegador): importação, dedup, fila, aprovação com bloqueios, funil, supressão, dashboard, exportação, falha explícita sem chave.
**Não testado**: chamada real à API da Anthropic (sem chave neste ambiente; o cliente é testado com um fetch simulado) e a pesquisa em sites reais. Faça a primeira qualificação com 1 empresa e confira o resultado.

## Caminho alternativo (n8n + Google Sheets)
Mantido em `workflows/`, `sheets/` e `docs/setup.md`; **não testado em instância n8n**. O app local reutiliza a mesma lógica de `src/lib`.

## Testes
```bash
npm test          # sem rede, empresas fictícias
npm run build     # regenera workflows/*.json
```
