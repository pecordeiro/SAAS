# Guia de segurança deste repositório

- Toda consulta a dados de cliente filtra por company_id da sessão (g.company.id).
  Buscar por id sem company_id é falha de isolamento (IDOR).
- Rotas de escrita exigem tenant_required com o papel mínimo correto.
- Formulários POST levam CSRF. Nenhuma rota de escrita aceita GET.
- Webhook do Asaas: validar o header asaas-access-token com comparação em tempo
  constante (hmac.compare_digest) e gravar o id do evento com UNIQUE antes de processar.
- Tokens (convite, reset de senha, API) são guardados só como hash.
- Não logar senha, token, DATABASE_URL, chave do Asaas nem payload completo de pagamento.
- Nenhum |safe ou Markup em conteúdo vindo do usuário.
- Redirecionamento só para caminho interno (sem open redirect).
- CSV exportado neutraliza células que começam com = + - @.
