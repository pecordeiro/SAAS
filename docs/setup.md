# Configuração

## 1. Google Sheets
1. Crie uma planilha e as abas de `sheets/schema.md` (importe `sheets/*.csv`).
2. Preencha `Config`: `funcionalidades_existentes` (separadas por `;`; **obrigatório** — sem isso nenhum e-mail é gerado), `remetente_nome`, `remetente_contato`, e links reais (vazios = não citados).
3. Copie o ID da planilha para `GOOGLE_SHEET_ID`.

## 2. n8n
Variáveis de ambiente do n8n (ver `.env.example`): `GOOGLE_SHEET_ID`, `ANTHROPIC_MODEL`, `REVIEW_UI_TOKEN`, `SENDER_NAME`, `SENDER_CONTACT`.
Para os Code nodes lerem `$env`, defina `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` (ou ajuste conforme sua versão).
Credenciais (criadas no n8n, nunca no repositório):
- **Google Sheets OAuth2** — vincule em todos os nós Google Sheets.
- **Header Auth** chamado "Anthropic (header x-api-key)": nome `x-api-key`, valor = sua chave.
Importe os 4 JSON (Workflows → Import from file), vincule as credenciais e ative.

## 3. Importar leads
```bash
curl -X POST "$N8N/webhook/montco-import?token=$REVIEW_UI_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "$(jq -Rs '{csv: .}' data/exemplo_leads.csv)"
```
Colunas aceitas: `nome, cnpj, site, cidade, uf, segmento, produtos, fonte_url, fonte_aquisicao` (separador `,` ou `;`). Resposta: `{"novos":1,"mesclados":1,...}`. Duplicados por CNPJ válido ou domínio são mesclados; nome+UF só gera aviso.

## 4. Qualificar e gerar rascunho
```bash
curl -X POST "$N8N/webhook/montco-qualify?token=$REVIEW_UI_TOKEN" -H 'Content-Type: application/json' -d '{"lead_id":"<id>"}'
```
Consulta apenas o site oficial cadastrado (uma requisição GET) e as fontes que você registrou. Sem site/fonte, o fator fica "desconhecido" (não penaliza). Falha explícita se faltar `ANTHROPIC_MODEL`, chave ou `funcionalidades_existentes`.

## 5. Revisar e aprovar
Abra `https://<n8n>/webhook/montco-review?token=<REVIEW_UI_TOKEN>`. Ações: aprovar, editar, rejeitar, marcar enviado manualmente, registrar resposta, mudar etapa, agendar, não contatar, excluir dados pessoais. A aprovação revalida o texto (dores sem evidência, links e recursos não configurados, supressão). Após aprovar, copie o e-mail e envie por você mesmo.

## 6. Dashboard e exportação
- `/webhook/montco-dashboard?token=...`
- `/webhook/montco-export?token=...&sheet=Leads|Historico|Fontes|Supressao&format=csv|json`

Use HTTPS e mantenha o token secreto; rode o n8n em rede privada.
