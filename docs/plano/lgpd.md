# LGPD — inventário, bases legais, retenção e direitos

Fase 7. **Rascunho técnico — precisa de revisão jurídica antes do go-live (risco L6).**

## Papéis
- **Controladora**: cada empresa cliente, para os dados que ela coloca no sistema (pessoas da
  equipe, produção). Para os dados de conta/cobrança do próprio cliente, a plataforma é
  controladora.
- **Operadora**: a plataforma (Controle de Produção) em relação aos dados das empresas.
- **Suboperadores** (contrato/DPA com cada um): ver tabela “Operadores”.
- Encarregado (DPO): a definir antes do go-live (art. 41); e-mail de contato nas páginas de
  privacidade.

## Inventário de dados pessoais
| Dado | Titular | Onde | Finalidade | Base legal (art. 7º) |
|---|---|---|---|---|
| Nome e e-mail | usuários (proprietário, supervisor, operador) | `users` | conta, login, avisos | execução de contrato (V) |
| Hash de senha (Argon2id), segredo TOTP cifrado, códigos de recuperação (hash) | usuários | `users`, `mfa_recovery_codes` | autenticação | execução de contrato (V); segurança — legítimo interesse (IX) |
| E-mail de convidado | convidados | `invitations` | enviar o convite | legítimo interesse da empresa (IX) / procedimentos preliminares de contrato (V) |
| IP e ação | usuários | `audit_logs.ip`, logs de aplicação | segurança, prova, Marco Civil art. 15 | obrigação legal (II) para registros de acesso; legítimo interesse (IX) |
| Hash de e-mail/IP com contagem de falhas | qualquer pessoa que tente entrar | `login_throttles` | bloqueio de força bruta | legítimo interesse (IX) |
| Autor de cada registro de peças | operadores | `progress_entries.user_id` | histórico de produção | execução de contrato (V) com a empresa |
| Dados de cobrança (nome/CPF/CNPJ do responsável, e-mail) | responsável pela assinatura | Asaas (não guardamos cartão); `payments`/`subscriptions` só ids e valores | cobrar | execução de contrato (V); obrigação legal fiscal (II) |
| Cookies | visitantes e usuários | navegador | sessão, “dispositivo confiável”, tema | estritamente necessários (sem consentimento); tema é preferência |

Não coletamos dados sensíveis (art. 5º, II) nem de crianças. Não há rastreamento de
marketing nem cookies de terceiros.

## Operadores (suboperadores)
| Operador | O que recebe | Onde | Transferência internacional |
|---|---|---|---|
| Render (hospedagem app + PostgreSQL + Redis) | todos os dados | EUA (região a confirmar; avaliar região mais próxima) | sim — art. 33, II (cláusulas contratuais/DPA do provedor) e informar na política |
| Resend (e-mail transacional) | e-mail, nome, conteúdo do e-mail | EUA | sim — idem |
| Asaas (pagamentos) | dados de cobrança | Brasil | não |
| Sentry (opcional, só com `SENTRY_DSN`) | stack trace sem PII (filtro em `logging_config.py`) | EUA/UE | sim, mínima; desligado por padrão |

## Retenção
| Dado | Prazo | Como |
|---|---|---|
| Dados da empresa | enquanto a assinatura existir; após pedido de exclusão, 30 dias de carência | `flask lgpd-purge` (diário) |
| Convites, resets e confirmações usados/vencidos | 30 dias | `flask lgpd-retencao` (diário) |
| `login_throttles` | 30 dias após a última falha | idem |
| `domain_events` publicados | 90 dias | idem |
| `audit_logs` de acesso da API (`api.request`) | 6 meses (Marco Civil, art. 15) | idem |
| demais `audit_logs` | 5 anos (prazo prescricional/consumidor) | idem |
| `platform_audit_logs` (prova de expurgo, operações) | 5 anos | idem |
| Logs de aplicação (stdout no host) | 6 meses | configuração do provedor de logs |
| Sentry | 90 dias | configuração do projeto no Sentry |
| Backups do banco | 30 dias (rotação do provedor) | dado apagado some dos backups ao fim do ciclo — informar na política |
| Dados fiscais de cobrança | 5 anos | ficam no Asaas (obrigação legal); o expurgo apaga as cópias locais |

## Direitos do titular (art. 18) — como atendemos
- **Confirmação e acesso / portabilidade**: o proprietário baixa em *Privacidade e dados* um
  ZIP com um CSV por tabela da empresa (`POST /app/privacidade/exportar`, auditado). Sem
  segredos (hashes, segredo TOTP). Usuário individual: perfil mostra os próprios dados;
  pedidos fora disso pelo e-mail do encarregado (prazo: 15 dias).
- **Correção**: perfil (nome, e-mail com reconfirmação).
- **Eliminação**: empresa — *Excluir a empresa* (senha + nome), carência de 30 dias,
  cancelável, aviso por e-mail a todos os proprietários; depois `flask lgpd-purge` apaga
  todas as linhas com o `company_id`, os usuários sem vínculo com outra empresa (com tokens,
  códigos de MFA e bloqueios de login) e a própria empresa, registrando só ids e contagens em
  `platform_audit_logs`. Usuário individual que quer sair de uma empresa: o proprietário o
  desativa; apagar a conta inteira é pedido ao encarregado (fluxo manual até existir tela).
- **Informação sobre compartilhamento**: tabela “Operadores” acima, na política de privacidade.
- **Revogação de consentimento**: não usamos consentimento como base (exceto preferência de
  tema, que o usuário troca a qualquer momento).

## Acesso de suporte
Só com motivo, prazo (≤ 72 h), autorização registrada, e-mail aos proprietários e trilha em
`audit_logs` (`flask suporte conceder|revogar|listar|expirar`). Ver `seguranca.md`.

## Rotinas agendadas (cron do Render)
```
flask lgpd-purge --operador cron        # diário
flask lgpd-retencao --operador cron     # diário
flask suporte expirar                   # de hora em hora (o acesso já não vale; só desativa e audita)
```

## Pendências
- Revisão jurídica de termos, privacidade e deste inventário (go/no-go, risco L6).
- Confirmar região do Render e assinar DPAs (Render, Resend, Sentry).
- Exportação gera o ZIP em memória: para empresas muito grandes, gerar em segundo plano.
- Tela para o usuário pedir exclusão da própria conta (hoje pelo encarregado).
