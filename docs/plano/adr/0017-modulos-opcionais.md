# ADR-0017 — Módulos opcionais por empresa (R6)

- Status: **aceito** em 2026-10-23, dentro do plano aprovado (`docs/plano/reestruturacao.md` §4.5 e
  §7 R6; decisão D5 = "confirmar a lista e que tudo começa desligado"). Complementa a ADR-0014 e
  segue a ADR-0009 (backend é a única fonte de regras).

## Contexto
O núcleo do produto é acompanhar **etapas** (ADR-0014). Funções construídas nas Etapas D a G e na
Fase 9 (responsável por atividade, alertas, aguardando peça, fotos, checklist, número de série,
API) estavam no caminho principal para todas as empresas. O plano pede que fiquem **opcionais,
desligadas por padrão, ligadas em Configurações › Módulos e marcadas com o selo "Opcional"**, e
que, desligadas, **as rotas respondam 404**.

## Decisão

1. **Catálogo único** em `app/services/modules.py` (`CATALOG`): chave estável, nome, descrição e
   as rotas (endpoints) de cada módulo. Módulos e rotas:

   | Chave | Módulo | Rotas (endpoints) |
   |---|---|---|
   | `atribuicao` | Responsáveis e progresso por pessoa | `app.project_people`, `edicao.activity_assign` |
   | `alertas` | Alertas e relatório semanal por e-mail | `app.alerts` |
   | `aguardando_peca` | Aguardando peça | `app.stage_waiting_part` |
   | `fotos` | Fotos e comentários | `qualidade.evidence`, `comment_create`, `comment_delete`, `photo_upload`, `photo_view`, `photo_delete` |
   | `checklist` | Checklist de inspeção | `qualidade.checklist`, `checklist_item_add`, `checklist_item_archive`, `checklist_required`, `inspection_start`, `inspection`, `inspection_save`, `inspection_correct` |
   | `unidades` | Número de série por unidade | `qualidade.units`, `units_generate`, `units_import`, `units_search`, `unit_detail`, `unit_status`, `unit_register` |
   | `api` | API de integração (só com `FEATURE_PUBLIC_API`) | `api_tokens_ui.*` e `api_v1.*` |

   Ficam **fora** dos módulos, como manda o §4.5: MFA (opcional por pessoa, em Perfil), painel
   interno (só equipe), modelos de etapas (parte do "Novo projeto"), importar/exportar planilha
   (núcleo, R7) e restaurar (núcleo, R8).

2. **Persistência**: tabela `company_modules` (`company_id`, `module`, `enabled`, `updated_at`,
   `updated_by_id`; UNIQUE `company_id, module`), dado da empresa com RLS `tenant_isolation`
   (migration `f1a7c3e9b2d4`, em `rls.RLS_TABLES`). **Sem linha = desligado**: empresa nova vê só o
   núcleo. Tabela em vez de coluna JSON em `companies` porque `companies` não tem RLS (é a raiz do
   tenant) e porque cada linha guarda quem mudou e quando.

3. **Recusa no servidor, num lugar só**: `tenancy.tenant_required` chama
   `modules.guard_endpoint(g.company)` logo depois de resolver a empresa e **antes** do papel:
   rota de módulo desligado responde **404 para qualquer papel** (não revela que existe). A API
   (token, sem sessão) faz a mesma checagem em `api_v1.authenticate` (404 em JSON). Um teste
   varre o `url_map` e confere que toda rota de cada módulo responde 404 com ele desligado.

4. **Telas só exibem** (`modules` no contexto dos templates): menu, botões e quadros de um módulo
   desligado não aparecem; os que aparecem levam o selo **"Opcional"**
   (`components/optional.html`). Onde um campo opcional fica dentro de uma tela do núcleo, o
   servidor ignora o que vier no POST com o módulo desligado: checklist no editor de modelos
   (mantém o checklist que o modelo já tinha), unidade na inspeção (vale a etapa inteira),
   "etapa parada" em Empresa (mantém o valor).

5. **Serviços e worker**: alertas e relatório semanal só para empresa com `alertas` ligado; sem
   `aguardando_peca` a marca é ignorada em painel, Preencher etapas, lista de projetos, alertas
   ("peça atrasada") e relatório (a coluna sai); sem `atribuicao` o e-mail de "atividade
   atribuída" não sai e o relatório semanal perde a aba Pessoas. Fora de requisição (worker) o
   estado é lido do banco a cada vez; em requisição, uma consulta por requisição (cache em `g`).

6. **Quem muda**: só o proprietário, em `/app/empresa/modulos` (Configurações › Módulos). O POST
   leva o estado inteiro (caixa marcada = ligado). Cada mudança grava `module.enabled` ou
   `module.disabled` em `audit_logs` com o módulo e o autor. Escrita em modo leitura → 402, como
   qualquer outra.

7. **Plano à parte**: limites e recursos de plano continuam em `entitlements` e não dependem dos
   módulos. Ligar o módulo API não libera a API num plano sem ela (403 `plan_feature_unavailable`
   continua, e a tela de Módulos avisa).

8. **Empresas que já existiam (migração de dados segura)**: a migration liga, em cada empresa, o
   módulo em que ela **já tem dados**, para ninguém perder acesso ao que usava:
   `atribuicao` (atividade com responsável), `alertas` (alerta gravado ou relatório semanal já
   feito), `aguardando_peca` (etapa marcada, com previsão, ou marca já alterada na auditoria),
   `fotos` (comentário ou foto), `checklist` (item de etapa ou de modelo, inspeção ou etapa que
   exige), `unidades` (número de série), `api` (cliente ou token). A leitura é feita empresa a
   empresa com `app.company_id` definido, então funciona com o RLS forçado. **Nenhum dado é
   apagado nem alterado**; desligar um módulo só esconde, e religar mostra tudo como estava. O
   downgrade apaga só a tabela nova.

## Consequências
- (+) "Empresa nova vê só o núcleo" vale de fato, e a recusa não depende do template.
- (+) Uma rota nova de módulo só precisa entrar no `CATALOG`; o teste do catálogo falha se a
  rota listada não existir.
- (−) Rota nova de módulo esquecida fora do `CATALOG` fica acessível; mitigação: revisão e o teste
  que varre as rotas de cada módulo.
- (−) Exportações (CSV/XLSX do projeto, exportação LGPD) e o JSON da API continuam com os campos
  dos módulos (responsável, aguardando peça): é dado da própria empresa e a portabilidade não deve
  depender de um interruptor de tela.
- (−) Preferências de e-mail ficam no Perfil da pessoa (valem para todas as empresas dela); o
  módulo decide se a empresa manda o e-mail.
