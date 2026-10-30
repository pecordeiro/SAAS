# Política de Privacidade — RASCUNHO

> **RASCUNHO — NÃO PUBLICAR SEM REVISÃO JURÍDICA.** Texto-base da Fase 7 (inventário técnico
> em `docs/plano/lgpd.md`). A Fase 6 cuida da página `/privacidade` e do layout.

Última atualização: [data da publicação]

## 1. Quem trata os seus dados
- Para os dados que a sua empresa coloca no Controle de Produção (equipe, produção), a
  **empresa cliente é a controladora** e nós somos **operadores**.
- Para os dados da conta do cliente e da cobrança, nós somos controladores.
- Encarregado (DPO): [nome] — [e-mail do encarregado].

## 2. Quais dados coletamos
- **Conta**: nome, e-mail, senha (guardada só como hash irreversível), configuração de
  verificação em duas etapas (segredo cifrado).
- **Uso**: registros de produção que você lança (com autor e horário), alterações
  administrativas (auditoria), endereço IP e data/hora de acesso.
- **Cobrança**: dados necessários para emitir cobranças, tratados pelo Asaas; não
  guardamos dados de cartão.
- **Cookies estritamente necessários**: sessão, “dispositivo confiável” (para não bloquear
  quem já usa o sistema) e preferência de tema. Não usamos cookies de publicidade nem de
  terceiros.

## 3. Para que usamos e com qual base legal
| Finalidade | Base legal (LGPD art. 7º) |
|---|---|
| Prestar o serviço contratado (contas, projetos, histórico, convites, e-mails do sistema) | execução de contrato |
| Segurança (bloqueio de tentativas, auditoria, prevenção a fraude) | legítimo interesse |
| Guardar registros de acesso por 6 meses | obrigação legal (Marco Civil da Internet, art. 15) |
| Cobrança e obrigações fiscais | execução de contrato e obrigação legal |

Não vendemos dados nem os usamos para publicidade.

## 4. Com quem compartilhamos
| Parceiro | Para quê | País |
|---|---|---|
| Render | hospedagem do site e do banco de dados | Estados Unidos |
| Resend | envio de e-mails do sistema | Estados Unidos |
| Asaas | cobrança | Brasil |
| Sentry (quando ativo) | diagnóstico de erros, sem dados pessoais | Estados Unidos/UE |

Transferências internacionais seguem o art. 33 da LGPD (cláusulas contratuais com os
provedores). Também podemos compartilhar dados quando a lei ou ordem judicial exigir.

## 5. Por quanto tempo guardamos
- Dados da empresa: enquanto a assinatura existir; após pedido de exclusão, 30 dias de
  carência e então apagamento definitivo (backups expiram em até 30 dias).
- Registros de acesso: 6 meses. Auditoria administrativa: 5 anos.
- Links de convite, redefinição de senha e confirmação: apagados 30 dias depois de usados
  ou vencidos.
- Dados fiscais: 5 anos, no parceiro de pagamentos.

## 6. Seus direitos
Você pode pedir confirmação e acesso, correção, portabilidade, eliminação, informação sobre
compartilhamento e oposição a tratamentos baseados em legítimo interesse. O proprietário da
empresa exporta todos os dados e pede a exclusão em **Privacidade e dados**; os demais
pedidos vão para o encarregado e são respondidos em até 15 dias. Se o pedido for sobre dados
que a sua empresa controla, encaminharemos à empresa.

## 7. Segurança
Conexão sempre cifrada (HTTPS), senhas com Argon2id, verificação em duas etapas, separação
rigorosa entre empresas (inclusive no banco de dados), registros de auditoria e acesso de
suporte só com motivo, prazo e aviso aos proprietários. Em caso de incidente com risco
relevante, comunicaremos a ANPD e os titulares nos prazos legais.

## 8. Alterações
Avisaremos mudanças relevantes por e-mail e no sistema.

Contato: [e-mail do encarregado].
