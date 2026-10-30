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

| Fotos de evidência (Etapa G) | pode aparecer pessoa/rosto na foto; quem enviou | armazenamento S3/R2 (objeto) + `activity_photos` (metadados) | prova de montagem / não conformidade | execução de contrato (V) com a empresa; a empresa é controladora |
| Comentários e respostas de inspeção (Etapa G) | autor (usuário); texto livre pode citar pessoas | `activity_comments`, `inspection_answers` | qualidade e rastreabilidade | execução de contrato (V) |

| Briefing de identidade visual (ADR-0019): nome e telefone/e-mail do contato, textos e imagens (logo, fotos de produto) | contato indicado pela empresa; pode aparecer pessoa na foto | `visual_briefings`, `visual_briefing_files` (+ objetos `<empresa>/briefing/`) | adaptar a identidade visual contratada | execução de contrato (V); a empresa é controladora |
| Reserva da ligação: nome e telefone de quem atende | contato indicado pela empresa | `call_bookings` (empresa) e cópia em `call_slots.booked_contact_*` (plataforma, para a equipe ligar) | fazer a ligação contratada | execução de contrato (V) |

Fotos: GPS, modelo da câmera e demais metadados EXIF são removidos no envio (reencode); a
interface avisa para não fotografar pessoas sem necessidade.

Não coletamos dados sensíveis (art. 5º, II) nem de crianças. Não há rastreamento de
marketing nem cookies de terceiros.

## Operadores (suboperadores)
| Operador | O que recebe | Onde | Transferência internacional |
|---|---|---|---|
| Cloudflare R2 ou AWS S3 (fotos de evidência, Etapa G — só se `STORAGE_BACKEND=s3`) | arquivos de foto (sem metadados EXIF) | região a escolher (R2: jurisdição configurável) | provável — art. 33, II; DPA do provedor |
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
- **Fotos (Etapa G)**: a exportação traz `activity_photos.csv` com os METADADOS (atividade,
  data, quem enviou, tamanho, SHA-256); os arquivos não vão no ZIP (gerado em memória) — o
  titular abre cada foto na tela ou pede a cópia ao encarregado. Apagar uma foto (supervisor+)
  remove o arquivo do armazenamento antes da linha. O expurgo da empresa apaga todos os
  arquivos antes das linhas; se o armazenamento falhar, o expurgo é desfeito e roda de novo.
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

## ADR-0019 — briefing e ligação
- Exportação: `visual_briefings.csv`, `visual_briefing_files.csv` (metadados) e `call_bookings.csv` saem no ZIP
  como as demais tabelas da empresa; as imagens abrem na tela do briefing.
- Expurgo: as imagens do briefing saem do armazenamento ANTES das linhas (como as fotos de evidência); a cópia
  do contato nos horários da plataforma (`call_slots`) é apagada e o horário fica livre
  (`services/agenda.py::release_company`).
- A equipe (`/interno`) não lê o conteúdo do briefing nem as imagens; vê só status, data e o contato da ligação.

