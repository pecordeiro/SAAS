# Resposta a incidentes de segurança

Fase 7. Vale para vazamento, acesso indevido (inclusive entre empresas), perda de dados,
indisponibilidade prolongada e segredo exposto. Base: LGPD art. 48 e Resolução CD/ANPD
nº 15/2024 (comunicação de incidente).

## Papéis
- **Responsável pelo incidente**: quem detectou até passar adiante; decide a severidade.
- **Encarregado (DPO)**: avalia risco aos titulares e faz as comunicações.
- **Quem executa**: aplica contenção e correção, sempre registrando o que fez e quando (UTC).

## 1. Conter (primeiras horas)
1. Abrir um registro do incidente (data/hora, quem detectou, o que se sabe) — tudo o que se
   fizer vai para ele.
2. Parar o vazamento: tirar a rota/feature do ar (flag, `FEATURE_PUBLIC_API=0`, deploy da
   versão anterior), revogar tokens (API, sessões: incrementar `session_version`), desativar
   contas ou acessos de suporte (`flask suporte revogar`).
3. Rotacionar segredos possivelmente expostos (seção “Rotação”).
4. Preservar evidência: exportar logs do período (o `X-Request-ID` liga resposta ↔ log),
   `audit_logs`, `platform_audit_logs`; não apagar nada antes de copiar.
5. Se o banco foi alterado indevidamente: snapshot antes de qualquer correção.

## 2. Avaliar (até 24 h)
- Quais empresas e titulares foram afetados (consultar `audit_logs` por período, IP e ação;
  logs por `route`/`company_id`/`user_id`).
- Quais dados (pessoais? de produção? credenciais?) e se estavam cifrados/hasheados.
- **Risco ou dano relevante** aos titulares? (Res. 15/2024: dados em larga escala, sensíveis,
  financeiros, de autenticação, ou que possam causar dano material/moral.) Registrar a
  conclusão e o porquê, mesmo quando a resposta for “não”.

## 3. Comunicar
- **ANPD**: se houver risco ou dano relevante, em até **3 dias úteis** do conhecimento do
  incidente, pelo formulário do site da ANPD, com: natureza dos dados, titulares afetados,
  medidas técnicas de proteção, riscos, motivo de eventual demora, medidas para reverter ou
  mitigar. Complementar depois se a investigação continuar.
- **Titulares afetados**: no mesmo prazo, linguagem simples, o que aconteceu, quais dados,
  o que fizemos, o que a pessoa deve fazer (ex.: trocar senha) e contato do encarregado.
- **Empresas clientes** (somos operadora): avisar os proprietários sem demora — elas são
  controladoras e também precisam avaliar e comunicar.
- Comunicação pública/status: só depois de alinhar o texto com o encarregado.
- Guardar o registro do incidente por **5 anos** (inclusive os não comunicados).

## 4. Corrigir e aprender
- Corrigir a causa, com teste que reproduz o ataque (ex.: caso A/B novo em
  `tests/test_isolation.py`).
- Revisão sem culpados em até 10 dias: linha do tempo, causa, o que funcionou, ações com
  responsável e prazo; atualizar `seguranca.md` e `riscos.md`.

## Rotação de segredos
Todos vêm de variáveis de ambiente (Render → Environment). Nunca colar segredo em chamado,
chat ou commit.

| Segredo | Como rotacionar sem derrubar todo mundo | Efeito colateral |
|---|---|---|
| `SECRET_KEY` | gerar nova (`python -c "import secrets; print(secrets.token_hex(32))"`); mover a antiga para `SECRET_KEY_FALLBACKS` (lista por vírgula); deploy. Sessões, prévias de importação e cookie de dispositivo assinados com a antiga continuam válidos. Depois de 12 h (vida da sessão) / 90 dias (dispositivo), tirar a antiga. **Em comprometimento: NÃO usar fallback** — todos saem. | formulários abertos perdem o CSRF (recarregar); “lembrar-me” cai |
| `MFA_ENCRYPTION_KEY` | definir `MFA_ENCRYPTION_KEY="nova,antiga"` (MultiFernet: cifra com a primeira, decifra com as duas); deploy; `flask mfa-rotacionar`; depois deixar só `nova`. Sem `MFA_ENCRYPTION_KEY`, a chave vem de `SECRET_KEY` + `SECRET_KEY_FALLBACKS` (mesma lógica) — recomenda-se uma chave própria em produção. | nenhum se seguir a ordem; segredo que não decifra com nenhuma chave exige o usuário reativar o MFA |
| Chave da API do Asaas | gerar nova no painel do Asaas, trocar `ASAAS_API_KEY`, deploy, revogar a antiga | chamadas em voo falham uma vez (retentativa) |
| Token do webhook do Asaas | trocar no painel e em `ASAAS_WEBHOOK_TOKEN` no mesmo minuto; reprocessar eventos recusados pela fila do Asaas | webhooks recusados no intervalo são reenviados pelo Asaas |
| `RESEND_API_KEY` | criar chave nova no Resend, trocar, deploy, apagar a antiga | e-mails no intervalo vão para o log de erro (sem conteúdo) |
| `DATABASE_URL` (senha do papel) | `ALTER ROLE ... PASSWORD` + atualizar a variável; com o Render, “rotate credentials” | reinício das conexões |
| `SENTRY_DSN` | gerar DSN novo no projeto e revogar o antigo | nenhum |
| Tokens da API de clientes | o proprietário revoga em Integrações → API; em incidente, revogar em lote no banco com auditoria | integrações param até receber token novo |

Periodicidade: `SECRET_KEY` e `MFA_ENCRYPTION_KEY` anualmente; chaves de terceiros a cada
6 meses ou na saída de alguém com acesso; sempre após suspeita.
