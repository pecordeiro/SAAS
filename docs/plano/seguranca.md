# Segurança — modelo de ameaças (STRIDE resumido)

Fase 7. Cada mitigação aponta para o código e o teste que a garantem. Revisar a cada fase que
abrir superfície nova (Fase 8: webhooks do Asaas; API v1 quando sair da flag).

## Ativos
| Ativo | Por quê importa |
|---|---|
| Dados de produção das empresas (projetos, histórico, modelos) | segredo industrial do cliente; vazamento entre empresas é o pior incidente (risco T1) |
| Contas (e-mail, nome, hash de senha, segredo TOTP, códigos de recuperação) | dado pessoal + acesso |
| Tokens (sessão, convite, reset, confirmação, API, dispositivo confiável) | equivalem a credencial |
| Assinatura e cobrança (Asaas) | dinheiro e dado fiscal |
| Segredos de operação (`SECRET_KEY`, `MFA_ENCRYPTION_KEY`, chaves Asaas/Resend, `DATABASE_URL`) | comprometem tudo |
| Trilhas (`audit_logs`, `platform_audit_logs`, logs) | prova em incidente e LGPD |

## Atores
- **Visitante anônimo** (internet): cadastro, login, links de e-mail.
- **Usuário legítimo de outra empresa** (o mais provável): tenta ler/alterar dados alheios (IDOR).
- **Membro de baixa permissão** (operador) tentando ações de supervisor/proprietário.
- **Quem cadastra o e-mail alheio** (pre-account takeover).
- **Integração com token da API** (ou quem roubou o token).
- **Asaas** (webhooks) e quem tenta forjá-los.
- **Operador da plataforma** (suporte, deploy, CLI) — acesso privilegiado, precisa de trilha.

## Superfícies e ameaças

### Login, sessão e MFA
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| S | força bruta / password spraying | Flask-Limiter (Redis) + bloqueio progressivo por conta e IP; dispositivo confiável | `services/lockout.py`, `services/trusted_device.py`; `tests/test_accounts.py` (429), `tests/test_auth.py` |
| S | roubo de cookie | `__Host-session`/`__Host-remember`/`__Host-dispositivo`, Secure, HttpOnly, SameSite=Lax, HSTS 2 anos; produção recusa subir com cookie inseguro | `config.py`, `security.py::_check_cookie_config`; `tests/test_fase7_security.py::test_producao_*` |
| S | sessão viva após troca de senha | `session_version` no id do Flask-Login | `app/__init__.py::load_user`; `tests/test_accounts.py` |
| T | CSRF | Flask-WTF em todo POST; SameSite=Lax; HTTPS confere Referer | `tests/test_auth.py`, `tests/test_lgpd.py::test_exportacao_sem_csrf_400` |
| I | enumeração de e-mail | mesma resposta/tempo em cadastro e reset | `tests/test_accounts.py` |
| E | MFA contornado | TOTP sem reuso, códigos de uso único, etapa de 5 min | `services/mfa.py` |

### XSS e injeção no navegador
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| T/E | XSS refletido/armazenado | Jinja com autoescape, sem `|safe` em dado de usuário; CSP `script-src 'self' 'nonce-…'`, `style-src 'self'`, `object-src 'none'`, `base-uri 'none'`; HTMX com `allowEval:false`/`allowScriptTags:false` | `security.py`; `tests/test_fase7_security.py::test_csp_*`, `tests/test_visual.py` (sem script/estilo inline) |
| T | clickjacking | `frame-ancestors 'none'` + `X-Frame-Options: DENY` | idem |
| I | vazamento por cache/Referer | `Cache-Control: no-store` em página logada; `Referrer-Policy` (no-referrer nas páginas de token) | `security.py::_apply_headers`; `test_pagina_logada_nao_fica_em_cache` |

### Isolamento multiempresa (IDOR)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| I/T | ler/alterar recurso de outra empresa pelo id | empresa só da sessão; `tenancy.get_or_404/scoped` → 404; RLS como 2ª barreira | `tenancy.py`, `rls.py`; `tests/test_isolation.py` (varre o `url_map` com e sem `FEATURE_PUBLIC_API` e exige caso A/B para toda rota `<uuid:>`), `tests/test_rls.py` |
| E | membro de papel menor | `tenant_required(min_role)` | `tests/test_fase4_routes.py`, `tests/test_accounts.py` |

### Convites e tokens de e-mail
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| S | adivinhar/reusar token | 32 bytes aleatórios, só SHA-256 no banco, uso único, expiração; GET não altera nada | `services/tokens.py`; `tests/test_accounts.py` |
| I | token em log | log de acesso grava o MOLDE da rota (`/convite/<token>`), nunca o caminho; filtro de texto com cara de token | `logging_config.py`; `test_log_de_acesso_usa_molde_da_rota_e_nao_o_token` |
| S | pre-account takeover | reset em conta não confirmada apaga MFA, confirma o e-mail, derruba sessões e **revoga tokens da API e convites pendentes** das empresas da conta (auditado como `account.claimed_by_reset`) | `services/accounts.py::_revoke_pre_confirmation_access`; `test_reset_em_conta_nao_confirmada_revoga_tokens_e_convites` |

Risco residual aceito: se quem cadastrou o e-mail alheio já convidou terceiros e eles
**aceitaram** antes da retomada, esses vínculos continuam; o dono os vê em Usuários (com
“Último acesso”) e pode desativá-los. Não há como distinguir automaticamente um convidado
legítimo de um cúmplice.

### Importação (upload)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| D | arquivo enorme | `MAX_CONTENT_LENGTH` → 413 antes de ler; rate limit `IMPORT_RATE_LIMIT` | `config.py`, `blueprints/dados.py`; `test_upload_acima_do_limite_413_sem_ler_o_corpo`, `test_importacao_tem_rate_limit_429` |
| D | zip bomb | soma declarada E tamanho REAL lido em streaming ≤ 30 MB, ≤ 500 entradas, sem zip cifrado | `services/importer.py::_inspect_zip`; `test_zip_bomb_*` |
| I/D | XXE / billion laughs | XML com `<!DOCTYPE`/`<!ENTITY` recusado antes do openpyxl; `defusedxml` instalado (o openpyxl passa a usá-lo) | idem; `test_xlsx_com_dtd_xxe_recusado`, `test_openpyxl_usa_defusedxml` |
| T | fórmula/CSV injection | fórmulas nunca avaliadas (`data_only`); exportação neutraliza `= + - @ TAB CR` | `services/exporter.py`; `tests/test_fase4_*`, `test_exportacao_neutraliza_formula` |
| I | arquivo em disco | multipart lido em `BytesIO` (nada em /tmp nem pasta pública) | `security.py::InMemoryUploadRequest`; `test_upload_fica_em_memoria` |

### Fotos de evidência (Etapa G, ADR-0011)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| T/E | arquivo malicioso com extensão de imagem (HTML, SVG com script, PDF, polyglot) | tipo pelos magic bytes (só JPEG/PNG/WebP), decodificação completa com Pillow, reencode para JPEG novo (bytes extras e metadados somem); nome e extensão enviados ignorados | `services/photos.py::process`; `tests/test_etapa_g_evidencias.py::test_upload_malicioso_*`, `test_polyglot_*` |
| D | bomba de descompressão / arquivo enorme | dimensões do cabeçalho ≤ `PHOTO_MAX_PIXELS` antes de decodificar, `DecompressionBombWarning` vira erro; corpo ≤ `PHOTO_MAX_REQUEST_BYTES` só nesta rota (413 antes de ler), foto ≤ 5 MB; `PHOTO_UPLOAD_RATE_LIMIT`; N por atividade e por empresa | `security.py::InMemoryUploadRequest`; `test_imagem_enorme_*`, `test_foto_acima_de_5_mb_*`, `test_outras_rotas_continuam_com_o_teto_global` |
| I | GPS/dados da câmera vazando | reencode sem EXIF/ICC/XMP | `test_foto_valida_e_reencodada_sem_exif_gps_*` |
| I | foto de outra empresa / link público | bucket privado, sem URL pública ou pré-assinada; só `/app/fotos/<uuid>` com `get_or_404` (404 cruzado); chave `<company_id>/fotos/<uuid>.jpg` gerada no servidor e validada por regex (sem traversal) | `services/storage.py::check_key`; `tests/test_isolation.py::test_etapa_g_*`, `tests/test_etapa_g_storage.py` |
| T | conteúdo trocado no bucket servido como foto | SHA-256 da imagem gravada conferido na leitura; resposta com `Content-Type: image/jpeg` fixo, `nosniff`, CSP `default-src 'none'; sandbox`, `Cache-Control: private` | `test_objeto_adulterado_*` |
| I | chave do S3 em log/erro | segredos só por env; erros do provedor sem URL assinada nem chave; `repr` sem segredo | `test_s3_*` |

### Checklist e unidades (Etapa G)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| S/R | assinatura forjada (outro usuário, data retroativa) | `signed_by_id`/`signed_at` vêm da sessão e do relógio do servidor; campos do formulário ignorados | `services/checklists.py::sign`; `test_fluxo_completo_assinatura_do_servidor_*` |
| T/R | alterar resposta assinada sem rastro | `locked_at` + guarda ORM (UPDATE/DELETE recusados); correção = nova linha (`supersedes_id` UNIQUE) com motivo, só supervisor+, auditada | idem |
| I/T | item/unidade/atividade de outra empresa no corpo | ids resolvidos com `get_or_404` e conferidos contra a etapa/projeto da URL → 404 | `test_etapa_g_checklist_item_de_b_*`, `test_etapa_g_unidades_ids_de_b_*` |
| T | busca por série com curinga SQL | `LIKE` com escape de `%`/`_` | `test_busca_por_serie_escapa_curingas` |

### Webhooks do Asaas (Fase 8, `app/blueprints/webhooks.py`)
| STRIDE | Ameaça | Mitigação |
|---|---|---|
| S | webhook forjado | `asaas-access-token` com `hmac.compare_digest`; em dúvida, consultar a API do Asaas |
| R/T | repetição/ordem | `webhook_events.external_event_id` UNIQUE gravado antes de processar |
| D | inundação | qualquer blueprint com “webhook” no nome recebe `WEBHOOK_RATE_LIMIT` por IP automaticamente (`security.py::_limit_webhook_blueprints`; `test_blueprint_de_webhook_ganha_rate_limit`) |
| I | payload em log | não logar payload; Sentry sem corpo (`max_request_body_size="never"`) |
| E | RLS | achar a assinatura pelo id do provedor antes de saber a empresa: política `subscriptions_provider_lookup` (Fase 8, migration `d8b2e6f4a1c7`) — ver ADR-0003 |

### API v1 (atrás de `FEATURE_PUBLIC_API`)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| S | token roubado/adivinhado | `cp_` + 256 bits, só SHA-256 no banco, expiração, revogação, auditoria por chamada | `services/api_tokens.py`; `tests/test_api_v1.py` |
| D | força bruta com tokens inventados | limite por token só para token EXISTENTE; inválido cai no balde do IP (+ teto por IP) | `blueprints/api_v1.py::token_key`; `test_api_rate_limit_com_tokens_inventados_conta_no_mesmo_balde` |
| I | token de A lê B | escopo de empresa do token + `get_or_404`; stubs 501 também resolvem o id na empresa (B → 404) | `tests/test_isolation.py::test_api_*` |
| E | RLS | política `api_tokens_by_token` | `tests/test_rls.py::test_token_da_api_autentica_com_rls_forcado_so_pelo_hash` |

### Operação (suporte, CLI, segredos, logs)
| STRIDE | Ameaça | Mitigação | Código / teste |
|---|---|---|---|
| R/E | suporte acessa empresa sem trilha | só por CLI, motivo ≥ 15 caracteres, “autorizado por”, prazo ≤ 72 h, papel ≤ supervisor, conta de suporte com MFA; e-mail aos proprietários; `audit_logs`; expira sozinho na requisição seguinte | `services/support.py`; `tests/test_lgpd.py::test_suporte_*` |
| I | segredo/PII em log ou Sentry | logs JSON filtrados (e-mail, token, chaves sensíveis); Sentry só com DSN, `send_default_pii=False`, sem corpo/cookies/Authorization/variáveis locais | `logging_config.py`; `test_formatter_json_*`, `test_sentry_*` |
| T | `X-Request-ID` forjado (log injection) | aceito só `[A-Za-z0-9._-]{8,64}` | `test_request_id_aceito_so_com_formato_seguro` |
| D | rate limit por processo | Redis obrigatório em produção (falha clara no boot) | `config.py::finalize_config`; `test_producao_sem_redis_falha_com_mensagem_clara` |
| T | dependência vulnerável | versões fixadas, `pip-audit` no CI, Dependabot semanal | `.github/workflows/ci.yml`, `.github/dependabot.yml` |
| R | expurgo LGPD sem prova | `platform_audit_logs` (sobrevive ao expurgo; só ids e contagens) | `tests/test_lgpd.py::test_expurgo_*` |

## Cabeçalhos (toda resposta)
`Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-<aleatório>'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`,
`Strict-Transport-Security: max-age=63072000; includeSubDomains` (fora de dev/test),
`Permissions-Policy` (câmera, microfone, geolocalização, pagamento, USB… desligados),
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: strict-origin-when-cross-origin`, `Cross-Origin-Opener-Policy` e
`Cross-Origin-Resource-Policy: same-origin`, `X-Request-ID`.
`csp_nonce()` existe no Jinja para o caso raro de `<script nonce="{{ csp_nonce() }}">`; hoje todo
JS é arquivo em `/static`.

## Rate limits (Redis em produção)
| Rota | Config |
|---|---|
| login, MFA | `LOGIN_RATE_LIMIT`, `MFA_RATE_LIMIT` + bloqueio progressivo |
| cadastro, reenvio de confirmação | `SIGNUP_RATE_LIMIT`, `EMAIL_RESEND_RATE_LIMIT` |
| esqueci/redefinir senha | `PASSWORD_RESET_RATE_LIMIT` |
| convidar, reenviar, aceitar convite | `INVITE_RATE_LIMIT` |
| importar (upload e confirmação) | `IMPORT_RATE_LIMIT` |
| webhooks (qualquer blueprint “webhook”) | `WEBHOOK_RATE_LIMIT` |
| API v1 | `API_RATE_LIMIT` (token existente) + `API_RATE_LIMIT_IP` |
| exportar / excluir empresa | `LGPD_EXPORT_RATE_LIMIT`, `LGPD_DELETE_RATE_LIMIT` |

## Dependências
`pip-audit` 2.10.1 em 2026-10-14: “No known vulnerabilities found” (requirements + dev).
Exceções: nenhuma. Se surgir CVE sem correção, documentar aqui (ID, por que não afeta,
prazo de revisão) e usar `--ignore-vuln ID` no CI.

## Revisão de segurança da Fase 7 (diff próprio)
Ver bloco “Fase 7” em `progresso.md` (achados, correções e riscos aceitos).
