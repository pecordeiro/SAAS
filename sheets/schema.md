# Esquema do Google Sheets (uma planilha, uma aba por tabela)

Crie as abas com exatamente estes cabeçalhos (linha 1). Os CSVs em `sheets/` podem ser importados.

| Aba | Colunas |
|---|---|
| Leads | id, nome, cnpj, site, cidade, uf, segmento, produtos, evidencias, ultima_pesquisa, contato_nome, contato_cargo, email, email_fonte, telefone, pagina_contato, score, justificativa, desconhecido, hipotese_problema, gancho, status, nao_contatar, proxima_acao, proxima_acao_data, resultado, motivo_perda, fonte_aquisicao, criado_em, atualizado_em |
| Fontes | lead_id, url, data_pesquisa, tipo, trecho, nivel (fato/inferencia/hipotese) |
| Fila | draft_id, lead_id, versao, assunto, corpo, validacao, estado (pendente/aprovado/rejeitado/enviado), criado_em, atualizado_em |
| Historico | em, lead_id, evento, de, para, por, detalhes |
| Supressao | lead_id, email, dominio, motivo, em |
| Config | chave, valor |

Chaves de `Config`: `peso_A`..`peso_G`, `min_amostra_conversao`, `etapas` (separadas por vírgula; vazio = padrão), `funcionalidades_existentes` (separadas por `;`), `funcionalidades_inexistentes` (termos proibidos, `;`), `link_apresentacao`, `link_site`, `link_formulario`, `link_kit_planilhas`, `link_roteiro`, `remetente_nome`, `remetente_contato`.
Links vazios = material não é citado.

Privacidade: guarde nome/cargo/e-mail/telefone apenas de canais comerciais publicados oficialmente, sempre com a URL da origem.
