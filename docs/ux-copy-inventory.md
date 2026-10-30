# Teroz — inventário de textos (UX copy)

Gerado a partir do código em 2026-10-29: cada texto que a pessoa lê (templates, e-mails e mensagens do backend), comparado com o estado anterior à auditoria (commit `HEAD`). Vocabulário em [`teroz-terminologia.md`](teroz-terminologia.md); voz em [`teroz-voice-and-tone.md`](teroz-voice-and-tone.md).

**Como ler o status:** *alterado* (o texto mudou; a coluna Problema traz o anterior e o motivo) · *incluído* (texto novo) · *revisado — mantido* (lido e aprovado sem mudança) · *mantido de propósito* (importação e exportação precisam reconhecer a planilha do cliente) · *pendente de revisão manual* (área que só passou pela troca automática de termos) · *técnico* (metadado, não é texto de leitura).

A extração é heurística (strings com cara de frase em português). Rotas, IDs, chaves e valores gravados no banco não são texto de leitura e não mudaram.

## Contagens

- Textos encontrados (estado atual): **3331** (antes: 3328)
- alterado: **288**
- incluído: **7**
- revisado — mantido: **2566**
- mantido de propósito: **178**
- pendente de revisão manual: **291**
- técnico (não é copy): **1**
- Textos removidos ou fundidos em outro: **4**

| Área | Total | alterado | incluído | revisado — mantido | mantido de propósito | pendente de revisão manual | técnico (não é copy) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Painéis e projetos | 865 | 92 | 0 | 773 | 0 | 0 | 0 |
| Importar e exportar | 335 | 24 | 0 | 133 | 178 | 0 | 0 |
| Site público | 300 | 35 | 2 | 263 | 0 | 0 | 0 |
| Entrar e conta | 264 | 27 | 3 | 234 | 0 | 0 | 0 |
| E-mail | 234 | 23 | 0 | 211 | 0 | 0 | 0 |
| Preencher etapas e Meta e equipe | 220 | 7 | 0 | 213 | 0 | 0 | 0 |
| Qualidade (fotos, checklist, unidades) | 207 | 22 | 0 | 185 | 0 | 0 | 0 |
| Identidade visual e ligação (planos Empresa/Implantação) | 169 | 2 | 0 | 0 | 0 | 167 | 0 |
| Componentes e layout | 142 | 18 | 2 | 121 | 0 | 0 | 1 |
| Empresa, módulos e LGPD | 127 | 9 | 0 | 118 | 0 | 0 | 0 |
| Outros | 108 | 11 | 0 | 97 | 0 | 0 | 0 |
| Assinatura e planos | 94 | 2 | 0 | 92 | 0 | 0 | 0 |
| Painel interno da equipe Teroz | 84 | 1 | 0 | 0 | 0 | 83 | 0 |
| Modelos de etapas | 74 | 7 | 0 | 67 | 0 | 0 | 0 |
| Histórico e auditoria | 66 | 7 | 0 | 59 | 0 | 0 | 0 |
| API | 42 | 1 | 0 | 0 | 0 | 41 | 0 |

## Antes → depois (todos os textos alterados)

| Arquivo:linha | Antes | Depois | Motivo |
|---|---|---|---|
| `app/__init__.py:173` | Requisição inválida. | Algo no envio não veio como esperado. Volte à página anterior e tente de novo. | clareza e voz (ver voice-and-tone) |
| `app/__init__.py:185` | Método não permitido. | Esta página não aceita esse envio. Volte e tente pela tela. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/account.py:327` | Uma empresa em que você é proprietário exige MFA: não dá para desativar. | Uma empresa em que você tem o papel Proprietário exige a verificação em duas etapas: não dá para desativá-la. | sem sigla técnica: verificação em duas etapas |
| `app/blueprints/app.py:657` | Atividade incluída. | Subatividade incluída. | glossário: atividade → subatividade |
| `app/blueprints/app.py:746` | Outra pessoa registrou antes: esta atividade agora está em {…} de {…}. | Outra pessoa registrou antes: esta subatividade agora está em {…} de {…}. | glossário: atividade → subatividade |
| `app/blueprints/dados.py:432` | Pré-visualização inválida. Envie o arquivo de novo. | Prévia inválida. Envie o arquivo de novo. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/dados.py:436` | Pré-visualização expirada ou inválida. Envie o arquivo de novo. | Prévia expirada ou inválida. Envie o arquivo de novo. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/dados.py:438` | Pré-visualização de outra sessão. Envie o arquivo de novo. | Prévia de outra sessão. Envie o arquivo de novo. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/dados.py:444` | Projeto importado: {…} etapas, {…} atividades. | Projeto importado: {…} etapas, {…} subatividades. | glossário: atividade → subatividade |
| `app/blueprints/edicao.py:309` | Atividade atualizada. | Subatividade atualizada. | glossário: atividade → subatividade |
| `app/blueprints/edicao.py:336` | Atividade sem responsável. | Subatividade sem responsável. | glossário: atividade → subatividade |
| `app/blueprints/edicao.py:398` | Atividade arquivada. Os registros dela continuam no histórico. | Subatividade arquivada. Os registros dela continuam no histórico. | glossário: atividade → subatividade |
| `app/blueprints/preencher.py:41` | Peças concluídas | Peças prontas | glossário: concluídas → prontas |
| `app/blueprints/public.py:35` | Verificação em duas etapas obrigatória (MFA) | Verificação em duas etapas obrigatória para proprietários | sem sigla técnica: verificação em duas etapas |
| `app/blueprints/qualidade.py:480` | Status da unidade atualizado. | Situação da unidade atualizada. | glossário: status → situação |
| `app/blueprints/team.py:116` | {…} foi desativado e perdeu o acesso. | {…} perdeu o acesso a esta empresa. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/team.py:128` | {…} foi reativado. | O acesso de {…} voltou. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/team.py:137` | Exigir MFA é um recurso do plano Empresa. | Exigir a verificação em duas etapas dos proprietários é um recurso do plano Empresa. | sem sigla técnica: verificação em duas etapas |
| `app/blueprints/team.py:147` | Exigência de MFA para proprietários | Verificação em duas etapas | sem sigla técnica: verificação em duas etapas |
| `app/blueprints/team.py:147` | Bem-vindo a {…}! | agora é obrigatória para os proprietários. | clareza e voz (ver voice-and-tone) |
| `app/blueprints/team.py:147` | Conta criada. Bem-vindo a {…}! | deixou de ser obrigatória para os proprietários. | clareza e voz (ver voice-and-tone) |
| `app/forms.py:81` | Linha {…}: nome da atividade vazio ou longo demais. | Linha {…}: nome da subatividade vazio ou longo demais. | glossário: atividade → subatividade |
| `app/forms.py:90` | No máximo {…} atividades por etapa. | No máximo {…} subatividades por etapa. | glossário: atividade → subatividade |
| `app/forms.py:122` | Atividades (uma por linha: Nome; minutos por unidade) | Subatividades (uma por linha: Nome; minutos por unidade) | glossário: atividade → subatividade |
| `app/forms.py:135` | Inclua pelo menos uma atividade. | Inclua pelo menos uma subatividade. | glossário: atividade → subatividade |
| `app/forms.py:183` | Nova atividade | Nova subatividade | glossário: atividade → subatividade |
| `app/forms.py:191` | Peças concluídas agora | Peças prontas agora | glossário: concluídas → prontas |
| `app/forms_accounts.py:62` | Atividade atribuída a mim | Subatividade atribuída a mim | glossário: atividade → subatividade |
| `app/forms_production.py:197` | Previstas (meta) | Meta (previstas) | clareza e voz (ver voice-and-tone) |
| `app/forms_production.py:198` | Concluídas (peças) | Peças prontas | clareza e voz (ver voice-and-tone) |
| `app/services/accounts.py:412` | Convite para {…} no Controle de Produção | Convite para {…} na Teroz | marca: o produto se chama Teroz |
| `app/services/api_tokens.py:34` | Registrar progresso de atividades | Registrar progresso de subatividades | glossário: atividade → subatividade |
| `app/services/audit.py:107` | Exigência de MFA alterada | Exigência de verificação em duas etapas alterada | sem sigla técnica: verificação em duas etapas |
| `app/services/audit.py:115` | Atividade arquivada | Subatividade arquivada | glossário: atividade → subatividade |
| `app/services/audit.py:117` | Atividade editada | Subatividade editada | glossário: atividade → subatividade |
| `app/services/audit.py:118` | Responsável da atividade alterado | Responsável da subatividade alterado | glossário: atividade → subatividade |
| `app/services/audit.py:119` | Atividade movida | Subatividade movida | glossário: atividade → subatividade |
| `app/services/audit.py:130` | Status da unidade alterado | Situação da unidade alterada | glossário: status → situação |
| `app/services/audit.py:137` | Exclusão da atividade desfeita | Exclusão da subatividade desfeita | glossário: atividade → subatividade |
| `app/services/billing/asaas.py:150` | O Asaas recusou a operação. | O Asaas recusou a operação. Confira os dados de cobrança e tente de novo; se continuar, fale com a gente. | clareza e voz (ver voice-and-tone) |
| `app/services/billing/service.py:348` | Controle de Produção — plano {…} | Teroz — plano {…} | marca: o produto se chama Teroz |
| `app/services/calc.py:926` | Peças concluídas ÷ unidades previstas. Você só digita as peças. | Peças prontas ÷ meta. Você só digita as peças. | glossário: concluídas → prontas |
| `app/services/calc.py:935` | Unidades concluídas da etapa (Tabela 2) | Unidades prontas da etapa (Tabela 2) | glossário: concluídas → prontas |
| `app/services/calc.py:936` | Menor número de peças concluídas entre as subatividades: uma unidade só está pronta quando passou por todas. | Menor número de peças prontas entre as subatividades: uma unidade só está pronta quando passou por todas. | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/services/calc.py:944` | Tempo ideal × unidades previstas. | Tempo ideal × meta. | clareza e voz (ver voice-and-tone) |
| `app/services/calc.py:949` | Tempo ideal × (previstas − peças concluídas). | Tempo ideal × (meta − peças prontas). | glossário: concluídas → prontas |
| `app/services/calc.py:958` | Tempo da etapa × (previstas − unidades concluídas). | Tempo da etapa × (meta − unidades prontas). | glossário: concluídas → prontas |
| `app/services/calc.py:965` | Unidades concluídas do projeto | Unidades prontas do projeto | glossário: concluídas → prontas |
| `app/services/calc.py:966` | Menor número de unidades concluídas entre todas as etapas: uma unidade só está pronta quando passou por todas. | Menor número de unidades prontas entre todas as etapas: uma unidade só está pronta quando passou por todas. | glossário: concluídas → prontas |
| `app/services/calc.py:970` | Progresso geral | Progresso pelas tarefas do projeto | clareza e voz (ver voice-and-tone) |
| `app/services/export_layout.py:202` | Exportado do Controle de Produção em {…}. Para devolver ao site, importe este arquivo. | Exportado da Teroz em {…}. Para devolver ao site, importe este arquivo. | marca: o produto se chama Teroz |
| `app/services/import_mapping.py:80` | A tarefa dentro da etapa, ex.: Soldar suporte. Se a sua planilha não tem esse nível, deixe sem coluna e o projeto entra no modo simples. | A subatividade dentro da etapa, ex.: Soldar suporte. Se a sua planilha não tem esse nível, deixe sem coluna e o projeto entra no modo simples. | clareza e voz (ver voice-and-tone) |
| `app/services/import_mapping.py:98` | Previstas (meta) | Meta (previstas) | clareza e voz (ver voice-and-tone) |
| `app/services/import_mapping.py:99` | Concluídas (peças) | Peças prontas | clareza e voz (ver voice-and-tone) |
| `app/services/import_mapping.py:194` | Previstas / meta (opcional) | Meta / previstas (opcional) | clareza e voz (ver voice-and-tone) |
| `app/services/import_mapping.py:195` | Concluídas (opcional) | Peças prontas (opcional) | clareza e voz (ver voice-and-tone) |
| `app/services/import_mapping.py:454` | mais de {…} atividades na etapa | mais de {…} subatividades na etapa | glossário: atividade → subatividade |
| `app/services/import_mapping.py:541` | com peças concluídas, informe a meta (coluna de previstas ou o número) | com peças prontas, informe a meta (coluna de meta ou o número) | glossário: concluídas → prontas |
| `app/services/importer.py:251` | mais de {…} atividades na etapa | mais de {…} subatividades na etapa | glossário: atividade → subatividade |
| `app/services/importer.py:688` | mais de {…} atividades na etapa | mais de {…} subatividades na etapa | glossário: atividade → subatividade |
| `app/services/importer.py:798` | atividade “{…}” inválida | subatividade “{…}” inválida | glossário: atividade → subatividade |
| `app/services/lgpd.py:161` | Exportação de dados da empresa — Controle de Produção Gerada em {…} (UTC). Um arquivo CSV por tabela (separador ';', UTF-8 com BOM, abre no Excel). Datas em ISO 8601 (UTC). Textos que começam com = + - @ ganham um apó… | Exportação de dados da empresa — Teroz Gerada em {…} (UTC). Um arquivo CSV por tabela (separador ';', UTF-8 com BOM, abre no Excel). Datas em ISO 8601 (UTC). Textos que começam com = + - @ ganham um apóstrofo para a p… | marca: o produto se chama Teroz; glossário: atividade → subatividade; sem sigla técnica: verificação em duas etapas |
| `app/services/mfa.py:103` | Controle de Produção | QR code da verificação em duas etapas | clareza e voz (ver voice-and-tone) |
| `app/services/modules.py:62` | Escolha quem cuida de cada atividade, avise a pessoa por e-mail e veja quantas peças cada um lançou. | Escolha quem cuida de cada subatividade, avise a pessoa por e-mail e veja quantas peças cada um lançou. | glossário: atividade → subatividade |
| `app/services/modules.py:83` | Guarde fotos e comentários em cada atividade, como registro do que foi feito. | Guarde fotos e comentários em cada subatividade, como registro do que foi feito. | glossário: atividade → subatividade |
| `app/services/modules.py:84` | Botão “Fotos e comentários” nas etapas e a tela de cada atividade. | Botão “Fotos e comentários” nas etapas e a tela de cada subatividade. | glossário: atividade → subatividade |
| `app/services/modules.py:128` | Ligue outros sistemas ao Controle de Produção com tokens de acesso. | Ligue outros sistemas à Teroz com tokens de acesso. | marca: o produto se chama Teroz |
| `app/services/notifications.py:26` | Nova atividade atribuída a você | Nova subatividade atribuída a você | glossário: atividade → subatividade |
| `app/services/photos.py:190` | Esta atividade já tem {…} fotos (o máximo). Apague uma para enviar outra. | Esta subatividade já tem {…} fotos (o máximo). Apague uma para enviar outra. | glossário: atividade → subatividade |
| `app/services/projects.py:120` | No modo simples cada etapa tem só o %: no máximo uma atividade por etapa. | No modo simples cada etapa tem só o %: no máximo uma subatividade por etapa. | glossário: atividade → subatividade |
| `app/services/projects.py:221` | Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo. | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | glossário: atividade → subatividade |
| `app/services/projects.py:223` | Máximo {…} peça(s) nesta atividade. | Máximo {…} peça(s) nesta subatividade. | glossário: atividade → subatividade |
| `app/services/projects.py:240` | Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo. | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | glossário: atividade → subatividade |
| `app/services/projects.py:330` | A atividade mudou enquanto você desfazia. Confira e tente de novo. | A subatividade mudou enquanto você desfazia. Confira e tente de novo. | glossário: atividade → subatividade |
| `app/services/projects.py:477` | Já há {…} peças registradas numa atividade: a quantidade não pode ser menor. | Já há {…} peças registradas numa subatividade: a quantidade não pode ser menor. | glossário: atividade → subatividade |
| `app/services/projects.py:540` | Esta atividade mudou enquanto você editava. | Esta subatividade mudou enquanto você editava. | glossário: atividade → subatividade |
| `app/services/projects.py:808` | Esta atividade não está excluída. | Esta subatividade não está excluída. | glossário: atividade → subatividade |
| `app/services/projects.py:811` | A etapa desta atividade também foi excluída: desfaça a exclusão da etapa primeiro. | A etapa desta subatividade também foi excluída: desfaça a exclusão da etapa primeiro. | glossário: atividade → subatividade |
| `app/services/projects.py:813` | No modo simples a etapa tem só o %: não dá para trazer uma segunda atividade. | No modo simples a etapa tem só o %: não dá para trazer uma segunda subatividade. | glossário: atividade → subatividade |
| `app/services/projects.py:844` | As peças concluídas não podem passar das previstas ({…}). | As peças prontas não podem passar das previstas ({…}). | glossário: concluídas → prontas |
| `app/services/projects.py:889` | As peças concluídas vão de 0 a {…}. | As peças prontas vão de 0 a {…}. | glossário: concluídas → prontas |
| `app/services/projects.py:891` | Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo. | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | glossário: atividade → subatividade |
| `app/services/projects.py:912` | Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo. | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | glossário: atividade → subatividade |
| `app/services/templates.py:272` | Nova atividade “{…}” em “{…}” ({…} min) | Nova subatividade “{…}” em “{…}” ({…} min) | glossário: atividade → subatividade |
| `app/services/templates.py:274` | Atividade “{…}” de “{…}” sai (fica arquivada com o histórico) | Subatividade “{…}” de “{…}” sai (fica arquivada com o histórico) | glossário: atividade → subatividade |
| `app/services/units.py:133` | Status inválido. | Situação inválida. | glossário: status → situação |
| `app/services/units.py:135` | Outra pessoa alterou esta unidade. Confira o status atual. | Outra pessoa alterou esta unidade. Confira a situação atual. | glossário: status → situação |
| `app/services/units.py:148` | Outra pessoa alterou esta unidade. Confira o status atual. | Outra pessoa alterou esta unidade. Confira a situação atual. | glossário: status → situação |
| `app/services/units.py:173` | Atividade de outro projeto. | Subatividade de outro projeto. | glossário: atividade → subatividade |
| `app/services/units.py:175` | A unidade {…} já foi registrada nesta atividade. | A unidade {…} já foi registrada nesta subatividade. | glossário: atividade → subatividade |
| `app/templates/_base.html:7` | Controle de Produção | Teroz | marca: o produto se chama Teroz |
| `app/templates/_base.html:8` | {% block description %}Acompanhe a produção por etapas: unidades concluídas, horas que faltam e prazo em dias úteis, do celular ao escritório.{% endblock %} | {% block description %}Acompanhe a produção por etapas: unidades prontas, horas que faltam e prazo em dias úteis, do celular ao escritório.{% endblock %} | glossário: concluídas → prontas |
| `app/templates/_base.html:21` | Controle de Produção | Teroz | marca: o produto se chama Teroz |
| `app/templates/account/companies.html:5` | Trocar de empresa · Controle de Produção | Trocar de empresa · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/confirm.html:4` | Confirmar e-mail · Controle de Produção | Confirmar e-mail · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/confirm_required.html:4` | Confirme seu e-mail · Controle de Produção | Confirme seu e-mail · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/mfa_codes.html:5` | Códigos de recuperação · Controle de Produção | Códigos de recuperação · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/mfa_setup.html:5` | Ativar verificação em duas etapas · Controle de Produção | Ativar verificação em duas etapas · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/profile.html:7` | Perfil · Controle de Produção | Perfil · Teroz | marca: o produto se chama Teroz |
| `app/templates/account/profile.html:90` | Atividade atribuída a mim (com o link) | Subatividade atribuída a mim (com o link) | glossário: atividade → subatividade |
| `app/templates/app/_painel.html:31` | Progresso geral (pelas tarefas) | Progresso pelas tarefas | mesmo nome do indicador em todas as telas |
| `app/templates/app/alerts.html:7` | Alertas · Controle de Produção | Alertas · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/api_tokens.html:10` | API · Controle de Produção | API · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/assinatura.html:9` | Assinatura · Controle de Produção | Assinatura · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/assinatura.html:53` | Status | Situação da assinatura | glossário: status → situação |
| `app/templates/app/assinatura.html:84` | Status | Situação | glossário: status → situação |
| `app/templates/app/assinatura_faturas.html:7` | Faturas · Assinatura · Controle de Produção | Faturas · Assinatura · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/assinatura_faturas.html:24` | Status | Situação | glossário: status → situação |
| `app/templates/app/assinatura_planos.html:7` | Planos · Assinatura · Controle de Produção | Planos · Assinatura · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/assinatura_planos.html:37` | MFA obrigatório | Verificação em duas etapas obrigatória | sem sigla técnica: verificação em duas etapas |
| `app/templates/app/detail/_kpis.html:6` | Progresso geral | Progresso pelas tarefas | clareza e voz (ver voice-and-tone) |
| `app/templates/app/history.html:13` | Histórico · {…} · Controle de Produção | Histórico · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/history.html:49` | Atividade | Subatividade | glossário: atividade → subatividade |
| `app/templates/app/history.html:51` | Todas as atividades | Todas as subatividades | glossário: atividade → subatividade |
| `app/templates/app/history.html:104` | Tente outra atividade ou pessoa, ou limpe os filtros. | Tente outra subatividade ou pessoa, ou limpe os filtros. | glossário: atividade → subatividade |
| `app/templates/app/painel.html:8` | Painel da operação · Controle de Produção | Painel da operação · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/people.html:10` | Pessoas · {…} · Controle de Produção | Pessoas · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/people.html:17` | Peças lançadas no período (desfazeres descontados) e atividades sob responsabilidade de cada pessoa. | Peças lançadas no período (desfazeres descontados) e subatividades sob responsabilidade de cada pessoa. | glossário: atividade → subatividade |
| `app/templates/app/people.html:44` | Progresso das atividades de | Progresso das subatividades de | glossário: atividade → subatividade |
| `app/templates/app/people.html:57` | Ninguém lançou peças neste projeto no período e nenhuma atividade tem responsável. | Ninguém lançou peças neste projeto no período e nenhuma subatividade tem responsável. | glossário: atividade → subatividade |
| `app/templates/app/project_dashboard.html:11` | Painel · {…} · Controle de Produção | Painel · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/project_dashboard.html:43` | ("Unidades prontas", r.unidades_concluidas, "/ " ~ project.quantity, "menor nº de unidades concluídas entre as etapas", None), | ("Unidades prontas", r.unidades_concluidas, "/ " ~ project.quantity, "a etapa mais atrasada define o número", None), | explica a regra em linguagem simples |
| `app/templates/app/project_dashboard.html:44` | ("Etapas concluídas", r.etapas_concluidas, "/ " ~ (d.etapas\|length), "tarefas concluídas: " ~ r.tarefas_concluidas ~ " de " ~ r.tarefas, None), | ("Etapas concluídas", r.etapas_concluidas, "/ " ~ (d.etapas\|length), "subatividades em 100%: " ~ r.tarefas_concluidas ~ " de " ~ r.tarefas, None), | glossário |
| `app/templates/app/project_dashboard.html:54` | Barras por etapa: progresso pelas tarefas e unidades concluídas. Valores na tabela de dados. | Barras por etapa: progresso pelas tarefas e unidades prontas. Valores na tabela de dados. | glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:54` | Unidades concluídas | Unidades prontas | glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:55` | Azul: progresso pelas tarefas (conta as parciais). Laranja: unidades 100% prontas ÷ previstas. Clique numa barra para preencher a etapa. | Azul: progresso pelas tarefas (conta as parciais). Laranja: unidades prontas ÷ meta. Clique numa barra para preencher a etapa. | glossário |
| `app/templates/app/project_dashboard.html:114` | Tabela 2 · Unidades concluídas por etapa | Tabela 2 · Unidades prontas por etapa | glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:121` | Peças concluídas de cada atividade sobre as previstas. | Peças prontas de cada subatividade sobre a meta. | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:121` | Feitas ÷ previstas, sem contar parciais. | Unidades prontas ÷ meta, sem contar as parciais. | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:130` | Previstas | Meta | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:142` | Previstas | Meta | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:155` | Feitas | Prontas | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:156` | Previstas | Meta | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:157` | % concluída | % pronta | glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:157` | Unidades concluídas de | Unidades prontas de | glossário: concluídas → prontas |
| `app/templates/app/project_dashboard.html:165` | Feitas | Prontas | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:166` | Previstas | Meta | clareza e voz (ver voice-and-tone) |
| `app/templates/app/project_dashboard.html:167` | % concluída | % pronta | glossário: concluídas → prontas |
| `app/templates/app/project_detail.html:54` | Status | Situação | glossário: status → situação |
| `app/templates/app/project_detail.html:105` | Nenhuma atividade nesta etapa. | Nenhuma subatividade nesta etapa. | glossário: atividade → subatividade |
| `app/templates/app/project_detail.html:112` | Nova atividade | Nova subatividade | glossário: atividade → subatividade |
| `app/templates/app/project_detail.html:119` | Incluir atividade | Incluir subatividade | glossário: atividade → subatividade |
| `app/templates/app/project_new.html:8` | Novo projeto · Controle de Produção | Novo projeto · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/project_new.html:79` | Você lança o % de cada etapa. Atividades ficam em branco (ou uma linha com o tempo da etapa). | Você lança o % de cada etapa. Subatividades ficam em branco (ou uma linha com o tempo da etapa). | glossário: atividade → subatividade |
| `app/templates/app/project_new.html:101` | Atividades | Subatividades | glossário: atividade → subatividade |
| `app/templates/app/projects.html:10` | Projetos · Controle de Produção | Projetos · Teroz | marca: o produto se chama Teroz |
| `app/templates/app/projects.html:37` | Buscar lote ou produto | Buscar projeto ou produto | glossário: projeto |
| `app/templates/app/projects.html:84` | Crie o primeiro lote com as etapas, a quantidade e o prazo. | Crie o primeiro projeto com as etapas, a meta e o prazo. | clareza e voz (ver voice-and-tone) |
| `app/templates/auth/forgot.html:5` | Esqueci a senha · Controle de Produção | Esqueci a senha · Teroz | marca: o produto se chama Teroz |
| `app/templates/auth/login.html:5` | Entrar · Controle de Produção | Entrar · Teroz | marca: o produto se chama Teroz |
| `app/templates/auth/login_mfa.html:5` | Verificação em duas etapas · Controle de Produção | Verificação em duas etapas · Teroz | marca: o produto se chama Teroz |
| `app/templates/auth/reset.html:5` | Nova senha · Controle de Produção | Nova senha · Teroz | marca: o produto se chama Teroz |
| `app/templates/auth/signup.html:5` | Cadastrar empresa · Controle de Produção | Cadastrar empresa · Teroz | marca: o produto se chama Teroz |
| `app/templates/auth/signup.html:33` | em 2 toques, direto do chão de fábrica. | : digite o total de peças prontas e pronto, direto do chão de fábrica. | clareza e voz (ver voice-and-tone) |
| `app/templates/auth/signup_done.html:4` | Confirme seu e-mail · Controle de Produção | Confirme seu e-mail · Teroz | marca: o produto se chama Teroz |
| `app/templates/base_app.html:64` | Teroz, Controle de Produção — Painel | Teroz — Painel | marca: o produto se chama Teroz |
| `app/templates/base_app.html:95` | Teroz, Controle de Produção — Painel | Teroz — Painel | marca: o produto se chama Teroz |
| `app/templates/base_app.html:96` | Controle de Produção | Teroz | marca: o produto se chama Teroz |
| `app/templates/base_publica.html:68` | © 2026 Controle de Produção | © 2026 Teroz | marca: o produto se chama Teroz |
| `app/templates/components/export_menu.html:14` | Uma linha por atividade | Uma linha por subatividade | glossário: atividade → subatividade |
| `app/templates/components/export_menu.html:18` | Uma linha por atividade, para filtrar no Excel | Uma linha por subatividade, para filtrar no Excel | glossário: atividade → subatividade |
| `app/templates/components/stepper.html:26` | {…} de {…} concluídas · faltam {…} | {…} de {…} prontas · faltam {…} | glossário: concluídas → prontas |
| `app/templates/dados/_import_mode.html:25` | Uma linha por etapa, com o % concluído (ou as concluídas). Para lançar por atividade, marque uma coluna como Subatividade. | Uma linha por etapa, com o % concluído (ou as concluídas). Para lançar por subatividade, marque uma coluna como Subatividade. | glossário: atividade → subatividade |
| `app/templates/dados/import.html:18` | Traga etapas e atividades de uma planilha .xlsx ou .csv. Nada é gravado antes da sua confirmação. | Traga etapas e subatividades de uma planilha .xlsx ou .csv. Nada é gravado antes da sua confirmação. | glossário: atividade → subatividade |
| `app/templates/dados/import.html:71` | Pré-visualização | Prévia | clareza e voz (ver voice-and-tone) |
| `app/templates/dados/import.html:81` | Cada linha vira uma atividade dentro da etapa, com tempo ideal e peças concluídas. | Cada linha vira uma subatividade dentro da etapa, com tempo ideal e peças prontas. | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/dados/import.html:97` | Etapa › atividade | Etapa › subatividade | glossário: atividade → subatividade |
| `app/templates/dados/import.html:105` | Concluídas | Peças prontas | clareza e voz (ver voice-and-tone) |
| `app/templates/dados/import.html:108` | Sem atividades | Sem subatividades | glossário: atividade → subatividade |
| `app/templates/dados/import_map.html:7` | Escolher colunas · Importar planilha · Controle de Produção | Escolher colunas · Importar planilha · Teroz | marca: o produto se chama Teroz |
| `app/templates/dados/import_map.html:106` | Use se a planilha não tem a coluna de previstas. | Use se a planilha não tem a coluna de meta (previstas). | clareza e voz (ver voice-and-tone) |
| `app/templates/edicao/compare.html:25` | O projeto já tem as mesmas etapas, atividades e tempos da versão atual. | O projeto já tem as mesmas etapas, subatividades e tempos da versão atual. | glossário: atividade → subatividade |
| `app/templates/edicao/compare.html:34` | Peças já registradas e o histórico não mudam. Etapas e atividades que saem ficam arquivadas. | Peças já registradas e o histórico não mudam. Etapas e subatividades que saem ficam arquivadas. | glossário: atividade → subatividade |
| `app/templates/edicao/project_edit.html:63` | Etapas e atividades | Etapas e subatividades | glossário: atividade → subatividade |
| `app/templates/edicao/project_edit.html:65` | Arraste pela alça ⠿ para reordenar etapas ou levar uma atividade para outra etapa; os botões Subir/Descer e “Mover” fazem o mesmo sem arrastar. | Arraste pela alça ⠿ para reordenar etapas ou levar uma subatividade para outra etapa; os botões Subir/Descer e “Mover” fazem o mesmo sem arrastar. | glossário: atividade → subatividade |
| `app/templates/edicao/project_edit.html:101` | Arrastar a atividade | Arrastar a subatividade | glossário: atividade → subatividade |
| `app/templates/edicao/project_edit.html:105` | Atividade | Subatividade | glossário: atividade → subatividade |
| `app/templates/edicao/project_edit.html:143` | Sem atividades. Inclua pela tela do projeto. | Sem subatividades. Inclua pela tela do projeto. | glossário: atividade → subatividade |
| `app/templates/edicao/restore.html:11` | Restaurar para uma data · {…} · Controle de Produção | Restaurar para uma data · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/edicao/restore.html:39` | Hora de {…}. Voltam só as peças concluídas de cada atividade; nomes, tempos, meta e etapas ficam como estão. O histórico não perde nada e dá para desfazer depois. | Hora de {…}. Voltam só as peças prontas de cada subatividade; nomes, tempos, meta e etapas ficam como estão. O histórico não perde nada e dá para desfazer depois. | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/edicao/restore.html:52` | ("Progresso geral", b.progresso_geral\|pct, a.progresso_geral\|pct), | ("Progresso pelas tarefas", b.progresso_geral\|pct, a.progresso_geral\|pct), | mesmo nome do indicador |
| `app/templates/edicao/restore.html:54` | ("Tarefas concluídas", b.tarefas_concluidas ~ " de " ~ b.tarefas, a.tarefas_concluidas ~ " de " ~ a.tarefas), | ("Subatividades em 100%", b.tarefas_concluidas ~ " de " ~ b.tarefas, a.tarefas_concluidas ~ " de " ~ a.tarefas), | glossário |
| `app/templates/edicao/restore.html:55` | ("Tempo que falta", b.tempo_restante_h\|horas, a.tempo_restante_h\|horas), | ("Horas que faltam", b.tempo_restante_h\|horas, a.tempo_restante_h\|horas), | mesmo nome do indicador |
| `app/templates/edicao/restore.html:70` | Peças concluídas agora e depois de restaurar, por etapa e atividade | Peças prontas agora e depois de restaurar, por etapa e subatividade | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/edicao/restore.html:71` | Etapa › atividade | Etapa › subatividade | glossário: atividade → subatividade |
| `app/templates/edicao/restore.html:87` | atividade muda | subatividade muda | glossário: atividade → subatividade |
| `app/templates/edicao/restore.html:87` | atividades mudam | subatividades mudam | glossário: atividade → subatividade |
| `app/templates/edicao/restore.html:92` | , com um lançamento de restauração por atividade no histórico. | , com um lançamento de restauração por subatividade no histórico. | glossário: atividade → subatividade |
| `app/templates/emails/_base.html:14` | Controle de Produção | Teroz | marca: o produto se chama Teroz |
| `app/templates/emails/_base.txt:1` | Controle de Produção | Teroz | marca: o produto se chama Teroz |
| `app/templates/emails/_base.txt:7` | Você recebeu esta mensagem por causa de uma ação na sua conta do Controle de Produção. | Você recebeu esta mensagem por causa de uma ação na sua conta da Teroz. | marca: o produto se chama Teroz |
| `app/templates/emails/activity_assigned.html:3` | Olá, {…}. Você agora é responsável por uma atividade na empresa {…}: | Olá, {…}. Você agora é responsável por uma subatividade na empresa {…}: | glossário: atividade → subatividade |
| `app/templates/emails/activity_assigned.html:7` | Abrir a atividade | Abrir a subatividade | glossário: atividade → subatividade |
| `app/templates/emails/activity_assigned.txt:2` | Olá, {…}. Você agora é responsável por uma atividade na empresa {…}: | Olá, {…}. Você agora é responsável por uma subatividade na empresa {…}: | glossário: atividade → subatividade |
| `app/templates/emails/activity_assigned.txt:8` | Abrir a atividade: {…} | Abrir a subatividade: {…} | glossário: atividade → subatividade |
| `app/templates/emails/activity_assigned.txt:10` | Você recebe este aviso porque uma atividade foi atribuída a você. | Você recebe este aviso porque uma subatividade foi atribuída a você. | glossário: atividade → subatividade |
| `app/templates/emails/activity_assigned.txt:11` | Para não receber mais, desligue "Atividade atribuída a mim" em {…} | Para não receber mais, desligue "Subatividade atribuída a mim" em {…} | glossário: atividade → subatividade |
| `app/templates/emails/billing_past_due.html:3` | O pagamento da assinatura do Controle de Produção da empresa | O pagamento da assinatura da Teroz da empresa | marca: o produto se chama Teroz |
| `app/templates/emails/billing_past_due.txt:2` | O pagamento da assinatura do Controle de Produção da empresa {…} venceu e ainda não foi identificado. | O pagamento da assinatura da Teroz da empresa {…} venceu e ainda não foi identificado. | marca: o produto se chama Teroz |
| `app/templates/emails/call_change_decided.html:7` | A equipe manteve a ligação de {…} (horário de Brasília). Se precisar, responda a este e-mail. | A equipe manteve a ligação de {…} (horário de Brasília). Se precisar de outra mudança, peça pela tela da ligação. | o rodapé diz que a caixa não é lida |
| `app/templates/emails/call_change_decided.txt:4` | A equipe cancelou a ligação de {…} (horário de Brasília). Se quiser outro horário, escolha um na tela da ligação. A equipe manteve a ligação de {…} (horário de Brasília). Se precisar, responda a este e-mail. | A equipe cancelou a ligação de {…} (horário de Brasília). Se quiser outro horário, escolha um na tela da ligação. A equipe manteve a ligação de {…} (horário de Brasília). Se precisar de outra mudança, peça pela tela d… | o rodapé diz que a caixa não é lida |
| `app/templates/emails/confirm_email.html:4` | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso ao Controle de Produção. | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso à Teroz. | marca: o produto se chama Teroz |
| `app/templates/emails/confirm_email.txt:4` | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso ao Controle de Produção. | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso à Teroz. | marca: o produto se chama Teroz |
| `app/templates/emails/deletion_requested.html:4` | Foi pedida a exclusão da empresa {…} no Controle de Produção. Todos os dados serão apagados definitivamente em | Foi pedida a exclusão da empresa {…} na Teroz. Todos os dados serão apagados definitivamente em | marca: o produto se chama Teroz |
| `app/templates/emails/deletion_requested.txt:4` | Foi pedida a exclusão da empresa {…} no Controle de Produção. | Foi pedida a exclusão da empresa {…} na Teroz. | marca: o produto se chama Teroz |
| `app/templates/emails/email_changed.txt:5` | Se não foi você, responda ao suporte imediatamente. | Se não foi você, peça uma nova senha agora e escreva para o contato indicado no site. | o rodapé diz que a caixa não é lida |
| `app/templates/emails/invite.html:3` | {…} convidou você para a empresa {…} no Controle de Produção, como {…}. | {…} convidou você para a empresa {…} na Teroz, como {…}. | marca: o produto se chama Teroz |
| `app/templates/emails/invite.txt:2` | {…} convidou você para a empresa {…} no Controle de Produção, como {…}. | {…} convidou você para a empresa {…} na Teroz, como {…}. | marca: o produto se chama Teroz |
| `app/templates/emails/support_access.html:4` | A equipe de suporte do Controle de Produção recebeu acesso temporário à empresa {…}. | A equipe de suporte da Teroz recebeu acesso temporário à empresa {…}. | marca: o produto se chama Teroz |
| `app/templates/emails/support_access.txt:4` | A equipe de suporte do Controle de Produção recebeu acesso temporário à empresa {…}. | A equipe de suporte da Teroz recebeu acesso temporário à empresa {…}. | marca: o produto se chama Teroz |
| `app/templates/empresa/modulos.html:8` | Módulos · Controle de Produção | Módulos · Teroz | marca: o produto se chama Teroz |
| `app/templates/empresa/settings.html:10` | Empresa · Controle de Produção | Empresa · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/400.html:2` | Requisição inválida · Controle de Produção | Pedido não concluído · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/400.html:4` | Não deu para concluir | Pedido não concluído | clareza e voz (ver voice-and-tone) |
| `app/templates/errors/400.html:5` | Requisição inválida. | Algo no envio não veio como esperado. Volte à página anterior e tente de novo. | clareza e voz (ver voice-and-tone) |
| `app/templates/errors/403.html:2` | Acesso negado · Controle de Produção | Acesso negado · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/403.html:4` | Você não tem permissão para isto | Você não tem permissão para fazer isso | clareza e voz (ver voice-and-tone) |
| `app/templates/errors/404.html:2` | Página não encontrada · Controle de Produção | Página não encontrada · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/429.html:2` | Muitas tentativas · Controle de Produção | Muitas tentativas · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/500.html:4` | Erro inesperado · Controle de Produção | Erro inesperado · Teroz | marca: o produto se chama Teroz |
| `app/templates/errors/500.html:7` | Já fomos avisados. Tente de novo em instantes. | Tente de novo em instantes. Se o erro continuar, escreva para o contato do site. | clareza e voz (ver voice-and-tone) |
| `app/templates/identidade/briefing.html:10` | Identidade visual · Controle de Produção | Identidade visual · Teroz | marca: o produto se chama Teroz |
| `app/templates/identidade/ligacao.html:10` | Ligação · Identidade visual · Controle de Produção | Ligação · Identidade visual · Teroz | marca: o produto se chama Teroz |
| `app/templates/interno/index.html:4` | Painel interno · Controle de Produção | Painel interno · Teroz | marca: o produto se chama Teroz |
| `app/templates/lgpd/index.html:6` | Privacidade e dados · Controle de Produção | Privacidade e dados · Teroz | marca: o produto se chama Teroz |
| `app/templates/lgpd/index.html:22` | Baixe um arquivo ZIP com uma planilha CSV para cada tipo de dado da empresa: projetos, etapas, atividades, registros de peças, modelos, usuários, convites, assinatura, auditoria e integrações. Senhas e chaves não são … | Baixe um arquivo ZIP com uma planilha CSV para cada tipo de dado da empresa: projetos, etapas, subatividades, registros de peças, modelos, usuários, convites, assinatura, auditoria e integrações. Senhas e chaves não s… | glossário: atividade → subatividade |
| `app/templates/modelos/_stages.html:23` | Atividades | Subatividades | glossário: atividade → subatividade |
| `app/templates/modelos/edit.html:42` | Na ordem de montagem. Em cada etapa, uma atividade por linha: | Na ordem de montagem. Em cada etapa, uma subatividade por linha: | glossário: atividade → subatividade |
| `app/templates/modelos/index.html:7` | Modelos de etapas · Controle de Produção | Modelos de etapas · Teroz | marca: o produto se chama Teroz |
| `app/templates/modelos/index.html:35` | Monte etapas e atividades com tempo ideal, ou importe um CSV. | Monte etapas e subatividades com tempo ideal, ou importe um CSV. | glossário: atividade → subatividade |
| `app/templates/modelos/versions.html:27` | — {…} ({…} min) , sem atividades | — {…} ({…} min) , sem subatividades | glossário: atividade → subatividade |
| `app/templates/preencher/_oob.html:12` | Unidades concluídas | Unidades prontas | glossário: concluídas → prontas |
| `app/templates/preencher/_painel.html:106` | Unidades concluídas | Unidades prontas | glossário: concluídas → prontas |
| `app/templates/preencher/_painel.html:210` | Peças concluídas da nova subatividade | Peças prontas da nova subatividade | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/preencher/fill.html:9` | Preencher etapas · {…} · Controle de Produção | Preencher etapas · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/preencher/goal_team.html:8` | Meta e equipe · {…} · Controle de Produção | Meta e equipe · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/preencher/how.html:4` | Como funciona · {…} · Controle de Produção | Como funciona · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/como_funciona.html:3` | Como funciona com a sua planilha · Controle de Produção | Como funciona com a sua planilha · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/como_funciona.html:21` | Atividade | Subatividade | glossário: atividade → subatividade |
| `app/templates/public/como_funciona.html:23` | Peças concluídas | Peças prontas | glossário: concluídas → prontas |
| `app/templates/public/como_funciona.html:36` | O sistema sugere o significado pelo nome do cabeçalho. Você corrige o que precisar: etapa, atividade, tempo ideal, peças previstas e concluídas ou prazo. | O sistema sugere o significado pelo nome do cabeçalho. Você corrige o que precisar: etapa, subatividade, tempo ideal, peças previstas e concluídas ou prazo. | glossário: atividade → subatividade |
| `app/templates/public/como_funciona.html:37` | Veja uma prévia com as etapas e as atividades. Se houver erro, o sistema mostra a linha, a coluna e o problema, e você volta às colunas sem enviar o arquivo de novo. | Veja uma prévia com as etapas e as subatividades. Se houver erro, o sistema mostra a linha, a coluna e o problema, e você volta às colunas sem enviar o arquivo de novo. | glossário: atividade → subatividade |
| `app/templates/public/como_funciona.html:37` | Tela Prévia e confirmar: etapas e atividades lidas da planilha, com tempo ideal e peças concluídas. | Tela Prévia e confirmar: etapas e subatividades lidas da planilha, com tempo ideal e peças prontas. | glossário: atividade → subatividade; glossário: concluídas → prontas |
| `app/templates/public/como_funciona.html:48` | Etapa, atividade e tempo | Etapa, subatividade e tempo | glossário: atividade → subatividade |
| `app/templates/public/como_funciona.html:48` | Se ela detalha as atividades de cada etapa, com tempo ideal e peças feitas, você ganha as horas que faltam e o prazo em dias úteis com mais precisão. | Se ela detalha as subatividades de cada etapa, com tempo ideal e peças feitas, você ganha as horas que faltam e o prazo em dias úteis com mais precisão. | glossário: atividade → subatividade |
| `app/templates/public/contato.html:4` | Contato · Controle de Produção | Contato · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/contato.html:5` | Fale com o Controle de Produção: dúvidas sobre planos, suporte e privacidade, por e-mail. | Fale com a Teroz: dúvidas sobre planos, suporte e privacidade, por e-mail. | marca: o produto se chama Teroz |
| `app/templates/public/index.html:5` | Controle de Produção · saiba em que etapa está cada lote | Teroz · saiba em que etapa está cada lote | marca: o produto se chama Teroz |
| `app/templates/public/index.html:29` | Painel de um lote no Teroz: progresso geral de 39%, horas que faltam, dias úteis até o prazo, barras de tarefas e unidades por etapa e a situação das etapas. | Painel de um projeto na Teroz: progresso pelas tarefas de 40%, horas que faltam, dias úteis até o prazo, barras de tarefas e unidades por etapa e a situação das etapas. | clareza e voz (ver voice-and-tone) |
| `app/templates/public/index.html:32` | Tela real do Teroz, com dados de exemplo. | Tela real da Teroz, com dados de exemplo. | clareza e voz (ver voice-and-tone) |
| `app/templates/public/index.html:53` | Envie o arquivo e diga qual coluna é a etapa, qual é a atividade e qual é o tempo. Se preferir, monte as etapas direto na tela. | Envie o arquivo e diga qual coluna é a etapa, qual é a subatividade e qual é o tempo. Se preferir, monte as etapas direto na tela. | glossário: atividade → subatividade |
| `app/templates/public/index.html:55` | Quem está na bancada registra as peças concluídas pelo celular. As horas que faltam e o prazo se recalculam na hora. | Quem está na bancada registra as peças prontas pelo celular. As horas que faltam e o prazo se recalculam na hora. | glossário: concluídas → prontas |
| `app/templates/public/index.html:75` | Atividade | Subatividade | glossário: atividade → subatividade |
| `app/templates/public/index.html:77` | Peças concluídas | Peças prontas | glossário: concluídas → prontas |
| `app/templates/public/index.html:87` | Etapas, atividades e peças vêm prontas. O que está abaixo fica desligado até você ativar em Configurações. | Etapas, subatividades e peças vêm prontas. O que está abaixo fica desligado até você ativar em Configurações. | glossário: atividade → subatividade |
| `app/templates/public/index.html:89` | Anexe fotos e observações ao registro de uma atividade. | Guarde fotos e observações em cada subatividade, como registro do que foi feito. | glossário: atividade → subatividade |
| `app/templates/public/index.html:89` | Uma lista de itens para conferir antes de dar a atividade como pronta. | Uma lista de conferência por etapa, assinada por quem inspecionou. | recurso real: o checklist é por etapa e só sinaliza (não trava) |
| `app/templates/public/index.html:89` | Aviso de etapa atrasada e um resumo semanal na caixa de entrada. | Aviso quando o prazo entra em risco ou uma etapa para, e um resumo toda segunda-feira. | recurso real (alertas: prazo em risco, etapa parada, peça atrasada; relatório semanal às segundas) |
| `app/templates/public/index.html:89` | Equipe | Responsáveis | clareza e voz (ver voice-and-tone) |
| `app/templates/public/index.html:89` | Atribua atividades a pessoas e veja o progresso de cada uma. | Defina quem cuida de cada subatividade e veja quantas peças cada pessoa lançou. | glossário: atividade → subatividade |
| `app/templates/public/precos.html:6` | Preços · Controle de Produção | Preços · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/precos.html:38` | Verificação em duas etapas obrigatória (MFA) | Verificação em duas etapas obrigatória para proprietários | sem sigla; escopo real |
| `app/templates/public/privacidade.html:4` | Política de privacidade · Controle de Produção | Política de privacidade · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/privacidade.html:5` | Como o Controle de Produção trata dados pessoais conforme a LGPD: o que coletamos, para quê, com quem compartilhamos e como exercer seus direitos. Rascunho para revisão jurídica. | Como a Teroz trata dados pessoais conforme a LGPD: o que coletamos, para quê, com quem compartilhamos e como exercer seus direitos. Rascunho para revisão jurídica. | marca: o produto se chama Teroz |
| `app/templates/public/privacidade.html:9` | O Controle de Produção é operado por uma empresa brasileira (razão social e CNPJ a preencher antes do lançamento). Somos controladores dos dados de conta e cobrança e operadores dos dados de produção que cada empresa-… | A Teroz é operada por uma empresa brasileira (razão social e CNPJ a preencher antes do lançamento). Somos controladores dos dados de conta e cobrança e operadores dos dados de produção que cada empresa-cliente registra. | concordância |
| `app/templates/public/privacidade.html:13` | Conta: nome, e-mail, senha (guardada só como hash) e vínculo com a empresa. Uso: quem registrou cada peça, quando e em qual atividade. Cobrança: dados de faturamento da empresa, tratados pelo provedor de pagamento. Té… | Conta: nome, e-mail, senha (guardada só como hash) e vínculo com a empresa. Uso: quem registrou cada peça, quando e em qual subatividade. Cobrança: dados de faturamento da empresa, tratados pelo provedor de pagamento.… | glossário: atividade → subatividade |
| `app/templates/public/termos.html:4` | Termos de uso · Controle de Produção | Termos de uso · Teroz | marca: o produto se chama Teroz |
| `app/templates/public/termos.html:5` | Termos de uso do Controle de Produção: conta, planos, pagamento, carência, seus dados e responsabilidades. Rascunho para revisão jurídica. | Termos de uso da Teroz: conta, planos, pagamento, carência, seus dados e responsabilidades. Rascunho para revisão jurídica. | marca: o produto se chama Teroz |
| `app/templates/public/termos.html:9` | O Controle de Produção é um serviço web para acompanhar a produção por etapas e atividades: progresso, unidades concluídas, tempo restante e prazo em dias úteis. Ele é oferecido a empresas, por assinatura. | A Teroz é um serviço web para acompanhar a produção por etapas e subatividades: progresso, unidades prontas, tempo restante e prazo em dias úteis. Ela é oferecida a empresas, por assinatura. | concordância |
| `app/templates/public/termos.html:25` | Não use o serviço para atividade ilegal, para tentar acessar dados de outra empresa, nem para sobrecarregar ou testar a segurança dele sem autorização por escrito. | Não use o serviço para atividade ilegal, para tentar acessar dados de outra empresa, nem para sobrecarregar o serviço ou testar a segurança dele sem autorização por escrito. | clareza |
| `app/templates/qualidade/checklist.html:12` | Checklist · {…} · Controle de Produção | Checklist · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/evidencias.html:9` | Evidências · {…} · Controle de Produção | Fotos e comentários · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/evidencias.html:16` | Evidências · {…} | Fotos e comentários · {…} | clareza e voz (ver voice-and-tone) |
| `app/templates/qualidade/evidencias.html:72` | Limite de {…} fotos nesta atividade. Apague uma para enviar outra. | Limite de {…} fotos nesta subatividade. Apague uma para enviar outra. | glossário: atividade → subatividade |
| `app/templates/qualidade/inspecao.html:9` | Inspeção · {…} · Controle de Produção | Inspeção · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/unidade.html:10` | Unidade {…} · Controle de Produção | Unidade {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/unidade.html:61` | Sem alterações de status. | Sem alterações de situação. | glossário: status → situação |
| `app/templates/qualidade/unidade.html:71` | Atividade concluída | Subatividade concluída | glossário: atividade → subatividade |
| `app/templates/qualidade/unidade.html:82` | Status | Situação | glossário: status → situação |
| `app/templates/qualidade/unidade.html:86` | Status da unidade | Situação da unidade | glossário: status → situação |
| `app/templates/qualidade/unidade.html:91` | Salvar status | Salvar situação | glossário: status → situação |
| `app/templates/qualidade/unidades.html:11` | Unidades · {…} · Controle de Produção | Unidades · {…} · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/unidades.html:38` | Status | Situação | glossário: status → situação |
| `app/templates/qualidade/unidades_busca.html:8` | Buscar unidade · Controle de Produção | Buscar unidade · Teroz | marca: o produto se chama Teroz |
| `app/templates/qualidade/unidades_busca.html:33` | Status | Situação | glossário: status → situação |
| `app/templates/team/accept.html:5` | Convite · Controle de Produção | Convite · Teroz | marca: o produto se chama Teroz |
| `app/templates/team/users.html:10` | Usuários · Controle de Produção | Usuários · Teroz | marca: o produto se chama Teroz |
| `app/templates/team/users.html:122` | Exigir MFA dos proprietários | Exigir dos proprietários | sem sigla técnica: verificação em duas etapas |

## Removidos ou fundidos

| Arquivo:linha (antes) | Texto |
|---|---|
| `app/blueprints/edicao.py:370` | Atividade movida. |
| `app/services/mfa.py:103` | QR code do MFA |
| `app/templates/components/brand.html:4` | Teroz, Controle de Produção |
| `app/templates/components/brand.html:5` | Teroz, Controle de Produção |

## Pendências e decisões humanas

- **Remetente dos e-mails** (`MAIL_FROM` em `render.yaml` e no ambiente): ainda “Controle de Produção <…>”. Muda na configuração de produção.
- **Planilha exportada** e **sinônimos do importador** mantêm “Atividade”, “Previstas”, “Feitas”: são o formato da planilha da equipe e o que a importação precisa reconhecer.
- **“Quantidade de equipamentos”** no formulário antigo de novo projeto: trocar por “Meta (unidades)” muda o rótulo que operadores já conhecem; decidir.
- **Situação “Atrasada”** supõe etapas em sequência (F-06): o texto só pode prometer o que a regra faz.
- **“Aguardando peça”** só sinaliza, não trava: confirmar se é o desejado antes de prometer mais na tela.
- **Identidade visual, Painel interno e API**: só a padronização automática de termos; falta leitura linha a linha.

## Inventário completo por área

Colunas: página · componente · arquivo:linha · contexto (tipo de texto) · texto atual · intenção · problema · texto proposto · status.

<details><summary><b>Painéis e projetos</b> (865)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/app.py | valor | `app/blueprints/app.py:38` | backend:valor | Qualquer prazo | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:39` | backend:valor | Com atraso previsto | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:40` | backend:valor | Vence em 7 dias | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:41` | backend:valor | Sem prazo | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | Response | `app/blueprints/app.py:243` | backend:Response | text/csv; charset=utf-8 | mensagem do backend | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:244` | backend:valor | attachment; filename="projetos.csv" | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:257` | backend:valor | Sem modelo (digitar as etapas) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | flash | `app/blueprints/app.py:279` | backend:flash | Projeto criado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:440` | backend:valor | Tabela 1 · Tarefas | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:440` | backend:valor | Tabela 2 · Unidades | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:489` | backend:valor | 7 dias | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:489` | backend:valor | 30 dias | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:489` | backend:valor | 90 dias | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:502` | backend:valor | Pessoa removida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | _render_detail | `app/blueprints/app.py:641` | backend:_render_detail | Informe o nome da etapa. | mensagem do backend | — | — | revisado — mantido |
| blueprints/app.py | flash | `app/blueprints/app.py:644` | backend:flash | Etapa incluída. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/app.py | _render_detail | `app/blueprints/app.py:654` | backend:_render_detail | Informe nome e tempo ideal (min) válidos. | mensagem do backend | — | — | revisado — mantido |
| blueprints/app.py | flash | `app/blueprints/app.py:657` | backend:flash | Subatividade incluída. | confirmação ou aviso após ação | antes: “Atividade incluída.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| blueprints/app.py | valor | `app/blueprints/app.py:681` | backend:valor | Confira a previsão (data) e a observação (até 140 caracteres). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:692` | backend:valor | marcada como aguardando peça | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:692` | backend:valor | sem a marca de aguardando peça | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:693` | backend:valor | Outra pessoa alterou esta etapa enquanto você editava: agora ela está {…}. Confira e salve de novo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | flash | `app/blueprints/app.py:705` | backend:flash | Etapa marcada como aguardando peça. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/app.py | flash | `app/blueprints/app.py:705` | backend:flash | Marca de aguardando peça retirada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/app.py | _render_detail | `app/blueprints/app.py:730` | backend:_render_detail | Informe um número inteiro de peças (mínimo 1). | mensagem do backend | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:746` | backend:valor | Outra pessoa registrou antes: esta subatividade agora está em {…} de {…}. | valor exibido (rótulo, opção, situação) | antes: “Outra pessoa registrou antes: esta atividade agora está em {…} de {…}.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| blueprints/app.py | valor | `app/blueprints/app.py:749` | backend:valor | Ela já está completa; nada a somar. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:751` | backend:valor | Confirme para somar +{…} sobre o valor atual. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:771` | backend:valor | +{…} em {…} · {…} de {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:794` | backend:valor | +{…} (faltam só {…}) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/app.py | valor | `app/blueprints/app.py:795` | backend:valor | +{…} (→ {…} de {…}) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:104` | backend:flash | Projeto atualizado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:115` | backend:flash | Projeto duplicado com progresso zerado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:125` | backend:flash | Marque a confirmação para arquivar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:130` | backend:flash | Projeto “{…}” apagado (arquivado). O histórico continua guardado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:132` | backend:flash | Projeto arquivado. O histórico continua guardado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:154` | backend:flash | Marque a confirmação para aplicar a versão do modelo. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:163` | backend:flash | Versão {…} do modelo aplicada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | _fill_error | `app/blueprints/edicao.py:194` | backend:_fill_error | {…} Agora: {…}. Confira e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/edicao.py | valor | `app/blueprints/edicao.py:197` | backend:valor | {…} Agora: {…}. Confira e salve de novo para confirmar a sua versão. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:208` | backend:flash | Informe o nome da etapa. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:221` | backend:flash | Etapa renomeada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:265` | backend:flash | Ordem das etapas salva. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:276` | backend:flash | Etapa “{…}” apagada. Para desfazer, use “Etapas apagadas” no fim da lista. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:278` | backend:flash | Etapa arquivada. Os registros dela continuam no histórico. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:292` | backend:flash | Informe nome e tempo ideal (min) válidos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | valor | `app/blueprints/edicao.py:299` | backend:valor | “{…}”, {…} min, {…} de {…} peças | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:309` | backend:flash | Subatividade atualizada. | confirmação ou aviso após ação | antes: “Atividade atualizada.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:336` | backend:flash | Responsável definido. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:336` | backend:flash | Subatividade sem responsável. | confirmação ou aviso após ação | antes: “Atividade sem responsável.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| blueprints/edicao.py | _fill_error | `app/blueprints/edicao.py:357` | backend:_fill_error | {…} Confira onde ela está agora e mova de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/edicao.py | valor | `app/blueprints/edicao.py:362` | backend:valor | {…} Agora ela está em “{…}”. Confira a posição e mova de novo para confirmar. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:370` | backend:flash | Subatividade movida. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:396` | backend:flash | Subatividade “{…}” apagada. Para desfazer, use “Subatividades apagadas” abaixo da tabela. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:398` | backend:flash | Subatividade arquivada. Os registros dela continuam no histórico. | confirmação ou aviso após ação | antes: “Atividade arquivada. Os registros dela continuam no histórico.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:417` | backend:flash | Marque a confirmação para desfazer. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:426` | backend:flash | Registro desfeito. {…}: {…} de {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | valor | `app/blueprints/edicao.py:456` | backend:valor | Data e hora inválidas. Escolha o dia e a hora no campo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/edicao.py | _restore_page | `app/blueprints/edicao.py:505` | backend:_restore_page | Data e hora inválidas. | mensagem do backend | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:506` | backend:flash | Marque a confirmação para restaurar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:520` | backend:flash | Projeto restaurado para {…}: {…} {…} no histórico. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:538` | backend:flash | Marque a confirmação para desfazer a restauração. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/edicao.py | flash | `app/blueprints/edicao.py:549` | backend:flash | Restauração desfeita. Os lançamentos dela continuam no histórico. | confirmação ou aviso após ação | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:42` | backend:formulário | Nome da empresa | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:43` | backend:formulário | Seu nome | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:51` | backend:formulário | Repita a senha | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:51` | backend:formulário | As senhas não conferem. | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:78` | backend:erro | Linha {…}: use o formato “Nome; minutos”. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:81` | backend:erro | Linha {…}: nome da subatividade vazio ou longo demais. | mensagem de erro | antes: “Linha {…}: nome da atividade vazio ou longo demais.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms.py | erro | `app/forms.py:85` | backend:erro | Linha {…}: tempo ideal inválido. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:87` | backend:erro | Linha {…}: tempo ideal deve ficar entre 0 e 100000 minutos. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:90` | backend:erro | No máximo {…} subatividades por etapa. | mensagem de erro | antes: “No máximo {…} atividades por etapa.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms.py | erro | `app/forms.py:107` | backend:erro | Checklist, linha {…}: no máximo {…} caracteres. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:113` | backend:erro | No máximo {…} itens de checklist por etapa. | mensagem de erro | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:122` | backend:formulário | Subatividades (uma por linha: Nome; minutos por unidade) | rótulo ou validação de campo | antes: “Atividades (uma por linha: Nome; minutos por unidade)” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms.py | formulário | `app/forms.py:124` | backend:formulário | Checklist de inspeção (um item por linha) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:125` | backend:formulário | Exigir checklist assinado | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:133` | backend:erro | Dê um nome à etapa. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:135` | backend:erro | Inclua pelo menos uma subatividade. | mensagem de erro | antes: “Inclua pelo menos uma atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms.py | erro | `app/forms.py:138` | backend:erro | No modo simples, deixe em branco ou use uma linha só (o tempo da etapa). | mensagem de erro | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:143` | backend:formulário | Nome do projeto | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:146` | backend:formulário | Quantidade de equipamentos | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:150` | backend:formulário | Pessoas montando | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:152` | backend:formulário | Horas por dia (por pessoa) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:159` | backend:erro | O prazo não pode ser antes do início. | mensagem de erro | — | — | revisado — mantido |
| forms.py | erro | `app/forms.py:163` | backend:erro | Inclua pelo menos uma etapa. | mensagem de erro | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:179` | backend:formulário | Nova etapa | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:183` | backend:formulário | Nova subatividade | rótulo ou validação de campo | antes: “Nova atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms.py | formulário | `app/forms.py:185` | backend:formulário | Tempo ideal (min por unidade) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms.py | formulário | `app/forms.py:191` | backend:formulário | Peças prontas agora | rótulo ou validação de campo | antes: “Peças concluídas agora” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| forms_production.py | formulário | `app/forms_production.py:38` | backend:formulário | Modelo de etapas | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:40` | backend:formulário | Como lançar o progresso | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:78` | backend:formulário | Nome do projeto | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:80` | backend:formulário | Quantidade de equipamentos | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:83` | backend:formulário | Pessoas na equipe | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:85` | backend:formulário | Horas por dia | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | erro | `app/forms_production.py:90` | backend:erro | O prazo não pode ser antes do início. | mensagem de erro | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:102` | backend:formulário | Tempo ideal (min) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:117` | backend:formulário | Aguardando peça | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:118` | backend:formulário | Previsão de chegada | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:139` | backend:formulário | Marque a confirmação. | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:147` | backend:formulário | Data e hora | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:149` | backend:formulário | Marque a confirmação. | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:153` | backend:formulário | Nome do modelo | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | erro | `app/forms_production.py:159` | backend:erro | Inclua pelo menos uma etapa. | mensagem de erro | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:175` | backend:formulário | Arquivo (.csv ou .xlsx) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:176` | backend:formulário | Nome do projeto | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:178` | backend:formulário | Quero escolher as colunas | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:193` | backend:formulário | Linha do cabeçalho | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | _column_choice | `app/forms_production.py:196` | backend:_column_choice | Tempo ideal (min) | mensagem do backend | — | — | revisado — mantido |
| forms_production.py | _column_choice | `app/forms_production.py:197` | backend:_column_choice | Meta (previstas) | mensagem do backend | antes: “Previstas (meta)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| forms_production.py | _column_choice | `app/forms_production.py:198` | backend:_column_choice | Peças prontas | mensagem do backend | antes: “Concluídas (peças)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| forms_production.py | _column_choice | `app/forms_production.py:199` | backend:_column_choice | % concluído | mensagem do backend | — | — | revisado — mantido |
| forms_production.py | _column_choice | `app/forms_production.py:200` | backend:_column_choice | Prazo (data) | mensagem do backend | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:201` | backend:formulário | Meta (unidades previstas) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:205` | backend:formulário | Unidade do tempo | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:207` | backend:formulário | Nome do projeto | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_production.py | formulário | `app/forms_production.py:221` | backend:formulário | Nome do projeto | rótulo ou validação de campo | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:24` | backend:valor | Em andamento | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:25` | backend:valor | Aguardando peça | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:27` | backend:valor | Não iniciada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:48` | backend:_plural | dia útil | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:48` | backend:_plural | dias úteis | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:48` | backend:valor | {…} dias úteis | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:64` | backend:valor | sem prazo definido | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:64` | backend:valor | sem prazo definido | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:68` | backend:valor | o prazo ({…}) passou há {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:69` | backend:valor | vencido há {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:75` | backend:valor | termina {…}, atraso de {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:76` | backend:valor | atraso de {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:82` | backend:valor | termina {…}, folga de {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:83` | backend:valor | folga de {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:86` | backend:valor | prazo {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:86` | backend:valor | prazo {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:93` | backend:_plural | etapa atrasada | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:93` | backend:_plural | etapas atrasadas | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:95` | backend:_plural | etapa aguardando peça | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:95` | backend:_plural | etapas aguardando peça | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:102` | backend:valor | Nenhum projeto ativo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:105` | backend:_plural | projeto ativo | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:105` | backend:_plural | projetos ativos | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | append | `app/services/dashboard.py:108` | backend:append | {…} com atraso | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | append | `app/services/dashboard.py:110` | backend:append | {…} no prazo | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:114` | backend:_plural | etapa atrasada | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:114` | backend:_plural | etapas atrasadas | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:116` | backend:_plural | etapa aguardando peça | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | _plural | `app/services/dashboard.py:116` | backend:_plural | etapas aguardando peça | mensagem do backend | — | — | revisado — mantido |
| services/dashboard.py | valor | `app/services/dashboard.py:169` | backend:valor | peça prevista {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:118` | backend:erro | modo de progresso inválido: {…} | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:120` | backend:erro | No modo simples cada etapa tem só o %: no máximo uma subatividade por etapa. | mensagem de erro | antes: “No modo simples cada etapa tem só o %: no máximo uma atividade por etapa.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:216` | backend:erro | Informe pelo menos 1 peça. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:221` | backend:erro | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | mensagem de erro | antes: “Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:223` | backend:erro | Máximo {…} peça(s) nesta subatividade. | mensagem de erro | antes: “Máximo {…} peça(s) nesta atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:240` | backend:erro | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | mensagem de erro | antes: “Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:309` | backend:erro | Este lançamento já é um desfazer. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:312` | backend:erro | Este lançamento é de uma restauração: desfaça a restauração inteira. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:314` | backend:erro | Este registro já foi desfeito. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:330` | backend:erro | A subatividade mudou enquanto você desfazia. Confira e tente de novo. | mensagem de erro | antes: “A atividade mudou enquanto você desfazia. Confira e tente de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:411` | backend:erro | Pessoa não encontrada na equipe. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:477` | backend:erro | Já há {…} peças registradas numa subatividade: a quantidade não pode ser menor. | mensagem de erro | antes: “Já há {…} peças registradas numa atividade: a quantidade não pode ser menor.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:479` | backend:erro | O prazo não pode ser antes do início. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:484` | backend:erro | O projeto tem {…} números de série cadastrados: a quantidade não pode ser menor. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:508` | backend:erro | Informe o nome da {…} (até 160 caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | valor | `app/services/projects.py:539` | backend:valor | Outra pessoa alterou esta etapa enquanto você editava. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/projects.py | valor | `app/services/projects.py:540` | backend:valor | Esta subatividade mudou enquanto você editava. | valor exibido (rótulo, opção, situação) | antes: “Esta atividade mudou enquanto você editava.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:579` | backend:erro | A observação da peça tem no máximo {…} caracteres. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:581` | backend:erro | Previsão de chegada da peça inválida. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:635` | backend:erro | Tempo ideal inválido. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | OrderConflict | `app/services/projects.py:693` | backend:OrderConflict | A lista de etapas mudou desde que a tela foi aberta. Confira a ordem atual e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:732` | backend:erro | Etapa de destino inválida. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:791` | backend:erro | Esta etapa não está excluída. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:808` | backend:erro | Esta subatividade não está excluída. | mensagem de erro | antes: “Esta atividade não está excluída.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:811` | backend:erro | A etapa desta subatividade também foi excluída: desfaça a exclusão da etapa primeiro. | mensagem de erro | antes: “A etapa desta atividade também foi excluída: desfaça a exclusão da etapa primeiro.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:813` | backend:erro | No modo simples a etapa tem só o %: não dá para trazer uma segunda subatividade. | mensagem de erro | antes: “No modo simples a etapa tem só o %: não dá para trazer uma segunda atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:841` | backend:erro | Use um número inteiro de peças, de 0 a {…}. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:844` | backend:erro | As peças prontas não podem passar das previstas ({…}). | mensagem de erro | antes: “As peças concluídas não podem passar das previstas ({…}).” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:863` | backend:erro | Tempo ideal inválido: use minutos de 0 a 100000, com até 2 casas (ex.: 7,5). | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:871` | backend:erro | Use um % de 0 a 100, inteiro ou com 1 casa (ex.: 45 ou 45,5). | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:889` | backend:erro | As peças prontas vão de 0 a {…}. | mensagem de erro | antes: “As peças concluídas vão de 0 a {…}.” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:891` | backend:erro | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | mensagem de erro | antes: “Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:898` | backend:erro | Para diminuir as peças, peça a um supervisor ou desfaça o lançamento no histórico. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:912` | backend:erro | Esta subatividade foi atualizada por outra pessoa. Confira os números e tente de novo. | mensagem de erro | antes: “Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/projects.py | erro | `app/services/projects.py:945` | backend:erro | Este projeto está no modo detalhado: lance as peças de cada subatividade. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:959` | backend:erro | Modo de progresso inválido. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | erro | `app/services/projects.py:968` | backend:erro | Para usar o modo simples, cada etapa pode ter no máximo uma subatividade. Têm mais de uma: {…}. Exclua ou junte as subatividades e tente de novo. | mensagem de erro | — | — | revisado — mantido |
| services/projects.py | create_project | `app/services/projects.py:1012` | backend:create_project | Cópia de {…} | mensagem do backend | — | — | revisado — mantido |
| app/_painel | texto | `app/templates/app/_painel.html:12` | template:texto | Atualizado às | texto na tela | — | — | revisado — mantido |
| app/_painel | texto | `app/templates/app/_painel.html:18` | template:texto | Preencher etapas | texto na tela | — | — | revisado — mantido |
| app/_painel | aria-label | `app/templates/app/_painel.html:27` | template:aria-label | Indicadores | nome para leitor de tela | — | — | revisado — mantido |
| app/_painel | texto | `app/templates/app/_painel.html:31` | template:texto | Progresso pelas tarefas | texto na tela | antes: “Progresso geral (pelas tarefas)” — mesmo nome do indicador em todas as telas | aplicado (texto atual) | alterado |
| app/_painel | macro | `app/templates/app/_painel.html:53` | template:macro | Concluída | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:53` | template:macro | Em andamento | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:53` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:53` | template:macro | Atrasada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:53` | template:macro | Não iniciada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | texto | `app/templates/app/_painel.html:57` | template:texto | Hoje (pelo prazo) | texto na tela | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:83` | template:macro | Atrasadas e aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:83` | template:macro | Etapas atrasadas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | texto | `app/templates/app/_painel.html:94` | template:texto | e mais {…} | texto na tela | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:96` | template:macro | Nenhuma etapa atrasada ou aguardando peça. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_painel | macro | `app/templates/app/_painel.html:96` | template:macro | Nenhuma etapa atrasada. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:4` | template:texto | Escolha um modelo de etapas para ver o tempo total, os dias úteis e o término previsto. Sem modelo, os números aparecem depois de criar. | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:6` | template:texto | Informe quantidade, equipe e horas por dia válidas para calcular o resumo. | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:9` | template:texto | Trabalho total | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:11` | template:texto | Dias úteis | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:11` | template:texto | informe a equipe | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:13` | template:texto | Dias úteis | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:14` | template:texto | Término previsto | texto na tela | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:18` | template:texto | {…} Cabe no prazo · folga de {…} {…} | texto na tela | — | — | revisado — mantido |
| app/_project_summary | macro | `app/templates/app/_project_summary.html:18` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_project_summary | macro | `app/templates/app/_project_summary.html:18` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:20` | template:texto | {…} Passa do prazo em {…} {…} | texto na tela | — | — | revisado — mantido |
| app/_project_summary | macro | `app/templates/app/_project_summary.html:20` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_project_summary | macro | `app/templates/app/_project_summary.html:20` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/_project_summary | texto | `app/templates/app/_project_summary.html:22` | template:texto | Informe o prazo para ver se cabe. | texto na tela | — | — | revisado — mantido |
| app/alerts | texto | `app/templates/app/alerts.html:7` | template:texto | Alertas · Teroz | texto na tela | antes: “Alertas · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/alerts | texto | `app/templates/app/alerts.html:12` | template:texto | Alertas{…} | texto na tela | — | — | revisado — mantido |
| app/alerts | texto | `app/templates/app/alerts.html:13` | template:texto | Últimos {…} dias · prazo em risco, atraso previsto , etapa parada há {…} dias úteis ou mais e peça atrasada e etapa parada há {…} dias úteis ou mais . | texto na tela | — | — | revisado — mantido |
| app/alerts | macro | `app/templates/app/alerts.html:18` | template:macro | Dia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/alerts | macro | `app/templates/app/alerts.html:18` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/alerts | data-label | `app/templates/app/alerts.html:22` | template:data-label | Dia | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/alerts | data-label | `app/templates/app/alerts.html:23` | template:data-label | Projeto | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/alerts | data-label | `app/templates/app/alerts.html:24` | template:data-label | Alerta | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/alerts | data-label | `app/templates/app/alerts.html:25` | template:data-label | Detalhe | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/alerts | macro | `app/templates/app/alerts.html:32` | template:macro | Nenhum alerta | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/alerts | macro | `app/templates/app/alerts.html:32` | template:macro | Quando um prazo entrar em risco, uma etapa ficar parada ou uma peça atrasar, o alerta aparece aqui e por e-mail. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/alerts | texto | `app/templates/app/alerts.html:35` | template:texto | Os alertas são conferidos várias vezes ao dia. O e-mail de cada situação se repete no máximo uma vez por semana; desligue em | texto na tela | — | — | revisado — mantido |
| app/alerts | texto | `app/templates/app/alerts.html:35` | template:texto | Perfil › Notificações | texto na tela | — | — | revisado — mantido |
| app/alerts | texto | `app/templates/app/alerts.html:35` | template:texto | Empresa | texto na tela | — | — | revisado — mantido |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:10` | template:texto | API · Teroz | texto na tela | antes: “API · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:15` | template:texto | API{…} | texto na tela | — | — | revisado — mantido |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:16` | template:texto | Tokens para integrar outros sistemas. Contrato em docs/api/openapi.yaml. | texto na tela | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:22` | template:macro | Token criado — copie agora | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:23` | template:texto | Ele não será mostrado de novo. Guarde em local seguro. | texto na tela | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:32` | template:macro | API indisponível no plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:32` | template:macro | A API faz parte do plano Empresa. Mude de plano para criar tokens. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:37` | template:texto | Novo token | texto na tela | — | — | revisado — mantido |
| app/api_tokens | texto | `app/templates/app/api_tokens.html:42` | template:texto | Permissões | texto na tela | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:48` | template:macro | Criar token | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:54` | template:macro | Integração | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:54` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | data-label | `app/templates/app/api_tokens.html:59` | template:data-label | Prefixo | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/api_tokens | data-label | `app/templates/app/api_tokens.html:60` | template:data-label | Permissões | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/api_tokens | data-label | `app/templates/app/api_tokens.html:61` | template:data-label | Validade | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:61` | template:macro | Sem expiração | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | data-label | `app/templates/app/api_tokens.html:62` | template:data-label | Último uso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:62` | template:macro | Nunca | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | data-label | `app/templates/app/api_tokens.html:63` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:63` | template:macro | Ativo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:63` | template:macro | Revogado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:63` | template:macro | Expirado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:68` | template:macro | Revogar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:78` | template:macro | Nenhum token ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/api_tokens | macro | `app/templates/app/api_tokens.html:78` | template:macro | Crie um token acima para integrar outro sistema. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:9` | template:texto | Assinatura · Teroz | texto na tela | antes: “Assinatura · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/assinatura | texto | `app/templates/app/assinatura.html:14` | template:texto | Assinatura | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:15` | template:texto | Plano {…} · sob orçamento R$ {…}/mês ({…}% de desconto) | texto na tela | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:20` | template:macro | Fale conosco | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:22` | template:macro | Trocar plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:22` | template:macro | Escolher plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:25` | template:macro | Dados de cobrança | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:40` | template:texto | ("Fatura vencida em " if open_payment.status == "overdue" else "Próxima fatura vence em ") ~ (open_payment.due_date\|data), | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:41` | template:texto | "R$ " ~ (open_payment.value_cents\|reais) ~ " — pague por Pix, boleto ou cartão na página segura do Asaas.", | texto na tela | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:46` | template:macro | Projetos ativos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:46` | template:macro | no plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:46` | template:macro | ilimitado no plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:47` | template:macro | Usuários | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:47` | template:macro | (com convites) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:51` | template:texto | Situação | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:53` | template:texto | Situação da assinatura | texto na tela | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| app/assinatura | texto | `app/templates/app/assinatura.html:55` | template:texto | Teste grátis até | texto na tela | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:58` | template:macro | Acesso completo até | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:58` | template:macro | Período pago até | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:61` | template:texto | Carência até | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:64` | template:texto | Cancelada em | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:68` | template:texto | Sua conta está em modo leitura: dá para ver e exportar tudo, nada foi apagado. Escolha um plano para voltar a registrar. | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:74` | template:texto | Faturas recentes | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:75` | template:texto | Ver todas | texto na tela | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:78` | template:macro | Vencimento | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:78` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | data-label | `app/templates/app/assinatura.html:83` | template:data-label | Valor | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/assinatura | data-label | `app/templates/app/assinatura.html:84` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| app/assinatura | texto | `app/templates/app/assinatura.html:90` | template:texto | Nenhuma fatura ainda. O teste grátis não pede cartão. | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:96` | template:texto | Cancelar assinatura | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:97` | template:texto | O cancelamento vale no fim do período já pago (ou do teste grátis) . Depois disso a conta fica em modo leitura e nenhum dado é apagado. | texto na tela | — | — | revisado — mantido |
| app/assinatura | macro | `app/templates/app/assinatura.html:98` | template:macro | Cancelar assinatura | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:101` | template:texto | "Novas cobranças deixam de ser geradas. Você mantém acesso completo até o fim do período pago; depois, modo leitura.", | texto na tela | — | — | revisado — mantido |
| app/assinatura | texto | `app/templates/app/assinatura.html:102` | template:texto | "Cancelar assinatura", url_for('billing.cancel'), cancel_label="Manter assinatura") }} | texto na tela | — | — | revisado — mantido |
| app/assinatura_cobranca | texto | `app/templates/app/assinatura_cobranca.html:7` | template:texto | Dados de cobrança · Assinatura | texto na tela | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:12` | template:macro | Planos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:12` | template:macro | Assinatura | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | texto | `app/templates/app/assinatura_cobranca.html:13` | template:texto | Dados de cobrança | texto na tela | — | — | revisado — mantido |
| app/assinatura_cobranca | texto | `app/templates/app/assinatura_cobranca.html:15` | template:texto | Plano {…} · R$ {…}/mês (com {…}% de desconto) · sem teste grátis | texto na tela | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:22` | template:macro | Não foi possível concluir | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:29` | template:macro | Só números ou com pontuação. Vai para a nota fiscal e para o Asaas. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:30` | template:macro | Recebe as faturas e os avisos de cobrança. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | texto | `app/templates/app/assinatura_cobranca.html:32` | template:texto | Ao continuar você vai para a página segura do Asaas para pagar por Pix, boleto ou cartão. A primeira fatura vence no fim do teste grátis; pagar antes não encurta o teste. O {…} não tem teste grátis: a primeira fatura … | texto na tela | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:35` | template:macro | Continuar para o pagamento | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:35` | template:macro | Salvar dados | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_cobranca | macro | `app/templates/app/assinatura_cobranca.html:36` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faixa | macro | `app/templates/app/assinatura_faixa.html:6` | template:macro | Fale com o proprietário da conta. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faturas | texto | `app/templates/app/assinatura_faturas.html:7` | template:texto | Faturas · Assinatura · Teroz | texto na tela | antes: “Faturas · Assinatura · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/assinatura_faturas | texto | `app/templates/app/assinatura_faturas.html:13` | template:texto | Faturas | texto na tela | — | — | revisado — mantido |
| app/assinatura_faturas | macro | `app/templates/app/assinatura_faturas.html:18` | template:macro | Vencimento | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faturas | macro | `app/templates/app/assinatura_faturas.html:18` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faturas | data-label | `app/templates/app/assinatura_faturas.html:23` | template:data-label | Valor | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/assinatura_faturas | data-label | `app/templates/app/assinatura_faturas.html:24` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| app/assinatura_faturas | data-label | `app/templates/app/assinatura_faturas.html:25` | template:data-label | Pago em | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/assinatura_faturas | data-label | `app/templates/app/assinatura_faturas.html:26` | template:data-label | Pagamento | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/assinatura_faturas | texto | `app/templates/app/assinatura_faturas.html:28` | template:texto | Pagar | texto na tela | — | — | revisado — mantido |
| app/assinatura_faturas | texto | `app/templates/app/assinatura_faturas.html:30` | template:texto | Ver fatura | texto na tela | — | — | revisado — mantido |
| app/assinatura_faturas | macro | `app/templates/app/assinatura_faturas.html:39` | template:macro | Nenhuma fatura ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faturas | macro | `app/templates/app/assinatura_faturas.html:39` | template:macro | As faturas aparecem aqui quando você assina um plano. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_faturas | macro | `app/templates/app/assinatura_faturas.html:39` | template:macro | Escolher plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:7` | template:texto | Planos · Assinatura · Teroz | texto na tela | antes: “Planos · Assinatura · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:13` | template:macro | Escolher plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:13` | template:macro | Trocar plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:14` | template:texto | Mensal, sem fidelidade. Pix, boleto ou cartão na página segura do Asaas. | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:19` | template:macro | Plano gerido pela nossa equipe | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:19` | template:macro | Seu plano é sob orçamento: para mudar ou cancelar, fale conosco. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:19` | template:macro | Fale conosco | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:27` | template:macro | Seu plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:30` | template:texto | Sob orçamento | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:30` | template:texto | online ou presencial | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:35` | template:texto | {…} projetos ativos | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:35` | template:macro | Ilimitados | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:36` | template:macro | Até | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:36` | template:macro | Pessoas ilimitadas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:37` | template:texto | Verificação em duas etapas obrigatória | texto na tela | antes: “MFA obrigatório” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:38` | template:texto | API de integração | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:39` | template:texto | Identidade visual personalizada | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:41` | template:texto | Sob orçamento, online ou presencial — fale conosco | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | texto | `app/templates/app/assinatura_planos.html:42` | template:texto | Sem teste grátis: cobrança ao contratar | texto na tela | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:46` | template:macro | Plano atual | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:48` | template:macro | Fale conosco | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:51` | template:macro | Fale conosco | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:53` | template:macro | Plano atual | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:55` | template:macro | Assinar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_planos | macro | `app/templates/app/assinatura_planos.html:55` | template:macro | Mudar para | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:7` | template:texto | Trocar para {…} · Assinatura | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:13` | template:texto | Trocar para {…} | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:18` | template:macro | Troca de plano indisponível | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:18` | template:macro | Ver faturas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:21` | template:macro | Não foi possível trocar o plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:26` | template:texto | Projeção | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:28` | template:texto | Hoje ({…}) | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:28` | template:texto | Sob orçamento R$ {…}/mês | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:29` | template:texto | Novo ({…}) | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:29` | template:texto | Sob orçamento R$ {…}/mês | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:31` | template:texto | Diferença por mês | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:31` | template:texto | 0 else ("−" if p.difference_cents | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:31` | template:macro | if p.difference_cents > 0 else ( | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:31` | template:macro | if p.difference_cents < 0 else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:34` | template:texto | Próxima fatura | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:36` | template:texto | Projetos ativos | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:36` | template:texto | {…} de {…} | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:37` | template:texto | Pessoas | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:37` | template:texto | {…} de {…} | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:41` | template:texto | Vale após o pagamento: a fatura em aberto passa a R$ {…} e os limites do {…} valem assim que ela for paga (dá para pagar antes do vencimento). | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:43` | template:texto | Vale a partir de {…}: até lá você continua com os limites do {…}, que já estão pagos. | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | texto | `app/templates/app/assinatura_troca.html:45` | template:texto | Sem cobrança proporcional. Seu desconto de {…}% continua valendo. | texto na tela | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:47` | template:macro | Confirmar troca | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/assinatura_troca | macro | `app/templates/app/assinatura_troca.html:48` | template:macro | Voltar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:12` | template:texto | Resp.: {…} | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:14` | template:texto | Último: {…} {…} · | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:27` | template:texto | Registrar peças em {…} | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | macro | `app/templates/app/detail/_activity.html:33` | template:macro | Concluída | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:38` | template:texto | {…} min | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | macro | `app/templates/app/detail/_activity.html:40` | template:macro | Progresso de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:45` | template:texto | url_for('app.activity_progress', activity_id=activity.id), activity.version, | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:46` | template:texto | detail_url ~ "#atividade-" ~ activity.id, error=err, open=err is not none, | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | texto | `app/templates/app/detail/_activity.html:47` | template:texto | delta=deltas.get(activity.id, 1), conflict=in_conflict) }} | texto na tela | — | — | revisado — mantido |
| app/detail/_activity | macro | `app/templates/app/detail/_activity.html:49` | template:macro | Concluída | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:5` | template:macro | Progresso por etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:5` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:5` | template:macro | Progresso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:8` | template:macro | Horas que faltam por etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:8` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_charts | macro | `app/templates/app/detail/_charts.html:8` | template:macro | Faltam | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | aria-label | `app/templates/app/detail/_kpis.html:4` | template:aria-label | Indicadores | nome para leitor de tela | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:5` | template:macro | Unidades | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:5` | template:macro | ~ project.quantity, sub= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:6` | template:macro | Progresso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:6` | template:macro | Progresso pelas tarefas | rótulo, botão ou ajuda de componente | antes: “Progresso geral” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:7` | template:macro | Faltam | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:9` | template:macro | Dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:9` | template:macro | informe a equipe | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:11` | template:macro | Dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:11` | template:macro | término | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:11` | template:macro | · atraso de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:11` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:11` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:13` | template:macro | Dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:13` | template:macro | término | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:13` | template:macro | · folga de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:13` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:13` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:15` | template:macro | Dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_kpis | macro | `app/templates/app/detail/_kpis.html:15` | template:macro | término previsto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:6` | template:texto | Equipe e prazo | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:8` | template:texto | Equipe | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:8` | template:texto | {…} {…} × {…} h/dia | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:9` | template:texto | Dias de trabalho | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:10` | template:texto | Início | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:11` | template:texto | Prazo | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:11` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:11` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:12` | template:texto | Término previsto | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:14` | template:texto | Atraso previsto | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:14` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:14` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:16` | template:texto | Folga | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:16` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:16` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:18` | template:texto | Tempo total | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:23` | template:texto | Pessoas · 7 dias | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | macro | `app/templates/app/detail/_lateral.html:29` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:30` | template:texto | · {…} padrão · {…}/{…} atribuída{…} | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:35` | template:texto | Ninguém lançou peças nos últimos 7 dias. | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:37` | template:texto | Ver progresso por pessoa | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:41` | template:texto | Recente | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:52` | template:texto | Toque em + para registrar a primeira peça. | texto na tela | — | — | revisado — mantido |
| app/detail/_lateral | texto | `app/templates/app/detail/_lateral.html:54` | template:texto | Ver histórico do projeto | texto na tela | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:6` | template:macro | Atraso previsto · | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:6` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:6` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | texto | `app/templates/app/detail/_meta.html:7` | template:texto | {…} no prazo · folga de {…} {…} | texto na tela | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:7` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:7` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:8` | template:macro | Prazo passou há | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:8` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_meta | macro | `app/templates/app/detail/_meta.html:8` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_stage_summary | macro | `app/templates/app/detail/_stage_summary.html:8` | template:macro | Checklist pendente | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_stage_summary | macro | `app/templates/app/detail/_stage_summary.html:8` | template:macro | Checklist assinado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_stage_summary | macro | `app/templates/app/detail/_stage_summary.html:9` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_stage_summary | macro | `app/templates/app/detail/_stage_summary.html:9` | template:macro | · prev. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/detail/_stage_summary | macro | `app/templates/app/detail/_stage_summary.html:11` | template:macro | Progresso de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:13` | template:texto | Histórico · {…} · Teroz | texto na tela | antes: “Histórico · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/history | texto | `app/templates/app/history.html:23` | template:texto | Histórico | texto na tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:24` | template:texto | {…} · {…} {…} com os filtros atuais | texto na tela | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:30` | template:macro | Restaurar para uma data | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | aria-label | `app/templates/app/history.html:36` | template:aria-label | Filtrar histórico | nome para leitor de tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:41` | template:texto | Projeto | texto na tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:43` | template:texto | Todos os projetos | texto na tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:49` | template:texto | Subatividade | texto na tela | antes: “Atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/history | texto | `app/templates/app/history.html:51` | template:texto | Todas as subatividades | texto na tela | antes: “Todas as atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/history | texto | `app/templates/app/history.html:57` | template:texto | Pessoa | texto na tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:59` | template:texto | Todas as pessoas | texto na tela | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:63` | template:macro | Filtrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:64` | template:macro | Limpar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:72` | template:macro | Peças por dia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:72` | template:macro | Dia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:72` | template:macro | Peças | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:76` | template:macro | Quando | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:76` | template:macro | Pessoa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:76` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:76` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:87` | template:texto | {…} → {…} de {…} | texto na tela | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:89` | template:macro | desfaz restauração | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:89` | template:macro | restauração | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:91` | template:texto | por {…} | texto na tela | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:92` | template:texto | Desfazer | texto na tela | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:104` | template:macro | Nenhum registro com estes filtros | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:104` | template:macro | Tente outra subatividade ou pessoa, ou limpe os filtros. | rótulo, botão ou ajuda de componente | antes: “Tente outra atividade ou pessoa, ou limpe os filtros.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/history | macro | `app/templates/app/history.html:104` | template:macro | Limpar filtros | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:106` | template:macro | Nenhum registro ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:106` | template:macro | Os registros aparecem quando alguém soma peças. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:106` | template:macro | Ir para o projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:108` | template:macro | Nenhum registro ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:108` | template:macro | Os registros aparecem quando alguém soma peças em qualquer projeto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | macro | `app/templates/app/history.html:108` | template:macro | Ir para Projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/history | texto | `app/templates/app/history.html:116` | template:texto | Alterações do projeto | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:8` | template:texto | Painel da operação · Teroz | texto na tela | antes: “Painel da operação · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/painel | macro | `app/templates/app/painel.html:17` | template:macro | Nenhum projeto ativo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:17` | template:macro | Crie um projeto com as etapas da produção para ver o painel aqui. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:17` | template:macro | Novo projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:19` | template:macro | Nenhum projeto ativo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:19` | template:macro | Quando houver um projeto em andamento, o painel aparece aqui. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:19` | template:macro | Ver projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | aria-label | `app/templates/app/painel.html:25` | template:aria-label | Resumo da operação | nome para leitor de tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:27` | template:texto | Progresso pelas tarefas | texto na tela | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:29` | template:macro | Progresso pelas tarefas, somando os projetos ativos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:30` | template:texto | {…}&nbsp;h trabalhadas de {…}&nbsp;h previstas | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:33` | template:texto | Unidades prontas | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:34` | template:texto | de {…} | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:35` | template:texto | unidades com todas as etapas prontas | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:38` | template:texto | Horas que faltam | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:40` | template:texto | trabalho estimado em {…} {…} | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:43` | template:texto | Próximo prazo | texto na tela | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:45` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:45` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:49` | template:texto | nenhum projeto com prazo definido | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:55` | template:texto | Precisa de atenção | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:66` | template:texto | e mais {…} | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:68` | template:texto | Nada precisa de atenção agora: nenhuma etapa atrasada{…}. | texto na tela | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:68` | template:macro | ou aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:71` | template:macro | concluídas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:71` | template:macro | em andamento | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:71` | template:macro | aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:71` | template:macro | não iniciadas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:79` | template:texto | Projetos ativos | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:80` | template:texto | Lista completa | texto na tela | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:82` | template:texto | Clique num projeto para abrir o painel dele. Mostrando {…} de {…} projetos ativos. | texto na tela | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:83` | template:macro | Projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:83` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:83` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:87` | template:data-label | Projeto | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:88` | template:data-label | Progresso pelas tarefas | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/painel | macro | `app/templates/app/painel.html:88` | template:macro | Progresso pelas tarefas de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:89` | template:texto | de {…} | texto na tela | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:89` | template:data-label | Unidades prontas | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/painel | texto | `app/templates/app/painel.html:90` | template:texto | de {…} | texto na tela | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:90` | template:data-label | Etapas concluídas | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:91` | template:data-label | Horas que faltam (h) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/painel | data-label | `app/templates/app/painel.html:92` | template:data-label | Prazo | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | texto | `app/templates/app/people.html:10` | template:texto | Pessoas · {…} · Teroz | texto na tela | antes: “Pessoas · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/people | texto | `app/templates/app/people.html:16` | template:texto | Progresso por pessoa{…} | texto na tela | — | — | revisado — mantido |
| app/people | texto | `app/templates/app/people.html:17` | template:texto | Peças lançadas no período (desfazeres descontados) e subatividades sob responsabilidade de cada pessoa. | texto na tela | antes: “Peças lançadas no período (desfazeres descontados) e atividades sob responsabilidade de cada pessoa.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/people | aria-label | `app/templates/app/people.html:21` | template:aria-label | Período | nome para leitor de tela | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:29` | template:macro | Peças por pessoa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:29` | template:macro | Pessoa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:29` | template:macro | Peças | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:31` | template:macro | Pessoa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:31` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:31` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:36` | template:data-label | Pessoa | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:36` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | texto | `app/templates/app/people.html:37` | template:texto | ({…} desfeito{…}) | texto na tela | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:37` | template:data-label | Peças | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:38` | template:data-label | Registros | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:39` | template:data-label | Horas-padrão | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:40` | template:data-label | Dias | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:41` | template:data-label | Atribuídas | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | texto | `app/templates/app/people.html:43` | template:texto | {…} de {…} concluída{…} · {…}/{…} peças | texto na tela | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:44` | template:macro | Progresso das subatividades de | rótulo, botão ou ajuda de componente | antes: “Progresso das atividades de” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/people | macro | `app/templates/app/people.html:44` | template:macro | pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | data-label | `app/templates/app/people.html:47` | template:data-label | Onde | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/people | texto | `app/templates/app/people.html:49` | template:texto | e mais {…} | texto na tela | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:57` | template:macro | Nada neste período | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/people | macro | `app/templates/app/people.html:57` | template:macro | Ninguém lançou peças neste projeto no período e nenhuma subatividade tem responsável. | rótulo, botão ou ajuda de componente | antes: “Ninguém lançou peças neste projeto no período e nenhuma atividade tem responsável.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/people | macro | `app/templates/app/people.html:57` | template:macro | Ver tudo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:11` | template:texto | Painel · {…} · Teroz | texto na tela | antes: “Painel · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:31` | template:macro | Nenhuma etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:31` | template:macro | Inclua a primeira etapa no projeto para ver o painel. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:31` | template:macro | Abrir o projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:36` | template:macro | nada pendente | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:38` | template:macro | informe a equipe para ver os dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:40` | template:macro | dias úteis · | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:43` | template:texto | ("Unidades prontas", r.unidades_concluidas, "/ " ~ project.quantity, "a etapa mais atrasada define o número", None), | texto na tela | antes: “("Unidades prontas", r.unidades_concluidas, "/ " ~ project.quantity, "menor nº de unidades concluídas entre as etapas", None),” — explica a regra em linguagem simples | aplicado (texto atual) | alterado |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:44` | template:texto | ("Etapas concluídas", r.etapas_concluidas, "/ " ~ (d.etapas\|length), "subatividades em 100%: " ~ r.tarefas_concluidas ~ " de " ~ r.tarefas, None), | texto na tela | antes: “("Etapas concluídas", r.etapas_concluidas, "/ " ~ (d.etapas\|length), "tarefas concluídas: " ~ r.tarefas_concluidas ~ " de " ~ r.tarefas, None),” — glossário | aplicado (texto atual) | alterado |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:45` | template:texto | ("Horas que faltam", r.tempo_restante_h\|num(1), "h", falta_sub, None), | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:46` | template:texto | ("Dias úteis até o prazo", d.prazo.until, ("dia útil" if d.prazo.until == 1 else "dias úteis") if d.prazo.until is not none else None, d.prazo.short, d.prazo.tone, d.prazo.text), | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:50` | template:texto | {…} {…}: {…} no progresso até ter tempo. | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:50` | template:macro | etapa ainda sem tempo ideal | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:50` | template:macro | etapas ainda sem tempo ideal | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:50` | template:macro | ela não pesa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:50` | template:macro | elas não pesam | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:54` | template:macro | Tarefas × unidades por etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:54` | template:macro | Barras por etapa: progresso pelas tarefas e unidades prontas. Valores na tabela de dados. | rótulo, botão ou ajuda de componente | antes: “Barras por etapa: progresso pelas tarefas e unidades concluídas. Valores na tabela de dados.” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:54` | template:macro | Pelas tarefas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:54` | template:macro | Unidades prontas | rótulo, botão ou ajuda de componente | antes: “Unidades concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:55` | template:texto | Azul: progresso pelas tarefas (conta as parciais). Laranja: unidades prontas ÷ meta. Clique numa barra para preencher a etapa. | texto na tela | antes: “Azul: progresso pelas tarefas (conta as parciais). Laranja: unidades 100% prontas ÷ previstas. Clique numa barra para preencher a etapa.” — glossário | aplicado (texto atual) | alterado |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:57` | template:texto | Ver dados em tabela | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:59` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:59` | template:texto | Pelas tarefas | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:59` | template:texto | Unidades | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:67` | template:texto | Situação das etapas | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | aria-label | `app/templates/app/project_dashboard.html:69` | template:aria-label | Rosca: {% for s in d.grafico.status %}{…} {…}{…}{% endfor %}. | nome para leitor de tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:75` | template:macro | Quanto cada etapa representa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:75` | template:macro | Mapa de blocos: o tamanho de cada bloco é o peso da etapa no projeto e a cor mostra o progresso. Valores na tabela de dados. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:76` | template:texto | Tamanho: tempo total da etapa. Cor: progresso pelas tarefas (mais escuro, mais pronto). | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:78` | template:texto | Ver dados em tabela | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:80` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:80` | template:texto | Peso | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:80` | template:texto | Progresso | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:88` | template:macro | Horas por etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:88` | template:macro | Colunas empilhadas por etapa: horas trabalhadas e horas que faltam. Total trabalhado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:88` | template:macro | h; faltam | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:88` | template:macro | Trabalhadas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:88` | template:macro | Faltam | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:89` | template:texto | Tempo total da etapa dividido em horas já trabalhadas e horas que faltam. O número embaixo é a etapa; passe o mouse para ver o nome. | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:91` | template:texto | Ver dados em tabela | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:93` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:93` | template:texto | Trabalhadas | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:93` | template:texto | Faltam | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | Equipe × prazo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | Dias úteis que faltam para equipes de 1 a 6 pessoas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | , com o prazo em | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | , legend=[( | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:99` | template:macro | )], class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:101` | template:texto | Hoje: {…} · {…} dias úteis · prazo em {…} {…} | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:101` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:101` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:104` | template:texto | Ver dados em tabela | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:106` | template:texto | Pessoas | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:106` | template:texto | Horas por dia (equipe) | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:106` | template:texto | Dias úteis | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:114` | template:macro | Tabela 1 · Progresso por etapa pelas tarefas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:114` | template:macro | Tabela 2 · Unidades prontas por etapa | rótulo, botão ou ajuda de componente | antes: “Tabela 2 · Unidades concluídas por etapa” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | aria-label | `app/templates/app/project_dashboard.html:115` | template:aria-label | Tabela de etapas | nome para leitor de tela | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:121` | template:texto | {…} Clique numa linha para preencher a etapa. | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:121` | template:macro | Peças prontas de cada subatividade sobre a meta. | rótulo, botão ou ajuda de componente | antes: “Peças concluídas de cada atividade sobre as previstas.” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:121` | template:macro | Unidades prontas ÷ meta, sem contar as parciais. | rótulo, botão ou ajuda de componente | antes: “Feitas ÷ previstas, sem contar parciais.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:123` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:123` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:123` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:127` | template:data-label | Etapa | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:127` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:127` | template:macro | · prev. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:128` | template:data-label | Tempo por unidade (min) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:129` | template:data-label | Peso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:130` | template:data-label | Meta | rótulo da coluna no modo cartão (celular) | antes: “Previstas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:131` | template:data-label | Progresso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:131` | template:macro | Progresso de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:132` | template:data-label | Tempo total (h) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:133` | template:data-label | Tempo que falta (h) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:139` | template:texto | Total | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:139` | template:data-label | Etapa | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:140` | template:data-label | Tempo por unidade (min) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:141` | template:data-label | Peso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:142` | template:data-label | Meta | rótulo da coluna no modo cartão (celular) | antes: “Previstas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:143` | template:data-label | Progresso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:144` | template:data-label | Tempo total (h) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:145` | template:data-label | Tempo que falta (h) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:150` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:150` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:150` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:154` | template:data-label | Etapa | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:155` | template:data-label | Prontas | rótulo da coluna no modo cartão (celular) | antes: “Feitas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:156` | template:data-label | Meta | rótulo da coluna no modo cartão (celular) | antes: “Previstas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:157` | template:data-label | % pronta | rótulo da coluna no modo cartão (celular) | antes: “% concluída” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | macro | `app/templates/app/project_dashboard.html:157` | template:macro | Unidades prontas de | rótulo, botão ou ajuda de componente | antes: “Unidades concluídas de” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:158` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | texto | `app/templates/app/project_dashboard.html:164` | template:texto | Total | texto na tela | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:164` | template:data-label | Etapa | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:165` | template:data-label | Prontas | rótulo da coluna no modo cartão (celular) | antes: “Feitas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:166` | template:data-label | Meta | rótulo da coluna no modo cartão (celular) | antes: “Previstas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:167` | template:data-label | % pronta | rótulo da coluna no modo cartão (celular) | antes: “% concluída” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| app/project_dashboard | data-label | `app/templates/app/project_dashboard.html:168` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:24` | template:macro | Painel | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:25` | template:macro | Histórico | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:27` | template:texto | Unidades | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:32` | template:texto | Ações | texto na tela | — | — | revisado — mantido |
| app/project_detail | aria-label | `app/templates/app/project_detail.html:32` | template:aria-label | Mais ações do projeto | nome para leitor de tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:34` | template:texto | Editar projeto | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:35` | template:texto | Comparar com o modelo | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:36` | template:texto | Arquivar projeto | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:47` | template:texto | Etapas | texto na tela | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:50` | template:macro | Nenhuma etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:50` | template:macro | Inclua a primeira etapa para começar a registrar peças. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:54` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:54` | template:texto | Unid. | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:54` | template:texto | Progresso | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:54` | template:texto | Faltam | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:54` | template:texto | Situação | texto na tela | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| app/project_detail | macro | `app/templates/app/project_detail.html:64` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:64` | template:macro | · previsão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:64` | template:macro | ), stage.part_note or | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:68` | template:macro | Atualizar aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:68` | template:macro | Marcar aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:72` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:72` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:74` | template:texto | Previsão de chegada | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:78` | template:texto | Observação (opcional) | texto na tela | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:81` | template:macro | Salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:87` | template:texto | Fotos e comentários | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:98` | template:texto | Checklist de inspeção ({…} itens) | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:105` | template:texto | Nenhuma subatividade nesta etapa. | texto na tela | antes: “Nenhuma atividade nesta etapa.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/project_detail | texto | `app/templates/app/project_detail.html:112` | template:texto | Nova subatividade | texto na tela | antes: “Nova atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/project_detail | texto | `app/templates/app/project_detail.html:116` | template:texto | Tempo ideal (min) | texto na tela | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:119` | template:macro | Incluir subatividade | rótulo, botão ou ajuda de componente | antes: “Incluir atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/project_detail | texto | `app/templates/app/project_detail.html:129` | template:texto | Ver gráficos por etapa | texto na tela | — | — | revisado — mantido |
| app/project_detail | texto | `app/templates/app/project_detail.html:140` | template:texto | Incluir etapa | texto na tela | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:143` | template:macro | Incluir etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | aria-label | `app/templates/app/project_detail.html:148` | template:aria-label | Equipe, prazo e registros recentes | nome para leitor de tela | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:155` | template:macro | Arquivar o projeto? | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:155` | template:macro | Ele sai da lista de projetos e libera o limite do plano. O histórico continua guardado e dá para exportar. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_detail | macro | `app/templates/app/project_detail.html:155` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:8` | template:texto | Novo projeto · Teroz | texto na tela | antes: “Novo projeto · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/project_new | texto | `app/templates/app/project_new.html:15` | template:texto | Novo projeto | texto na tela | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:21` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:24` | template:texto | Modelo de etapas | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:32` | template:texto | {…} etapas · {…} por unidade | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:39` | template:texto | Sem modelo | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:40` | template:texto | Digitar as etapas abaixo | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:44` | template:texto | Com modelo, as etapas são copiadas da versão atual e os blocos de etapas abaixo são ignorados. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:44` | template:texto | Criar modelo de etapas | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:47` | template:texto | Nenhum modelo ainda. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:47` | template:texto | Criar modelo de etapas | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:47` | template:texto | ou digite as etapas abaixo. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:51` | template:texto | Projeto | texto na tela | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:52` | template:macro | Lote 2026-017 | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:53` | template:macro | Equipamento compacto CX-10 | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:56` | template:macro | Quantidade de equipamentos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:64` | template:macro | Pessoas na equipe | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:65` | template:macro | Horas por dia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:65` | template:macro | Por pessoa. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:68` | template:texto | Ajustar em Empresa | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:73` | template:texto | Etapas (sem modelo) | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:74` | template:texto | Preencha só as etapas que vai usar. | texto na tela | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:79` | template:macro | Simples | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:79` | template:macro | Você lança o % de cada etapa. Subatividades ficam em branco (ou uma linha com o tempo da etapa). | rótulo, botão ou ajuda de componente | antes: “Você lança o % de cada etapa. Atividades ficam em branco (ou uma linha com o tempo da etapa).” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/project_new | macro | `app/templates/app/project_new.html:79` | template:macro | Detalhado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:79` | template:macro | Subatividades com tempo ideal e peças, igual à planilha: uma por linha, Nome; minutos por unidade. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:89` | template:texto | Com modelo, o projeto usa o modo detalhado. Dá para trocar depois em Meta e equipe. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:95` | template:texto | Mais etapas (até {…}) | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:99` | template:texto | Etapa {…} | texto na tela | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:100` | template:macro | Nome da etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:100` | template:macro | Montagem mecânica | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:101` | template:macro | Subatividades | rótulo, botão ou ajuda de componente | antes: “Atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| app/project_new | macro | `app/templates/app/project_new.html:101` | template:macro | Ex.: Fixação da base; 120 | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:111` | template:macro | Criar projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | macro | `app/templates/app/project_new.html:112` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:118` | template:texto | Resumo | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:121` | template:texto | hx-include="#form-projeto [name=template_id]:checked, #form-projeto [name=quantity], #form-projeto [name=start_date], #form-projeto [name=due_date], #form-projeto [name=people], #form-projeto [name=hours_per_day]" | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:122` | template:texto | hx-trigger="load, input from:#form-projeto delay:300ms, change from:#form-projeto" | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:124` | template:texto | Calculando… | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:128` | template:texto | Como o prazo é calculado | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:129` | template:texto | Tempo total = soma dos tempos ideais × quantidade. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:130` | template:texto | Dias úteis = horas que faltam ÷ (pessoas × horas por dia), pulando fins de semana e feriados da empresa. | texto na tela | — | — | revisado — mantido |
| app/project_new | texto | `app/templates/app/project_new.html:131` | template:texto | Depois de criar, os números aparecem no painel do projeto e se atualizam a cada peça registrada. | texto na tela | — | — | revisado — mantido |
| app/projects | texto | `app/templates/app/projects.html:10` | template:texto | Projetos · Teroz | texto na tela | antes: “Projetos · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| app/projects | texto | `app/templates/app/projects.html:15` | template:texto | Projetos | texto na tela | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:18` | template:macro | Exportar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:19` | template:macro | Importar planilha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:20` | template:macro | Novo projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:21` | template:macro | Novo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | aria-label | `app/templates/app/projects.html:26` | template:aria-label | Filtrar projetos | nome para leitor de tela | — | — | revisado — mantido |
| app/projects | texto | `app/templates/app/projects.html:27` | template:texto | hx-get="{…}" hx-target="#lista-projetos" hx-select="#lista-projetos" hx-swap="outerHTML" | texto na tela | — | — | revisado — mantido |
| app/projects | aria-label | `app/templates/app/projects.html:29` | template:aria-label | Situação | nome para leitor de tela | — | — | revisado — mantido |
| app/projects | texto | `app/templates/app/projects.html:37` | template:texto | Buscar projeto ou produto | texto na tela | antes: “Buscar lote ou produto” — glossário: projeto | aplicado (texto atual) | alterado |
| app/projects | placeholder | `app/templates/app/projects.html:38` | template:placeholder | Ex.: 2026-014 | exemplo no campo | — | — | revisado — mantido |
| app/projects | texto | `app/templates/app/projects.html:41` | template:texto | Prazo | texto na tela | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:46` | template:macro | Filtrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:47` | template:macro | Limpar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:53` | template:macro | Projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:53` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:53` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | data-label | `app/templates/app/projects.html:62` | template:data-label | Unidades | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:63` | template:macro | Progresso de | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | data-label | `app/templates/app/projects.html:64` | template:data-label | Faltam | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/projects | data-label | `app/templates/app/projects.html:65` | template:data-label | Prazo | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:69` | template:macro | Atraso previsto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:69` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:69` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | texto | `app/templates/app/projects.html:70` | template:texto | no prazo | texto na tela | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:71` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:82` | template:macro | Nenhum projeto encontrado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:82` | template:macro | Nada combina com estes filtros. Tente outra busca ou veja todos os projetos. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:82` | template:macro | Ver todos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:84` | template:macro | Nenhum projeto ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:84` | template:macro | Crie o primeiro projeto com as etapas, a meta e o prazo. | rótulo, botão ou ajuda de componente | antes: “Crie o primeiro lote com as etapas, a quantidade e o prazo.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| app/projects | macro | `app/templates/app/projects.html:84` | template:macro | Novo projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:86` | template:macro | Nenhum projeto para você | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| app/projects | macro | `app/templates/app/projects.html:86` | template:macro | Quando um supervisor criar um projeto, ele aparece aqui. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | texto | `app/templates/edicao/compare.html:9` | template:texto | Comparar com o modelo · {…} | texto na tela | — | — | revisado — mantido |
| edicao/compare | texto | `app/templates/edicao/compare.html:15` | template:texto | Comparar com o modelo | texto na tela | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:18` | template:macro | projeto: v | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:19` | template:macro | atual: v | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:25` | template:macro | Nada a aplicar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:25` | template:macro | O projeto já tem as mesmas etapas, subatividades e tempos da versão atual. | rótulo, botão ou ajuda de componente | antes: “O projeto já tem as mesmas etapas, atividades e tempos da versão atual.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/compare | texto | `app/templates/edicao/compare.html:28` | template:texto | O que muda no projeto | texto na tela | — | — | revisado — mantido |
| edicao/compare | texto | `app/templates/edicao/compare.html:34` | template:texto | Peças já registradas e o histórico não mudam. Etapas e subatividades que saem ficam arquivadas. | texto na tela | antes: “Peças já registradas e o histórico não mudam. Etapas e atividades que saem ficam arquivadas.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/compare | macro | `app/templates/edicao/compare.html:38` | template:macro | Confirmo: aplicar a versão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:38` | template:macro | a este projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:40` | template:macro | Aplicar versão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/compare | macro | `app/templates/edicao/compare.html:41` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:10` | template:texto | Editar · {…} | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:20` | template:macro | Subir | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:21` | template:macro | Descer | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:27` | template:texto | Editar projeto | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:32` | template:macro | Duplicar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:34` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:40` | template:macro | O modelo “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:40` | template:macro | ” tem uma versão nova (v | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:40` | template:macro | Compare antes de aplicar: nada muda sem a sua confirmação. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:40` | template:macro | Comparar com o modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:47` | template:texto | Dados do projeto | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:58` | template:macro | Por pessoa. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:59` | template:macro | Salvar dados | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:63` | template:texto | Etapas e subatividades | texto na tela | antes: “Etapas e atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:64` | template:texto | Arquivar tira da tela e dos cálculos, mas os registros continuam no histórico e na exportação. | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:65` | template:texto | Arraste pela alça ⠿ para reordenar etapas ou levar uma subatividade para outra etapa; os botões Subir/Descer e “Mover” fazem o mesmo sem arrastar. | texto na tela | antes: “Arraste pela alça ⠿ para reordenar etapas ou levar uma atividade para outra etapa; os botões Subir/Descer e “Mover” fazem o mesmo sem arrastar.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/project_edit | title | `app/templates/edicao/project_edit.html:82` | template:title | Arrastar a etapa | dica ao passar o mouse | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:86` | template:texto | Nome da etapa | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:88` | template:macro | Confirmar e salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:88` | template:macro | Renomear | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:93` | template:macro | Arquivar etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | title | `app/templates/edicao/project_edit.html:101` | template:title | Arrastar a subatividade | dica ao passar o mouse | antes: “Arrastar a atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:105` | template:texto | Subatividade | texto na tela | antes: “Atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:107` | template:texto | Tempo ideal (min) | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:109` | template:texto | min · {…}/{…} | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:110` | template:macro | Confirmar e salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:110` | template:macro | Salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:115` | template:texto | Responsável por {…} | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:117` | template:texto | Sem responsável | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:120` | template:macro | Atribuir | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:130` | template:texto | Mover {…} para a etapa | texto na tela | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:134` | template:macro | Mover | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:139` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | texto | `app/templates/edicao/project_edit.html:143` | template:texto | Sem subatividades. Inclua pela tela do projeto. | texto na tela | antes: “Sem atividades. Inclua pela tela do projeto.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:152` | template:macro | Arquivar o projeto? | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:152` | template:macro | Ele sai da lista de projetos e libera o limite do plano. O histórico continua guardado. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/project_edit | macro | `app/templates/edicao/project_edit.html:152` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:11` | template:texto | Restaurar para uma data · {…} · Teroz | texto na tela | antes: “Restaurar para uma data · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:17` | template:texto | {…}Histórico | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:18` | template:texto | Restaurar para uma data | texto na tela | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:24` | template:macro | Algo mudou desde a prévia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:24` | template:macro | Alguém lançou peças depois que você abriu a prévia, então nada foi restaurado. Veja a prévia nova abaixo e confirme de novo. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:31` | template:texto | Para quando voltar | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:34` | template:texto | Data e hora | texto na tela | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:37` | template:macro | Ver o que muda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:39` | template:texto | Hora de {…}. Voltam só as peças prontas de cada subatividade; nomes, tempos, meta e etapas ficam como estão. O histórico não perde nada e dá para desfazer depois. | texto na tela | antes: “Hora de {…}. Voltam só as peças concluídas de cada atividade; nomes, tempos, meta e etapas ficam como estão. O histórico não perde nada e dá para desfazer depois.” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:45` | template:texto | O que muda | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:46` | template:texto | Como o projeto ficaria se voltasse para {…}. | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:52` | template:texto | ("Progresso pelas tarefas", b.progresso_geral\|pct, a.progresso_geral\|pct), | texto na tela | antes: “("Progresso geral", b.progresso_geral\|pct, a.progresso_geral\|pct),” — mesmo nome do indicador | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:53` | template:texto | ("Unidades prontas", b.unidades_concluidas ~ " de " ~ project.quantity, a.unidades_concluidas ~ " de " ~ project.quantity), | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:54` | template:texto | ("Subatividades em 100%", b.tarefas_concluidas ~ " de " ~ b.tarefas, a.tarefas_concluidas ~ " de " ~ a.tarefas), | texto na tela | antes: “("Tarefas concluídas", b.tarefas_concluidas ~ " de " ~ b.tarefas, a.tarefas_concluidas ~ " de " ~ a.tarefas),” — glossário | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:55` | template:texto | ("Horas que faltam", b.tempo_restante_h\|horas, a.tempo_restante_h\|horas), | texto na tela | antes: “("Tempo que falta", b.tempo_restante_h\|horas, a.tempo_restante_h\|horas),” — mesmo nome do indicador | aplicado (texto atual) | alterado |
| edicao/restore | macro | `app/templates/edicao/restore.html:65` | template:macro | Nada a restaurar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:65` | template:macro | Em | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:65` | template:macro | o projeto estava igual a agora. Escolha outra data e hora. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:70` | template:texto | Peças prontas agora e depois de restaurar, por etapa e subatividade | texto na tela | antes: “Peças concluídas agora e depois de restaurar, por etapa e atividade” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:71` | template:texto | Etapa › subatividade | texto na tela | antes: “Etapa › atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/restore | texto | `app/templates/edicao/restore.html:71` | template:texto | Agora | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:71` | template:texto | Depois | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:71` | template:texto | Diferença | texto na tela | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:78` | template:data-label | Agora | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:79` | template:data-label | Depois | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:80` | template:data-label | Diferença | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:87` | template:texto | {…} {…}; as outras ficam como estão. | texto na tela | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:87` | template:macro | subatividade muda | rótulo, botão ou ajuda de componente | antes: “atividade muda” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/restore | macro | `app/templates/edicao/restore.html:87` | template:macro | subatividades mudam | rótulo, botão ou ajuda de componente | antes: “atividades mudam” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/restore | macro | `app/templates/edicao/restore.html:92` | template:macro | Entendi: as peças voltam para | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:92` | template:macro | , com um lançamento de restauração por subatividade no histórico. | rótulo, botão ou ajuda de componente | antes: “, com um lançamento de restauração por atividade no histórico.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| edicao/restore | macro | `app/templates/edicao/restore.html:94` | template:macro | Restaurar o projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:95` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:103` | template:texto | Restaurações deste projeto | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:107` | template:texto | Restaurações feitas neste projeto, mais recentes primeiro | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:108` | template:texto | Voltou para | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:108` | template:texto | Feita em | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:108` | template:texto | Por | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:108` | template:texto | Lançamentos | texto na tela | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:108` | template:texto | Ação | texto na tela | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:113` | template:data-label | Feita em | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:114` | template:data-label | Por | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | data-label | `app/templates/edicao/restore.html:115` | template:data-label | Lançamentos | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| edicao/restore | texto | `app/templates/edicao/restore.html:118` | template:texto | Desfazer restauração | texto na tela | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:126` | template:macro | Nenhuma restauração ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:126` | template:macro | Quando você restaurar o projeto para uma data, ela aparece aqui e pode ser desfeita. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:131` | template:macro | Desfazer a restauração para | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/restore | macro | `app/templates/edicao/restore.html:131` | template:macro | , url_for('edicao.project_restore_undo', project_id=project.id, restore_id=r.restore_id), variant= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | texto | `app/templates/edicao/undo.html:8` | template:texto | Desfazer registro · {…} | texto na tela | — | — | revisado — mantido |
| edicao/undo | texto | `app/templates/edicao/undo.html:14` | template:texto | {…}Histórico | texto na tela | — | — | revisado — mantido |
| edicao/undo | texto | `app/templates/edicao/undo.html:15` | template:texto | Desfazer registro | texto na tela | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:20` | template:macro | Este lançamento já é um desfazer | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:20` | template:macro | Voltar ao histórico | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:22` | template:macro | Este registro já foi desfeito | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:22` | template:macro | Voltar ao histórico | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | texto | `app/templates/edicao/undo.html:26` | template:texto | Desfazer {…} de {…} em {…}? | texto na tela | — | — | revisado — mantido |
| edicao/undo | texto | `app/templates/edicao/undo.html:27` | template:texto | {…} › {…} · {…}. O total volta para {…} de {…}. O registro original continua no histórico, marcado como desfeito. | texto na tela | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:28` | template:macro | Confirmo que quero desfazer este registro | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:30` | template:macro | Desfazer | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| edicao/undo | macro | `app/templates/edicao/undo.html:31` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>Importar e exportar</b> (335)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/dados.py | valor | `app/blueprints/dados.py:64` | backend:valor | attachment; filename="{…}" | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/dados.py | _download | `app/blueprints/dados.py:73` | backend:_download | text/csv; charset=utf-8 | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _download | `app/blueprints/dados.py:102` | backend:_download | text/csv; charset=utf-8 | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | valor | `app/blueprints/dados.py:110` | backend:valor | Arquivo grande demais: o limite é {…} MB. Deixe só a aba com os dados e envie de novo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:142` | backend:_page | Escolha um arquivo .xlsx ou .csv para enviar. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | ImportError_ | `app/blueprints/dados.py:184` | backend:ImportError_ | Planilha grande demais para escolher as colunas. Deixe só a aba com os dados e envie de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | valor | `app/blueprints/dados.py:197` | backend:valor | — não usar — | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:255` | backend:_page | Dados inválidos. Envie o arquivo de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:259` | backend:_page | Planilha expirada ou inválida. Envie o arquivo de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:261` | backend:_page | Planilha de outra sessão. Envie o arquivo de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _mapping_page | `app/blueprints/dados.py:277` | backend:_mapping_page | Unidade do tempo inválida: escolha minutos ou horas. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | valor | `app/blueprints/dados.py:339` | backend:valor | Seu plano {…} permite {…} projetos ativos e já há {…}. Dá para importar {…} agora: desmarque {…} ou arquive projetos antes. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:381` | backend:_page | Prévia expirada ou de outra sessão. Envie o arquivo de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _projects_page | `app/blueprints/dados.py:387` | backend:_projects_page | Marque ao menos um projeto para importar. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:407` | backend:_page | Prévia expirada ou inválida. Envie o arquivo de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/dados.py | _page | `app/blueprints/dados.py:432` | backend:_page | Prévia inválida. Envie o arquivo de novo. | mensagem do backend | antes: “Pré-visualização inválida. Envie o arquivo de novo.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/dados.py | _page | `app/blueprints/dados.py:436` | backend:_page | Prévia expirada ou inválida. Envie o arquivo de novo. | mensagem do backend | antes: “Pré-visualização expirada ou inválida. Envie o arquivo de novo.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/dados.py | _page | `app/blueprints/dados.py:438` | backend:_page | Prévia de outra sessão. Envie o arquivo de novo. | mensagem do backend | antes: “Pré-visualização de outra sessão. Envie o arquivo de novo.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/dados.py | flash | `app/blueprints/dados.py:444` | backend:flash | Projeto importado: {…} etapas, {…} subatividades. | confirmação ou aviso após ação | antes: “Projeto importado: {…} etapas, {…} atividades.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/export_layout.py | valor | `app/services/export_layout.py:45` | backend:valor | Em andamento | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:46` | backend:valor | Não iniciada | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:196` | backend:put | Preencha só as células amarelas: nome e tempo ideal de cada subatividade, a meta e as peças concluídas. As outras células são fórmulas e se recalculam sozinhas. | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:202` | backend:put | Exportado da Teroz em {…}. Para devolver ao site, importe este arquivo. | mensagem do backend | antes: “Exportado do Controle de Produção em {…}. Para devolver ao site, importe este arquivo.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| services/export_layout.py | put | `app/services/export_layout.py:207` | backend:put | Meta: quantas unidades vamos montar (previstas) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:210` | backend:valor | Unidades concluídas (prontas em todas as etapas) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:210` | backend:valor | =B{…}&" de "&C{…} | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:211` | backend:valor | Progresso geral (pelas tarefas) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:212` | backend:valor | Unidades concluídas (soma das etapas) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:212` | backend:valor | =B{…}&" de "&C{…} | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:213` | backend:valor | Tempo que falta (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:214` | backend:valor | Dias úteis restantes (aba Equipe) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:219` | backend:put | Ir para o resumo final ↓ | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:226` | backend:put | RESUMO FINAL | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:233` | backend:valor | Unidades concluídas (prontas em todas as etapas) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:234` | backend:valor | Etapas concluídas | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:235` | backend:valor | Tarefas (subatividades) concluídas | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:235` | backend:valor | =SUMIF(O:O,"Tarefas 100%",P:P) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:236` | backend:valor | Unidades concluídas (soma das etapas) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:237` | backend:valor | Tempo trabalhado (h) = progresso geral | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:238` | backend:valor | Tempo de 1 unidade (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:239` | backend:valor | Tempo que falta (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:240` | backend:valor | Dias úteis restantes (aba Equipe) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:241` | backend:valor | Etapas ainda sem tempo definido | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:258` | backend:put | Tabela 1 – Progresso por etapa pelas tarefas (peças concluídas de cada subatividade, sobre as previstas) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:282` | backend:put | Tabela 2 – Unidades concluídas por etapa (feitas ÷ previstas, sem contar as parciais) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:317` | backend:put | Peso no projeto | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:320` | backend:put | Unidades previstas | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:323` | backend:put | Unidades concluídas | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:344` | backend:put | Total da etapa (progresso pelas tarefas) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:355` | backend:put | Unidades concluídas ÷ previstas (menor nº de peças entre as subatividades) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:365` | backend:valor | Tarefas 100% | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:400` | backend:DataValidation | Tempo ideal em minutos (número ≥ 0). | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:402` | backend:DataValidation | Peças concluídas (número inteiro ≥ 0). | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:404` | backend:DataValidation | Meta: número inteiro ≥ 1. | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:420` | backend:put | Equipe e prazo | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:421` | backend:put | Relação simples: dias úteis = horas de trabalho ÷ (pessoas × horas por dia). Considera que as pessoas trabalham em paralelo. | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:425` | backend:valor | Tempo que falta (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:426` | backend:valor | Tempo total da meta (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:427` | backend:valor | Dias úteis restantes | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | valor | `app/services/export_layout.py:428` | backend:valor | Dias úteis para a meta inteira | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:433` | backend:put | Pessoas montando | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:435` | backend:put | Horas de trabalho por dia (por pessoa) | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:437` | backend:put | E se mudar o tamanho da equipe? | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:444` | backend:put | Datas do projeto | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:445` | backend:put | Início do projeto | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | put | `app/services/export_layout.py:447` | backend:put | Prazo de entrega | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:450` | backend:DataValidation | Pessoas: inteiro de 1 a 1000. | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:452` | backend:DataValidation | Horas por dia: de 0,5 a 24. | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/export_layout.py | DataValidation | `app/services/export_layout.py:454` | backend:DataValidation | Use uma data (dd/mm/aaaa). | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:30` | backend:valor | Horas por dia | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:33` | backend:valor | Tempo ideal (min) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:34` | backend:valor | Peças concluídas | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:36` | backend:valor | % concluído | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:37` | backend:valor | Tempo que falta (h) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:46` | backend:valor | etapa arquivada | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | writerow | `app/services/exporter.py:150` | backend:writerow | Lote 2026-001 | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | writerow | `app/services/exporter.py:150` | backend:writerow | 1. Preparação | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | writerow | `app/services/exporter.py:150` | backend:writerow | Separar componentes | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | writerow | `app/services/exporter.py:151` | backend:writerow | 1. Preparação | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | writerow | `app/services/exporter.py:151` | backend:writerow | Conferir a base | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:193` | backend:valor | Unidades concluídas | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:193` | backend:valor | Horas que faltam | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:194` | backend:valor | Término previsto | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:223` | backend:valor | Unidades concluídas | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:223` | backend:valor | Peças na semana | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:224` | backend:valor | Horas que faltam | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:224` | backend:valor | Término previsto | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:224` | backend:valor | Atraso previsto (dias úteis) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:224` | backend:valor | Etapas aguardando peça | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:226` | backend:valor | Peças (saldo) | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | valor | `app/services/exporter.py:226` | backend:valor | Dias com lançamento | valor exibido (rótulo, opção, situação) | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | tuple | `app/services/exporter.py:243` | backend:tuple | Etapas aguardando peça | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/exporter.py | append | `app/services/exporter.py:250` | backend:append | Relatório semanal · {…} | mensagem do backend | formato da planilha da equipe (cabeçalhos e fórmulas) | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:78` | backend:valor | O grupo de trabalho, ex.: Soldagem. É a única coluna obrigatória. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:80` | backend:valor | A subatividade dentro da etapa, ex.: Soldar suporte. Se a sua planilha não tem esse nível, deixe sem coluna e o projeto entra no modo simples. | valor exibido (rótulo, opção, situação) | antes: “A tarefa dentro da etapa, ex.: Soldar suporte. Se a sua planilha não tem esse nível, deixe sem coluna e o projeto entra no modo simples.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/import_mapping.py | valor | `app/services/import_mapping.py:83` | backend:valor | Quanto tempo leva para fazer uma unidade, ex.: 12 (minutos) ou 0,2 (horas). Escolha a unidade abaixo. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:85` | backend:valor | Quantas unidades o projeto vai produzir, ex.: 200. Vale o mesmo número em todas as linhas; sem essa coluna, digite a meta em Projeto. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:88` | backend:valor | Quantas unidades já ficaram prontas naquela linha, ex.: 80. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:89` | backend:valor | Quanto da etapa já está pronto, ex.: 45%, 45 ou 0,45. Serve quando a planilha não traz as peças. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:90` | backend:valor | A data de entrega, ex.: 31/12/2026. Se houver várias datas, usamos a última. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:97` | backend:valor | Tempo ideal (min) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:98` | backend:valor | Meta (previstas) | valor exibido (rótulo, opção, situação) | antes: “Previstas (meta)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/import_mapping.py | valor | `app/services/import_mapping.py:99` | backend:valor | Peças prontas | valor exibido (rótulo, opção, situação) | antes: “Concluídas (peças)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/import_mapping.py | valor | `app/services/import_mapping.py:100` | backend:valor | % concluído | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:101` | backend:valor | Prazo (data) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:119` | backend:valor | tempo ideal (min) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:119` | backend:valor | tempo ideal | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:119` | backend:valor | tempo padrao | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:119` | backend:valor | tempo (min) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:120` | backend:valor | duracao (min) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:123` | backend:valor | unidades previstas | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:124` | backend:valor | total previsto | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:127` | backend:valor | pecas concluidas | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:128` | backend:valor | unidades concluidas | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:128` | backend:valor | qtd feita | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:131` | backend:valor | % concluido | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:131` | backend:valor | % da etapa | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:132` | backend:valor | % realizado | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:132` | backend:valor | concluido (%) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:132` | backend:valor | % feito | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:134` | backend:valor | data de entrega | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:134` | backend:valor | data fim | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:192` | backend:valor | Subatividade (opcional) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:193` | backend:valor | Tempo ideal (opcional) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:194` | backend:valor | Meta / previstas (opcional) | valor exibido (rótulo, opção, situação) | antes: “Previstas / meta (opcional)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/import_mapping.py | valor | `app/services/import_mapping.py:195` | backend:valor | Peças prontas (opcional) | valor exibido (rótulo, opção, situação) | antes: “Concluídas (opcional)” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/import_mapping.py | valor | `app/services/import_mapping.py:196` | backend:valor | % da etapa (opcional) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:197` | backend:valor | Prazo (opcional) | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:216` | backend:append | {…} está em duas colunas ({…} e {…}). Escolha uma. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:240` | backend:valor | Coluna {…} | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | ImportError_ | `app/services/import_mapping.py:287` | backend:ImportError_ | A planilha está vazia. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:340` | backend:append | Escolha a coluna da etapa. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:347` | backend:append | {…}: coluna inexistente. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:349` | backend:append | {…} e {…} usam a mesma coluna. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:372` | backend:error | escolha minutos ou horas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:376` | backend:error | aba ou linha de cabeçalho inválida | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:384` | backend:valor | Projeto importado | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:400` | backend:error | mais de {…} linhas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:403` | backend:error | nenhuma linha de dados depois do cabeçalho | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:425` | backend:error | nome com mais de 160 caracteres | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:429` | backend:error | “{…}” repetida (sem subatividade, uma linha por etapa) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:433` | backend:error | mais de {…} etapas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:454` | backend:error | mais de {…} subatividades na etapa | mensagem de erro | antes: “mais de {…} atividades na etapa” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/import_mapping.py | error | `app/services/import_mapping.py:459` | backend:error | nenhuma etapa encontrada | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:465` | backend:append | Com peças e % mapeados, valem as peças; o % foi usado só onde as peças estão vazias. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:468` | backend:append | Sem subatividades: cada etapa entra com uma subatividade de mesmo nome (modo simples). | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:502` | backend:valor | Os tempos são muito pequenos para minutos (média de {…}). Se a planilha usa horas, volte às colunas e escolha “Horas”. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | valor | `app/services/import_mapping.py:507` | backend:valor | Os tempos são muito grandes para horas (média de {…}). Se a planilha usa minutos, volte às colunas e escolha “Minutos”. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:516` | backend:error | número inteiro entre 1 e {…} | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:529` | backend:error | número inteiro entre 1 e {…} | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:536` | backend:error | {…} diferente da linha {…} ({…}); o projeto tem uma meta só | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:541` | backend:error | com peças prontas, informe a meta (coluna de meta ou o número) | mensagem de erro | antes: “com peças concluídas, informe a meta (coluna de previstas ou o número)” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/import_mapping.py | append | `app/services/import_mapping.py:545` | backend:append | Meta não informada: usamos {…} unidades para guardar o %. Ajuste depois. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:548` | backend:append | Meta não informada: usamos 1 unidade. Ajuste depois. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:558` | backend:error | data inválida (use dd/mm/aaaa) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | append | `app/services/import_mapping.py:565` | backend:append | Prazos diferentes por linha: usamos o último ({…}). | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | error | `app/services/import_mapping.py:579` | backend:error | use um % entre 0 e 100 (ex.: 45%, 45 ou 0,45) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/import_mapping.py | ImportError_ | `app/services/import_mapping.py:631` | backend:ImportError_ | Dados da planilha inválidos; envie o arquivo de novo. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | valor | `app/services/importer.py:85` | backend:valor | Linha {…}, {…}: {…} | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:204` | backend:error | faltam as colunas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:219` | backend:error | mais de {…} linhas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:229` | backend:error | nome com mais de 160 caracteres | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:233` | backend:error | use ativa, arquivada ou etapa arquivada | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:238` | backend:error | mais de {…} etapas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:251` | backend:error | mais de {…} subatividades na etapa | mensagem de erro | antes: “mais de {…} atividades na etapa” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/importer.py | error | `app/services/importer.py:255` | backend:error | nenhuma linha de dados | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:263` | backend:error | informe o nome do projeto na primeira linha | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:269` | backend:error | número inteiro entre 1 e {…} | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:274` | backend:error | data inválida (use dd/mm/aaaa) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:276` | backend:error | antes do início | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:284` | backend:error | número inteiro entre 1 e 1000 | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:292` | backend:error | número entre 0,5 e 24 | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:303` | backend:error | nome com mais de 160 caracteres | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:312` | backend:error | tempo ideal | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:312` | backend:error | número inválido | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:321` | backend:error | número inteiro inválido | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:324` | backend:error | maior que a quantidade ({…}) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | valor | `app/services/importer.py:339` | backend:valor | Planilha com texto demais. Deixe só a aba com os dados e tente de novo. | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:391` | backend:ImportError_ | O arquivo não parece um CSV de texto. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:413` | backend:ImportError_ | CSV inválido: {…} | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:456` | backend:ImportError_ | Escolha um arquivo .csv ou .xlsx. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:458` | backend:ImportError_ | Arquivo maior que {…} MB. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:465` | backend:ImportError_ | Envie um arquivo .csv ou .xlsx (o conteúdo precisa bater com a extensão). | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:524` | backend:ImportError_ | Planilha grande demais depois de descompactada. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:530` | backend:ImportError_ | Planilha protegida por senha não é aceita. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:539` | backend:ImportError_ | Planilha grande demais depois de descompactada. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:542` | backend:ImportError_ | Planilha com definição de documento (DTD) não é aceita. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:547` | backend:ImportError_ | O arquivo não é uma planilha .xlsx válida. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | ImportError_ | `app/services/importer.py:561` | backend:ImportError_ | Não foi possível ler a planilha .xlsx. | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | valor | `app/services/importer.py:588` | backend:valor | como funciona | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | compile | `app/services/importer.py:590` | backend:compile | ^\s*(?:(?P<name>.+?)\s+[-–—]\s+)?(?P<role>acompanhamento\|equipe\|como funciona)\s*$ | mensagem do backend | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | valor | `app/services/importer.py:629` | backend:valor | Projeto importado | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:648` | backend:error | nenhum bloco de etapa encontrado (título “N. Nome” seguido de “Unidades previstas”) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | valor | `app/services/importer.py:650` | backend:valor | Projeto importado | valor exibido (rótulo, opção, situação) | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:653` | backend:error | linha “Meta…” (quantidade prevista) não encontrada | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:660` | backend:error | B (meta) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:660` | backend:error | número inteiro entre 1 e {…} | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:675` | backend:error | Equipe!B ({…}) | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:675` | backend:error | valor inválido | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:688` | backend:error | mais de {…} subatividades na etapa | mensagem de erro | antes: “mais de {…} atividades na etapa” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/importer.py | error | `app/services/importer.py:691` | backend:error | mais de {…} etapas | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:774` | backend:error | pré-visualização inválida; envie o arquivo de novo | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:784` | backend:error | fora do limite | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:786` | backend:error | pessoas ou horas por dia fora do limite | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:788` | backend:error | nenhuma etapa ou etapas demais | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:791` | backend:error | etapa inválida | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| services/importer.py | error | `app/services/importer.py:798` | backend:error | subatividade “{…}” inválida | mensagem de erro | antes: “atividade “{…}” inválida” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/importer.py | erro | `app/services/importer.py:805` | backend:erro | importação com erros não pode ser gravada | mensagem de erro | sinônimos de leitura da planilha do cliente | — | mantido de propósito |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:8` | template:texto | Confira as colunas | texto na tela | — | — | revisado — mantido |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:16` | template:texto | Falta a coluna da Etapa | texto na tela | — | — | revisado — mantido |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:17` | template:texto | Marque qual coluna traz o nome da etapa. É a única obrigatória. | texto na tela | — | — | revisado — mantido |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:24` | template:texto | Vai entrar no modo simples | texto na tela | — | — | revisado — mantido |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:25` | template:texto | Uma linha por etapa, com o % concluído (ou as concluídas). Para lançar por subatividade, marque uma coluna como Subatividade. | texto na tela | antes: “Uma linha por etapa, com o % concluído (ou as concluídas). Para lançar por atividade, marque uma coluna como Subatividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:32` | template:texto | Vai entrar no modo detalhado | texto na tela | — | — | revisado — mantido |
| dados/_import_mode | texto | `app/templates/dados/_import_mode.html:33` | template:texto | Cada linha vira uma subatividade dentro da etapa. Etapa vazia numa linha usa a etapa da linha de cima. | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:11` | template:macro | Prévia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:11` | template:macro | Enviar arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:17` | template:texto | Importar planilha | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:18` | template:texto | Traga etapas e subatividades de uma planilha .xlsx ou .csv. Nada é gravado antes da sua confirmação. | texto na tela | antes: “Traga etapas e atividades de uma planilha .xlsx ou .csv. Nada é gravado antes da sua confirmação.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| dados/import | macro | `app/templates/dados/import.html:22` | template:macro | Enviar arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:22` | template:macro | Escolher colunas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:22` | template:macro | automático | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:22` | template:macro | Prévia e confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:22` | template:macro | Passos da importação | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:24` | template:macro | Não deu para ler o arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:46` | template:texto | {…} {…} na planilha | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:47` | template:texto | Nada foi gravado. Corrija as linhas abaixo na planilha e envie de novo , ou volte e mude as colunas . | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:49` | template:macro | Linha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:49` | template:macro | Coluna | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:49` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:49` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:53` | template:texto | Linha {…} Arquivo | texto na tela | — | — | revisado — mantido |
| dados/import | data-label | `app/templates/dados/import.html:54` | template:data-label | Coluna | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| dados/import | data-label | `app/templates/dados/import.html:55` | template:data-label | Problema | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:60` | template:texto | Mostrando 50 de {…} problemas. | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:62` | template:macro | Voltar às colunas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:63` | template:macro | Enviar outro arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:71` | template:texto | Prévia | texto na tela | antes: “Pré-visualização” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| dados/import | macro | `app/templates/dados/import.html:73` | template:macro | Modo simples | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:73` | template:macro | Modo detalhado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:76` | template:texto | meta {…} {…} | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:77` | template:texto | prazo {…} | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:80` | template:texto | Uma linha por etapa, com o % concluído. | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:81` | template:texto | Cada linha vira uma subatividade dentro da etapa, com tempo ideal e peças prontas. | texto na tela | antes: “Cada linha vira uma atividade dentro da etapa, com tempo ideal e peças concluídas.” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| dados/import | texto | `app/templates/dados/import.html:82` | template:texto | Formato da planilha de acompanhamento reconhecido. Formato do site reconhecido. | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:86` | template:macro | Confira a unidade do tempo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:89` | template:texto | Tempo ideal somado (por unidade) | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:90` | template:texto | {…} min | texto na tela | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:91` | template:texto | · unidade da planilha: {…} | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:91` | template:macro | horas (convertidas para minutos) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:95` | template:macro | Limite do plano atingido | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:95` | template:macro | Seu plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:95` | template:macro | projetos ativos. Arquive um projeto ou mude de plano para importar. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:97` | template:macro | Etapa › subatividade | rótulo, botão ou ajuda de componente | antes: “Etapa › atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| dados/import | macro | `app/templates/dados/import.html:97` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:97` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | data-label | `app/templates/dados/import.html:104` | template:data-label | Tempo ideal (min) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:105` | template:texto | de {…} | texto na tela | — | — | revisado — mantido |
| dados/import | data-label | `app/templates/dados/import.html:105` | template:data-label | Peças prontas | rótulo da coluna no modo cartão (celular) | antes: “Concluídas” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| dados/import | texto | `app/templates/dados/import.html:108` | template:texto | Sem subatividades | texto na tela | antes: “Sem atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| dados/import | macro | `app/templates/dados/import.html:118` | template:macro | Importar projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:119` | template:macro | Voltar às colunas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:120` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:129` | template:texto | Enviar arquivo | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:130` | template:macro | Planilha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:130` | template:macro | Planilha .xlsx ou .csv, até | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:130` | template:macro | MB e 5.000 linhas. O formato do site e a planilha de acompanhamento são reconhecidos sozinhos; nas outras, você escolhe as colunas. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:131` | template:macro | Se ficar vazio, usamos o nome do arquivo. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | texto | `app/templates/dados/import.html:132` | template:texto | Quero escolher as colunas mesmo assim | texto na tela | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:134` | template:macro | Ler a planilha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import | macro | `app/templates/dados/import.html:135` | template:macro | Baixar modelo .csv | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:7` | template:texto | Escolher colunas · Importar planilha · Teroz | texto na tela | antes: “Escolher colunas · Importar planilha · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| dados/import_map | texto | `app/templates/dados/import_map.html:12` | template:texto | {…}Enviar outro arquivo | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:13` | template:texto | Importar planilha | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:14` | template:texto | Diga o que cada coluna é. Só a Etapa é obrigatória. | texto na tela | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:18` | template:macro | Enviar arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:18` | template:macro | Escolher colunas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:18` | template:macro | Prévia e confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:18` | template:macro | Passos da importação | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:26` | template:texto | Onde estão os dados | texto na tela | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:28` | template:macro | abas no arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:28` | template:macro | Arquivo com uma aba | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:29` | template:macro | A linha com os nomes das colunas. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:30` | template:macro | Reler a aba | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:34` | template:texto | Esta aba não tem dados abaixo da linha {…}. Escolha outra aba ou outra linha de cabeçalho e clique em “Reler a aba”. | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:40` | template:texto | O que cada coluna é | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:41` | template:texto | Já deixamos uma sugestão pelo nome das colunas. Confira e ajuste; colunas sem uso ficam em “Não usar”. | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:47` | template:texto | Como preencher cada campo | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:51` | template:texto | (obrigatório) | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:61` | template:texto | Colunas da aba {…} | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:62` | template:texto | Coluna | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:62` | template:texto | Exemplos | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:62` | template:texto | Isto é… | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:69` | template:texto | Sem nome | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:69` | template:texto | (coluna {…}) | texto na tela | — | — | revisado — mantido |
| dados/import_map | data-label | `app/templates/dados/import_map.html:71` | template:data-label | Exemplos | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:76` | template:texto | Coluna {…} ({…}) : isto é… | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:78` | template:texto | hx-get="{…}" hx-trigger="change" hx-include="[data-map-select]" | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:80` | template:texto | Não usar | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:92` | template:texto | Nenhuma coluna com dados nesta aba. | texto na tela | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:97` | template:texto | Unidade do tempo | texto na tela | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:99` | template:macro | Em que unidade está a coluna de tempo ideal. Se escolher horas, convertemos para minutos e mostramos o total na prévia. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | texto | `app/templates/dados/import_map.html:104` | template:texto | Projeto | texto na tela | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:106` | template:macro | Use se a planilha não tem a coluna de meta (previstas). | rótulo, botão ou ajuda de componente | antes: “Use se a planilha não tem a coluna de previstas.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| dados/import_map | macro | `app/templates/dados/import_map.html:107` | template:macro | Se ficar vazio, usamos o nome do arquivo. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:112` | template:macro | Ver prévia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_map | macro | `app/templates/dados/import_map.html:113` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:8` | template:macro | Escolher projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:8` | template:macro | Prévia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:13` | template:texto | {…}Enviar outro arquivo | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:14` | template:texto | Importar planilha | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:15` | template:texto | Este arquivo tem vários projetos. Escolha quais importar. Confira os projetos escolhidos e confirme. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:19` | template:macro | Enviar arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:19` | template:macro | Escolher projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:19` | template:macro | Prévia e confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:19` | template:macro | Passos da importação | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:22` | template:macro | Passa do limite do plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:28` | template:texto | Projetos encontrados | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:29` | template:texto | Cada projeto tem as abas Acompanhamento, Equipe e Como funciona. Todos vêm marcados; desmarque o que não quiser trazer. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:44` | template:texto | meta {…} | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:45` | template:texto | abas “{…} - …” | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:45` | template:texto | abas sem prefixo | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:49` | template:texto | Linha {…}, {…}: {…} | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:50` | template:texto | … e mais {…}. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:52` | template:texto | Este não pode ser importado como está. Corrija a aba e envie o arquivo de novo. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:58` | template:texto | Seu plano {…}: {…} de {…} projetos ativos em uso. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:62` | template:macro | Ver prévia | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:63` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:70` | template:texto | {…} {…} para importar | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:71` | template:texto | Um projeto novo para cada item. Nada é gravado antes de você confirmar. | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:82` | template:texto | meta {…} | texto na tela | — | — | revisado — mantido |
| dados/import_projects | texto | `app/templates/dados/import_projects.html:85` | template:texto | {…}Ver as etapas | texto na tela | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:100` | template:macro | Importar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:108` | template:macro | Voltar e mudar a escolha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| dados/import_projects | macro | `app/templates/dados/import_projects.html:111` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>Site público</b> (300)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/public.py | valor | `app/blueprints/public.py:35` | backend:valor | Verificação em duas etapas obrigatória para proprietários | valor exibido (rótulo, opção, situação) | antes: “Verificação em duas etapas obrigatória (MFA)” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| blueprints/public.py | valor | `app/blueprints/public.py:36` | backend:valor | API para ligar a outros sistemas | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:37` | backend:valor | Identidade visual da sua empresa | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:61` | backend:valor | Projetos ilimitados | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:61` | backend:valor | {…} projetos ativos | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:62` | backend:valor | {…} pessoas | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:62` | backend:valor | Pessoas ilimitadas | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:126` | backend:valor | <?xml version="1.0" encoding="UTF-8"?> <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:133` | backend:valor | User-agent: * | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:134` | backend:valor | Allow: / | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:135` | backend:valor | Disallow: /app/ | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:136` | backend:valor | Disallow: /conta/ | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:137` | backend:valor | Disallow: /convite/ | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:138` | backend:valor | Disallow: /senha/ | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:139` | backend:valor | Disallow: /api/ | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/public.py | valor | `app/blueprints/public.py:140` | backend:valor | Sitemap: {…}{…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:7` | template:texto | site site--marca | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:16` | template:texto | Pular para o conteúdo | texto na tela | — | — | revisado — mantido |
| base_publica | aria-label | `app/templates/base_publica.html:22` | template:aria-label | Site | nome para leitor de tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:24` | template:texto | Como funciona | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:25` | template:texto | Sua planilha | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:27` | template:texto | Preços | texto na tela | — | — | revisado — mantido |
| base_publica | macro | `app/templates/base_publica.html:29` | template:macro | Abrir o painel | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:31` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| base_publica | macro | `app/templates/base_publica.html:32` | template:macro | Teste grátis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_publica | title | `app/templates/base_publica.html:40` | template:title | Alternar entre tema claro e escuro | dica ao passar o mouse | texto novo na revisão | aplicado (texto atual) | incluído |
| base_publica | texto | `app/templates/base_publica.html:42` | template:texto | Tema escuro | texto na tela | texto novo na revisão | aplicado (texto atual) | incluído |
| base_publica | texto | `app/templates/base_publica.html:45` | template:texto | Abrir menu | texto na tela | — | — | revisado — mantido |
| base_publica | aria-label | `app/templates/base_publica.html:55` | template:aria-label | Rodapé | nome para leitor de tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:56` | template:texto | Sua planilha | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:58` | template:texto | Preços | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:60` | template:texto | Termos | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:62` | template:texto | Privacidade | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:64` | template:texto | Contato | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:66` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:68` | template:texto | © 2026 Teroz | texto na tela | antes: “© 2026 Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| base_publica | aria-label | `app/templates/base_publica.html:72` | template:aria-label | Menu | nome para leitor de tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:77` | template:texto | Menu | texto na tela | — | — | revisado — mantido |
| base_publica | aria-label | `app/templates/base_publica.html:78` | template:aria-label | Fechar menu | nome para leitor de tela | — | — | revisado — mantido |
| base_publica | aria-label | `app/templates/base_publica.html:80` | template:aria-label | Site | nome para leitor de tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:81` | template:texto | Como funciona | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:82` | template:texto | Funciona com a sua planilha | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:83` | template:texto | Preços | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:85` | template:texto | Painel | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:87` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:89` | template:texto | Termos de uso | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:90` | template:texto | Privacidade | texto na tela | — | — | revisado — mantido |
| base_publica | texto | `app/templates/base_publica.html:91` | template:texto | Contato | texto na tela | — | — | revisado — mantido |
| base_publica | macro | `app/templates/base_publica.html:94` | template:macro | Começar teste grátis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/_legal | aria-label | `app/templates/public/_legal.html:7` | template:aria-label | Nesta página | nome para leitor de tela | — | — | revisado — mantido |
| public/_legal | texto | `app/templates/public/_legal.html:9` | template:texto | Nesta página | texto na tela | — | — | revisado — mantido |
| public/_legal | texto | `app/templates/public/_legal.html:19` | template:texto | Atualizado em {…} | texto na tela | — | — | revisado — mantido |
| public/_legal | macro | `app/templates/public/_legal.html:20` | template:macro | Rascunho para revisão jurídica | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/_legal | macro | `app/templates/public/_legal.html:20` | template:macro | Este texto ainda não foi revisado por advogado e pode mudar antes do lançamento. Não o trate como contrato final. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/_legal | texto | `app/templates/public/_legal.html:22` | template:texto | Voltar ao topo | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:3` | template:texto | Como funciona com a sua planilha · Teroz | texto na tela | antes: “Como funciona com a sua planilha · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:4` | template:texto | Traga a planilha que a sua equipe já usa: você escolhe a aba, diz o que cada coluna significa, confere os erros e importa. Depois exporte no formato da equipe, com fórmulas funcionando. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:10` | template:texto | Como funciona com a sua planilha | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:11` | template:texto | Sua planilha entra. A conta sai pronta. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:12` | template:texto | Você não precisa começar do zero nem refazer o que a equipe já montou. Envie o arquivo, diga o que cada coluna significa e o sistema passa a calcular progresso, horas que faltam e prazo em dias úteis. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:14` | template:texto | Começar teste grátis de {…} dias | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:15` | template:texto | Ver preços | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:19` | template:texto | Quais colunas são quais? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:20` | template:texto | Fase | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:20` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:21` | template:texto | Serviço | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:21` | template:texto | Subatividade | texto na tela | antes: “Atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:22` | template:texto | Tempo | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:22` | template:texto | Tempo ideal | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:23` | template:texto | Feitas | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:23` | template:texto | Peças prontas | texto na tela | antes: “Peças concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:24` | template:texto | Nomes de colunas de exemplo. Na sua planilha, você escolhe os seus. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:31` | template:texto | Importar | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:32` | template:texto | Três passos para trazer o arquivo. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:33` | template:texto | Aceitamos planilhas em Excel (XLSX) e em CSV, até 2 MB e 2.000 linhas de dados. Nada é salvo até você conferir e confirmar. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:35` | template:texto | Envie o arquivo | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:35` | template:texto | Escolha a planilha no seu computador. Se ela tem várias abas, você diz qual aba tem os dados. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | alt | `app/templates/public/como_funciona.html:35` | template:alt | Tela Importar planilha, no passo Enviar arquivo. | descrição de imagem | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:36` | template:texto | Diga o que é cada coluna | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:36` | template:texto | O sistema sugere o significado pelo nome do cabeçalho. Você corrige o que precisar: etapa, subatividade, tempo ideal, peças previstas e concluídas ou prazo. | texto na tela | antes: “O sistema sugere o significado pelo nome do cabeçalho. Você corrige o que precisar: etapa, atividade, tempo ideal, peças previstas e concluídas ou prazo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/como_funciona | alt | `app/templates/public/como_funciona.html:36` | template:alt | Tela Escolher colunas: cada coluna da planilha com exemplos e o significado escolhido, como Etapa, Subatividade e Tempo ideal. | descrição de imagem | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:37` | template:texto | Confira e confirme | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:37` | template:texto | Veja uma prévia com as etapas e as subatividades. Se houver erro, o sistema mostra a linha, a coluna e o problema, e você volta às colunas sem enviar o arquivo de novo. | texto na tela | antes: “Veja uma prévia com as etapas e as atividades. Se houver erro, o sistema mostra a linha, a coluna e o problema, e você volta às colunas sem enviar o arquivo de novo.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/como_funciona | alt | `app/templates/public/como_funciona.html:37` | template:alt | Tela Prévia e confirmar: etapas e subatividades lidas da planilha, com tempo ideal e peças prontas. | descrição de imagem | antes: “Tela Prévia e confirmar: etapas e atividades lidas da planilha, com tempo ideal e peças concluídas.” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:44` | template:texto | Do seu jeito | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:45` | template:texto | Sua planilha pode ser simples ou detalhada. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:47` | template:texto | Só etapa e porcentagem | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:47` | template:texto | Se a planilha diz apenas quanto cada etapa já avançou, o sistema acompanha por etapa. É o jeito mais rápido de começar. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:48` | template:texto | Etapa, subatividade e tempo | texto na tela | antes: “Etapa, atividade e tempo” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:48` | template:texto | Se ela detalha as subatividades de cada etapa, com tempo ideal e peças feitas, você ganha as horas que faltam e o prazo em dias úteis com mais precisão. | texto na tela | antes: “Se ela detalha as atividades de cada etapa, com tempo ideal e peças feitas, você ganha as horas que faltam e o prazo em dias úteis com mais precisão.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:49` | template:texto | Vários projetos no mesmo arquivo | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:49` | template:texto | Quando o arquivo tem mais de um projeto, você escolhe quais importar. Cada um vira um projeto separado. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:50` | template:texto | Importou errado? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:50` | template:texto | Cada mudança fica no histórico, com quem fez e quando. Dá para voltar o projeto a uma data anterior e desfazer a volta. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:58` | template:texto | Exportar | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:59` | template:texto | E a planilha continua útil. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:61` | template:texto | Abas Acompanhamento e Equipe | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:61` | template:texto | A exportação traz as mesmas abas que a equipe já conhece, com indicadores, etapas e cenários de 1 a 6 pessoas. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:62` | template:texto | Fórmulas funcionando | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:62` | template:texto | Ao abrir no Excel, as contas se recalculam quando você muda um valor. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:63` | template:texto | Células de entrada em amarelo | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:63` | template:texto | O que se preenche à mão fica destacado, como no modelo que você já usa. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:67` | template:texto | Sem ficar preso | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:68` | template:texto | Você exporta em planilha quando quiser, em qualquer plano, até com a assinatura atrasada. Seus dados são seus. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:75` | template:texto | Dúvidas sobre a planilha | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:77` | template:texto | Minha planilha tem outro formato. Funciona? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:77` | template:texto | Funciona. Você diz o que cada coluna significa. Só a coluna da etapa é obrigatória; as outras ajudam a calcular horas e prazo. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:78` | template:texto | A importação apaga o que já tenho no sistema? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:78` | template:texto | Não. Cada importação cria projetos novos. Antes de confirmar, você vê a prévia e o limite de projetos do seu plano. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:79` | template:texto | O que acontece se houver erro numa linha? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:79` | template:texto | O sistema lista cada erro com a linha, a coluna e o motivo. Você corrige a planilha ou muda a escolha das colunas e tenta de novo. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:80` | template:texto | Meu arquivo é grande. E agora? | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:80` | template:texto | O limite é de 2 MB e 2.000 linhas de dados. Se passar disso, deixe no arquivo só a aba com os dados do projeto. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:87` | template:texto | Traga sua planilha e veja. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:88` | template:texto | {…} dias grátis, sem cartão, nos planos Essencial e Profissional. | texto na tela | — | — | revisado — mantido |
| public/como_funciona | texto | `app/templates/public/como_funciona.html:89` | template:texto | Começar teste grátis | texto na tela | — | — | revisado — mantido |
| public/contato | texto | `app/templates/public/contato.html:4` | template:texto | Contato · Teroz | texto na tela | antes: “Contato · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/contato | texto | `app/templates/public/contato.html:5` | template:texto | Fale com a Teroz: dúvidas sobre planos, suporte e privacidade, por e-mail. | texto na tela | antes: “Fale com o Controle de Produção: dúvidas sobre planos, suporte e privacidade, por e-mail.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/contato | texto | `app/templates/public/contato.html:9` | template:texto | Contato | texto na tela | — | — | revisado — mantido |
| public/contato | texto | `app/templates/public/contato.html:10` | template:texto | Fale com a gente. | texto na tela | — | — | revisado — mantido |
| public/contato | texto | `app/templates/public/contato.html:11` | template:texto | Dúvidas sobre planos, suporte ou privacidade? Escreva para a gente. | texto na tela | — | — | revisado — mantido |
| public/contato | texto | `app/templates/public/contato.html:13` | template:texto | E-mail | texto na tela | — | — | revisado — mantido |
| public/contato | texto | `app/templates/public/contato.html:15` | template:texto | Respondemos em dias úteis. Para suporte, informe o nome da empresa e o que aconteceu. Nunca envie a sua senha. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:5` | template:texto | Teroz · saiba em que etapa está cada lote | texto na tela | antes: “Controle de Produção · saiba em que etapa está cada lote” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:6` | template:texto | Acompanhe a produção etapa por etapa: progresso, unidades prontas, horas que faltam e prazo em dias úteis. Importe a sua planilha e comece com {…} dias grátis, sem cartão. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:11` | template:texto | Para quem monta sob encomenda | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:12` | template:texto | Saiba | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:12` | template:texto | está | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:13` | template:texto | Acompanhe a produção etapa por etapa: quanto cada uma já avançou, quantas unidades estão prontas, quantas horas faltam e qual é o prazo em dias úteis. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:15` | template:texto | Começar teste grátis de {…} dias | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:16` | template:texto | Ver como funciona | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:18` | template:texto | Sem cartão. Cancele quando quiser. | texto na tela | — | — | revisado — mantido |
| public/index | alt | `app/templates/public/index.html:29` | template:alt | Painel de um projeto na Teroz: progresso pelas tarefas de 40%, horas que faltam, dias úteis até o prazo, barras de tarefas e unidades por etapa e a situação das etapas. | descrição de imagem | antes: “Painel de um lote no Teroz: progresso geral de 39%, horas que faltam, dias úteis até o prazo, barras de tarefas e unidades por etapa e a situação das etapas.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:32` | template:texto | Tela real da Teroz, com dados de exemplo. | texto na tela | antes: “Tela real do Teroz, com dados de exemplo.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:38` | template:texto | Feito para quem monta: | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Robôs industriais | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Painéis elétricos | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Transformadores | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Máquinas sob encomenda | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Quadros de comando | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:41` | template:texto | Linhas de montagem | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:49` | template:texto | Como funciona | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:50` | template:texto | Três passos, sem treinamento longo. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:51` | template:texto | Quem monta lotes já conhece as etapas. O sistema só faz a conta. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:53` | template:texto | Traga sua planilha | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:53` | template:texto | Envie o arquivo e diga qual coluna é a etapa, qual é a subatividade e qual é o tempo. Se preferir, monte as etapas direto na tela. | texto na tela | antes: “Envie o arquivo e diga qual coluna é a etapa, qual é a atividade e qual é o tempo. Se preferir, monte as etapas direto na tela.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/index | alt | `app/templates/public/index.html:53` | template:alt | Tela Importar planilha, no passo Enviar arquivo. | descrição de imagem | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:54` | template:texto | Veja o painel | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:54` | template:texto | Cada etapa mostra o progresso pelas tarefas e as unidades prontas. Você vê também as horas que faltam e o prazo em dias úteis. | texto na tela | — | — | revisado — mantido |
| public/index | alt | `app/templates/public/index.html:54` | template:alt | Gráfico Tarefas × unidades por etapa, do painel do projeto. | descrição de imagem | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:55` | template:texto | Lance o progresso | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:55` | template:texto | Quem está na bancada registra as peças prontas pelo celular. As horas que faltam e o prazo se recalculam na hora. | texto na tela | antes: “Quem está na bancada registra as peças concluídas pelo celular. As horas que faltam e o prazo se recalculam na hora.” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| public/index | alt | `app/templates/public/index.html:55` | template:alt | Preencher etapas no celular: lista de etapas com o progresso de cada uma. | descrição de imagem | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:63` | template:texto | Sua planilha continua útil | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:64` | template:texto | Funciona com a planilha que você já tem. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:66` | template:texto | Importa qualquer planilha | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:66` | template:texto | Escolha a aba, indique o que cada coluna significa e confira os erros por linha antes de salvar. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:67` | template:texto | Vários projetos de uma vez | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:67` | template:texto | Se o arquivo tem mais de um projeto, você escolhe quais importar. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:68` | template:texto | Exporta no formato da equipe | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:68` | template:texto | As abas Acompanhamento e Equipe, com as fórmulas funcionando e as células de entrada em amarelo. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:70` | template:texto | Ver o passo a passo da planilha | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:73` | template:texto | Quais colunas são quais? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:74` | template:texto | Fase | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:74` | template:texto | Etapa | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:75` | template:texto | Serviço | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:75` | template:texto | Subatividade | texto na tela | antes: “Atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:76` | template:texto | Tempo | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:76` | template:texto | Tempo ideal | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:77` | template:texto | Feitas | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:77` | template:texto | Peças prontas | texto na tela | antes: “Peças concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:78` | template:texto | Nomes de colunas de exemplo. Na sua planilha, você escolhe os seus. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:85` | template:texto | Opcional, quando você precisar | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:86` | template:texto | O começo é simples. O resto você liga se quiser. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:87` | template:texto | Etapas, subatividades e peças vêm prontas. O que está abaixo fica desligado até você ativar em Configurações. | texto na tela | antes: “Etapas, atividades e peças vêm prontas. O que está abaixo fica desligado até você ativar em Configurações.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Fotos e comentários | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Guarde fotos e observações em cada subatividade, como registro do que foi feito. | rótulo, botão ou ajuda de componente | antes: “Anexe fotos e observações ao registro de uma atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Checklist de inspeção | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Uma lista de conferência por etapa, assinada por quem inspecionou. | rótulo, botão ou ajuda de componente | antes: “Uma lista de itens para conferir antes de dar a atividade como pronta.” — recurso real: o checklist é por etapa e só sinaliza (não trava) | aplicado (texto atual) | alterado |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Alertas por e-mail | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Aviso quando o prazo entra em risco ou uma etapa para, e um resumo toda segunda-feira. | rótulo, botão ou ajuda de componente | antes: “Aviso de etapa atrasada e um resumo semanal na caixa de entrada.” — recurso real (alertas: prazo em risco, etapa parada, peça atrasada; relatório semanal às segundas) | aplicado (texto atual) | alterado |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Responsáveis | rótulo, botão ou ajuda de componente | antes: “Equipe” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| public/index | macro | `app/templates/public/index.html:89` | template:macro | Defina quem cuida de cada subatividade e veja quantas peças cada pessoa lançou. | rótulo, botão ou ajuda de componente | antes: “Atribua atividades a pessoas e veja o progresso de cada uma.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/index | texto | `app/templates/public/index.html:92` | template:texto | Opcional | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:102` | template:texto | Preços | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:103` | template:texto | Preço por empresa, não por pessoa. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:104` | template:texto | Teste grátis de {…} dias, sem cartão, nos planos Essencial e Profissional. O plano Empresa cobra ao contratar. A Implantação é sob orçamento, online ou presencial, com acompanhamento de 1 mês e treinamento. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:110` | template:texto | Pagamento por Pix, boleto ou cartão. Histórico de cada registro, modelos de etapas e exportação em todos os planos. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:110` | template:texto | Comparar os planos em detalhe | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:116` | template:texto | Dúvidas | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:116` | template:texto | Perguntas frequentes | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:118` | template:texto | O que preciso para começar? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:118` | template:texto | Um navegador e as etapas do seu produto. Você pode digitar as etapas na tela ou importar a planilha que a equipe já usa. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:119` | template:texto | Preciso abandonar minha planilha? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:119` | template:texto | Não. Você importa a planilha para começar e pode exportar no formato da equipe quando quiser. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:120` | template:texto | Como o prazo em dias úteis é calculado? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:120` | template:texto | Horas que faltam divididas pelo que a equipe produz por dia: pessoas vezes horas por dia. A tela “Como funciona” mostra cada conta com os números do seu projeto. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:121` | template:texto | Funciona no celular? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:121` | template:texto | Sim. Quem está na bancada registra as peças pelo celular, em poucos toques. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:122` | template:texto | O teste grátis pede cartão? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:122` | template:texto | Não. São {…} dias nos planos Essencial e Profissional, sem cartão. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:123` | template:texto | Os dados da minha empresa ficam separados dos de outras? | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:123` | template:texto | Sim. Cada empresa só enxerga os próprios dados. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:130` | template:texto | Descubra onde cada lote está hoje. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:131` | template:texto | {…} dias grátis, sem cartão, nos planos Essencial e Profissional. Planos a partir de R$ {…} por mês. | texto na tela | — | — | revisado — mantido |
| public/index | texto | `app/templates/public/index.html:132` | template:texto | Começar teste grátis | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:6` | template:texto | Preços · Teroz | texto na tela | antes: “Preços · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/precos | texto | `app/templates/public/precos.html:7` | template:texto | Planos por empresa , a partir de R$ {…} por mês . {…} dias grátis, sem cartão, no Essencial e no Profissional. Projetos, pessoas, histórico e exportação. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:13` | template:texto | Preços | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:14` | template:texto | Preço por empresa, não por pessoa. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:15` | template:texto | {…} dias grátis, sem cartão, no Essencial e no Profissional. O plano Empresa cobra ao contratar e a Implantação é sob orçamento, online ou presencial. Você troca de plano quando quiser. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:22` | template:texto | Pagamento por Pix, boleto ou cartão. O preço é mensal e vale para a empresa toda. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:28` | template:texto | Compare os planos | texto na tela | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:29` | template:macro | Recurso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:32` | template:macro | Comparação dos planos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:34` | template:texto | Projetos ativos | texto na tela | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:34` | template:macro | projetos ativos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:35` | template:texto | Pessoas | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:36` | template:texto | Preço por mês | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:36` | template:texto | Sob orçamento R$ {…} | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:37` | template:texto | Teste grátis de {…} dias, sem cartão | texto na tela | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:37` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:38` | template:texto | Verificação em duas etapas obrigatória para proprietários | texto na tela | antes: “Verificação em duas etapas obrigatória (MFA)” — sem sigla; escopo real | aplicado (texto atual) | alterado |
| public/precos | macro | `app/templates/public/precos.html:38` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:39` | template:texto | API para ligar a outros sistemas | texto na tela | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:39` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:40` | template:texto | Identidade visual da sua empresa | texto na tela | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:40` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:41` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:42` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | macro | `app/templates/public/precos.html:43` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:44` | template:texto | Modelos de etapas, histórico e exportação em planilha | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:44` | template:texto | Sim | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:53` | template:texto | Todos os planos incluem | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:55` | template:texto | Modelos de etapas com versões: os projetos antigos não mudam quando você edita o modelo. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:56` | template:texto | Histórico completo de cada registro, com quem registrou e quando. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:57` | template:texto | Exportação em planilha (CSV e XLSX), sempre disponível, até com a assinatura atrasada. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:58` | template:texto | Pagamento por Pix, boleto ou cartão. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:65` | template:texto | Perguntas frequentes | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:67` | template:texto | Como pago? | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:67` | template:texto | Depois do teste (Essencial ou Profissional), você escolhe o plano e paga por Pix, boleto ou cartão. A cobrança é mensal e por empresa, não por usuário. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:68` | template:texto | E se eu atrasar o pagamento? | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:68` | template:texto | Você tem 7 dias de carência com tudo funcionando. Depois, a empresa fica só para leitura: dá para ver e exportar tudo, mas não registrar. Seus dados nunca são apagados por atraso. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:69` | template:texto | Posso cancelar quando quiser? | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:69` | template:texto | Sim. Você cancela na tela de assinatura, sem multa, e continua com acesso até o fim do período pago. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:70` | template:texto | Emitem nota fiscal? | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:70` | template:texto | A nota fiscal de serviço segue a regra do seu município e do seu cadastro. Fale com a gente em | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:70` | template:texto | para combinar. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:77` | template:texto | Comece pelo teste grátis. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:78` | template:texto | {…} dias, sem cartão, nos planos Essencial e Profissional. | texto na tela | — | — | revisado — mantido |
| public/precos | texto | `app/templates/public/precos.html:79` | template:texto | Começar teste grátis | texto na tela | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:2` | template:macro | Política de privacidade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Quem somos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Dados que coletamos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Para que usamos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Com quem compartilhamos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Seus direitos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Segurança e retenção | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | macro | `app/templates/public/privacidade.html:3` | template:macro | Contato do encarregado (DPO) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:4` | template:texto | Política de privacidade · Teroz | texto na tela | antes: “Política de privacidade · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/privacidade | texto | `app/templates/public/privacidade.html:5` | template:texto | Como a Teroz trata dados pessoais conforme a LGPD: o que coletamos, para quê, com quem compartilhamos e como exercer seus direitos. Rascunho para revisão jurídica. | texto na tela | antes: “Como o Controle de Produção trata dados pessoais conforme a LGPD: o que coletamos, para quê, com quem compartilhamos e como exercer seus direitos. Rascunho para revisão jurídica.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/privacidade | texto | `app/templates/public/privacidade.html:8` | template:texto | 1. Quem somos | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:9` | template:texto | A Teroz é operada por uma empresa brasileira (razão social e CNPJ a preencher antes do lançamento). Somos controladores dos dados de conta e cobrança e operadores dos dados de produção que cada empresa-cliente registra. | texto na tela | antes: “O Controle de Produção é operado por uma empresa brasileira (razão social e CNPJ a preencher antes do lançamento). Somos controladores dos dados de conta e cobrança e operadores dos dados de produção que cada empresa-…” — concordância | aplicado (texto atual) | alterado |
| public/privacidade | texto | `app/templates/public/privacidade.html:12` | template:texto | 2. Dados que coletamos | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:13` | template:texto | Conta: nome, e-mail, senha (guardada só como hash) e vínculo com a empresa. Uso: quem registrou cada peça, quando e em qual subatividade. Cobrança: dados de faturamento da empresa, tratados pelo provedor de pagamento.… | texto na tela | antes: “Conta: nome, e-mail, senha (guardada só como hash) e vínculo com a empresa. Uso: quem registrou cada peça, quando e em qual atividade. Cobrança: dados de faturamento da empresa, tratados pelo provedor de pagamento. Té…” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| public/privacidade | texto | `app/templates/public/privacidade.html:16` | template:texto | 3. Para que usamos | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:17` | template:texto | Para prestar o serviço, autenticar acessos, calcular e exibir o andamento da produção, cobrar a assinatura, prevenir abuso e cumprir obrigações legais. Não vendemos dados pessoais. | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:20` | template:texto | 4. Com quem compartilhamos | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:21` | template:texto | Apenas com fornecedores necessários à operação: hospedagem, envio de e-mail e processamento de pagamentos. Cada fornecedor recebe o mínimo necessário. | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:24` | template:texto | 5. Seus direitos | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:25` | template:texto | Você pode pedir confirmação do tratamento, acesso, correção, portabilidade, eliminação e informações sobre compartilhamento, conforme a LGPD. Escreva para o contato abaixo. | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:28` | template:texto | 6. Segurança e retenção | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:29` | template:texto | Isolamos os dados de cada empresa, protegemos o acesso com senha e, opcionalmente, verificação em duas etapas, e mantemos os dados enquanto a conta existir. Ao excluir a empresa, os dados são apagados após um prazo de… | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:32` | template:texto | 7. Contato do encarregado (DPO) | texto na tela | — | — | revisado — mantido |
| public/privacidade | texto | `app/templates/public/privacidade.html:33` | template:texto | Fale com o encarregado pelo e-mail | texto na tela | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:2` | template:macro | Termos de uso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | O serviço | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Conta e acesso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Planos, pagamento e carência | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Seus dados | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Uso aceitável | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Responsabilidade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | macro | `app/templates/public/termos.html:3` | template:macro | Mudanças e contato | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:4` | template:texto | Termos de uso · Teroz | texto na tela | antes: “Termos de uso · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/termos | texto | `app/templates/public/termos.html:5` | template:texto | Termos de uso da Teroz: conta, planos, pagamento, carência, seus dados e responsabilidades. Rascunho para revisão jurídica. | texto na tela | antes: “Termos de uso do Controle de Produção: conta, planos, pagamento, carência, seus dados e responsabilidades. Rascunho para revisão jurídica.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| public/termos | texto | `app/templates/public/termos.html:8` | template:texto | 1. O serviço | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:9` | template:texto | A Teroz é um serviço web para acompanhar a produção por etapas e subatividades: progresso, unidades prontas, tempo restante e prazo em dias úteis. Ela é oferecida a empresas, por assinatura. | texto na tela | antes: “O Controle de Produção é um serviço web para acompanhar a produção por etapas e atividades: progresso, unidades concluídas, tempo restante e prazo em dias úteis. Ele é oferecido a empresas, por assinatura.” — concordância | aplicado (texto atual) | alterado |
| public/termos | texto | `app/templates/public/termos.html:12` | template:texto | 2. Conta e acesso | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:13` | template:texto | Quem cadastra a empresa vira proprietário e responde pelas pessoas que convidar. Cada pessoa usa o próprio acesso e mantém a senha em segredo. Avise-nos se suspeitar de uso indevido da conta. | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:16` | template:texto | 3. Planos, pagamento e carência | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:17` | template:texto | Há um período de teste gratuito, sem cartão. Depois dele, o uso depende de um plano pago, cobrado por empresa. Se o pagamento atrasar, há uma carência de 7 dias com o serviço normal; passada a carência, a empresa fica… | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:20` | template:texto | 4. Seus dados | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:21` | template:texto | Os dados de produção da empresa pertencem à empresa. Você pode exportá-los a qualquer momento. O tratamento de dados pessoais está descrito na | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:21` | template:texto | Política de privacidade | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:24` | template:texto | 5. Uso aceitável | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:25` | template:texto | Não use o serviço para atividade ilegal, para tentar acessar dados de outra empresa, nem para sobrecarregar o serviço ou testar a segurança dele sem autorização por escrito. | texto na tela | antes: “Não use o serviço para atividade ilegal, para tentar acessar dados de outra empresa, nem para sobrecarregar ou testar a segurança dele sem autorização por escrito.” — clareza | aplicado (texto atual) | alterado |
| public/termos | texto | `app/templates/public/termos.html:28` | template:texto | 6. Responsabilidade | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:29` | template:texto | Os cálculos de prazo são estimativas a partir dos números que a própria empresa registra. O serviço é entregue como está, e a responsabilidade é limitada ao valor pago nos últimos 12 meses, nos termos da lei. | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:32` | template:texto | 7. Mudanças e contato | texto na tela | — | — | revisado — mantido |
| public/termos | texto | `app/templates/public/termos.html:33` | template:texto | Podemos atualizar estes termos; avisaremos por e-mail antes de mudanças relevantes. Dúvidas: | texto na tela | — | — | revisado — mantido |

</details>

<details><summary><b>Entrar e conta</b> (264)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/account.py | flash | `app/blueprints/account.py:65` | backend:flash | A empresa exige verificação em duas etapas para proprietários. Ative para continuar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:95` | backend:flash | E-mail confirmado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:119` | backend:flash | Enviamos um novo link para {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:159` | backend:flash | Nome atualizado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:173` | backend:flash | Preferências de e-mail salvas. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:188` | backend:flash | Enviamos um link de confirmação para {…}. O e-mail só muda depois de confirmar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:211` | backend:flash | Senha trocada. As outras sessões foram encerradas. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:223` | backend:flash | Você saiu de todos os dispositivos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:243` | backend:flash | Confirme seu e-mail antes de ativar a verificação em duas etapas. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | append | `app/blueprints/account.py:297` | backend:append | Código inválido. Confira o horário do celular e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:327` | backend:flash | Uma empresa em que você tem o papel Proprietário exige a verificação em duas etapas: não dá para desativá-la. | confirmação ou aviso após ação | antes: “Uma empresa em que você é proprietário exige MFA: não dá para desativar.” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| blueprints/account.py | flash | `app/blueprints/account.py:334` | backend:flash | Verificação em duas etapas desativada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:337` | backend:flash | Senha ou código incorretos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:354` | backend:flash | Senha incorreta. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/account.py | flash | `app/blueprints/account.py:387` | backend:flash | Agora você está em {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/auth.py | valor | `app/blueprints/auth.py:23` | backend:valor | E-mail ou senha incorretos. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/auth.py | valor | `app/blueprints/auth.py:24` | backend:valor | Código inválido. Confira o aplicativo e tente de novo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/auth.py | valor | `app/blueprints/auth.py:25` | backend:valor | Se houver conta com esse e-mail, enviamos um link válido por 1 hora. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/auth.py | valor | `app/blueprints/auth.py:57` | backend:valor | Muitas tentativas. Tente de novo em {…} {…}. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/auth.py | flash | `app/blueprints/auth.py:115` | backend:flash | Se o cadastro estiver pendente, enviamos um novo link de confirmação. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/auth.py | flash | `app/blueprints/auth.py:191` | backend:flash | Entre de novo para continuar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/auth.py | flash | `app/blueprints/auth.py:223` | backend:flash | Você saiu. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/auth.py | flash | `app/blueprints/auth.py:253` | backend:flash | Senha trocada. Entre com a nova senha. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:58` | backend:flash | Convite enviado para {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:79` | backend:flash | Convite reenviado (vale por mais 7 dias). | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:89` | backend:flash | Convite cancelado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/team.py | _page | `app/blueprints/team.py:99` | backend:_page | Escolha um papel válido. | mensagem do backend | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:104` | backend:flash | Papel de {…} atualizado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:116` | backend:flash | {…} perdeu o acesso a esta empresa. | confirmação ou aviso após ação | antes: “{…} foi desativado e perdeu o acesso.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/team.py | flash | `app/blueprints/team.py:128` | backend:flash | O acesso de {…} voltou. | confirmação ou aviso após ação | antes: “{…} foi reativado.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/team.py | _page | `app/blueprints/team.py:137` | backend:_page | Exigir a verificação em duas etapas dos proprietários é um recurso do plano Empresa. | mensagem do backend | antes: “Exigir MFA é um recurso do plano Empresa.” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| blueprints/team.py | _page | `app/blueprints/team.py:140` | backend:_page | Ative a verificação em duas etapas na sua conta antes de exigir dos proprietários. | mensagem do backend | — | — | revisado — mantido |
| blueprints/team.py | flash | `app/blueprints/team.py:147` | backend:flash | Verificação em duas etapas | confirmação ou aviso após ação | antes: “Exigência de MFA para proprietários” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| blueprints/team.py | flash | `app/blueprints/team.py:147` | backend:flash | agora é obrigatória para os proprietários. | confirmação ou aviso após ação | antes: “Bem-vindo a {…}!” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/team.py | flash | `app/blueprints/team.py:147` | backend:flash | deixou de ser obrigatória para os proprietários. | confirmação ou aviso após ação | antes: “Conta criada. Bem-vindo a {…}!” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/team.py | flash | `app/blueprints/team.py:177` | backend:flash | Você agora faz parte de {…}. | confirmação ou aviso após ação | texto novo na revisão | aplicado (texto atual) | incluído |
| blueprints/team.py | flash | `app/blueprints/team.py:196` | backend:flash | Conta criada. Você agora faz parte de {…}. | confirmação ou aviso após ação | texto novo na revisão | aplicado (texto atual) | incluído |
| forms_accounts.py | valor | `app/forms_accounts.py:25` | backend:valor | Nova senha | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| forms_accounts.py | valor | `app/forms_accounts.py:29` | backend:valor | Repita a nova senha | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:30` | backend:formulário | As senhas não conferem. | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | _email_field | `app/forms_accounts.py:55` | backend:_email_field | Novo e-mail | mensagem do backend | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:56` | backend:formulário | Senha atual | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:62` | backend:formulário | Subatividade atribuída a mim | rótulo ou validação de campo | antes: “Atividade atribuída a mim” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| forms_accounts.py | formulário | `app/forms_accounts.py:63` | backend:formulário | Alertas de produção | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:64` | backend:formulário | Relatório semanal | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:68` | backend:formulário | Senha atual | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:74` | backend:formulário | Código de 6 dígitos | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:78` | backend:formulário | Senha atual | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:79` | backend:formulário | Código do aplicativo ou de recuperação | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:83` | backend:formulário | Senha atual | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | valor | `app/forms_accounts.py:87` | backend:valor | Operador — registra peças | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| forms_accounts.py | valor | `app/forms_accounts.py:88` | backend:valor | Supervisor — monta projetos e exporta | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| forms_accounts.py | valor | `app/forms_accounts.py:89` | backend:valor | Proprietário — tudo, inclusive assinatura | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:103` | backend:formulário | Seu nome | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | _confirm | `app/forms_accounts.py:105` | backend:_confirm | Repita a senha | mensagem do backend | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:118` | backend:formulário | Sua senha | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_accounts.py | formulário | `app/forms_accounts.py:119` | backend:formulário | Digite o nome da empresa para confirmar | rótulo ou validação de campo | — | — | revisado — mantido |
| models/accounts.py | valor | `app/models/accounts.py:43` | backend:valor | role IN ('owner', 'supervisor', 'operator') | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:130` | backend:send_template | Tentativa de cadastro com o seu e-mail | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:151` | backend:send_template | Confirme seu e-mail | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:151` | backend:send_template | Confirme seu novo e-mail | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:205` | backend:erro | Este e-mail já está em uso por outra conta. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:208` | backend:send_template | Seu e-mail de acesso foi trocado | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:219` | backend:erro | Este e-mail já está em uso por outra conta. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:234` | backend:send_template | Redefinir a senha | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:274` | backend:send_template | Sua senha foi trocada | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:331` | backend:erro | Senha atual incorreta. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:335` | backend:send_template | Sua senha foi trocada | assunto do e-mail | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:342` | backend:erro | Senha atual incorreta. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:346` | backend:erro | Confirme o seu e-mail atual antes de trocar. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:349` | backend:erro | Este já é o seu e-mail. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | send_template | `app/services/accounts.py:412` | backend:send_template | Convite para {…} na Teroz | assunto do e-mail | antes: “Convite para {…} no Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| services/accounts.py | erro | `app/services/accounts.py:425` | backend:erro | Você não pode convidar alguém com esse papel. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:432` | backend:erro | Esta pessoa já faz parte da empresa. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:435` | backend:erro | Esta pessoa foi desativada. Só o proprietário pode convidá-la de novo. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:443` | backend:erro | Você não pode alterar este convite. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:465` | backend:erro | Este convite não está mais pendente. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:467` | backend:erro | Você não pode alterar este convite. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:480` | backend:erro | Este convite não está mais pendente. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:482` | backend:erro | Você não pode alterar este convite. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:517` | backend:erro | Este convite já foi usado. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:526` | backend:erro | Você já faz parte desta empresa. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:533` | backend:erro | Este convite não pode reativar o seu acesso. Fale com o proprietário da empresa. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:564` | backend:erro | Este convite foi enviado para outro e-mail. Saia e entre com a conta certa. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:573` | backend:erro | Já existe conta com este e-mail. Entre para aceitar o convite. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:582` | backend:erro | Já existe conta com este e-mail. Entre para aceitar o convite. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:615` | backend:erro | A empresa precisa de pelo menos um proprietário ativo. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:620` | backend:erro | Papel inválido. | mensagem de erro | — | — | revisado — mantido |
| services/accounts.py | erro | `app/services/accounts.py:624` | backend:erro | Acesso de suporte não pode virar proprietário. | mensagem de erro | — | — | revisado — mantido |
| services/mfa.py | save | `app/services/mfa.py:103` | backend:save | QR code da verificação em duas etapas | mensagem do backend | antes: “Controle de Produção” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| account/companies | texto | `app/templates/account/companies.html:5` | template:texto | Trocar de empresa · Teroz | texto na tela | antes: “Trocar de empresa · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/companies | texto | `app/templates/account/companies.html:8` | template:texto | Suas empresas | texto na tela | — | — | revisado — mantido |
| account/companies | macro | `app/templates/account/companies.html:16` | template:macro | Atual | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/companies | macro | `app/templates/account/companies.html:21` | template:macro | Entrar nesta empresa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | texto | `app/templates/account/confirm.html:4` | template:texto | Confirmar e-mail · Teroz | texto na tela | antes: “Confirmar e-mail · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/confirm | texto | `app/templates/account/confirm.html:9` | template:texto | Confirmar e-mail | texto na tela | — | — | revisado — mantido |
| account/confirm | texto | `app/templates/account/confirm.html:13` | template:texto | Toque no botão para confirmar o seu endereço de e-mail. | texto na tela | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:16` | template:macro | Confirmar e-mail | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:19` | template:macro | Este link venceu. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:19` | template:macro | Links de confirmação valem 24 horas. Entre e peça outro. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:19` | template:macro | Entrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:21` | template:macro | Este link não vale mais. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:21` | template:macro | Ele já foi usado ou está incompleto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm | macro | `app/templates/account/confirm.html:21` | template:macro | Entrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | texto | `app/templates/account/confirm_required.html:4` | template:texto | Confirme seu e-mail · Teroz | texto na tela | antes: “Confirme seu e-mail · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/confirm_required | texto | `app/templates/account/confirm_required.html:7` | template:texto | Confirme seu e-mail | texto na tela | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:11` | template:macro | Seu acesso está pausado até confirmar o e-mail. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:11` | template:macro | Já se passaram 7 dias desde o cadastro. Confirme | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:11` | template:macro | para continuar. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:13` | template:macro | Falta confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:15` | template:macro | E-mail confirmado. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | macro | `app/templates/account/confirm_required.html:20` | template:macro | Reenviar e-mail de confirmação | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/confirm_required | texto | `app/templates/account/confirm_required.html:23` | template:texto | Trocar o e-mail no perfil | texto na tela | — | — | revisado — mantido |
| account/mfa_codes | texto | `app/templates/account/mfa_codes.html:5` | template:texto | Códigos de recuperação · Teroz | texto na tela | antes: “Códigos de recuperação · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/mfa_codes | texto | `app/templates/account/mfa_codes.html:8` | template:texto | Códigos de recuperação | texto na tela | — | — | revisado — mantido |
| account/mfa_codes | macro | `app/templates/account/mfa_codes.html:11` | template:macro | Guarde estes códigos agora. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/mfa_codes | macro | `app/templates/account/mfa_codes.html:11` | template:macro | Eles não aparecem de novo. Cada um vale uma vez, se você perder o celular. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/mfa_codes | macro | `app/templates/account/mfa_codes.html:17` | template:macro | Pronto, guardei | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/mfa_setup | texto | `app/templates/account/mfa_setup.html:5` | template:texto | Ativar verificação em duas etapas · Teroz | texto na tela | antes: “Ativar verificação em duas etapas · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/mfa_setup | texto | `app/templates/account/mfa_setup.html:9` | template:texto | Verificação em duas etapas | texto na tela | — | — | revisado — mantido |
| account/mfa_setup | texto | `app/templates/account/mfa_setup.html:13` | template:texto | Abra o aplicativo autenticador no celular e leia o QR code. | texto na tela | — | — | revisado — mantido |
| account/mfa_setup | texto | `app/templates/account/mfa_setup.html:14` | template:texto | Ou digite a chave: | texto na tela | — | — | revisado — mantido |
| account/mfa_setup | texto | `app/templates/account/mfa_setup.html:15` | template:texto | Digite o código de 6 dígitos que aparece no aplicativo. | texto na tela | — | — | revisado — mantido |
| account/mfa_setup | alt | `app/templates/account/mfa_setup.html:17` | template:alt | QR code para o aplicativo autenticador | descrição de imagem | — | — | revisado — mantido |
| account/mfa_setup | macro | `app/templates/account/mfa_setup.html:21` | template:macro | Ativar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:7` | template:texto | Perfil · Teroz | texto na tela | antes: “Perfil · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| account/profile | texto | `app/templates/account/profile.html:11` | template:texto | Perfil | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:16` | template:texto | Nome | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:20` | template:macro | Salvar nome | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:25` | template:texto | E-mail | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:27` | template:macro | Confirmado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:27` | template:macro | Não confirmado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:29` | template:texto | Reenviar confirmação | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:33` | template:macro | Enviamos um link para o novo endereço; o e-mail só muda depois de confirmar. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:35` | template:macro | Trocar e-mail | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:40` | template:texto | Senha | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:44` | template:macro | Mín. 10 caracteres. As outras sessões serão encerradas. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:46` | template:macro | Trocar senha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:51` | template:texto | Verificação em duas etapas | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:53` | template:texto | {…} Restam {…} códigos de recuperação. | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:53` | template:macro | Ativa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:57` | template:texto | Senha atual | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:60` | template:macro | Gerar novos códigos de recuperação | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:65` | template:texto | Senha atual | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:69` | template:texto | Código do aplicativo ou de recuperação | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:72` | template:macro | Desativar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:75` | template:texto | Proteja a conta com um código do celular (Google Authenticator, Authy, 1Password…). | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:77` | template:macro | Ativar verificação em duas etapas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:79` | template:texto | Confirme seu e-mail para poder ativar. | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:85` | template:texto | Notificações por e-mail | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:89` | template:texto | Quero receber | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:90` | template:macro | Subatividade atribuída a mim (com o link) | rótulo, botão ou ajuda de componente | antes: “Atividade atribuída a mim (com o link)” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| account/profile | macro | `app/templates/account/profile.html:90` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:91` | template:macro | Alertas de produção: prazo em risco, atraso previsto, etapa parada, peça atrasada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:91` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:92` | template:macro | Relatório semanal com planilha (XLSX) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:92` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:93` | template:texto | Alertas e relatório semanal só chegam a supervisores e proprietários. Vale para todas as suas empresas. | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:95` | template:macro | Salvar preferências | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:100` | template:texto | Sessões | texto na tela | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:101` | template:texto | “Sair” encerra só este aparelho. Use o botão abaixo se perdeu um celular ou entrou num computador de outra pessoa. | texto na tela | — | — | revisado — mantido |
| account/profile | macro | `app/templates/account/profile.html:104` | template:macro | Sair de todos os dispositivos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| account/profile | texto | `app/templates/account/profile.html:107` | template:texto | Trocar de empresa | texto na tela | — | — | revisado — mantido |
| auth/forgot | texto | `app/templates/auth/forgot.html:5` | template:texto | Esqueci a senha · Teroz | texto na tela | antes: “Esqueci a senha · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/forgot | texto | `app/templates/auth/forgot.html:10` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| auth/forgot | texto | `app/templates/auth/forgot.html:11` | template:texto | Esqueci a senha | texto na tela | — | — | revisado — mantido |
| auth/forgot | texto | `app/templates/auth/forgot.html:12` | template:texto | Enviaremos um link para criar uma nova. | texto na tela | — | — | revisado — mantido |
| auth/forgot | macro | `app/templates/auth/forgot.html:16` | template:macro | Enviar link | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/login | texto | `app/templates/auth/login.html:5` | template:texto | Entrar · Teroz | texto na tela | antes: “Entrar · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/login | texto | `app/templates/auth/login.html:10` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| auth/login | macro | `app/templates/auth/login.html:19` | template:macro | Entrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/login | texto | `app/templates/auth/login.html:21` | template:texto | Esqueci a senha | texto na tela | — | — | revisado — mantido |
| auth/login | texto | `app/templates/auth/login.html:23` | template:texto | Ainda não tem conta? | texto na tela | — | — | revisado — mantido |
| auth/login | texto | `app/templates/auth/login.html:23` | template:texto | Cadastre a empresa | texto na tela | — | — | revisado — mantido |
| auth/login_mfa | texto | `app/templates/auth/login_mfa.html:5` | template:texto | Verificação em duas etapas · Teroz | texto na tela | antes: “Verificação em duas etapas · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/login_mfa | texto | `app/templates/auth/login_mfa.html:10` | template:texto | Verificação em duas etapas | texto na tela | — | — | revisado — mantido |
| auth/login_mfa | texto | `app/templates/auth/login_mfa.html:11` | template:texto | Digite o código de 6 dígitos do aplicativo autenticador ou um código de recuperação. | texto na tela | — | — | revisado — mantido |
| auth/login_mfa | macro | `app/templates/auth/login_mfa.html:18` | template:macro | Confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/login_mfa | texto | `app/templates/auth/login_mfa.html:21` | template:texto | Voltar para Entrar | texto na tela | — | — | revisado — mantido |
| auth/reset | texto | `app/templates/auth/reset.html:5` | template:texto | Nova senha · Teroz | texto na tela | antes: “Nova senha · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/reset | texto | `app/templates/auth/reset.html:10` | template:texto | Criar nova senha | texto na tela | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:15` | template:macro | Mín. 10 caracteres. As outras sessões serão encerradas. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:17` | template:macro | Salvar nova senha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:20` | template:macro | Este link venceu. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:20` | template:macro | Links de troca de senha valem 1 hora. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:20` | template:macro | Pedir outro | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:22` | template:macro | Este link não vale mais. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:22` | template:macro | Ele já foi usado ou está incompleto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/reset | macro | `app/templates/auth/reset.html:22` | template:macro | Pedir outro | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:5` | template:texto | Cadastrar empresa · Teroz | texto na tela | antes: “Cadastrar empresa · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/signup | texto | `app/templates/auth/signup.html:12` | template:texto | Comece o teste grátis | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:13` | template:texto | 14 dias no Profissional · sem cartão | texto na tela | — | — | revisado — mantido |
| auth/signup | macro | `app/templates/auth/signup.html:20` | template:macro | E-mail de trabalho | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup | macro | `app/templates/auth/signup.html:21` | template:macro | Mín. 10 caracteres. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup | macro | `app/templates/auth/signup.html:23` | template:macro | Criar conta | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:26` | template:texto | Já tem conta? | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:26` | template:texto | Entrar | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:29` | template:texto | O que você ganha no teste | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:31` | template:texto | Unidades e horas que faltam | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:31` | template:texto | por lote, calculadas a cada registro. | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:32` | template:texto | Prazo em dias úteis | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:32` | template:texto | com feriados e a jornada da equipe. | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:33` | template:texto | Registro pelo celular | texto na tela | — | — | revisado — mantido |
| auth/signup | texto | `app/templates/auth/signup.html:33` | template:texto | : digite o total de peças prontas e pronto, direto do chão de fábrica. | texto na tela | antes: “em 2 toques, direto do chão de fábrica.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| auth/signup_done | texto | `app/templates/auth/signup_done.html:4` | template:texto | Confirme seu e-mail · Teroz | texto na tela | antes: “Confirme seu e-mail · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| auth/signup_done | texto | `app/templates/auth/signup_done.html:9` | template:texto | Confirme seu e-mail | texto na tela | — | — | revisado — mantido |
| auth/signup_done | macro | `app/templates/auth/signup_done.html:10` | template:macro | Enviamos um e-mail para | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup_done | macro | `app/templates/auth/signup_done.html:11` | template:macro | Entrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup_done | macro | `app/templates/auth/signup_done.html:14` | template:macro | Reenviar e-mail | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| auth/signup_done | texto | `app/templates/auth/signup_done.html:17` | template:texto | E-mail errado? | texto na tela | — | — | revisado — mantido |
| auth/signup_done | texto | `app/templates/auth/signup_done.html:17` | template:texto | Cadastrar de novo | texto na tela | — | — | revisado — mantido |
| team/accept | texto | `app/templates/team/accept.html:5` | template:texto | Convite · Teroz | texto na tela | antes: “Convite · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| team/accept | texto | `app/templates/team/accept.html:11` | template:texto | Convite | texto na tela | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:13` | template:macro | Este convite venceu. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:13` | template:macro | Convites valem 7 dias. Peça a quem convidou para reenviar. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:15` | template:macro | Este convite não vale mais. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:15` | template:macro | Ele já foi usado, foi cancelado ou o link está incompleto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | texto | `app/templates/team/accept.html:18` | template:texto | Entrar em {…} | texto na tela | — | — | revisado — mantido |
| team/accept | texto | `app/templates/team/accept.html:19` | template:texto | Convite para {…} como {…}. | texto na tela | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:23` | template:macro | Você entrou com outra conta. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:23` | template:macro | Este convite é para | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:27` | template:macro | Aceitar convite | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | texto | `app/templates/team/accept.html:31` | template:texto | Você já tem conta com este e-mail. Entre para aceitar. | texto na tela | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:32` | template:macro | Entrar e aceitar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:38` | template:macro | Mín. 10 caracteres. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/accept | macro | `app/templates/team/accept.html:40` | template:macro | Criar conta e entrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:10` | template:texto | Usuários · Teroz | texto na tela | antes: “Usuários · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| team/users | texto | `app/templates/team/users.html:15` | template:texto | Usuários | texto na tela | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:16` | template:texto | {…} de {…} usuários (convites pendentes contam) | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:18` | template:macro | Convidar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:21` | template:macro | Uso do plano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:28` | template:macro | Nome | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:28` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:28` | template:macro | , class_= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:32` | template:texto | (você) | texto na tela | — | — | revisado — mantido |
| team/users | data-label | `app/templates/team/users.html:33` | template:data-label | E-mail | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| team/users | data-label | `app/templates/team/users.html:34` | template:data-label | Papel | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:34` | template:macro | Desativado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | data-label | `app/templates/team/users.html:35` | template:data-label | Último acesso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| team/users | data-label | `app/templates/team/users.html:36` | template:data-label | Duas etapas | rótulo da coluna no modo cartão (celular) | texto novo na revisão | aplicado (texto atual) | incluído |
| team/users | macro | `app/templates/team/users.html:36` | template:macro | Sim | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:36` | template:macro | Não | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | data-label | `app/templates/team/users.html:37` | template:data-label | Ações | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:43` | template:texto | Papel de {…} | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:45` | template:macro | Operador | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:45` | template:macro | Supervisor | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:45` | template:macro | Proprietário | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:49` | template:macro | Mudar papel | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:52` | template:macro | Desativar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:57` | template:macro | Reativar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:69` | template:texto | Convites pendentes | texto na tela | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:75` | template:texto | Enviado {…} · vence {…} | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:80` | template:macro | Reenviar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:84` | template:macro | Cancelar convite | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:92` | template:texto | Nenhum convite pendente. | texto na tela | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:97` | template:texto | Convidar pessoa | texto na tela | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:102` | template:texto | Papel | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:110` | template:macro | Enviar convite | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:116` | template:texto | Segurança | texto na tela | — | — | revisado — mantido |
| team/users | texto | `app/templates/team/users.html:118` | template:texto | Exigir verificação em duas etapas dos proprietários: | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:122` | template:macro | Desligar exigência | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:122` | template:macro | Exigir dos proprietários | rótulo, botão ou ajuda de componente | antes: “Exigir MFA dos proprietários” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| team/users | texto | `app/templates/team/users.html:125` | template:texto | Exigir verificação em duas etapas dos proprietários é um recurso do plano Empresa. | texto na tela | — | — | revisado — mantido |
| team/users | macro | `app/templates/team/users.html:129` | template:macro | Desativar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>E-mail</b> (234)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| services/email.py | post | `app/services/email.py:117` | backend:post | Bearer {…} | mensagem do backend | — | — | revisado — mantido |
| services/email.py | error | `app/services/email.py:122` | backend:error | Resend: falha de rede (%s) | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:123` | backend:erro | falha ao enviar e-mail | mensagem de erro | — | — | revisado — mantido |
| services/email.py | error | `app/services/email.py:125` | backend:error | Resend: HTTP %s ao enviar '%s' | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:126` | backend:erro | falha ao enviar e-mail | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:137` | backend:erro | MAIL_BACKEND=resend exige RESEND_API_KEY. | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:140` | backend:erro | MAIL_BACKEND desconhecido: {…} | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:159` | backend:erro | outbox só existe no backend console | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:170` | backend:erro | APP_BASE_URL é obrigatório para montar links de e-mail fora de development/test. | mensagem de erro | — | — | revisado — mantido |
| services/email.py | error | `app/services/email.py:220` | backend:error | falha inesperada ao enviar e-mail '%s' (%s) | mensagem de erro | — | — | revisado — mantido |
| services/email.py | erro | `app/services/email.py:221` | backend:erro | falha ao enviar e-mail | mensagem de erro | — | — | revisado — mantido |
| services/email.py | error | `app/services/email.py:239` | backend:error | falha inesperada ao enviar e-mail '%s' (%s) | mensagem de erro | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:25` | backend:valor | Nova requisição de identidade visual | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:26` | backend:valor | Nova subatividade atribuída a você | valor exibido (rótulo, opção, situação) | antes: “Nova atividade atribuída a você” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/notifications.py | valor | `app/services/notifications.py:157` | backend:valor | Relatório semanal de produção | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/notifications.py | append | `app/services/notifications.py:224` | backend:append | Unidades concluídas | mensagem do backend | — | — | revisado — mantido |
| services/notifications.py | append | `app/services/notifications.py:226` | backend:append | Peças na semana | mensagem do backend | — | — | revisado — mantido |
| services/notifications.py | append | `app/services/notifications.py:227` | backend:append | Horas que faltam | mensagem do backend | — | — | revisado — mantido |
| services/notifications.py | append | `app/services/notifications.py:229` | backend:append | Término previsto | mensagem do backend | — | — | revisado — mantido |
| services/notifications.py | append | `app/services/notifications.py:230` | backend:append | Atraso previsto (dias úteis) | mensagem do backend | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:234` | backend:valor | Etapas aguardando peça | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:261` | backend:valor | Pessoa removida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:262` | backend:valor | Peças (saldo) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/notifications.py | valor | `app/services/notifications.py:266` | backend:valor | Dias com lançamento | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| emails/_base | content | `app/templates/emails/_base.html:6` | e-mail:content | width=device-width, initial-scale=1 | metadado do e-mail | — | — | revisado — mantido |
| emails/_base | content | `app/templates/emails/_base.html:7` | e-mail:content | light dark | metadado do e-mail | — | — | revisado — mantido |
| emails/_base | texto | `app/templates/emails/_base.html:14` | e-mail:texto | Teroz | corpo do e-mail | antes: “Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/_base | texto | `app/templates/emails/_base.txt:1` | e-mail:texto | Teroz | corpo do e-mail | antes: “Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/_base | texto | `app/templates/emails/_base.txt:7` | e-mail:texto | Você recebeu esta mensagem por causa de uma ação na sua conta da Teroz. | corpo do e-mail | antes: “Você recebeu esta mensagem por causa de uma ação na sua conta do Controle de Produção.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/_base | texto | `app/templates/emails/_base.txt:8` | e-mail:texto | Se não foi você, ignore este e-mail ou troque a senha. Não responda: esta caixa não é lida. | corpo do e-mail | — | — | revisado — mantido |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.html:3` | e-mail:texto | Olá, {…}. Você agora é responsável por uma subatividade na empresa {…}: | corpo do e-mail | antes: “Olá, {…}. Você agora é responsável por uma atividade na empresa {…}:” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.html:7` | e-mail:texto | Abrir a subatividade | corpo do e-mail | antes: “Abrir a atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.html:8` | e-mail:texto | Se o botão não abrir, copie o endereço: {…}. Se você participa de mais de uma empresa, entre na {…} antes. | corpo do e-mail | — | — | revisado — mantido |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:2` | e-mail:texto | Olá, {…}. Você agora é responsável por uma subatividade na empresa {…}: | corpo do e-mail | antes: “Olá, {…}. Você agora é responsável por uma atividade na empresa {…}:” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:5` | e-mail:texto | Etapa: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:6` | e-mail:texto | Projeto: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:8` | e-mail:texto | Abrir a subatividade: {…} | corpo do e-mail | antes: “Abrir a atividade: {…}” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:9` | e-mail:texto | Se você participa de mais de uma empresa, entre na {…} antes. | corpo do e-mail | — | — | revisado — mantido |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:10` | e-mail:texto | Você recebe este aviso porque uma subatividade foi atribuída a você. | corpo do e-mail | antes: “Você recebe este aviso porque uma atividade foi atribuída a você.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:11` | e-mail:texto | Para não receber mais, desligue "Subatividade atribuída a mim" em {…} | corpo do e-mail | antes: “Para não receber mais, desligue "Atividade atribuída a mim" em {…}” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| emails/activity_assigned | texto | `app/templates/emails/activity_assigned.txt:12` | e-mail:texto | Não responda: esta caixa não é lida. | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.html:3` | e-mail:texto | Olá, {…}. Estes são os alertas de hoje da empresa {…}: | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.html:6` | e-mail:texto | Abrir o projeto | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.html:9` | e-mail:texto | Ver todos os alertas | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:2` | e-mail:texto | Olá, {…}. Estes são os alertas de hoje da empresa {…}: | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:5` | e-mail:texto | Abrir o projeto: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:7` | e-mail:texto | Ver todos os alertas: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:8` | e-mail:texto | Você recebe este resumo porque é supervisor ou proprietário na empresa {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:9` | e-mail:texto | Para não receber mais, desligue "Alertas de produção" em {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/alerts_digest | texto | `app/templates/emails/alerts_digest.txt:10` | e-mail:texto | Não responda: esta caixa não é lida. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.html:3` | e-mail:texto | A troca do plano | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.html:3` | e-mail:texto | para o | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.html:3` | e-mail:texto | da empresa {…} não foi aplicada: o uso atual não cabe no plano menor. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.html:5` | e-mail:texto | Vocês continuam no plano {…}, com o mesmo valor. Para rebaixar, ajuste o uso e peça a troca de novo. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.html:6` | e-mail:texto | Ver assinatura | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.txt:2` | e-mail:texto | A troca do plano {…} para o {…} da empresa {…} não foi aplicada: o uso atual não cabe no plano menor. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_downgrade_canceled | texto | `app/templates/emails/billing_downgrade_canceled.txt:6` | e-mail:texto | Vocês continuam no plano {…}, com o mesmo valor. Para rebaixar, ajuste o uso e peça a troca de novo: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:3` | e-mail:texto | O pagamento da assinatura da Teroz da empresa | corpo do e-mail | antes: “O pagamento da assinatura do Controle de Produção da empresa” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:3` | e-mail:texto | venceu e ainda não foi identificado. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:4` | e-mail:texto | Você tem até | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:4` | e-mail:texto | para regularizar. Depois disso a conta entra em modo leitura: dá para ver e exportar tudo, mas não registrar. Nenhum dado é apagado. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:5` | e-mail:texto | Pagar por Pix, boleto ou cartão | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.html:6` | e-mail:texto | Se já pagou, desconsidere esta mensagem (boleto pode levar até 3 dias úteis para compensar). | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.txt:2` | e-mail:texto | O pagamento da assinatura da Teroz da empresa {…} venceu e ainda não foi identificado. | corpo do e-mail | antes: “O pagamento da assinatura do Controle de Produção da empresa {…} venceu e ainda não foi identificado.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.txt:4` | e-mail:texto | Você tem até {…} para regularizar. Depois disso a conta entra em modo leitura: dá para ver e exportar tudo, mas não registrar. Nenhum dado é apagado. | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.txt:6` | e-mail:texto | Pague por Pix, boleto ou cartão: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/billing_past_due | texto | `app/templates/emails/billing_past_due.txt:8` | e-mail:texto | Se já pagou, desconsidere esta mensagem (boleto pode levar até 3 dias úteis para compensar). | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.html:4` | e-mail:texto | A ligação com a equipe para falar da identidade visual da sua empresa está marcada para {…} (horário de Brasília), com duração de {…} minutos. | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.html:5` | e-mail:texto | Precisa remarcar ou cancelar? Peça pela tela da ligação: | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.html:6` | e-mail:texto | Ver a ligação | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.html:7` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.txt:4` | e-mail:texto | A ligação com a equipe para falar da identidade visual da sua empresa está marcada para {…} (horário de Brasília), com duração de {…} minutos. | corpo do e-mail | — | — | revisado — mantido |
| emails/call_booked | texto | `app/templates/emails/call_booked.txt:6` | e-mail:texto | Precisa remarcar ou cancelar? Peça pela tela da ligação: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.html:3` | e-mail:texto | Olá , {…} . | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.html:5` | e-mail:texto | A equipe cancelou a ligação de {…} (horário de Brasília). Se quiser outro horário, escolha um na tela da ligação. | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.html:7` | e-mail:texto | A equipe manteve a ligação de {…} (horário de Brasília). Se precisar de outra mudança, peça pela tela da ligação. | corpo do e-mail | antes: “A equipe manteve a ligação de {…} (horário de Brasília). Se precisar, responda a este e-mail.” — o rodapé diz que a caixa não é lida | aplicado (texto atual) | alterado |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.html:9` | e-mail:texto | Ver a ligação | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.html:10` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.txt:2` | e-mail:texto | Olá , {…} . | corpo do e-mail | — | — | revisado — mantido |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.txt:4` | e-mail:texto | A equipe cancelou a ligação de {…} (horário de Brasília). Se quiser outro horário, escolha um na tela da ligação. A equipe manteve a ligação de {…} (horário de Brasília). Se precisar de outra mudança, peça pela tela d… | corpo do e-mail | antes: “A equipe cancelou a ligação de {…} (horário de Brasília). Se quiser outro horário, escolha um na tela da ligação. A equipe manteve a ligação de {…} (horário de Brasília). Se precisar, responda a este e-mail.” — o rodapé diz que a caixa não é lida | aplicado (texto atual) | alterado |
| emails/call_change_decided | texto | `app/templates/emails/call_change_decided.txt:6` | e-mail:texto | Ver a ligação: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.html:4` | e-mail:texto | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso à Teroz. | corpo do e-mail | antes: “Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso ao Controle de Produção.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.html:6` | e-mail:texto | Confirmar e-mail | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.html:7` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.txt:4` | e-mail:texto | Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso à Teroz. | corpo do e-mail | antes: “Para trocar o e-mail da sua conta para este endereço, confirme pelo link abaixo. Confirme seu e-mail para manter o acesso ao Controle de Produção.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.txt:5` | e-mail:texto | O link vale 24 horas e só pode ser usado uma vez. | corpo do e-mail | — | — | revisado — mantido |
| emails/confirm_email | texto | `app/templates/emails/confirm_email.txt:7` | e-mail:texto | Confirmar e-mail: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_cancelled | texto | `app/templates/emails/deletion_cancelled.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_cancelled | texto | `app/templates/emails/deletion_cancelled.html:4` | e-mail:texto | A exclusão da empresa {…} foi cancelada. Nenhum dado foi apagado. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_cancelled | texto | `app/templates/emails/deletion_cancelled.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_cancelled | texto | `app/templates/emails/deletion_cancelled.txt:4` | e-mail:texto | A exclusão da empresa {…} foi cancelada. Nenhum dado foi apagado. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.html:4` | e-mail:texto | Foi pedida a exclusão da empresa {…} na Teroz. Todos os dados serão apagados definitivamente em | corpo do e-mail | antes: “Foi pedida a exclusão da empresa {…} no Controle de Produção. Todos os dados serão apagados definitivamente em” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.html:5` | e-mail:texto | Até lá tudo continua funcionando e qualquer proprietário pode cancelar em Privacidade e dados. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.html:6` | e-mail:texto | Se você não reconhece este pedido, entre e cancele agora e troque a sua senha. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.txt:4` | e-mail:texto | Foi pedida a exclusão da empresa {…} na Teroz. | corpo do e-mail | antes: “Foi pedida a exclusão da empresa {…} no Controle de Produção.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.txt:5` | e-mail:texto | Todos os dados serão apagados definitivamente em {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.txt:7` | e-mail:texto | Até lá tudo continua funcionando e qualquer proprietário pode cancelar em Privacidade e dados. | corpo do e-mail | — | — | revisado — mantido |
| emails/deletion_requested | texto | `app/templates/emails/deletion_requested.txt:8` | e-mail:texto | Se você não reconhece este pedido, entre e cancele agora e troque a sua senha. | corpo do e-mail | — | — | revisado — mantido |
| emails/email_changed | texto | `app/templates/emails/email_changed.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/email_changed | texto | `app/templates/emails/email_changed.html:4` | e-mail:texto | O e-mail de acesso da sua conta foi trocado para {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/email_changed | texto | `app/templates/emails/email_changed.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/email_changed | texto | `app/templates/emails/email_changed.txt:4` | e-mail:texto | O e-mail de acesso da sua conta foi trocado para {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/email_changed | texto | `app/templates/emails/email_changed.txt:5` | e-mail:texto | Se não foi você, peça uma nova senha agora e escreva para o contato indicado no site. | corpo do e-mail | antes: “Se não foi você, responda ao suporte imediatamente.” — o rodapé diz que a caixa não é lida | aplicado (texto atual) | alterado |
| emails/invite | texto | `app/templates/emails/invite.html:3` | e-mail:texto | {…} convidou você para a empresa {…} na Teroz, como {…}. | corpo do e-mail | antes: “{…} convidou você para a empresa {…} no Controle de Produção, como {…}.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/invite | texto | `app/templates/emails/invite.html:4` | e-mail:texto | O convite vale 7 dias e só pode ser usado uma vez. | corpo do e-mail | — | — | revisado — mantido |
| emails/invite | texto | `app/templates/emails/invite.html:5` | e-mail:texto | Aceitar convite | corpo do e-mail | — | — | revisado — mantido |
| emails/invite | texto | `app/templates/emails/invite.html:6` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/invite | texto | `app/templates/emails/invite.txt:2` | e-mail:texto | {…} convidou você para a empresa {…} na Teroz, como {…}. | corpo do e-mail | antes: “{…} convidou você para a empresa {…} no Controle de Produção, como {…}.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/invite | texto | `app/templates/emails/invite.txt:4` | e-mail:texto | O convite vale 7 dias e só pode ser usado uma vez. | corpo do e-mail | — | — | revisado — mantido |
| emails/invite | texto | `app/templates/emails/invite.txt:6` | e-mail:texto | Aceitar convite: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.html:4` | e-mail:texto | A senha da sua conta foi trocada e as outras sessões foram encerradas. | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.html:6` | e-mail:texto | Pedir nova senha | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.html:7` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.txt:4` | e-mail:texto | A senha da sua conta foi trocada e as outras sessões foram encerradas. | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.txt:5` | e-mail:texto | Se não foi você, peça uma nova senha agora: | corpo do e-mail | — | — | revisado — mantido |
| emails/password_changed | texto | `app/templates/emails/password_changed.txt:7` | e-mail:texto | Pedir nova senha: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.html:4` | e-mail:texto | Recebemos um pedido para criar uma nova senha. O link vale 1 hora e só pode ser usado uma vez. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.html:7` | e-mail:texto | Criar nova senha | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.html:8` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.txt:4` | e-mail:texto | Recebemos um pedido para criar uma nova senha. O link vale 1 hora e só pode ser usado uma vez. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.txt:5` | e-mail:texto | Ao trocar a senha, as sessões abertas em outros aparelhos são encerradas. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.txt:6` | e-mail:texto | Se não foi você, ignore este e-mail: sua senha continua a mesma. | corpo do e-mail | — | — | revisado — mantido |
| emails/reset_password | texto | `app/templates/emails/reset_password.txt:8` | e-mail:texto | Criar nova senha: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.html:4` | e-mail:texto | Alguém tentou criar uma conta nova com este e-mail, que já está cadastrado. | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.html:6` | e-mail:texto | Entrar | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.html:7` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.html:8` | e-mail:texto | Esqueci a senha | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.txt:4` | e-mail:texto | Alguém tentou criar uma conta nova com este e-mail, que já está cadastrado. | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.txt:5` | e-mail:texto | Se foi você, entre na sua conta. Se esqueceu a senha, peça uma nova: | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.txt:7` | e-mail:texto | Entrar: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/signup_existing | texto | `app/templates/emails/signup_existing.txt:8` | e-mail:texto | Esqueci a senha: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_briefing_filled | texto | `app/templates/emails/staff_briefing_filled.html:3` | e-mail:texto | A empresa {…} preencheu o briefing de identidade visual. A requisição está em “Briefing preenchido” no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_briefing_filled | texto | `app/templates/emails/staff_briefing_filled.html:4` | e-mail:texto | Abrir o painel interno | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_briefing_filled | texto | `app/templates/emails/staff_briefing_filled.html:5` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_briefing_filled | texto | `app/templates/emails/staff_briefing_filled.txt:2` | e-mail:texto | A empresa {…} preencheu o briefing de identidade visual. A requisição está em "Briefing preenchido" no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_briefing_filled | texto | `app/templates/emails/staff_briefing_filled.txt:4` | e-mail:texto | Abrir o painel interno: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_booked | texto | `app/templates/emails/staff_call_booked.html:3` | e-mail:texto | A empresa {…} marcou a ligação de identidade visual para {…} (horário de Brasília). O contato está no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_booked | texto | `app/templates/emails/staff_call_booked.html:4` | e-mail:texto | Ver horários e reservas | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_booked | texto | `app/templates/emails/staff_call_booked.html:5` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_booked | texto | `app/templates/emails/staff_call_booked.txt:2` | e-mail:texto | A empresa {…} marcou a ligação de identidade visual para {…} (horário de Brasília). O contato está no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_booked | texto | `app/templates/emails/staff_call_booked.txt:4` | e-mail:texto | Ver horários e reservas: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_change_request | texto | `app/templates/emails/staff_call_change_request.html:3` | e-mail:texto | A empresa {…} pediu: {…} (ligação de {…}, horário de Brasília). Decida no painel interno: cancelar a reserva ou mantê-la. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_change_request | texto | `app/templates/emails/staff_call_change_request.html:4` | e-mail:texto | Ver horários e reservas | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_change_request | texto | `app/templates/emails/staff_call_change_request.html:5` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_change_request | texto | `app/templates/emails/staff_call_change_request.txt:2` | e-mail:texto | A empresa {…} pediu: {…} (ligação de {…}, horário de Brasília). Decida no painel interno: cancelar a reserva ou mantê-la. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_call_change_request | texto | `app/templates/emails/staff_call_change_request.txt:4` | e-mail:texto | Ver horários e reservas: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_visual_request | texto | `app/templates/emails/staff_visual_request.html:3` | e-mail:texto | Uma empresa passou a ter direito à identidade visual (plano {…}) . A requisição já está no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_visual_request | texto | `app/templates/emails/staff_visual_request.html:4` | e-mail:texto | Abrir o painel interno | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_visual_request | texto | `app/templates/emails/staff_visual_request.html:5` | e-mail:texto | Se o botão não abrir, copie o endereço: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_visual_request | texto | `app/templates/emails/staff_visual_request.txt:2` | e-mail:texto | Uma empresa passou a ter direito à identidade visual (plano {…}) . A requisição já está no painel interno. | corpo do e-mail | — | — | revisado — mantido |
| emails/staff_visual_request | texto | `app/templates/emails/staff_visual_request.txt:4` | e-mail:texto | Abrir o painel interno: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:3` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:4` | e-mail:texto | A equipe de suporte da Teroz recebeu acesso temporário à empresa {…}. | corpo do e-mail | antes: “A equipe de suporte do Controle de Produção recebeu acesso temporário à empresa {…}.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/support_access | texto | `app/templates/emails/support_access.html:6` | e-mail:texto | Pessoa: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:7` | e-mail:texto | Papel: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:8` | e-mail:texto | Motivo: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:9` | e-mail:texto | Válido até: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.html:11` | e-mail:texto | O acesso expira sozinho e fica registrado na auditoria. Se não reconhece este pedido, desative a pessoa em Usuários e fale com o suporte. | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:2` | e-mail:texto | Olá, {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:4` | e-mail:texto | A equipe de suporte da Teroz recebeu acesso temporário à empresa {…}. | corpo do e-mail | antes: “A equipe de suporte do Controle de Produção recebeu acesso temporário à empresa {…}.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| emails/support_access | texto | `app/templates/emails/support_access.txt:6` | e-mail:texto | Pessoa: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:7` | e-mail:texto | Papel: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:8` | e-mail:texto | Motivo: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:9` | e-mail:texto | Válido até: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/support_access | texto | `app/templates/emails/support_access.txt:11` | e-mail:texto | O acesso expira sozinho e fica registrado na auditoria. Se não reconhece este pedido, desative a pessoa em Usuários e fale com o suporte. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:3` | e-mail:texto | Olá, {…}. Resumo da produção da empresa {…} de {…}. A planilha completa (projetos e pessoas) vai em anexo. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:4` | e-mail:texto | Projetos | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Projeto | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Progresso | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Unidades | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Peças na semana | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Prazo | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:7` | e-mail:texto | Término previsto | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:11` | e-mail:texto | {…} (aguardando peça) | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:11` | e-mail:macro | Projeto | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:11` | e-mail:macro | Etapas aguardando peça | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:12` | e-mail:macro | Progresso | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:13` | e-mail:macro | Unidades concluídas | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:13` | e-mail:macro | Quantidade | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:14` | e-mail:macro | Peças na semana | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:15` | e-mail:macro | Prazo | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:16` | e-mail:texto | {…} — atraso de {…} {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:16` | e-mail:macro | Término previsto | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:16` | e-mail:macro | Atraso previsto (dias úteis) | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:16` | e-mail:macro | dia útil | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:16` | e-mail:macro | dias úteis | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:22` | e-mail:texto | Nenhum projeto ativo. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:24` | e-mail:texto | Pessoas | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:28` | e-mail:texto | {…}: {…} peças em {…} registros ({…} h-padrão) | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:28` | e-mail:macro | Pessoa | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:28` | e-mail:macro | Peças (saldo) | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:28` | e-mail:macro | Registros | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.html:28` | e-mail:macro | Horas-padrão | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:31` | e-mail:texto | E mais {…} pessoas na planilha. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:33` | e-mail:texto | Nenhum lançamento na semana. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.html:35` | e-mail:texto | Abrir os projetos | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:2` | e-mail:texto | Olá, {…}. Resumo da produção da empresa {…} de {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:3` | e-mail:texto | A planilha completa (projetos e pessoas) vai em anexo. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:6` | e-mail:texto | - {…} (aguardando peça) : {…}, {…}/{…} unidades, {…} peças na semana, prazo {…}, término previsto {…} (atraso de {…} {…}) | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Projeto | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Etapas aguardando peça | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Progresso | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Unidades concluídas | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Quantidade | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Peças na semana | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Prazo | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Término previsto | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | Atraso previsto (dias úteis) | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | dia útil | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:6` | e-mail:macro | dias úteis | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:7` | e-mail:texto | Nenhum projeto ativo. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:10` | e-mail:texto | - {…}: {…} peças em {…} registros ({…} h-padrão) | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:10` | e-mail:macro | Pessoa | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:10` | e-mail:macro | Peças (saldo) | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:10` | e-mail:macro | Registros | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | macro | `app/templates/emails/weekly_report.txt:10` | e-mail:macro | Horas-padrão | botão ou bloco do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:11` | e-mail:texto | Nenhum lançamento na semana. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:12` | e-mail:texto | E mais {…} pessoas na planilha. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:14` | e-mail:texto | Abrir os projetos: {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:15` | e-mail:texto | Você recebe este relatório porque é supervisor ou proprietário na empresa {…}. | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:16` | e-mail:texto | Para não receber mais, desligue "Relatório semanal" em {…} | corpo do e-mail | — | — | revisado — mantido |
| emails/weekly_report | texto | `app/templates/emails/weekly_report.txt:17` | e-mail:texto | Não responda: esta caixa não é lida. | corpo do e-mail | — | — | revisado — mantido |

</details>

<details><summary><b>Preencher etapas e Meta e equipe</b> (220)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:40` | backend:valor | Tempo ideal | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:41` | backend:valor | Peças prontas | valor exibido (rótulo, opção, situação) | antes: “Peças concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:42` | backend:valor | % concluído | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:118` | backend:flash | Crie um projeto para começar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:118` | backend:flash | Ainda não há projetos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | _respond | `app/blueprints/preencher.py:282` | backend:_respond | Nada mudou. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:296` | backend:valor | Outra pessoa mudou “{…}” enquanto você editava: agora {…} min e {…} de {…} peças. O seu valor ficou no campo: saia dele de novo para salvar por cima. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | _respond | `app/blueprints/preencher.py:306` | backend:_respond | Salvo ({…} de “{…}”) · {…} | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | _respond | `app/blueprints/preencher.py:317` | backend:_respond | No modo simples a etapa não tem subatividades. Troque o modo em Meta e equipe. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | _respond | `app/blueprints/preencher.py:331` | backend:_respond | Subatividade “{…}” incluída · {…} | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | _respond | `app/blueprints/preencher.py:368` | backend:_respond | Nada mudou. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:383` | backend:valor | Outra pessoa mudou a etapa “{…}” enquanto você editava. Os números ao lado já são os de agora; o seu valor ficou no campo: saia dele de novo para salvar por cima. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:395` | backend:valor | Salvo: {…} em {…} ({…} de {…} unidades) · {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:397` | backend:valor | Salvo ({…} da etapa) · {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:413` | backend:flash | Etapa “{…}” incluída. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:429` | backend:flash | Digite um nome para o projeto (até 160 caracteres). | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:432` | backend:flash | Já existe um projeto com esse nome. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | NewStage | `app/blueprints/preencher.py:436` | backend:NewStage | Etapa {…} | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:440` | backend:flash | Projeto “{…}” criado com {…} etapas. Dê nome a elas e ajuste a meta em Meta e equipe. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:459` | backend:flash | Etapa “{…}” de volta. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:478` | backend:flash | Subatividade “{…}” de volta. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | dict | `app/blueprints/preencher.py:503` | backend:dict | Você lança o % de cada etapa. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | dict | `app/blueprints/preencher.py:504` | backend:dict | Subatividades com tempo ideal e peças, igual à planilha. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:524` | backend:erro | Informe o nome do projeto (até 160 caracteres). | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:528` | backend:erro | A meta é um número inteiro de 1 a 100000. | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:532` | backend:erro | Pessoas: um número inteiro de 1 a 1000. | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:540` | backend:erro | Horas por dia: de 0,5 a 24 (até 2 casas, ex.: 7,5). | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:548` | backend:erro | Prazo: use uma data válida (dd/mm/aaaa). | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | erro | `app/blueprints/preencher.py:549` | backend:erro | Campo desconhecido. | mensagem de erro | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:553` | backend:valor | nome do projeto | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:553` | backend:valor | horas por dia | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | _team_respond | `app/blueprints/preencher.py:586` | backend:_team_respond | Nada mudou. | mensagem do backend | — | — | revisado — mantido |
| blueprints/preencher.py | valor | `app/blueprints/preencher.py:588` | backend:valor | Salvo ({…}) · {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:621` | backend:flash | Modo simples ligado: lance o % de cada etapa. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/preencher.py | flash | `app/blueprints/preencher.py:622` | backend:flash | Modo detalhado ligado: lance as peças de cada subatividade. | confirmação ou aviso após ação | — | — | revisado — mantido |
| preencher/_cabecalho | aria-label | `app/templates/preencher/_cabecalho.html:7` | template:aria-label | Projetos | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_cabecalho | title | `app/templates/preencher/_cabecalho.html:13` | template:title | Renomear projeto | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_cabecalho | aria-label | `app/templates/preencher/_cabecalho.html:13` | template:aria-label | Renomear o projeto {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_cabecalho | title | `app/templates/preencher/_cabecalho.html:14` | template:title | Apagar projeto | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_cabecalho | aria-label | `app/templates/preencher/_cabecalho.html:14` | template:aria-label | Apagar o projeto {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_cabecalho | texto | `app/templates/preencher/_cabecalho.html:21` | template:texto | Novo projeto | texto na tela | — | — | revisado — mantido |
| preencher/_cabecalho | title | `app/templates/preencher/_cabecalho.html:21` | template:title | Novo projeto (nasce com 5 etapas, modo simples) | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_cabecalho | texto | `app/templates/preencher/_cabecalho.html:24` | template:texto | Nome do novo projeto | texto na tela | — | — | revisado — mantido |
| preencher/_cabecalho | placeholder | `app/templates/preencher/_cabecalho.html:25` | template:placeholder | Ex.: Lote 2026-015 | exemplo no campo | — | — | revisado — mantido |
| preencher/_cabecalho | texto | `app/templates/preencher/_cabecalho.html:26` | template:texto | Criar | texto na tela | — | — | revisado — mantido |
| preencher/_cabecalho | macro | `app/templates/preencher/_cabecalho.html:36` | template:macro | Modo simples | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_cabecalho | macro | `app/templates/preencher/_cabecalho.html:36` | template:macro | Modo detalhado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_cabecalho | texto | `app/templates/preencher/_cabecalho.html:37` | template:texto | Unidades | texto na tela | — | — | revisado — mantido |
| preencher/_cabecalho | macro | `app/templates/preencher/_cabecalho.html:41` | template:macro | Apagar o projeto “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_cabecalho | macro | `app/templates/preencher/_cabecalho.html:41` | template:macro | Ele sai das telas e libera o limite do plano. As peças lançadas e o histórico continuam guardados. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_cabecalho | macro | `app/templates/preencher/_cabecalho.html:41` | template:macro | Apagar projeto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:6` | template:texto | Com a equipe atual: {…} {…} × {…}&nbsp;h por dia | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:8` | template:texto | Termina em | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:10` | template:texto | Nada pendente: todas as etapas estão prontas. | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:12` | template:texto | Sem previsão: informe as pessoas e as horas por dia. | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:15` | template:texto | Prazo {…} · faltam {…} {…} no calendário | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | macro | `app/templates/preencher/_equipe.html:15` | template:macro | dia útil | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_equipe | macro | `app/templates/preencher/_equipe.html:15` | template:macro | dias úteis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:16` | template:texto | Sem prazo definido: preencha o prazo para ver a folga ou o atraso. | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:21` | template:texto | Dias de trabalho para terminar | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:23` | template:texto | {…}&nbsp;h que faltam, no ritmo da equipe atual | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:26` | template:texto | Dias de trabalho para a meta inteira | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:28` | template:texto | {…}&nbsp;h para {…} unidade{…}, do zero | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | macro | `app/templates/preencher/_equipe.html:28` | template:macro | if project.quantity == 1 else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:37` | template:texto | Dias úteis restantes conforme o tamanho da equipe | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:38` | template:texto | Pessoas | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:38` | template:texto | Horas por dia (equipe) | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:38` | template:texto | Dias úteis restantes | texto na tela | — | — | revisado — mantido |
| preencher/_equipe | texto | `app/templates/preencher/_equipe.html:42` | template:texto | equipe atual | texto na tela | — | — | revisado — mantido |
| preencher/_oob | aria-label | `app/templates/preencher/_oob.html:12` | template:aria-label | Unidades prontas | nome para leitor de tela | antes: “Unidades concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:20` | template:texto | Nome da etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:25` | template:texto | Etapa {…} de {…} · {…} | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:31` | template:texto | Apagar etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:38` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:38` | template:macro | · previsão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:38` | template:macro | ), st.part_note or | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:45` | template:macro | Atualizar aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:45` | template:macro | Marcar aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:51` | template:macro | Aguardando peça | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:51` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:53` | template:texto | Previsão de chegada | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:57` | template:texto | Observação (opcional) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | macro | `app/templates/preencher/_painel.html:60` | template:macro | Salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:66` | template:texto | Fotos e comentários | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:75` | template:texto | Checklist de inspeção ({…} itens) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:78` | template:texto | Progresso por pessoa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:88` | template:texto | Progresso da etapa {…} | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:90` | template:texto | % concluído da etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:91` | template:texto | Tempo da etapa (min por unidade) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:92` | template:texto | Unidades prontas | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:93` | template:texto | Tempo total (min) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:94` | template:texto | Tempo que falta (min) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:95` | template:texto | Salvar | texto na tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:101` | template:aria-label | % concluído da etapa {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:103` | template:aria-label | Tempo da etapa em minutos por unidade | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:106` | template:aria-label | Unidades prontas | nome para leitor de tela | antes: “Unidades concluídas” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:109` | template:texto | Salvar | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:115` | template:texto | Digite o % concluído da etapa (0 a 100, inteiro ou com 1 casa). Ele vira unidades prontas: % × meta, arredondado. Salva ao sair do campo (Tab ou Enter); Esc desfaz. | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:127` | template:texto | Subatividades | texto na tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:128` | template:aria-label | {…} subatividade{…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:129` | template:texto | Lance o total de peças prontas de cada uma. | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:133` | template:texto | Subatividades da etapa {…} | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:135` | template:texto | Subatividade | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:136` | template:texto | Tempo ideal (min por unidade) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:137` | template:texto | Peso na etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:138` | template:texto | Peças prontas (total) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:139` | template:texto | Progresso | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:140` | template:texto | Tempo total (min) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:141` | template:texto | Tempo que falta (min) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:143` | template:texto | Responsável | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:145` | template:texto | Ações | texto na tela | — | — | revisado — mantido |
| preencher/_painel | title | `app/templates/preencher/_painel.html:154` | template:title | Arraste para reordenar | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:154` | template:aria-label | Nome da subatividade | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:155` | template:texto | (concluída) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | title | `app/templates/preencher/_painel.html:155` | template:title | Concluída | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:156` | template:texto | (concluída) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | title | `app/templates/preencher/_painel.html:156` | template:title | Concluída | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:162` | template:aria-label | Tempo ideal de {…} (min) | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | data-label | `app/templates/preencher/_painel.html:166` | template:data-label | Peças prontas (total) | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:166` | template:aria-label | Total de peças prontas de {…} (0 a {…}) | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | data-label | `app/templates/preencher/_painel.html:171` | template:data-label | Responsável | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:178` | template:texto | Salvar | texto na tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:182` | template:aria-label | Ações de {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:191` | template:texto | Mover para a etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:195` | template:texto | Mover | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:198` | template:texto | Apagar subatividade | texto na tela | — | — | revisado — mantido |
| preencher/_painel | placeholder | `app/templates/preencher/_painel.html:207` | template:placeholder | Nova subatividade… | exemplo no campo | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:207` | template:aria-label | Nome da nova subatividade | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:208` | template:aria-label | Tempo ideal da nova subatividade (min) | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_painel | aria-label | `app/templates/preencher/_painel.html:210` | template:aria-label | Peças prontas da nova subatividade | nome para leitor de tela | antes: “Peças concluídas da nova subatividade” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:217` | template:texto | Incluir | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:224` | template:texto | Total da etapa | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:234` | template:texto | Digite o | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:234` | template:texto | de peças prontas de cada subatividade, não só as de hoje. Salva ao sair do campo (Tab ou Enter); Esc desfaz. | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:235` | template:texto | Aqui ficam o nome, o tempo ideal de cada subatividade (min por unidade) e a ordem. O peso na etapa e os tempos total e que falta saem do tempo ideal × meta. Para lançar peças, volte a “Registrar produção”. | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:238` | template:texto | Subatividades apagadas ({…}) | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:241` | template:texto | · {…} peças | texto na tela | — | — | revisado — mantido |
| preencher/_painel | texto | `app/templates/preencher/_painel.html:245` | template:texto | Desfazer | texto na tela | — | — | revisado — mantido |
| preencher/_partes | aria-label | `app/templates/preencher/_partes.html:14` | template:aria-label | Progresso pelas tarefas: {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:17` | template:texto | {…} de {…} unid. prontas | texto na tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:24` | template:texto | Peso no projeto | texto na tela | — | — | revisado — mantido |
| preencher/_partes | macro | `app/templates/preencher/_partes.html:30` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:41` | template:texto | Progresso da etapa Progresso pelas tarefas (conta as parciais) | texto na tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:44` | template:texto | {…} de {…} subatividade{…} em 100% | texto na tela | — | — | revisado — mantido |
| preencher/_partes | macro | `app/templates/preencher/_partes.html:44` | template:macro | if sel.r.tarefas == 1 else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:48` | template:texto | Unidades prontas da etapa (conta a subatividade mais atrasada) | texto na tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:50` | template:texto | Situação: {…} | texto na tela | — | — | revisado — mantido |
| preencher/_partes | aria-label | `app/templates/preencher/_partes.html:70` | template:aria-label | Atribuir {…} a | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:71` | template:texto | Atribuir a | texto na tela | — | — | revisado — mantido |
| preencher/_partes | placeholder | `app/templates/preencher/_partes.html:72` | template:placeholder | Digite um nome ou um e-mail | exemplo no campo | — | — | revisado — mantido |
| preencher/_partes | aria-label | `app/templates/preencher/_partes.html:72` | template:aria-label | Buscar pessoa por nome ou e-mail | nome para leitor de tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:77` | template:texto | Sugestões | texto na tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:80` | template:texto | Tirar o responsável | texto na tela | — | — | revisado — mantido |
| preencher/_partes | texto | `app/templates/preencher/_partes.html:90` | template:texto | Ninguém encontrado. | texto na tela | — | — | revisado — mantido |
| preencher/_partes | title | `app/templates/preencher/_partes.html:95` | template:title | Responsável: {…} | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/_partes | aria-label | `app/templates/preencher/_partes.html:95` | template:aria-label | {…}: responsável {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:9` | template:texto | Preencher etapas · {…} · Teroz | texto na tela | antes: “Preencher etapas · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| preencher/fill | texto | `app/templates/preencher/fill.html:25` | template:texto | Etapas apagadas ({…}) | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:32` | template:texto | Desfazer | texto na tela | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:40` | template:macro | Preencher etapas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:49` | template:macro | Nenhuma etapa ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:49` | template:macro | Inclua a primeira etapa para começar a lançar o progresso. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:49` | template:macro | Peça a um supervisor para incluir as etapas do projeto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:53` | template:texto | Nome da etapa | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:54` | template:texto | Incluir etapa | texto na tela | — | — | revisado — mantido |
| preencher/fill | aria-label | `app/templates/preencher/fill.html:63` | template:aria-label | O que fazer nesta tela | nome para leitor de tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:64` | template:texto | Registrar produção | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:65` | template:texto | Configurar etapas | texto na tela | — | — | revisado — mantido |
| preencher/fill | aria-label | `app/templates/preencher/fill.html:72` | template:aria-label | Etapas do projeto | nome para leitor de tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:73` | template:texto | Etapas · progresso pelas tarefas | texto na tela | — | — | revisado — mantido |
| preencher/fill | title | `app/templates/preencher/fill.html:84` | template:title | Arraste para reordenar | dica ao passar o mouse | — | — | revisado — mantido |
| preencher/fill | aria-label | `app/templates/preencher/fill.html:88` | template:aria-label | Ações da etapa {…} | nome para leitor de tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:90` | template:texto | Renomear | texto na tela | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:91` | template:macro | Mover para cima | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:91` | template:macro | Mover para baixo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:102` | template:texto | Apagar etapa | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:111` | template:texto | Arraste pela alça ⠿ para mudar a ordem. | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:115` | template:texto | + Nova etapa | texto na tela | — | — | revisado — mantido |
| preencher/fill | texto | `app/templates/preencher/fill.html:116` | template:texto | Incluir | texto na tela | — | — | revisado — mantido |
| preencher/fill | placeholder | `app/templates/preencher/fill.html:116` | template:placeholder | Nome da etapa | exemplo no campo | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:128` | template:macro | Apagar “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:128` | template:macro | ” e todas as suas subatividades? | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:128` | template:macro | Ela sai da tela e das contas. As peças lançadas ficam no histórico, e dá para desfazer em “Etapas apagadas”, no fim da lista. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:128` | template:macro | Apagar etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:135` | template:macro | Apagar a subatividade “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:135` | template:macro | Ela sai da etapa e das contas. As peças lançadas ficam no histórico, e dá para desfazer em “Subatividades apagadas”, abaixo da tabela. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/fill | macro | `app/templates/preencher/fill.html:135` | template:macro | Apagar subatividade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:8` | template:texto | Meta e equipe · {…} · Teroz | texto na tela | antes: “Meta e equipe · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| preencher/goal_team | macro | `app/templates/preencher/goal_team.html:16` | template:macro | Meta e equipe | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:24` | template:texto | Meta, equipe e prazo | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:25` | template:texto | A meta vale para todas as etapas: cada uma precisa chegar a esse número de unidades. | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:29` | template:texto | Nome do projeto | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:31` | template:texto | Meta: quantas unidades vamos montar | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:33` | template:texto | Pessoas montando | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:35` | template:texto | Horas de trabalho por dia (por pessoa) | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:37` | template:texto | Prazo | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:39` | template:texto | Salvar | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:43` | template:texto | Meta | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:43` | template:texto | {…} unidades | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:44` | template:texto | Pessoas montando | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:45` | template:texto | Horas por dia (por pessoa) | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:46` | template:texto | Prazo | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:48` | template:texto | Só supervisores mudam a meta e a equipe. | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:54` | template:texto | Previsão | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:59` | template:texto | Simular o tamanho da equipe | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:59` | template:texto | De 1 a 6 pessoas | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:60` | template:texto | Dias de trabalho = horas que faltam ÷ (pessoas × horas por dia). Considera que as pessoas trabalham em paralelo, sem mudar a meta nem o prazo. | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:66` | template:texto | Modo de lançar o progresso | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:71` | template:texto | Modo de progresso | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:79` | template:texto | Salvar modo | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | texto | `app/templates/preencher/goal_team.html:81` | template:texto | Do simples para o detalhado, cada etapa ganha a primeira subatividade. Do detalhado para o simples, só se cada etapa tiver no máximo uma subatividade. | texto na tela | — | — | revisado — mantido |
| preencher/goal_team | macro | `app/templates/preencher/goal_team.html:83` | template:macro | Simples: o % de cada etapa é lançado direto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/goal_team | macro | `app/templates/preencher/goal_team.html:83` | template:macro | Detalhado: peças de cada subatividade, igual à planilha. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:4` | template:texto | Como funciona · {…} · Teroz | texto na tela | antes: “Como funciona · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| preencher/how | macro | `app/templates/preencher/how.html:12` | template:macro | Como funciona | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:16` | template:texto | Como cada conta funciona | texto na tela | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:17` | template:texto | A coluna “Exemplo” usa os números que estão agora no projeto e muda junto com eles. | texto na tela | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:20` | template:texto | Conta | texto na tela | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:20` | template:texto | Como é calculada | texto na tela | — | — | revisado — mantido |
| preencher/how | texto | `app/templates/preencher/how.html:20` | template:texto | Exemplo com os números atuais | texto na tela | — | — | revisado — mantido |

</details>

<details><summary><b>Qualidade (fotos, checklist, unidades)</b> (207)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/qualidade.py | valor | `app/blueprints/qualidade.py:40` | backend:valor | default-src 'none'; sandbox | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:90` | backend:flash | Comentário publicado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:101` | backend:flash | Comentário apagado (registrado na auditoria). | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | _evidence_page | `app/blueprints/qualidade.py:118` | backend:_evidence_page | Escolha uma foto. | mensagem do backend | — | — | revisado — mantido |
| blueprints/qualidade.py | _evidence_page | `app/blueprints/qualidade.py:128` | backend:_evidence_page | Não foi possível guardar a foto agora. Tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:135` | backend:flash | Foto enviada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | valor | `app/blueprints/qualidade.py:155` | backend:valor | private, max-age=300 | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/qualidade.py | valor | `app/blueprints/qualidade.py:157` | backend:valor | inline; filename="foto-{…}{…}.jpg" | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/qualidade.py | _evidence_page | `app/blueprints/qualidade.py:172` | backend:_evidence_page | Não foi possível apagar a foto agora. Tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:174` | backend:flash | Foto apagada (registrado na auditoria). | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:226` | backend:flash | Item incluído no checklist. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:237` | backend:flash | Item arquivado. Respostas antigas continuam guardadas. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:248` | backend:flash | A etapa passa a sinalizar checklist pendente. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:248` | backend:flash | Checklist deixa de ser exigido. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:331` | backend:flash | Inspeção assinada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:331` | backend:flash | Rascunho salvo. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:349` | backend:flash | Correção registrada. A resposta anterior continua no histórico. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:407` | backend:flash | {…} números de série cadastrados. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:421` | backend:flash | {…} números de série cadastrados. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:480` | backend:flash | Situação da unidade atualizada. | confirmação ou aviso após ação | antes: “Status da unidade atualizado.” — glossário: status → situação | aplicado (texto atual) | alterado |
| blueprints/qualidade.py | flash | `app/blueprints/qualidade.py:501` | backend:flash | +1 em {…} · unidade {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| services/checklists.py | valor | `app/services/checklists.py:41` | backend:valor | Não conforme | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:76` | backend:erro | Escreva o item (até {…} caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:79` | backend:erro | No máximo {…} itens ativos por etapa. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:81` | backend:erro | Este item já está no checklist. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:135` | backend:erro | Esta etapa ainda não tem itens de checklist. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:195` | backend:erro | Resultado inválido (use OK, Não conforme ou N/A). | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:198` | backend:erro | Observação com no máximo {…} caracteres. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | InspectionConflict | `app/services/checklists.py:205` | backend:InspectionConflict | Outra pessoa mexeu nesta inspeção enquanto você preenchia. Confira e salve de novo. | mensagem do backend | — | — | revisado — mantido |
| services/checklists.py | InspectionConflict | `app/services/checklists.py:218` | backend:InspectionConflict | Outra pessoa mexeu nesta inspeção enquanto você preenchia. Confira e salve de novo. | mensagem do backend | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:230` | backend:erro | Inspeção já assinada: mudanças só por correção registrada. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:252` | backend:erro | Esta inspeção já foi assinada. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:256` | backend:erro | Responda todos os itens antes de assinar ({…} sem resposta). | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:258` | backend:erro | Item “Não conforme” precisa de observação. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:283` | backend:erro | Só inspeção assinada recebe correção; o rascunho se edita direto. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:285` | backend:erro | Item não pertence a esta inspeção. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:289` | backend:erro | Explique o motivo da correção ({…} a {…} caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:291` | backend:erro | Item “Não conforme” precisa de observação. | mensagem de erro | — | — | revisado — mantido |
| services/checklists.py | erro | `app/services/checklists.py:294` | backend:erro | Nada mudou nesta resposta. | mensagem de erro | — | — | revisado — mantido |
| services/comments.py | erro | `app/services/comments.py:57` | backend:erro | Escreva o comentário. | mensagem de erro | — | — | revisado — mantido |
| services/comments.py | erro | `app/services/comments.py:59` | backend:erro | O comentário tem no máximo {…} caracteres. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:102` | backend:erro | Escolha uma foto. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:104` | backend:erro | Foto maior que {…} MB. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:107` | backend:erro | Envie uma foto JPEG, PNG ou WebP. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:114` | backend:erro | Envie uma foto JPEG, PNG ou WebP. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:117` | backend:erro | Foto com dimensões grandes demais. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:125` | backend:erro | Foto com dimensões grandes demais. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:127` | backend:erro | Não foi possível ler a foto. Envie um JPEG, PNG ou WebP válido. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:184` | backend:erro | Fotos não estão disponíveis neste ambiente. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:187` | backend:erro | A legenda tem no máximo {…} caracteres. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | erro | `app/services/photos.py:190` | backend:erro | Esta subatividade já tem {…} fotos (o máximo). Apague uma para enviar outra. | mensagem de erro | antes: “Esta atividade já tem {…} fotos (o máximo). Apague uma para enviar outra.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/photos.py | erro | `app/services/photos.py:193` | backend:erro | A empresa atingiu o limite de fotos guardadas. Apague fotos antigas ou fale com o suporte. | mensagem de erro | — | — | revisado — mantido |
| services/photos.py | ObjectNotFound | `app/services/photos.py:237` | backend:ObjectNotFound | Foto corrompida. | mensagem do backend | — | — | revisado — mantido |
| services/photos.py | StorageDisabled | `app/services/photos.py:278` | backend:StorageDisabled | Há fotos da empresa, mas o armazenamento não está configurado. | mensagem do backend | — | — | revisado — mantido |
| services/units.py | valor | `app/services/units.py:29` | backend:valor | Em produção | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:55` | backend:erro | {…}número de série inválido: use letras, números e . _ / - (até {…} caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:78` | backend:erro | Já cadastrado(s) neste projeto: {…}{…}. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:82` | backend:erro | O projeto tem {…} equipamentos: com estes, seriam {…} números de série. Aumente a quantidade do projeto ou cadastre menos. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:102` | backend:erro | Prefixo inválido: letras, números e . _ / - (até {…} caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:104` | backend:erro | Número inicial ou dígitos inválidos. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:106` | backend:erro | Quantidade entre 1 e {…}. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:115` | backend:erro | No máximo {…} números por vez. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | validate_serial | `app/services/units.py:121` | backend:validate_serial | Item {…}: | mensagem do backend | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:123` | backend:erro | Item {…}: {…} repetido na lista. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:127` | backend:erro | Cole pelo menos um número de série. | mensagem de erro | — | — | revisado — mantido |
| services/units.py | erro | `app/services/units.py:133` | backend:erro | Situação inválida. | mensagem de erro | antes: “Status inválido.” — glossário: status → situação | aplicado (texto atual) | alterado |
| services/units.py | UnitConflict | `app/services/units.py:135` | backend:UnitConflict | Outra pessoa alterou esta unidade. Confira a situação atual. | mensagem do backend | antes: “Outra pessoa alterou esta unidade. Confira o status atual.” — glossário: status → situação | aplicado (texto atual) | alterado |
| services/units.py | UnitConflict | `app/services/units.py:148` | backend:UnitConflict | Outra pessoa alterou esta unidade. Confira a situação atual. | mensagem do backend | antes: “Outra pessoa alterou esta unidade. Confira o status atual.” — glossário: status → situação | aplicado (texto atual) | alterado |
| services/units.py | erro | `app/services/units.py:173` | backend:erro | Subatividade de outro projeto. | mensagem de erro | antes: “Atividade de outro projeto.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/units.py | erro | `app/services/units.py:175` | backend:erro | A unidade {…} já foi registrada nesta subatividade. | mensagem de erro | antes: “A unidade {…} já foi registrada nesta atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:12` | template:texto | Checklist · {…} · Teroz | texto na tela | antes: “Checklist · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:18` | template:texto | Checklist · {…}{…} | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:21` | template:macro | Checklist pendente | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:21` | template:macro | Checklist assinado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:22` | template:texto | Exigido nesta etapa — só avisa; não bloqueia o registro de peças. | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:24` | template:texto | Não exigido nesta etapa. | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:33` | template:texto | Itens | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:42` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:42` | template:macro | Arquivar item | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:49` | template:texto | Nenhum item ainda. Inclua abaixo ou defina no modelo de etapas. | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:55` | template:texto | Novo item | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:58` | template:macro | Incluir item | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:62` | template:macro | Exigir checklist assinado nesta etapa (sinaliza “pendente”) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:62` | template:macro | , id= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:63` | template:macro | Salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:69` | template:texto | Inspeções | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:75` | template:texto | Unidade | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | texto | `app/templates/qualidade/checklist.html:77` | template:texto | Etapa inteira (sem unidade) | texto na tela | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:82` | template:macro | Nova inspeção | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:86` | template:macro | Aberta em | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:86` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | data-label | `app/templates/qualidade/checklist.html:90` | template:data-label | Aberta em | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/checklist | data-label | `app/templates/qualidade/checklist.html:91` | template:data-label | Unidade | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/checklist | data-label | `app/templates/qualidade/checklist.html:92` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:92` | template:macro | Assinada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:92` | template:macro | Rascunho | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | data-label | `app/templates/qualidade/checklist.html:93` | template:data-label | Assinatura | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:93` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:99` | template:macro | Nenhuma inspeção | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/checklist | macro | `app/templates/qualidade/checklist.html:99` | template:macro | Abra uma inspeção, marque cada item e assine. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:9` | template:texto | Fotos e comentários · {…} · Teroz | texto na tela | antes: “Evidências · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:16` | template:texto | Fotos e comentários · {…} | texto na tela | antes: “Evidências · {…}” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:20` | template:macro | Checklist da etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:26` | template:texto | Fotos | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:37` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:41` | template:texto | Apagar | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:44` | template:texto | A foto some para todos. Fica registrado quem apagou. | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:45` | template:macro | Apagar foto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:53` | template:macro | Nenhuma foto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:53` | template:macro | Fotografe a montagem pronta ou o defeito encontrado. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:61` | template:texto | Nova foto | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:63` | template:texto | JPEG, PNG ou WebP até {…} MB. A localização (GPS) e os dados da câmera são removidos. | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:66` | template:texto | Legenda | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:69` | template:macro | Enviar foto | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:72` | template:texto | Limite de {…} fotos nesta subatividade. Apague uma para enviar outra. | texto na tela | antes: “Limite de {…} fotos nesta atividade. Apague uma para enviar outra.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:75` | template:texto | O envio de fotos não está configurado neste ambiente. | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:80` | template:texto | Comentários | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:85` | template:texto | Novo comentário | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:87` | template:texto | Até {…} caracteres. Visível para toda a equipe da empresa. | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:89` | template:macro | Publicar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:95` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:99` | template:texto | Apagar | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:102` | template:texto | O comentário some para todos. Fica registrado quem apagou (sem o texto). | texto na tela | — | — | revisado — mantido |
| qualidade/evidencias | macro | `app/templates/qualidade/evidencias.html:103` | template:macro | Apagar comentário | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/evidencias | texto | `app/templates/qualidade/evidencias.html:111` | template:texto | Nenhum comentário ainda. | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:9` | template:texto | Inspeção · {…} · Teroz | texto na tela | antes: “Inspeção · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:15` | template:texto | {…}Checklist · {…} | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:16` | template:texto | Inspeção · {…} {…} | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:18` | template:texto | por {…} em | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | macro | `app/templates/qualidade/inspecao.html:18` | template:macro | Assinada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/inspecao | macro | `app/templates/qualidade/inspecao.html:18` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:19` | template:texto | aberta em | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | macro | `app/templates/qualidade/inspecao.html:19` | template:macro | Rascunho | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:40` | template:texto | Observação | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:40` | template:texto | (obrigatória se não conforme) | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:46` | template:texto | Salvar rascunho | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:47` | template:texto | Assinar como {…} | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:49` | template:texto | Ao assinar ficam gravados seu usuário e a data/hora do servidor. Depois disso, mudanças só por correção registrada (supervisor). | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | aria-label | `app/templates/qualidade/inspecao.html:52` | template:aria-label | Respostas | nome para leitor de tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:57` | template:texto | (item arquivado) | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:60` | template:texto | Sem resposta. | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:64` | template:texto | Histórico ({…}) | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:67` | template:texto | · correção: {…} | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | macro | `app/templates/qualidade/inspecao.html:67` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:74` | template:texto | Registrar correção | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:84` | template:texto | Observação | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | texto | `app/templates/qualidade/inspecao.html:88` | template:texto | Motivo da correção | texto na tela | — | — | revisado — mantido |
| qualidade/inspecao | macro | `app/templates/qualidade/inspecao.html:91` | template:macro | Registrar correção | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:10` | template:texto | Unidade {…} · Teroz | texto na tela | antes: “Unidade {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:15` | template:texto | {…}Unidades · {…} | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:17` | template:texto | cadastrada em | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:26` | template:texto | Lançamentos | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:32` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:36` | template:texto | Nenhum lançamento ligado a esta unidade. | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:40` | template:texto | Inspeções | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:45` | template:macro | Assinada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:45` | template:macro | Rascunho | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:46` | template:macro | Pessoa removida | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:50` | template:texto | Nenhuma inspeção desta unidade. | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:54` | template:texto | Alterações | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:61` | template:texto | Sem alterações de situação. | texto na tela | antes: “Sem alterações de status.” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:68` | template:texto | Registrar nesta unidade | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:71` | template:texto | Subatividade concluída | texto na tela | antes: “Atividade concluída” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:74` | template:texto | {…} › {…} (já registrada) | texto na tela | — | — | revisado — mantido |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:78` | template:macro | Registrar +1 | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:82` | template:texto | Situação | texto na tela | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidade | texto | `app/templates/qualidade/unidade.html:86` | template:texto | Situação da unidade | texto na tela | antes: “Status da unidade” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidade | macro | `app/templates/qualidade/unidade.html:91` | template:macro | Salvar situação | rótulo, botão ou ajuda de componente | antes: “Salvar status” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:11` | template:texto | Unidades · {…} · Teroz | texto na tela | antes: “Unidades · {…} · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:17` | template:texto | Unidades{…} | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:18` | template:texto | equipamentos com número de série. | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:26` | template:texto | Buscar número de série | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:29` | template:macro | Buscar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:33` | template:macro | Número de série | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:33` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | data-label | `app/templates/qualidade/unidades.html:37` | template:data-label | Número de série | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/unidades | data-label | `app/templates/qualidade/unidades.html:38` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidades | data-label | `app/templates/qualidade/unidades.html:39` | template:data-label | Cadastrada em | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:45` | template:macro | Nada encontrado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:45` | template:macro | Nenhum número de série com “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:45` | template:macro | ” neste projeto. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:47` | template:macro | Nenhuma unidade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:47` | template:macro | Cadastre os números de série para acompanhar cada equipamento. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:53` | template:texto | Gerar faixa | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:56` | template:texto | Prefixo | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:58` | template:texto | Ex.: prefixo MT-, início 1, 3 dígitos → MT-001, MT-002… | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:62` | template:texto | Início | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:66` | template:texto | Quantidade | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:71` | template:texto | Dígitos | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:74` | template:macro | Gerar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:77` | template:texto | Colar lista | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:80` | template:texto | Números de série | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | texto | `app/templates/qualidade/unidades.html:82` | template:texto | Um por linha (ou separados por ; ou ,). Letras, números e . _ / -. | texto na tela | — | — | revisado — mantido |
| qualidade/unidades | macro | `app/templates/qualidade/unidades.html:84` | template:macro | Cadastrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | texto | `app/templates/qualidade/unidades_busca.html:8` | template:texto | Buscar unidade · Teroz | texto na tela | antes: “Buscar unidade · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| qualidade/unidades_busca | texto | `app/templates/qualidade/unidades_busca.html:13` | template:texto | Buscar unidade{…} | texto na tela | — | — | revisado — mantido |
| qualidade/unidades_busca | texto | `app/templates/qualidade/unidades_busca.html:14` | template:texto | Encontre o equipamento pelo número de série e veja o histórico completo. | texto na tela | — | — | revisado — mantido |
| qualidade/unidades_busca | texto | `app/templates/qualidade/unidades_busca.html:20` | template:texto | Número de série | texto na tela | — | — | revisado — mantido |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:23` | template:macro | Buscar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:27` | template:macro | Número de série | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:27` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | data-label | `app/templates/qualidade/unidades_busca.html:31` | template:data-label | Número de série | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/unidades_busca | data-label | `app/templates/qualidade/unidades_busca.html:32` | template:data-label | Projeto | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| qualidade/unidades_busca | data-label | `app/templates/qualidade/unidades_busca.html:33` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | antes: “Status” — glossário: status → situação | aplicado (texto atual) | alterado |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:39` | template:macro | Nada encontrado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:39` | template:macro | Nenhum número de série com “ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| qualidade/unidades_busca | macro | `app/templates/qualidade/unidades_busca.html:39` | template:macro | ” nos projetos ativos. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>Identidade visual e ligação (planos Empresa/Implantação)</b> (169)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/identidade.py | valor | `app/blueprints/identidade.py:67` | backend:valor | default-src 'none'; sandbox | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:126` | backend:formulário | Nome da empresa | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:128` | backend:formulário | Cores de preferência | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:129` | backend:formulário | Fontes de preferência | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:131` | backend:formulário | Sites de referência | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:134` | backend:formulário | Tom de voz | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:135` | backend:formulário | Sem preferência | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:139` | backend:formulário | Nome do contato | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:140` | backend:formulário | Telefone (com DDD) | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | formulário | `app/blueprints/identidade.py:141` | backend:formulário | E-mail do contato | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _briefing_page | `app/blueprints/identidade.py:224` | backend:_briefing_page | Confira os campos destacados. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _staff_email | `app/blueprints/identidade.py:237` | backend:_staff_email | Briefing de identidade visual preenchido | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:242` | backend:flash | Briefing enviado. A equipe foi avisada e vai entrar em contato. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:244` | backend:flash | Briefing salvo. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _briefing_page | `app/blueprints/identidade.py:258` | backend:_briefing_page | Escolha uma imagem. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _briefing_page | `app/blueprints/identidade.py:268` | backend:_briefing_page | Não foi possível guardar a imagem agora. Tente de novo. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:275` | backend:flash | Logo enviado. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:275` | backend:flash | Foto de produto enviada. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | valor | `app/blueprints/identidade.py:294` | backend:valor | private, max-age=300 | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | valor | `app/blueprints/identidade.py:296` | backend:valor | inline; filename="briefing-{…}{…}.jpg" | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _briefing_page | `app/blueprints/identidade.py:315` | backend:_briefing_page | Não foi possível apagar a imagem agora. Tente de novo. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:317` | backend:flash | Imagem apagada. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | send_template | `app/blueprints/identidade.py:380` | backend:send_template | Ligação de identidade visual marcada | assunto do e-mail | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _staff_email | `app/blueprints/identidade.py:388` | backend:_staff_email | Ligação de identidade visual marcada | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:394` | backend:flash | Ligação marcada para {…} (horário de Brasília). | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | _staff_email | `app/blueprints/identidade.py:414` | backend:_staff_email | Pedido de mudança na ligação de identidade visual | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/identidade.py | flash | `app/blueprints/identidade.py:421` | backend:flash | Pedido enviado. A equipe vai responder por e-mail. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | valor | `app/services/agenda.py:39` | backend:valor | Cancelar a ligação | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | valor | `app/services/agenda.py:39` | backend:valor | Remarcar a ligação | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:104` | backend:erro | Informe o nome de quem vai atender a ligação. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:106` | backend:erro | Nome do contato: no máximo {…} caracteres. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:108` | backend:erro | Informe um telefone com DDD (só números, espaço, parênteses, + ou -). | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:119` | backend:erro | O agendamento faz parte dos planos Empresa e Implantação. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:123` | backend:erro | Escolha um horário da lista. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:126` | backend:erro | Sua empresa já tem uma ligação marcada. Para mudar, peça pela própria tela. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:129` | backend:erro | Esse horário não existe mais. Escolha outro. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:131` | backend:erro | Esse horário já passou ou está perto demais. Escolha outro. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | SlotTaken | `app/services/agenda.py:133` | backend:SlotTaken | Esse horário acabou de ser reservado. Escolha outro. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | SlotTaken | `app/services/agenda.py:149` | backend:SlotTaken | Esse horário acabou de ser reservado por outra pessoa. Escolha outro. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | SlotTaken | `app/services/agenda.py:166` | backend:SlotTaken | Esse horário acabou de ser reservado por outra pessoa. Escolha outro. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:192` | backend:erro | Escolha cancelar ou remarcar. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:194` | backend:erro | Reserva não encontrada. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:210` | backend:erro | Reserva não encontrada. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:256` | backend:erro | Duração entre {…} e {…} minutos. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:259` | backend:erro | O horário precisa ser no futuro. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:262` | backend:erro | Já existe um horário começando nesse momento. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:269` | backend:erro | Já existe um horário começando nesse momento. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:278` | backend:erro | Esse horário está reservado. Cancele a reserva antes de remover. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:285` | backend:erro | Esse horário acabou de ser reservado. Atualize a página. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:312` | backend:erro | Esse horário não está reservado. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/agenda.py | erro | `app/services/agenda.py:345` | backend:erro | Não há pedido de mudança para esse horário. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:171` | backend:erro | Sites de referência: no máximo {…} endereços. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:174` | backend:erro | Sites de referência: no máximo {…} endereços. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:178` | backend:erro | Sites de referência: cada endereço com até {…} caracteres. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:188` | backend:erro | Sites de referência: use endereços completos, começando com http:// ou https://. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:196` | backend:erro | {…}: no máximo {…} caracteres. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:203` | backend:_limit | Nome da empresa | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:205` | backend:_limit | Cores de preferência | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:206` | backend:_limit | Fontes de preferência | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:207` | backend:_limit | Nome do contato | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:208` | backend:_limit | Telefone do contato | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | _limit | `app/services/visual.py:209` | backend:_limit | E-mail do contato | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:213` | backend:erro | Tom de voz inválido. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:217` | backend:erro | Telefone do contato: use só números, espaço, parênteses, + ou -. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:219` | backend:erro | E-mail do contato inválido. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | valor | `app/services/visual.py:226` | backend:valor | Nome da empresa | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | valor | `app/services/visual.py:226` | backend:valor | Nome do contato | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | valor | `app/services/visual.py:226` | backend:valor | Telefone ou e-mail do contato | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | append | `app/services/visual.py:229` | backend:append | Nome da empresa | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | append | `app/services/visual.py:233` | backend:append | Nome do contato | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | append | `app/services/visual.py:235` | backend:append | Telefone ou e-mail do contato | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:251` | backend:erro | A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:318` | backend:erro | Envie uma imagem .jpg, .jpeg, .png ou .webp. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:326` | backend:erro | Tipo de imagem inválido. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:329` | backend:erro | O envio de imagens não está disponível neste ambiente. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:332` | backend:erro | A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:342` | backend:erro | Já há um logo. Apague o atual para enviar outro. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:343` | backend:erro | O limite é de {…} fotos de produto. Apague uma para enviar outra. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | ObjectNotFound | `app/services/visual.py:396` | backend:ObjectNotFound | Imagem corrompida. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | erro | `app/services/visual.py:403` | backend:erro | A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/visual.py | StorageDisabled | `app/services/visual.py:432` | backend:StorageDisabled | Há imagens do briefing, mas o armazenamento não está configurado. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/_honeypot | texto | `app/templates/identidade/_honeypot.html:4` | template:texto | Não preencha este campo | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:10` | template:texto | Identidade visual · Teroz | texto na tela | antes: “Identidade visual · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:15` | template:texto | Identidade visual | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:16` | template:texto | Conte como é a sua empresa. A equipe usa estas respostas para adaptar o visual do sistema à sua marca. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:19` | template:macro | Agendar a ligação | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:24` | template:macro | Nova | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:24` | template:macro | Briefing preenchido | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:24` | template:macro | Em andamento | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:24` | template:macro | Entregue | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:24` | template:macro | Andamento da identidade visual | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:27` | template:macro | A equipe já está trabalhando na sua identidade visual | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:27` | template:macro | Para mudar alguma resposta, fale com a equipe: ela reabre o briefing para você. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:29` | template:macro | Briefing enviado à equipe | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:29` | template:macro | Você ainda pode ajustar as respostas até a equipe começar o trabalho. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:36` | template:texto | Briefing | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:40` | template:texto | Empresa e produtos | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:41` | template:macro | Como a marca aparece para o cliente. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:42` | template:macro | O que vocês fabricam ou montam. Uma linha por produto, se preferir. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:46` | template:texto | Preferências | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:48` | template:macro | Ex.: verde-escuro e cinza, ou os códigos da marca. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:49` | template:macro | Ex.: a fonte do logo ou do site atual. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:51` | template:macro | Até 5 endereços que vocês gostam, um por linha, começando com https://. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:53` | template:texto | Tom de voz | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:54` | template:texto | Tom de voz é o jeito que a marca fala com o cliente: mais sério, equilibrado ou mais próximo. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:64` | template:texto | Contato para a ligação | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:65` | template:texto | Quem a equipe procura para conversar sobre a marca. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:68` | template:macro | Telefone ou e-mail: pelo menos um. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:74` | template:texto | Para enviar à equipe, falta: {…}. Você pode salvar e terminar depois. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:76` | template:macro | Salvar briefing | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:80` | template:texto | Suas respostas | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:82` | template:texto | Nome da empresa | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:83` | template:texto | Produtos | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:84` | template:texto | Cores de preferência | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:85` | template:texto | Fontes de preferência | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:86` | template:texto | Sites de referência | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:87` | template:texto | Tom de voz | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:87` | template:macro | Sem preferência | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:88` | template:texto | Contato | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:94` | template:texto | Logo e fotos de produto | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:104` | template:macro | Logo | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:104` | template:macro | Foto de produto | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:108` | template:macro | Apagar | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:115` | template:macro | Nenhuma imagem ainda | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:115` | template:macro | Envie o logo atual (se houver) e fotos dos produtos. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:124` | template:texto | Tipo | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:126` | template:texto | Foto de produto ({…}/{…}) | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:127` | template:texto | Logo ({…}/1) | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:130` | template:macro | Imagem | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:130` | template:macro | Escolher imagem | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:130` | template:macro | JPEG, PNG ou WebP até | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:130` | template:macro | MB. Os dados da câmera e a localização são removidos. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:132` | template:macro | Enviar imagem | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:135` | template:texto | O envio de imagens não está configurado neste ambiente. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:140` | template:texto | Ligação com a equipe | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:142` | template:texto | Marcada para | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:142` | template:texto | (horário de Brasília). | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | texto | `app/templates/identidade/briefing.html:144` | template:texto | Escolha um horário para conversar com a equipe sobre a marca. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:146` | template:macro | Ver a ligação | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/briefing | macro | `app/templates/identidade/briefing.html:146` | template:macro | Escolher horário | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:9` | template:macro | terça | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:9` | template:macro | sábado | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:10` | template:texto | Ligação · Identidade visual · Teroz | texto na tela | antes: “Ligação · Identidade visual · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:15` | template:texto | {…}Identidade visual | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:16` | template:texto | Ligação com a equipe | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:17` | template:texto | Uma conversa para entender a sua marca. Horários de Brasília. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:27` | template:texto | Sua ligação | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:28` | template:texto | , {…}, às | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:30` | template:texto | Duração | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:30` | template:texto | {…} min | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:31` | template:texto | Contato | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:34` | template:macro | Pedido enviado: | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:34` | template:macro | A equipe vai responder por e-mail. Até lá, o horário continua reservado. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:40` | template:texto | Precisa mudar? | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:41` | template:texto | A equipe recebe o pedido e responde por e-mail. Nada muda até ela responder. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:43` | template:texto | Remarcar | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:44` | template:texto | Cancelar | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:47` | template:macro | Enviar pedido | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:56` | template:texto | Escolha um horário | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:66` | template:texto | {…} min | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:74` | template:texto | Quem atende | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:77` | template:texto | Nome | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:77` | template:texto | (obrigatório) | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:81` | template:texto | Telefone com DDD | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | texto | `app/templates/identidade/ligacao.html:81` | template:texto | (obrigatório) | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:86` | template:macro | Reservar horário | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:90` | template:macro | Nenhum horário livre agora | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:90` | template:macro | A equipe abre novos horários toda semana. Volte em alguns dias ou responda o briefing enquanto isso. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| identidade/ligacao | macro | `app/templates/identidade/ligacao.html:90` | template:macro | Ir para o briefing | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |

</details>

<details><summary><b>Componentes e layout</b> (142)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| _base | content | `app/templates/_base.html:6` | template:content | width=device-width, initial-scale=1, viewport-fit=cover | metadado da página | — | — | técnico (não é copy) |
| _base | texto | `app/templates/_base.html:7` | template:texto | Teroz | texto na tela | antes: “Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| _base | content | `app/templates/_base.html:8` | template:content | {% block description %}Acompanhe a produção por etapas: unidades prontas, horas que faltam e prazo em dias úteis, do celular ao escritório.{% endblock %} | metadado da página | antes: “{% block description %}Acompanhe a produção por etapas: unidades concluídas, horas que faltam e prazo em dias úteis, do celular ao escritório.{% endblock %}” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| _base | content | `app/templates/_base.html:9` | template:content | light dark | metadado da página | — | — | revisado — mantido |
| _base | content | `app/templates/_base.html:21` | template:content | Teroz | metadado da página | antes: “Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| base_app | macro | `app/templates/base_app.html:23` | template:macro | Empresa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:26` | template:macro | Usuários | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:29` | template:macro | Assinatura | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:32` | template:macro | Privacidade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:33` | template:macro | Módulos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:37` | template:macro | Identidade visual | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:40` | template:macro | Modelos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:41` | template:macro | Planilha | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:43` | template:macro | Alertas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:50` | template:macro | Unidades | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:52` | template:macro | )) in (nav_settings \| map(attribute= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | content | `app/templates/base_app.html:56` | template:content | noindex, nofollow | metadado da página | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:60` | template:texto | Pular para o conteúdo | texto na tela | — | — | revisado — mantido |
| base_app | aria-label | `app/templates/base_app.html:62` | template:aria-label | Menu lateral | nome para leitor de tela | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:64` | template:macro | Teroz — Painel | rótulo, botão ou ajuda de componente | antes: “Teroz, Controle de Produção — Painel” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| base_app | texto | `app/templates/base_app.html:74` | template:texto | Configurações | texto na tela | — | — | revisado — mantido |
| base_app | aria-label | `app/templates/base_app.html:75` | template:aria-label | Configurações | nome para leitor de tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:84` | template:texto | Trocar empresa | texto na tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:89` | template:texto | Sair | texto na tela | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:95` | template:macro | Teroz — Painel | rótulo, botão ou ajuda de componente | antes: “Teroz, Controle de Produção — Painel” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| base_app | macro | `app/templates/base_app.html:96` | template:macro | Teroz | rótulo, botão ou ajuda de componente | antes: “Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| base_app | texto | `app/templates/base_app.html:97` | template:texto | Conta e opções de {…} | texto na tela | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:102` | template:macro | Confirme seu e-mail. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:102` | template:macro | Sem confirmar, o acesso dura 7 dias desde o cadastro. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:102` | template:macro | Reenviar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:105` | template:macro | Assinatura em modo leitura — registros pausados | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | macro | `app/templates/base_app.html:105` | template:macro | Dá para ver e exportar tudo. Para voltar a gravar, regularize a assinatura. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| base_app | aria-label | `app/templates/base_app.html:123` | template:aria-label | Fechar | nome para leitor de tela | — | — | revisado — mantido |
| base_app | aria-label | `app/templates/base_app.html:125` | template:aria-label | Mais | nome para leitor de tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:129` | template:texto | Perfil | texto na tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:131` | template:texto | Trocar empresa | texto na tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:136` | template:texto | Configurações | texto na tela | — | — | revisado — mantido |
| base_app | texto | `app/templates/base_app.html:145` | template:texto | Sair | texto na tela | — | — | revisado — mantido |
| components/alert | aria-label | `app/templates/components/alert.html:14` | template:aria-label | Fechar aviso | nome para leitor de tela | — | — | revisado — mantido |
| components/badge | texto | `app/templates/components/badge.html:4` | template:texto | "Concluída": ("success", "check"), | texto na tela | — | — | revisado — mantido |
| components/badge | texto | `app/templates/components/badge.html:5` | template:texto | "Em andamento": ("progress", "progress"), | texto na tela | — | — | revisado — mantido |
| components/badge | texto | `app/templates/components/badge.html:6` | template:texto | "Não iniciada": ("neutral", "circle"), | texto na tela | — | — | revisado — mantido |
| components/badge | texto | `app/templates/components/badge.html:7` | template:texto | "Atrasado": ("danger", "alert"), | texto na tela | — | — | revisado — mantido |
| components/brand | alt | `app/templates/components/brand.html:4` | template:alt | Teroz | descrição de imagem | — | — | revisado — mantido |
| components/brand | alt | `app/templates/components/brand.html:5` | template:alt | Teroz | descrição de imagem | texto novo na revisão | aplicado (texto atual) | incluído |
| components/brand | macro | `app/templates/components/brand.html:9` | template:macro | Teroz | rótulo, botão ou ajuda de componente | texto novo na revisão | aplicado (texto atual) | incluído |
| components/button | macro | `app/templates/components/button.html:4` | template:macro | btn btn-- | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/button | macro | `app/templates/components/button.html:4` | template:macro | if block else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/button | macro | `app/templates/components/button.html:4` | template:macro | if icon_only else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/button | macro | `app/templates/components/button.html:4` | template:macro | if loading else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/button | macro | `app/templates/components/button.html:4` | template:macro | ~ class_) if class_ else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/chart | macro | `app/templates/components/chart.html:2` | template:macro | , orientation= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/chart | macro | `app/templates/components/chart.html:2` | template:macro | , table_headers=( | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/chart | texto | `app/templates/components/chart.html:8` | template:texto | Sem registros neste período. | texto na tela | — | — | revisado — mantido |
| components/chart | texto | `app/templates/components/chart.html:40` | template:texto | Ver dados em tabela | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:5` | template:texto | Exportar | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:8` | template:texto | Planilha no formato da equipe (.xlsx) | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:9` | template:texto | Etapas, totais, Tabelas 1 e 2 e aba Equipe, com fórmulas | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:11` | template:texto | Lista simples | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:13` | template:texto | Lista simples (.csv) | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:14` | template:texto | Uma linha por subatividade | texto na tela | antes: “Uma linha por atividade” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| components/export_menu | texto | `app/templates/components/export_menu.html:17` | template:texto | Lista simples (.xlsx) | texto na tela | — | — | revisado — mantido |
| components/export_menu | texto | `app/templates/components/export_menu.html:18` | template:texto | Uma linha por subatividade, para filtrar no Excel | texto na tela | antes: “Uma linha por atividade, para filtrar no Excel” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| components/field | texto | `app/templates/components/field.html:17` | template:texto | (obrigatório) | texto na tela | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:18` | template:macro | PasswordField | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | texto | `app/templates/components/field.html:19` | template:texto | Mostrar | texto na tela | — | — | revisado — mantido |
| components/field | title | `app/templates/components/field.html:38` | template:title | Confira os campos destacados | dica ao passar o mouse | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:38` | template:macro | Item | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:40` | template:macro | CSRFTokenField | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:40` | template:macro | HiddenField | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:41` | template:macro | FieldList | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:46` | template:macro | ~ outer ~ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | macro | `app/templates/components/field.html:70` | template:macro | Escolher arquivo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/field | texto | `app/templates/components/field.html:81` | template:texto | Nenhum arquivo escolhido | texto na tela | — | — | revisado — mantido |
| components/kpi | macro | `app/templates/components/kpi.html:3` | template:macro | sem dados ainda | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/kpi | macro | `app/templates/components/kpi.html:4` | template:macro | if href else | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/modal | macro | `app/templates/components/modal.html:3` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | macro | `app/templates/components/nav.html:3` | template:macro | Principal | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | macro | `app/templates/components/nav.html:12` | template:macro | Mais | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | aria-label | `app/templates/components/nav.html:13` | template:aria-label | Principal | nome para leitor de tela | — | — | revisado — mantido |
| components/nav | aria-label | `app/templates/components/nav.html:27` | template:aria-label | Fechar aviso | nome para leitor de tela | — | — | revisado — mantido |
| components/nav | texto | `app/templates/components/nav.html:38` | template:texto | Tema | texto na tela | — | — | revisado — mantido |
| components/nav | macro | `app/templates/components/nav.html:40` | template:macro | Sistema | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | macro | `app/templates/components/nav.html:40` | template:macro | Claro | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | macro | `app/templates/components/nav.html:40` | template:macro | Escuro | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/nav | texto | `app/templates/components/nav.html:48` | template:texto | Aplicar tema | texto na tela | — | — | revisado — mantido |
| components/optional | texto | `app/templates/components/optional.html:3` | template:texto | Opcional | texto na tela | — | — | revisado — mantido |
| components/optional | title | `app/templates/components/optional.html:3` | template:title | Módulo opcional: o proprietário liga ou desliga em Configurações › Módulos | dica ao passar o mouse | — | — | revisado — mantido |
| components/pagination | aria-label | `app/templates/components/pagination.html:6` | template:aria-label | Paginação | nome para leitor de tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:7` | template:texto | Mostrando {…}–{…} de {…} | texto na tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:11` | template:texto | Anterior | texto na tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:13` | template:texto | Anterior | texto na tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:15` | template:texto | Página {…} de {…} | texto na tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:26` | template:texto | Próxima | texto na tela | — | — | revisado — mantido |
| components/pagination | texto | `app/templates/components/pagination.html:28` | template:texto | Próxima | texto na tela | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:5` | template:texto | Recomendado | texto na tela | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:8` | template:texto | Sob orçamento | texto na tela | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:8` | template:texto | online ou presencial | texto na tela | — | — | revisado — mantido |
| components/plan_card | macro | `app/templates/components/plan_card.html:17` | template:macro | dias grátis, sem cartão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/plan_card | macro | `app/templates/components/plan_card.html:17` | template:macro | Valor combinado em orçamento, sem teste grátis | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/plan_card | macro | `app/templates/components/plan_card.html:17` | template:macro | Sem teste grátis: a cobrança começa ao contratar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:20` | template:texto | Fale conosco | texto na tela | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:22` | template:texto | Começar teste grátis | texto na tela | — | — | revisado — mantido |
| components/plan_card | texto | `app/templates/components/plan_card.html:24` | template:texto | Começar com o {…} | texto na tela | — | — | revisado — mantido |
| components/progress | macro | `app/templates/components/progress.html:2` | template:macro | Progresso | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | aria-label | `app/templates/components/stepper.html:7` | template:aria-label | Diminuir quantidade | nome para leitor de tela | — | — | revisado — mantido |
| components/stepper | aria-label | `app/templates/components/stepper.html:9` | template:aria-label | Aumentar quantidade | nome para leitor de tela | — | — | revisado — mantido |
| components/stepper | aria-label | `app/templates/components/stepper.html:24` | template:aria-label | Fechar | nome para leitor de tela | — | — | revisado — mantido |
| components/stepper | texto | `app/templates/components/stepper.html:26` | template:texto | {…} de {…} prontas · faltam {…} | texto na tela | antes: “{…} de {…} concluídas · faltam {…}” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| components/stepper | texto | `app/templates/components/stepper.html:33` | template:texto | Quantidade a somar em {…} | texto na tela | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:35` | template:macro | ~ sid ~ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:35` | template:macro | , label= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:35` | template:macro | ~ activity_name, describedby=sid ~ | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | texto | `app/templates/components/stepper.html:36` | template:texto | quantidade a somar (editável) | texto na tela | — | — | revisado — mantido |
| components/stepper | texto | `app/templates/components/stepper.html:40` | template:texto | (→ {…} de {…}) | texto na tela | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:40` | template:macro | Confirmar e somar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:40` | template:macro | Registrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:41` | template:macro | Confirmar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/stepper | macro | `app/templates/components/stepper.html:41` | template:macro | Registrar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/steps | macro | `app/templates/components/steps.html:3` | template:macro | Passos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| components/steps | texto | `app/templates/components/steps.html:9` | template:texto | Passo {…} de {…} , feito : | texto na tela | — | — | revisado — mantido |
| components/toast | aria-label | `app/templates/components/toast.html:7` | template:aria-label | Fechar mensagem | nome para leitor de tela | — | — | revisado — mantido |
| errors/400 | texto | `app/templates/errors/400.html:2` | template:texto | Pedido não concluído · Teroz | texto na tela | antes: “Requisição inválida · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| errors/400 | texto | `app/templates/errors/400.html:4` | template:texto | Pedido não concluído | texto na tela | antes: “Não deu para concluir” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| errors/400 | macro | `app/templates/errors/400.html:5` | template:macro | Algo no envio não veio como esperado. Volte à página anterior e tente de novo. | rótulo, botão ou ajuda de componente | antes: “Requisição inválida.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| errors/402 | macro | `app/templates/errors/402.html:8` | template:macro | Ver planos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| errors/402 | macro | `app/templates/errors/402.html:9` | template:macro | Ir para Projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| errors/403 | texto | `app/templates/errors/403.html:2` | template:texto | Acesso negado · Teroz | texto na tela | antes: “Acesso negado · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| errors/403 | texto | `app/templates/errors/403.html:4` | template:texto | Você não tem permissão para fazer isso | texto na tela | antes: “Você não tem permissão para isto” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| errors/403 | texto | `app/templates/errors/403.html:5` | template:texto | Peça a um supervisor ou proprietário. | texto na tela | — | — | revisado — mantido |
| errors/404 | texto | `app/templates/errors/404.html:2` | template:texto | Página não encontrada · Teroz | texto na tela | antes: “Página não encontrada · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| errors/404 | texto | `app/templates/errors/404.html:4` | template:texto | Página não encontrada | texto na tela | — | — | revisado — mantido |
| errors/404 | texto | `app/templates/errors/404.html:5` | template:texto | O endereço pode ter mudado ou você não tem acesso a este item. | texto na tela | — | — | revisado — mantido |
| errors/429 | texto | `app/templates/errors/429.html:2` | template:texto | Muitas tentativas · Teroz | texto na tela | antes: “Muitas tentativas · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| errors/429 | texto | `app/templates/errors/429.html:4` | template:texto | Muitas tentativas | texto na tela | — | — | revisado — mantido |
| errors/429 | texto | `app/templates/errors/429.html:5` | template:texto | Aguarde alguns minutos e tente de novo. | texto na tela | — | — | revisado — mantido |
| errors/500 | texto | `app/templates/errors/500.html:4` | template:texto | Erro inesperado · Teroz | texto na tela | antes: “Erro inesperado · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| errors/500 | texto | `app/templates/errors/500.html:6` | template:texto | Algo deu errado do nosso lado | texto na tela | — | — | revisado — mantido |
| errors/500 | texto | `app/templates/errors/500.html:7` | template:texto | Tente de novo em instantes. Se o erro continuar, escreva para o contato do site. | texto na tela | antes: “Já fomos avisados. Tente de novo em instantes.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| errors/500 | macro | `app/templates/errors/500.html:9` | template:macro | Página inicial | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| errors/_layout | macro | `app/templates/errors/_layout.html:14` | template:macro | Ir para Projetos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| errors/_layout | macro | `app/templates/errors/_layout.html:16` | template:macro | Página inicial | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>Empresa, módulos e LGPD</b> (127)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/empresa.py | flash | `app/blueprints/empresa.py:78` | backend:flash | Dados da empresa salvos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/empresa.py | flash | `app/blueprints/empresa.py:94` | backend:flash | Feriado incluído. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/empresa.py | flash | `app/blueprints/empresa.py:105` | backend:flash | Feriado removido. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/empresa.py | _modules_page | `app/blueprints/empresa.py:159` | backend:_modules_page | Módulo desconhecido. Recarregue a página e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/empresa.py | _modules_page | `app/blueprints/empresa.py:164` | backend:_modules_page | Módulo desconhecido. Recarregue a página e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/empresa.py | flash | `app/blueprints/empresa.py:167` | backend:flash | Nada mudou nos módulos. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/empresa.py | flash | `app/blueprints/empresa.py:170` | backend:flash | Módulos salvos: {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/lgpd.py | _limit | `app/blueprints/lgpd.py:57` | backend:_limit | 3 per hour | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | _page | `app/blueprints/lgpd.py:62` | backend:_page | Formulário expirado. Tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | valor | `app/blueprints/lgpd.py:67` | backend:valor | attachment; filename="{…}" | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/lgpd.py | _limit | `app/blueprints/lgpd.py:73` | backend:_limit | 5 per hour | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | _page | `app/blueprints/lgpd.py:80` | backend:_page | Senha incorreta. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | _page | `app/blueprints/lgpd.py:82` | backend:_page | O nome digitado não confere com o da empresa. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | flash | `app/blueprints/lgpd.py:85` | backend:flash | Exclusão agendada para {…}. Você pode cancelar até lá. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/lgpd.py | _page | `app/blueprints/lgpd.py:94` | backend:_page | Formulário expirado. Tente de novo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | flash | `app/blueprints/lgpd.py:97` | backend:flash | Exclusão cancelada. Nada foi apagado. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:114` | backend:option | Só mostra o que seria apagado. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:115` | backend:option | Quem está rodando (vai para platform_audit_logs). | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:120` | backend:echo | Nenhuma empresa com carência vencida. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | valor | `app/blueprints/lgpd.py:124` | backend:valor | seria apagada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:126` | backend:echo | Empresa {…} {…}: {…} linha(s), até {…} usuário(s), {…} arquivo(s) de foto. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:132` | backend:option | Só conta o que seria apagado. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | AppGroup | `app/blueprints/lgpd.py:141` | backend:AppGroup | Acesso temporário de suporte (auditado; avisa os proprietários). | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:146` | backend:option | Id (UUID) da empresa. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:147` | backend:option | Motivo (chamado, pedido do cliente...). Vai para a auditoria e o e-mail. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | option | `app/blueprints/lgpd.py:150` | backend:option | Quem autorizou o acesso. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:160` | backend:echo | Acesso concedido até {…} UTC. Proprietários avisados por e-mail. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:174` | backend:echo | Acesso revogado. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:174` | backend:echo | Nada a revogar. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:183` | backend:echo | Nenhum acesso de suporte ativo. | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:185` | backend:echo | {…} empresa={…} papel={…} até={…} | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:193` | backend:echo | {…} acesso(s) expirado(s). | mensagem do backend | — | — | revisado — mantido |
| blueprints/lgpd.py | echo | `app/blueprints/lgpd.py:204` | backend:echo | {…} segredo(s) recifrado(s). | mensagem do backend | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:16` | backend:formulário | Nome da empresa | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:19` | backend:formulário | Jornada padrão (horas por dia) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:25` | backend:formulário | Dias de trabalho | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:33` | backend:formulário | Alerta de etapa parada (dias úteis sem lançamento) | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:39` | backend:formulário | Informe a data do feriado. | rótulo ou validação de campo | — | — | revisado — mantido |
| forms_company.py | formulário | `app/forms_company.py:40` | backend:formulário | Nome do feriado | rótulo ou validação de campo | — | — | revisado — mantido |
| models/privacy.py | erro | `app/models/privacy.py:39` | backend:erro | platform_audit_logs é append-only. | mensagem de erro | — | — | revisado — mantido |
| models/privacy.py | erro | `app/models/privacy.py:44` | backend:erro | platform_audit_logs é append-only. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:77` | backend:erro | Informe o nome da empresa (até 120 caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:80` | backend:erro | CNPJ inválido. Confira os 14 dígitos. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:83` | backend:erro | Marque pelo menos um dia de trabalho na semana. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:85` | backend:erro | A jornada deve ficar entre 0,5 e 24 horas por dia. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:90` | backend:erro | Etapa parada: informe de {…} a {…} dias úteis. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:123` | backend:erro | Dê um nome ao feriado (até 120 caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:125` | backend:erro | Data fora do intervalo aceito. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:128` | backend:erro | Já existe um feriado da empresa nesta data. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:131` | backend:erro | Limite de {…} feriados da empresa atingido. | mensagem de erro | — | — | revisado — mantido |
| services/company.py | erro | `app/services/company.py:149` | backend:erro | Feriados nacionais não podem ser removidos. | mensagem de erro | — | — | revisado — mantido |
| services/lgpd.py | valor | `app/services/lgpd.py:161` | backend:valor | Exportação de dados da empresa — Teroz Gerada em {…} (UTC). Um arquivo CSV por tabela (separador ';', UTF-8 com BOM, abre no Excel). Datas em ISO 8601 (UTC). Textos que começam com = + - @ ganham um apóstrofo para a p… | valor exibido (rótulo, opção, situação) | antes: “Exportação de dados da empresa — Controle de Produção Gerada em {…} (UTC). Um arquivo CSV por tabela (separador ';', UTF-8 com BOM, abre no Excel). Datas em ISO 8601 (UTC). Textos que começam com = + - @ ganham um apó…” — marca: o produto se chama Teroz; glossário: atividade → subatividade; sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| services/lgpd.py | _notify_owners | `app/services/lgpd.py:248` | backend:_notify_owners | Exclusão da empresa agendada | mensagem do backend | — | — | revisado — mantido |
| services/lgpd.py | _notify_owners | `app/services/lgpd.py:263` | backend:_notify_owners | Exclusão da empresa cancelada | mensagem do backend | — | — | revisado — mantido |
| services/lgpd.py | erro | `app/services/lgpd.py:313` | backend:erro | Empresa sem pedido de exclusão ou ainda na carência. | mensagem de erro | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:61` | backend:Module | Responsáveis e progresso por pessoa | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:62` | backend:Module | Escolha quem cuida de cada subatividade, avise a pessoa por e-mail e veja quantas peças cada um lançou. | mensagem do backend | antes: “Escolha quem cuida de cada atividade, avise a pessoa por e-mail e veja quantas peças cada um lançou.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/modules.py | Module | `app/services/modules.py:63` | backend:Module | Campo “Responsável”, quadro “Pessoas” e a tela de progresso por pessoa. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:68` | backend:Module | Alertas e relatório semanal por e-mail | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:69` | backend:Module | Avisa quando um prazo está em risco ou uma etapa parou, e manda um resumo toda segunda-feira. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:70` | backend:Module | Tela de alertas e os e-mails de alerta e do relatório semanal. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:75` | backend:Module | Aguardando peça | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:76` | backend:Module | Marque a etapa que parou por falta de peça, com a data prevista de chegada. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:77` | backend:Module | Marca “Aguardando peça” nas etapas, no painel e na lista de projetos. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:82` | backend:Module | Fotos e comentários | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:83` | backend:Module | Guarde fotos e comentários em cada subatividade, como registro do que foi feito. | mensagem do backend | antes: “Guarde fotos e comentários em cada atividade, como registro do que foi feito.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/modules.py | Module | `app/services/modules.py:84` | backend:Module | Botão “Fotos e comentários” nas etapas e a tela de cada subatividade. | mensagem do backend | antes: “Botão “Fotos e comentários” nas etapas e a tela de cada atividade.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/modules.py | Module | `app/services/modules.py:96` | backend:Module | Checklist de inspeção | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:97` | backend:Module | Lista de conferência por etapa, preenchida e assinada por quem inspecionou. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:98` | backend:Module | Checklist nas etapas e nos modelos, e as telas de inspeção. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:112` | backend:Module | Número de série por unidade | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:113` | backend:Module | Cadastre o número de série de cada unidade e veja o histórico de cada uma. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:114` | backend:Module | Telas de unidades e a busca por número de série. | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:127` | backend:Module | API de integração | mensagem do backend | — | — | revisado — mantido |
| services/modules.py | Module | `app/services/modules.py:128` | backend:Module | Ligue outros sistemas à Teroz com tokens de acesso. | mensagem do backend | antes: “Ligue outros sistemas ao Controle de Produção com tokens de acesso.” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| services/modules.py | Module | `app/services/modules.py:129` | backend:Module | Tela de tokens e o endereço /api/v1. | mensagem do backend | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:8` | template:texto | Módulos · Teroz | texto na tela | antes: “Módulos · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:13` | template:texto | Módulos | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:14` | template:texto | O essencial é acompanhar as etapas. O resto é opcional: ligue só o que a sua equipe usa. | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:20` | template:texto | Sempre ligado | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:21` | template:texto | Painel, Preencher etapas, Meta e equipe, Como funciona, Projetos, Histórico e Planilha. | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:28` | template:texto | Módulos opcionais | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:29` | template:texto | Desligar esconde o módulo para todos na empresa, mas não apaga nada. Ao ligar de novo, tudo volta como estava. | texto na tela | — | — | revisado — mantido |
| empresa/modulos | macro | `app/templates/empresa/modulos.html:40` | template:macro | Ligado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/modulos | macro | `app/templates/empresa/modulos.html:40` | template:macro | Desligado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:44` | template:texto | Onde aparece: {…} | texto na tela | — | — | revisado — mantido |
| empresa/modulos | texto | `app/templates/empresa/modulos.html:46` | template:texto | O plano {…} não inclui a API. Ligado, o módulo só passa a funcionar num plano com API. | texto na tela | — | — | revisado — mantido |
| empresa/modulos | macro | `app/templates/empresa/modulos.html:53` | template:macro | Salvar módulos | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:10` | template:texto | Empresa · Teroz | texto na tela | antes: “Empresa · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| empresa/settings | texto | `app/templates/empresa/settings.html:15` | template:texto | Empresa | texto na tela | — | — | revisado — mantido |
| empresa/settings | aria-label | `app/templates/empresa/settings.html:21` | template:aria-label | Seções da empresa | nome para leitor de tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:22` | template:texto | Dados | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:23` | template:texto | Calendário | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:24` | template:texto | Feriados | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:26` | template:texto | Alertas | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:28` | template:texto | Módulos | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:36` | template:texto | Dados da empresa | texto na tela | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:38` | template:macro | 14 dígitos; conferimos o dígito verificador. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:39` | template:texto | Calendário | texto na tela | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:40` | template:macro | Sugerida nos novos projetos. Cada projeto tem a sua. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:42` | template:texto | Dias de trabalho | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:48` | template:texto | Fins de semana e feriados não contam nos dias úteis. | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:51` | template:texto | Alertas | texto na tela | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:52` | template:macro | Etapa em andamento sem nenhum lançamento por este número de dias úteis gera o alerta “etapa parada”. De 1 a 60; padrão 3. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:54` | template:macro | Salvar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:58` | template:texto | Feriados da empresa | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:59` | template:texto | Os feriados nacionais já entram automaticamente. Inclua aqui recessos e feriados municipais. | texto na tela | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:64` | template:macro | Recesso de fim de ano | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:65` | template:macro | Incluir feriado | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:68` | template:macro | Data | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | macro | `app/templates/empresa/settings.html:68` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:77` | template:texto | Remover | texto na tela | — | — | revisado — mantido |
| empresa/settings | aria-label | `app/templates/empresa/settings.html:77` | template:aria-label | Remover feriado {…} de {…} | nome para leitor de tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:85` | template:texto | Nenhum feriado próprio ainda. | texto na tela | — | — | revisado — mantido |
| empresa/settings | texto | `app/templates/empresa/settings.html:89` | template:texto | Próximos feriados nacionais (automáticos) | texto na tela | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:6` | template:texto | Privacidade e dados · Teroz | texto na tela | antes: “Privacidade e dados · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| lgpd/index | texto | `app/templates/lgpd/index.html:11` | template:texto | Privacidade e dados | texto na tela | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:12` | template:texto | Direitos da empresa sobre os dados guardados aqui (LGPD). | texto na tela | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:21` | template:texto | Exportar todos os dados | texto na tela | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:22` | template:texto | Baixe um arquivo ZIP com uma planilha CSV para cada tipo de dado da empresa: projetos, etapas, subatividades, registros de peças, modelos, usuários, convites, assinatura, auditoria e integrações. Senhas e chaves não s… | texto na tela | antes: “Baixe um arquivo ZIP com uma planilha CSV para cada tipo de dado da empresa: projetos, etapas, atividades, registros de peças, modelos, usuários, convites, assinatura, auditoria e integrações. Senhas e chaves não são …” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| lgpd/index | macro | `app/templates/lgpd/index.html:25` | template:macro | Baixar ZIP | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:30` | template:texto | Excluir a empresa | texto na tela | — | — | revisado — mantido |
| lgpd/index | macro | `app/templates/lgpd/index.html:32` | template:macro | Exclusão agendada | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| lgpd/index | macro | `app/templates/lgpd/index.html:32` | template:macro | Todos os dados da empresa serão apagados definitivamente em | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| lgpd/index | macro | `app/templates/lgpd/index.html:35` | template:macro | Cancelar a exclusão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| lgpd/index | texto | `app/templates/lgpd/index.html:38` | template:texto | A exclusão apaga projetos, histórico, modelos, usuários sem outra empresa, assinatura e auditoria. Há uma carência de {…} dias para você mudar de ideia; depois disso não há como recuperar. Exporte os dados antes. | texto na tela | — | — | revisado — mantido |
| lgpd/index | macro | `app/templates/lgpd/index.html:43` | template:macro | Pedir exclusão da empresa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |

</details>

<details><summary><b>Outros</b> (108)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| __init__.py | valor | `app/__init__.py:146` | backend:valor | Entre para continuar. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| __init__.py | page | `app/__init__.py:169` | backend:page | Formulário expirado ou inválido. Recarregue a página e tente de novo. | mensagem do backend | — | — | revisado — mantido |
| __init__.py | page | `app/__init__.py:173` | backend:page | Algo no envio não veio como esperado. Volte à página anterior e tente de novo. | mensagem do backend | antes: “Requisição inválida.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| __init__.py | page | `app/__init__.py:185` | backend:page | Esta página não aceita esse envio. Volte e tente pela tela. | mensagem do backend | antes: “Método não permitido.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| blueprints/webhooks.py | error | `app/blueprints/webhooks.py:44` | backend:error | webhook asaas recusado: ASAAS_WEBHOOK_TOKEN não configurado | mensagem de erro | — | — | revisado — mantido |
| blueprints/webhooks.py | jsonify | `app/blueprints/webhooks.py:56` | backend:jsonify | payload too large | mensagem do backend | — | — | revisado — mantido |
| blueprints/webhooks.py | jsonify | `app/blueprints/webhooks.py:59` | backend:jsonify | invalid payload | mensagem do backend | — | — | revisado — mantido |
| blueprints/webhooks.py | error | `app/blueprints/webhooks.py:82` | backend:error | webhook asaas %s %s falhou: %s | mensagem de erro | — | — | revisado — mantido |
| formatting.py | valor | `app/formatting.py:73` | backend:valor | Hoje, {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| formatting.py | valor | `app/formatting.py:75` | backend:valor | Ontem, {…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| models/platform.py | erro | `app/models/platform.py:37` | backend:erro | audit_logs é append-only: não pode ser alterado. | mensagem de erro | — | — | revisado — mantido |
| models/platform.py | erro | `app/models/platform.py:42` | backend:erro | audit_logs é append-only: não pode ser apagado. | mensagem de erro | — | — | revisado — mantido |
| models/production.py | erro | `app/models/production.py:185` | backend:erro | progress_entries é append-only: não pode ser alterado. | mensagem de erro | — | — | revisado — mantido |
| models/production.py | erro | `app/models/production.py:190` | backend:erro | progress_entries é append-only: não pode ser apagado. | mensagem de erro | — | — | revisado — mantido |
| models/quality.py | erro | `app/models/quality.py:201` | backend:erro | Resposta assinada não muda: registre uma correção (nova linha). | mensagem de erro | — | — | revisado — mantido |
| models/quality.py | erro | `app/models/quality.py:207` | backend:erro | Resposta assinada não pode ser apagada. | mensagem de erro | — | — | revisado — mantido |
| models/templates.py | valor | `app/models/templates.py:48` | backend:valor | TemplateVersion \| None | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| security.py | valor | `app/security.py:31` | backend:valor | accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=(), browsing-topics=() | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| security.py | valor | `app/security.py:34` | backend:valor | max-age=63072000; includeSubDomains | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| security.py | append | `app/security.py:116` | backend:append | {…}_COOKIE_NAME sem __Host- | mensagem do backend | — | — | revisado — mantido |
| security.py | append | `app/security.py:118` | backend:append | SESSION_COOKIE_DOMAIN (incompatível com __Host-) | mensagem do backend | — | — | revisado — mantido |
| security.py | erro | `app/security.py:120` | backend:erro | Cookies inseguros em produção: | mensagem de erro | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:50` | backend:valor | Alertas de produção | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:53` | backend:valor | Atraso previsto | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:54` | backend:valor | Prazo em risco | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:55` | backend:valor | Etapa parada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:56` | backend:valor | Peça atrasada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:77` | backend:valor | Término previsto em {…}, depois do prazo de {…} ({…} de atraso). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:83` | backend:valor | O prazo de {…} passou há {…} e o projeto não terminou. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:88` | backend:valor | Término previsto em {…}, com folga de só {…} até o prazo ({…}). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:92` | backend:valor | Prazo em {…} ({…}) e sem previsão de término (confira a equipe do projeto). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:97` | backend:valor | Etapa “{…}” sem lançamento há {…} (último em {…}). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/alerts.py | valor | `app/services/alerts.py:102` | backend:valor | Etapa “{…}” aguardando peça: a previsão era {…} e a marca não foi atualizada. Confirme a nova data ou retire a marca. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/calc.py | valor | `app/services/calc.py:32` | backend:valor | Em andamento | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/calc.py | valor | `app/services/calc.py:33` | backend:valor | Não iniciada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/calc.py | erro | `app/services/calc.py:247` | backend:erro | dias_semana não pode ser vazio | mensagem de erro | — | — | revisado — mantido |
| services/calc.py | erro | `app/services/calc.py:740` | backend:erro | dias_parada fora de 1..60 | mensagem de erro | — | — | revisado — mantido |
| services/calc.py | valor | `app/services/calc.py:857` | backend:valor | (preencha a primeira etapa) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:907` | backend:add | % concluído da etapa | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:908` | backend:add | Você digita o % da etapa. O sistema guarda como unidades: % × meta, arredondado. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:913` | backend:add | Peso da subatividade na etapa | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:914` | backend:add | Tempo ideal da subatividade ÷ soma dos tempos da etapa. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:915` | backend:add | {…}: {…} min ÷ {…} min = {…} | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:918` | backend:add | Peso da etapa no projeto | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:919` | backend:add | Tempo da etapa ÷ tempo de 1 unidade (soma de todas as etapas). | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:920` | backend:add | Etapa sem tempo informado vale 60 min. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:921` | backend:add | {…}: {…} min ÷ {…} min = {…} | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:925` | backend:add | % concluído da subatividade | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:926` | backend:add | Peças prontas ÷ meta. Você só digita as peças. | mensagem do backend | antes: “Peças concluídas ÷ unidades previstas. Você só digita as peças.” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:930` | backend:add | Progresso da etapa pelas tarefas (Tabela 1) | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:931` | backend:add | Soma de (peso × % concluído) das subatividades. Conta as parciais. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:935` | backend:add | Unidades prontas da etapa (Tabela 2) | mensagem do backend | antes: “Unidades concluídas da etapa (Tabela 2)” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:936` | backend:add | Menor número de peças prontas entre as subatividades: uma unidade só está pronta quando passou por todas. | mensagem do backend | antes: “Menor número de peças concluídas entre as subatividades: uma unidade só está pronta quando passou por todas.” — glossário: atividade → subatividade; glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:938` | backend:add | {…}: menor nº de peças = {…} → {…} ÷ {…} = {…}, mesmo com as tarefas em {…} | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:943` | backend:add | Tempo total da subatividade | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:944` | backend:add | Tempo ideal × meta. | mensagem do backend | antes: “Tempo ideal × unidades previstas.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:945` | backend:add | {…}: {…} min × {…} = {…} min | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:948` | backend:add | Tempo que falta | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:949` | backend:add | Tempo ideal × (meta − peças prontas). | mensagem do backend | antes: “Tempo ideal × (previstas − peças concluídas).” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:951` | backend:add | {…}: {…} min × ({…} − {…}) = {…} min | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:957` | backend:add | Tempo que falta da etapa | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:958` | backend:add | Tempo da etapa × (meta − unidades prontas). | mensagem do backend | antes: “Tempo da etapa × (previstas − unidades concluídas).” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:960` | backend:add | {…}: {…} min × ({…} − {…}) = {…} min | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:965` | backend:add | Unidades prontas do projeto | mensagem do backend | antes: “Unidades concluídas do projeto” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:966` | backend:add | Menor número de unidades prontas entre todas as etapas: uma unidade só está pronta quando passou por todas. | mensagem do backend | antes: “Menor número de unidades concluídas entre todas as etapas: uma unidade só está pronta quando passou por todas.” — glossário: concluídas → prontas | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:967` | backend:add | Menor valor entre as etapas = {…} de {…} | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:970` | backend:add | Progresso pelas tarefas do projeto | mensagem do backend | antes: “Progresso geral” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/calc.py | add | `app/services/calc.py:971` | backend:add | 1 − tempo que falta ÷ tempo total, somando todas as etapas. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:975` | backend:add | (informe o tempo das etapas) | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:980` | backend:add | Dias úteis restantes (Meta e equipe) | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:981` | backend:add | Tempo que falta ÷ (pessoas × horas por dia). | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:983` | backend:add | {…} h ÷ ({…} × {…} h) = {…} dias úteis | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:986` | backend:add | (informe pessoas e horas por dia) | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:990` | backend:add | Dias úteis para a meta inteira | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:991` | backend:add | Tempo total ÷ (pessoas × horas por dia), como se começasse do zero. | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:993` | backend:add | {…} h ÷ ({…} × {…} h) = {…} dias úteis | mensagem do backend | — | — | revisado — mantido |
| services/calc.py | add | `app/services/calc.py:996` | backend:add | (informe pessoas e horas por dia) | mensagem do backend | — | — | revisado — mantido |
| services/events.py | erro | `app/services/events.py:48` | backend:erro | Tipo de evento desconhecido: {…} | mensagem de erro | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:20` | backend:valor | Confraternização Universal | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:22` | backend:valor | Dia do Trabalho | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:23` | backend:valor | Independência do Brasil | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:24` | backend:valor | Nossa Senhora Aparecida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:26` | backend:valor | Proclamação da República | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | valor | `app/services/holidays.py:27` | backend:valor | Dia Nacional de Zumbi e da Consciência Negra | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/holidays.py | append | `app/services/holidays.py:51` | backend:append | Sexta-feira da Paixão | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:72` | backend:erro | Chave de objeto inválida. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | StorageDisabled | `app/services/storage.py:98` | backend:StorageDisabled | Armazenamento de fotos não configurado. | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | StorageDisabled | `app/services/storage.py:101` | backend:StorageDisabled | Armazenamento de fotos não configurado. | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | StorageDisabled | `app/services/storage.py:104` | backend:StorageDisabled | Armazenamento de fotos não configurado. | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:118` | backend:erro | Chave de objeto inválida. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | ObjectNotFound | `app/services/storage.py:138` | backend:ObjectNotFound | Objeto não encontrado. | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:179` | backend:erro | Requisição assinada não aceita query string. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | valor | `app/services/storage.py:202` | backend:valor | AWS4-HMAC-SHA256 Credential={…}/{…}, SignedHeaders={…}, Signature={…} | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:227` | backend:erro | STORAGE_S3_ENDPOINT precisa ser https://. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:229` | backend:erro | STORAGE_S3_BUCKET inválido. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:231` | backend:erro | STORAGE_S3_ADDRESSING deve ser path ou virtual. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | valor | `app/services/storage.py:247` | backend:valor | <S3Storage {…}://{…} bucket={…} region={…}> | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:268` | backend:erro | Falha ao falar com o armazenamento de fotos. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:276` | backend:erro | O armazenamento recusou a foto. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | ObjectNotFound | `app/services/storage.py:281` | backend:ObjectNotFound | Objeto não encontrado. | mensagem do backend | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:284` | backend:erro | Falha ao ler a foto. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:291` | backend:erro | Falha ao apagar a foto. | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:303` | backend:erro | STORAGE_BACKEND desconhecido: {…} (use local, s3 ou none). | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:311` | backend:erro | STORAGE_BACKEND=local é só para development/test; em produção use s3 (R2/S3). | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:318` | backend:erro | STORAGE_BACKEND=s3 exige | mensagem de erro | — | — | revisado — mantido |
| services/storage.py | erro | `app/services/storage.py:320` | backend:erro | STORAGE_S3_ENDPOINT precisa ser https:// fora de development/test. | mensagem de erro | — | — | revisado — mantido |
| tenancy.py | erro | `app/tenancy.py:100` | backend:erro | Papel desconhecido: {…} | mensagem de erro | — | — | revisado — mantido |
| tenancy.py | erro | `app/tenancy.py:134` | backend:erro | Nenhuma empresa ativa: use tenant_required antes de consultar dados. | mensagem de erro | — | — | revisado — mantido |

</details>

<details><summary><b>Assinatura e planos</b> (94)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/billing.py | erro | `app/blueprints/billing.py:36` | backend:erro | CPF ou CNPJ inválido: confira os números. | mensagem de erro | — | — | revisado — mantido |
| blueprints/billing.py | formulário | `app/blueprints/billing.py:40` | backend:formulário | Nome ou razão social | rótulo ou validação de campo | — | — | revisado — mantido |
| blueprints/billing.py | formulário | `app/blueprints/billing.py:41` | backend:formulário | CPF ou CNPJ | rótulo ou validação de campo | — | — | revisado — mantido |
| blueprints/billing.py | formulário | `app/blueprints/billing.py:43` | backend:formulário | E-mail de cobrança | rótulo ou validação de campo | — | — | revisado — mantido |
| blueprints/billing.py | valor | `app/blueprints/billing.py:164` | backend:valor | Plano {…} em vigor. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/billing.py | valor | `app/blueprints/billing.py:166` | backend:valor | Troca para {…} pedida: os novos limites valem assim que a fatura no valor novo for paga. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/billing.py | valor | `app/blueprints/billing.py:169` | backend:valor | Troca para {…} agendada: vale a partir de {…}, fim do período já pago. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| blueprints/billing.py | flash | `app/blueprints/billing.py:212` | backend:flash | Assinatura criada. A fatura aparece aqui assim que o Asaas gerar. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/billing.py | flash | `app/blueprints/billing.py:216` | backend:flash | Dados de cobrança atualizados. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/billing.py | flash | `app/blueprints/billing.py:270` | backend:flash | Assinatura cancelada. Acesso completo até {…}. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/billing.py | flash | `app/blueprints/billing.py:270` | backend:flash | Assinatura cancelada. | confirmação ou aviso após ação | — | — | revisado — mantido |
| models/billing.py | valor | `app/models/billing.py:33` | backend:valor | {…} IN ( | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/asaas.py | erro | `app/services/billing/asaas.py:122` | backend:erro | Pagamento não configurado (ASAAS_API_KEY ausente). | mensagem de erro | — | — | revisado — mantido |
| services/billing/asaas.py | error | `app/services/billing/asaas.py:144` | backend:error | asaas %s %s: falha de rede (%s) | mensagem de erro | — | — | revisado — mantido |
| services/billing/asaas.py | erro | `app/services/billing/asaas.py:145` | backend:erro | Não foi possível falar com o Asaas agora. Tente de novo em instantes. | mensagem de erro | — | — | revisado — mantido |
| services/billing/asaas.py | valor | `app/services/billing/asaas.py:150` | backend:valor | O Asaas recusou a operação. Confira os dados de cobrança e tente de novo; se continuar, fale com a gente. | valor exibido (rótulo, opção, situação) | antes: “O Asaas recusou a operação.” — clareza e voz (ver voice-and-tone) | aplicado (texto atual) | alterado |
| services/billing/asaas.py | error | `app/services/billing/asaas.py:161` | backend:error | asaas %s %s: HTTP %s %s | mensagem de erro | — | — | revisado — mantido |
| services/billing/fake.py | erro | `app/services/billing/fake.py:88` | backend:erro | Cliente não encontrado no provedor. | mensagem de erro | — | — | revisado — mantido |
| services/billing/fake.py | erro | `app/services/billing/fake.py:94` | backend:erro | Cliente não encontrado no provedor. | mensagem de erro | — | — | revisado — mantido |
| services/billing/fake.py | erro | `app/services/billing/fake.py:144` | backend:erro | Assinatura não encontrada no provedor. | mensagem de erro | — | — | revisado — mantido |
| services/billing/notify.py | valor | `app/services/billing/notify.py:23` | backend:valor | Pagamento da assinatura em atraso | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/notify.py | error | `app/services/billing/notify.py:77` | backend:error | falha ao enviar aviso de atraso (%s) | mensagem de erro | — | — | revisado — mantido |
| services/billing/notify.py | valor | `app/services/billing/notify.py:81` | backend:valor | Troca de plano não aplicada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/notify.py | error | `app/services/billing/notify.py:99` | backend:error | falha ao enviar aviso de downgrade (%s) | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:76` | backend:update | Assinatura contratada | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:77` | backend:update | Assinatura cancelada | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:78` | backend:update | Dados de cobrança atualizados | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:79` | backend:update | Teste grátis estendido | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:80` | backend:update | Desconto concedido | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:81` | backend:update | Troca para plano menor não aplicada | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:82` | backend:update | Plano atribuído pela equipe da plataforma | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | update | `app/services/billing/service.py:83` | backend:update | Identidade visual personalizada contratada | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:88` | backend:valor | Teste grátis | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:90` | backend:valor | Pagamento em atraso | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:92` | backend:valor | Encerrada (modo leitura) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:93` | backend:valor | Teste grátis | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:104` | backend:valor | Aguardando pagamento | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:187` | backend:erro | Pagamento não configurado: defina ASAAS_API_KEY. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:190` | backend:erro | Provedor de pagamento desconhecido: {…}. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:224` | backend:valor | Plano sob orçamento: fale conosco para contratar ou mudar. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:225` | backend:valor | Seu plano é gerido pela nossa equipe: fale conosco para mudar ou cancelar. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:335` | backend:erro | Informe o nome ou a razão social (2 a 120 caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:337` | backend:erro | CPF ou CNPJ inválido: confira os números. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:339` | backend:erro | Informe um e-mail de cobrança válido. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:348` | backend:valor | Teroz — plano {…} | valor exibido (rótulo, opção, situação) | antes: “Controle de Produção — plano {…}” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| services/billing/service.py | erro | `app/services/billing/service.py:357` | backend:erro | O plano {…} permite {…} projetos ativos e você tem {…}. Arquive ou conclua {…} projeto(s) antes de trocar. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:362` | backend:erro | O plano {…} permite {…} usuários e você tem {…} (com convites pendentes). Desative ou revogue {…} usuário(s)/convite(s) antes de trocar. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:384` | backend:erro | Plano indisponível. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:388` | backend:erro | Sua assinatura já está ativa: use “Trocar plano”. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | error | `app/services/billing/service.py:470` | backend:error | não foi possível guardar o cliente do provedor (%s) | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:477` | backend:erro | Ainda não há dados de cobrança: escolha um plano para assinar. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:514` | backend:valor | Pagamento em atraso: regularize antes de trocar de plano. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:555` | backend:erro | Plano indisponível. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:558` | backend:erro | Assinatura encerrada: escolha o plano e assine de novo. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:560` | backend:erro | Pagamento em atraso: regularize a fatura antes de trocar de plano. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:563` | backend:erro | Esse já é o seu plano. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:581` | backend:valor | após o pagamento | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:644` | backend:erro | A assinatura já está cancelada. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | error | `app/services/billing/service.py:685` | backend:error | downgrade não aplicado; falha ao restaurar valor no provedor: %s | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | error | `app/services/billing/service.py:724` | backend:error | cobrança %s pertence a outra empresa: ignorada | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | error | `app/services/billing/service.py:925` | backend:error | reconciliação da empresa %s falhou: %s | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:936` | backend:erro | Motivo obrigatório (mínimo {…} caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:944` | backend:erro | Dias entre 1 e 90. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:947` | backend:erro | O plano {…} não tem teste grátis (só Essencial e Profissional). | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:949` | backend:erro | Só dá para estender o teste grátis de quem ainda não pagou nenhuma mensalidade. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | record | `app/services/billing/service.py:960` | backend:record | admin da plataforma | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:969` | backend:erro | Desconto entre 0 e {…}%. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:972` | backend:erro | Plano sob orçamento: o valor é combinado no contrato, sem desconto aqui. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | record | `app/services/billing/service.py:985` | backend:record | admin da plataforma | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:1003` | backend:erro | Plano inexistente ou inativo. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:1007` | backend:erro | A empresa já está no plano {…}. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | erro | `app/services/billing/service.py:1020` | backend:erro | Sem assinatura ativa no provedor: o cliente assina esse plano pela tela de assinatura. | mensagem de erro | — | — | revisado — mantido |
| services/billing/service.py | record | `app/services/billing/service.py:1040` | backend:record | admin da plataforma | mensagem do backend | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1063` | backend:valor | Escolha um plano para continuar depois do teste. Pix, boleto ou cartão. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1064` | backend:valor | Teste grátis: falta{…} {…} dia{…}. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1064` | backend:valor | Teste grátis. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1065` | backend:valor | Escolher plano | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1070` | backend:valor | Pagamento em atraso. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1071` | backend:valor | Regularize até {…} para não entrar em modo leitura. Nenhum dado é apagado. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1072` | backend:valor | Pagar agora | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1078` | backend:valor | Assinatura cancelada. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1079` | backend:valor | Acesso completo até {…}; depois, modo leitura (seus dados continuam guardados). | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/billing/service.py | valor | `app/services/billing/service.py:1080` | backend:valor | Assinar de novo | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/entitlements.py | valor | `app/services/entitlements.py:51` | backend:valor | Arquive um projeto ou mude de plano. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/entitlements.py | valor | `app/services/entitlements.py:58` | backend:valor | Limite do plano | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/entitlements.py | valor | `app/services/entitlements.py:66` | backend:valor | Limite do plano atingido | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/entitlements.py | valor | `app/services/entitlements.py:70` | backend:valor | Assinatura em modo leitura | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/entitlements.py | erro | `app/services/entitlements.py:156` | backend:erro | Sua assinatura está em modo leitura: dá para ver e exportar tudo, mas não gravar. Regularize a assinatura para voltar a registrar. | mensagem de erro | — | — | revisado — mantido |
| services/entitlements.py | erro | `app/services/entitlements.py:195` | backend:erro | Seu plano {…} permite {…} projetos ativos. {…} | mensagem de erro | — | — | revisado — mantido |
| services/entitlements.py | erro | `app/services/entitlements.py:205` | backend:erro | Seu plano {…} permite {…} usuários (contando convites pendentes). Remova alguém ou mude de plano. | mensagem de erro | — | — | revisado — mantido |
| services/entitlements.py | erro | `app/services/entitlements.py:216` | backend:erro | {…} não está disponível no plano {…}. | mensagem de erro | — | — | revisado — mantido |
| services/plans.py | valor | `app/services/plans.py:45` | backend:valor | Implantação feita pela nossa equipe técnica, online ou presencial | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/plans.py | valor | `app/services/plans.py:46` | backend:valor | 1 mês de acompanhamento e manutenção | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/plans.py | valor | `app/services/plans.py:47` | backend:valor | Treinamento do sistema para a sua equipe | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |

</details>

<details><summary><b>Painel interno da equipe Teroz</b> (84)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/interno.py | formulário | `app/blueprints/interno.py:39` | backend:formulário | Anotação interna | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | formulário | `app/blueprints/interno.py:43` | backend:formulário | Informe a data. | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | formulário | `app/blueprints/interno.py:44` | backend:formulário | Hora (Brasília) | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | formulário | `app/blueprints/interno.py:44` | backend:formulário | Informe a hora. | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | formulário | `app/blueprints/interno.py:46` | backend:formulário | Duração (minutos) | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | flash | `app/blueprints/interno.py:110` | backend:flash | Requisição atualizada. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | flash | `app/blueprints/interno.py:155` | backend:flash | Horário criado: {…} (Brasília). | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | flash | `app/blueprints/interno.py:176` | backend:flash | Horário removido. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | _slots_page | `app/blueprints/interno.py:196` | backend:_slots_page | Ação inválida. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | send_template | `app/blueprints/interno.py:203` | backend:send_template | Sua ligação de identidade visual | assunto do e-mail | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | flash | `app/blueprints/interno.py:210` | backend:flash | Reserva cancelada e horário liberado. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | flash | `app/blueprints/interno.py:210` | backend:flash | Pedido recusado; a reserva continua. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | AppGroup | `app/blueprints/interno.py:216` | backend:AppGroup | Equipe da plataforma (painel /interno; auditado). | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | echo | `app/blueprints/interno.py:237` | backend:echo | {…} agora é da equipe (acessa /interno). | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | echo | `app/blueprints/interno.py:249` | backend:echo | {…} saiu da equipe; sessões abertas derrubadas. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | echo | `app/blueprints/interno.py:256` | backend:echo | Ninguém na equipe. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/interno.py | echo | `app/blueprints/interno.py:258` | backend:echo | {…} mfa={…} | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | valor | `app/services/staff.py:38` | backend:valor | Briefing preenchido | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | valor | `app/services/staff.py:39` | backend:valor | Em andamento | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:108` | backend:erro | Estado inválido. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:111` | backend:erro | Anotação com no máximo {…} caracteres. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:131` | backend:erro | Usuário não encontrado ou desativado. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:138` | backend:erro | Motivo obrigatório (mínimo {…} caracteres). | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:140` | backend:erro | Informe quem autorizou (--autorizado-por). | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/staff.py | erro | `app/services/staff.py:148` | backend:erro | A conta da equipe precisa de e-mail confirmado e MFA ativo. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:45` | backend:erro | Usuário de suporte não encontrado ou desativado. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:55` | backend:erro | Empresa não encontrada. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:67` | backend:erro | Motivo obrigatório (mínimo {…} caracteres). | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:69` | backend:erro | Informe quem autorizou (--autorizado-por). | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:72` | backend:erro | Prazo entre 1 e {…} horas. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:74` | backend:erro | Papel de suporte: operator ou supervisor. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:77` | backend:erro | A conta de suporte precisa de e-mail confirmado e MFA ativo. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | erro | `app/services/support.py:84` | backend:erro | Esta pessoa já é membro da empresa; acesso de suporte não se aplica. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/support.py | send_template | `app/services/support.py:122` | backend:send_template | Acesso de suporte concedido à sua empresa | assunto do e-mail | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/base | content | `app/templates/interno/base.html:2` | template:content | noindex, nofollow | metadado da página | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/base | texto | `app/templates/interno/base.html:6` | template:texto | Painel interno | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:9` | template:texto | Plano {…} · aberta em {…} | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:13` | template:texto | Contato do cliente | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:17` | template:texto | Ligação | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:19` | template:texto | (Brasília) · {…} min · {…} · | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:20` | template:texto | Pedido do cliente: {…}. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:22` | template:texto | Sem ligação marcada. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:24` | template:texto | O conteúdo do briefing e as imagens ficam com a empresa: este painel não os lê (ADR-0019). | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:25` | template:texto | Horários e reservas | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:28` | template:texto | Acompanhamento | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | macro | `app/templates/interno/detail.html:33` | template:macro | Salvar | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/detail | texto | `app/templates/interno/detail.html:35` | template:texto | Última alteração por {…} em {…}. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:7` | template:texto | Horários da ligação · Painel interno | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:12` | template:texto | Horários da ligação | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:13` | template:texto | Horários de Brasília. Só aparecem para empresas no plano Empresa ou Implantação. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:19` | template:texto | Novo horário | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:23` | template:macro | Use o seletor; o formato depende do navegador (aqui a lista sempre mostra dd/mm/aaaa). | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:24` | template:macro | Use o seletor; hora de Brasília, no formato HH:MM. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:26` | template:macro | Entre 10 e 240 minutos. | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:27` | template:macro | Criar horário | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:32` | template:macro | Início | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:32` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | data-label | `app/templates/interno/horarios.html:37` | template:data-label | Início | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:38` | template:texto | {…} min | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | data-label | `app/templates/interno/horarios.html:38` | template:data-label | Duração | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | data-label | `app/templates/interno/horarios.html:39` | template:data-label | Situação | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:41` | template:macro | Pedido: | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:41` | template:macro | Reservado | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:42` | template:macro | Livre | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | data-label | `app/templates/interno/horarios.html:44` | template:data-label | Empresa e contato | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | data-label | `app/templates/interno/horarios.html:50` | template:data-label | Ações | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:56` | template:macro | Cancelar reserva | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:62` | template:macro | Manter reserva | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | macro | `app/templates/interno/horarios.html:68` | template:macro | Remover | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/horarios | texto | `app/templates/interno/horarios.html:78` | template:texto | Nenhum horário cadastrado. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | texto | `app/templates/interno/index.html:4` | template:texto | Painel interno · Teroz | texto na tela | antes: “Painel interno · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| interno/index | texto | `app/templates/interno/index.html:8` | template:texto | Identidade visual | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | texto | `app/templates/interno/index.html:9` | template:texto | Requisições abertas quando uma empresa contrata o plano Empresa ou Implantação. | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | texto | `app/templates/interno/index.html:12` | template:texto | Horários da ligação e reservas | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | aria-label | `app/templates/interno/index.html:13` | template:aria-label | Filtrar por estado | nome para leitor de tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | texto | `app/templates/interno/index.html:14` | template:texto | Todas | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | macro | `app/templates/interno/index.html:20` | template:macro | Empresa | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | macro | `app/templates/interno/index.html:20` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | data-label | `app/templates/interno/index.html:24` | template:data-label | Empresa | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | data-label | `app/templates/interno/index.html:25` | template:data-label | Plano | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | data-label | `app/templates/interno/index.html:26` | template:data-label | Contato | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | data-label | `app/templates/interno/index.html:27` | template:data-label | Aberta em | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | data-label | `app/templates/interno/index.html:28` | template:data-label | Estado | rótulo da coluna no modo cartão (celular) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| interno/index | texto | `app/templates/interno/index.html:34` | template:texto | Nenhuma requisição neste estado . | texto na tela | só passou pela padronização automática de termos | — | pendente de revisão manual |

</details>

<details><summary><b>Modelos de etapas</b> (74)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/modelos.py | flash | `app/blueprints/modelos.py:80` | backend:flash | Modelo criado (versão 1). | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/modelos.py | flash | `app/blueprints/modelos.py:107` | backend:flash | Modelo salvo. As etapas não mudaram, então a versão continua a mesma. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/modelos.py | flash | `app/blueprints/modelos.py:109` | backend:flash | Versão {…} criada. Projetos existentes não mudam. | confirmação ou aviso após ação | — | — | revisado — mantido |
| blueprints/modelos.py | flash | `app/blueprints/modelos.py:135` | backend:flash | Modelo arquivado. Os projetos criados dele continuam iguais. | confirmação ou aviso após ação | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:62` | backend:erro | Informe o nome do modelo (até 160 caracteres). | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:68` | backend:erro | Já existe um modelo com este nome. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:74` | backend:erro | Inclua pelo menos uma etapa. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:235` | backend:erro | Modelo não encontrado. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:238` | backend:erro | Modelo sem versão. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | valor | `app/services/templates.py:268` | backend:valor | Nova etapa “{…}” | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/templates.py | valor | `app/services/templates.py:270` | backend:valor | Etapa “{…}” sai do projeto (fica arquivada com o histórico) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/templates.py | valor | `app/services/templates.py:272` | backend:valor | Nova subatividade “{…}” em “{…}” ({…} min) | valor exibido (rótulo, opção, situação) | antes: “Nova atividade “{…}” em “{…}” ({…} min)” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/templates.py | valor | `app/services/templates.py:274` | backend:valor | Subatividade “{…}” de “{…}” sai (fica arquivada com o histórico) | valor exibido (rótulo, opção, situação) | antes: “Atividade “{…}” de “{…}” sai (fica arquivada com o histórico)” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/templates.py | valor | `app/services/templates.py:276` | backend:valor | Checklist de inspeção de “{…}” muda (itens novos entram; respostas antigas ficam) | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/templates.py | valor | `app/services/templates.py:278` | backend:valor | Tempo ideal de “{…}” ({…}): {…} → {…} min | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/templates.py | valor | `app/services/templates.py:279` | backend:valor | Ordem das etapas muda | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:393` | backend:erro | Este projeto não veio de um modelo. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:395` | backend:erro | O modelo mudou desde a comparação. Confira as diferenças de novo. | mensagem de erro | — | — | revisado — mantido |
| services/templates.py | erro | `app/services/templates.py:397` | backend:erro | O projeto já está na versão atual do modelo. | mensagem de erro | — | — | revisado — mantido |
| modelos/_stages | texto | `app/templates/modelos/_stages.html:15` | template:texto | Etapa {…} | texto na tela | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:17` | template:macro | Subir etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:18` | template:macro | Descer etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:19` | template:macro | Remover etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:22` | template:macro | Nome da etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:23` | template:macro | Subatividades | rótulo, botão ou ajuda de componente | antes: “Atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:23` | template:macro | Uma por linha: Nome; minutos por unidade | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:26` | template:macro | Checklist de inspeção (opcional) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:26` | template:macro | Um item por linha (ex.: Torque dos parafusos conferido). Copiado para os projetos novos. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | macro | `app/templates/modelos/_stages.html:27` | template:macro | Exigir checklist assinado (só avisa; não bloqueia o registro) | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/_stages | texto | `app/templates/modelos/_stages.html:33` | template:texto | Adicionar etapa | texto na tela | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:9` | template:macro | Novo modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:15` | template:macro | Novo modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | texto | `app/templates/modelos/edit.html:17` | template:texto | {…} etapas | texto na tela | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:17` | template:macro | ~ template.current_version.number, | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:22` | template:macro | Versões | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:23` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | texto | `app/templates/modelos/edit.html:30` | template:texto | Salvar | texto na tela | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:31` | template:macro | Etapa | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | texto | `app/templates/modelos/edit.html:34` | template:texto | Modelo | texto na tela | — | — | revisado — mantido |
| modelos/edit | texto | `app/templates/modelos/edit.html:41` | template:texto | Etapas | texto na tela | — | — | revisado — mantido |
| modelos/edit | texto | `app/templates/modelos/edit.html:42` | template:texto | Na ordem de montagem. Em cada etapa, uma subatividade por linha: | texto na tela | antes: “Na ordem de montagem. Em cada etapa, uma atividade por linha:” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| modelos/edit | texto | `app/templates/modelos/edit.html:42` | template:texto | Nome; minutos por unidade | texto na tela | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:48` | template:macro | projeto(s) usam este modelo. Ao salvar com etapas diferentes criamos a versão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:48` | template:macro | ; eles não mudam. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:51` | template:macro | Salvar como nova versão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:51` | template:macro | Criar modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:52` | template:macro | Cancelar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:57` | template:macro | Arquivar o modelo? | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:57` | template:macro | Ele some da lista e do novo projeto. Projetos criados dele não mudam. | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/edit | macro | `app/templates/modelos/edit.html:57` | template:macro | Arquivar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | texto | `app/templates/modelos/index.html:7` | template:texto | Modelos de etapas · Teroz | texto na tela | antes: “Modelos de etapas · Controle de Produção” — marca: o produto se chama Teroz | aplicado (texto atual) | alterado |
| modelos/index | texto | `app/templates/modelos/index.html:11` | template:texto | Modelos de etapas | texto na tela | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:13` | template:macro | Importar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:14` | template:macro | Novo modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:19` | template:macro | Modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:19` | template:macro | )], caption= | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | data-label | `app/templates/modelos/index.html:24` | template:data-label | Versão | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:24` | template:macro | ~ (version.number if version else 1), | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | data-label | `app/templates/modelos/index.html:25` | template:data-label | Etapas | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| modelos/index | data-label | `app/templates/modelos/index.html:26` | template:data-label | Tempo/un. | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| modelos/index | data-label | `app/templates/modelos/index.html:27` | template:data-label | Em uso | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| modelos/index | data-label | `app/templates/modelos/index.html:28` | template:data-label | Atualizado | rótulo da coluna no modo cartão (celular) | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:35` | template:macro | Nenhum modelo de etapas | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:35` | template:macro | Monte etapas e subatividades com tempo ideal, ou importe um CSV. | rótulo, botão ou ajuda de componente | antes: “Monte etapas e atividades com tempo ideal, ou importe um CSV.” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| modelos/index | macro | `app/templates/modelos/index.html:35` | template:macro | Novo modelo | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/index | macro | `app/templates/modelos/index.html:35` | template:macro | Importar | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/versions | texto | `app/templates/modelos/versions.html:5` | template:texto | Versões · {…} | texto na tela | — | — | revisado — mantido |
| modelos/versions | texto | `app/templates/modelos/versions.html:11` | template:texto | Versões | texto na tela | — | — | revisado — mantido |
| modelos/versions | macro | `app/templates/modelos/versions.html:12` | template:macro | versão | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/versions | macro | `app/templates/modelos/versions.html:12` | template:macro | versões | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/versions | macro | `app/templates/modelos/versions.html:20` | template:macro | ~ version.number, | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/versions | macro | `app/templates/modelos/versions.html:21` | template:macro | Atual | rótulo, botão ou ajuda de componente | — | — | revisado — mantido |
| modelos/versions | texto | `app/templates/modelos/versions.html:22` | template:texto | {…} · {…} etapas · {…} por unidade | texto na tela | — | — | revisado — mantido |
| modelos/versions | texto | `app/templates/modelos/versions.html:27` | template:texto | — {…} ({…} min) , sem subatividades | texto na tela | antes: “— {…} ({…} min) , sem atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |

</details>

<details><summary><b>Histórico e auditoria</b> (66)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| services/audit.py | valor | `app/services/audit.py:99` | backend:valor | Papel alterado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:100` | backend:valor | Pessoa removida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:101` | backend:valor | Convite enviado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:102` | backend:valor | Convite revogado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:103` | backend:valor | Convite reenviado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:104` | backend:valor | Convite aceito | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:105` | backend:valor | Pessoa desativada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:106` | backend:valor | Pessoa reativada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:107` | backend:valor | Exigência de verificação em duas etapas alterada | valor exibido (rótulo, opção, situação) | antes: “Exigência de MFA alterada” — sem sigla técnica: verificação em duas etapas | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:108` | backend:valor | Plano alterado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:109` | backend:valor | Exclusão da empresa pedida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:110` | backend:valor | Projeto editado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:111` | backend:valor | Projeto arquivado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:112` | backend:valor | Projeto duplicado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:113` | backend:valor | Projeto importado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:114` | backend:valor | Etapa arquivada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:115` | backend:valor | Subatividade arquivada | valor exibido (rótulo, opção, situação) | antes: “Atividade arquivada” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:116` | backend:valor | Etapa renomeada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:117` | backend:valor | Subatividade editada | valor exibido (rótulo, opção, situação) | antes: “Atividade editada” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:118` | backend:valor | Responsável da subatividade alterado | valor exibido (rótulo, opção, situação) | antes: “Responsável da atividade alterado” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:119` | backend:valor | Subatividade movida | valor exibido (rótulo, opção, situação) | antes: “Atividade movida” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:120` | backend:valor | Etapas reordenadas | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:121` | backend:valor | Aguardando peça alterado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:122` | backend:valor | Comentário apagado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:123` | backend:valor | Foto apagada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:124` | backend:valor | Item de checklist incluído | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:125` | backend:valor | Item de checklist arquivado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:126` | backend:valor | Exigência de checklist alterada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:127` | backend:valor | Inspeção assinada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:128` | backend:valor | Inspeção corrigida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:129` | backend:valor | Números de série cadastrados | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:130` | backend:valor | Situação da unidade alterada | valor exibido (rótulo, opção, situação) | antes: “Status da unidade alterado” — glossário: status → situação | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:131` | backend:valor | Versão do modelo aplicada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:132` | backend:valor | Modelo arquivado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:133` | backend:valor | Registro desfeito | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:134` | backend:valor | Projeto restaurado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:135` | backend:valor | Restauração desfeita | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:136` | backend:valor | Exclusão da etapa desfeita | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:137` | backend:valor | Exclusão da subatividade desfeita | valor exibido (rótulo, opção, situação) | antes: “Exclusão da atividade desfeita” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/audit.py | valor | `app/services/audit.py:138` | backend:valor | Peças corrigidas para menos | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:139` | backend:valor | Modo de progresso alterado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:140` | backend:valor | Dados da empresa alterados | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:141` | backend:valor | Módulo opcional ligado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:142` | backend:valor | Módulo opcional desligado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:143` | backend:valor | Feriado incluído | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:144` | backend:valor | Feriado removido | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:145` | backend:valor | Exclusão da empresa cancelada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:146` | backend:valor | Dados da empresa exportados | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:147` | backend:valor | Acesso de suporte concedido | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:148` | backend:valor | Acesso de suporte revogado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:149` | backend:valor | Acesso de suporte expirado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:150` | backend:valor | Conta retomada pelo dono do e-mail | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:151` | backend:valor | Briefing de identidade visual salvo | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:152` | backend:valor | Briefing de identidade visual enviado à equipe | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:153` | backend:valor | Imagem do briefing enviada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:154` | backend:valor | Imagem do briefing apagada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:155` | backend:valor | Ligação agendada | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:156` | backend:valor | Mudança na ligação pedida | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:157` | backend:valor | Ligação cancelada pela equipe | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/audit.py | valor | `app/services/audit.py:158` | backend:valor | Pedido de mudança na ligação recusado | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/restore.py | valor | `app/services/restore.py:46` | backend:valor | O projeto mudou depois da prévia. Confira a nova prévia e confirme de novo. | valor exibido (rótulo, opção, situação) | — | — | revisado — mantido |
| services/restore.py | erro | `app/services/restore.py:228` | backend:erro | Projeto arquivado não pode ser restaurado. | mensagem de erro | — | — | revisado — mantido |
| services/restore.py | NothingToRestore | `app/services/restore.py:321` | backend:NothingToRestore | Nada a restaurar: nesse momento o projeto já estava como está agora. | mensagem do backend | — | — | revisado — mantido |
| services/restore.py | erro | `app/services/restore.py:389` | backend:erro | Isto já é um desfazer de restauração. | mensagem de erro | — | — | revisado — mantido |
| services/restore.py | erro | `app/services/restore.py:391` | backend:erro | Esta restauração já foi desfeita. | mensagem de erro | — | — | revisado — mantido |
| services/restore.py | erro | `app/services/restore.py:399` | backend:erro | Não dá para desfazer: {…} mudou depois da restauração ({…} de {…}). | mensagem de erro | — | — | revisado — mantido |

</details>

<details><summary><b>API</b> (42)</summary>

| Página | Componente | Arquivo:linha | Contexto | Texto atual | Intenção | Problema | Proposto | Status |
|---|---|---|---|---|---|---|---|---|
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:72` | backend:valor | Requisição inválida | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:73` | backend:valor | Recurso não encontrado | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:74` | backend:valor | Método não permitido | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:75` | backend:valor | Corpo grande demais | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:76` | backend:valor | Muitas requisições | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:105` | backend:problem | Erro interno | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:109` | backend:valor | Bearer realm="api" | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:109` | backend:valor | Bearer realm="api", error="invalid_token" | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:110` | backend:problem | Não autenticado | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | _unauthorized | `app/blueprints/api_v1.py:169` | backend:_unauthorized | Envie o cabeçalho Authorization: Bearer <token>. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | _unauthorized | `app/blueprints/api_v1.py:172` | backend:_unauthorized | Token inválido. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:181` | backend:valor | Token revogado. | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | valor | `app/blueprints/api_v1.py:181` | backend:valor | Token expirado. | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:185` | backend:problem | Recurso não encontrado | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:189` | backend:problem | Recurso indisponível no plano | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:191` | backend:problem | A API não está disponível no plano {…}. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:239` | backend:problem | Escopo insuficiente | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:241` | backend:problem | O token não tem o escopo {…}. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:242` | backend:problem | Bearer realm="api", error="insufficient_scope", scope="{…}" | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | erro | `app/blueprints/api_v1.py:357` | backend:erro | cursor inválido | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:369` | backend:problem | Parâmetro inválido | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:369` | backend:problem | limit deve ser um inteiro. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:371` | backend:problem | Parâmetro inválido | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:371` | backend:problem | limit deve estar entre 1 e {…}. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:378` | backend:problem | Parâmetro inválido | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:378` | backend:problem | cursor inválido. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:399` | backend:problem | Não implementado | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:399` | backend:problem | Rota reservada no contrato; ainda não disponível. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | problem | `app/blueprints/api_v1.py:425` | backend:problem | Recurso não encontrado | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | formulário | `app/blueprints/api_v1.py:432` | backend:formulário | Nome da integração | rótulo ou validação de campo | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | require_feature | `app/blueprints/api_v1.py:471` | backend:require_feature | A API | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | _page | `app/blueprints/api_v1.py:474` | backend:_page | Informe o nome e escolha ao menos uma permissão. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | _page | `app/blueprints/api_v1.py:479` | backend:_page | Já existe uma integração com esse nome. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | _page | `app/blueprints/api_v1.py:496` | backend:_page | Formulário expirado. Tente de novo. | mensagem do backend | só passou pela padronização automática de termos | — | pendente de revisão manual |
| blueprints/api_v1.py | flash | `app/blueprints/api_v1.py:499` | backend:flash | Token revogado. | confirmação ou aviso após ação | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | valor | `app/services/api_tokens.py:33` | backend:valor | Ler projetos, resumos e eventos | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | valor | `app/services/api_tokens.py:34` | backend:valor | Registrar progresso de subatividades | valor exibido (rótulo, opção, situação) | antes: “Registrar progresso de atividades” — glossário: atividade → subatividade | aplicado (texto atual) | alterado |
| services/api_tokens.py | valor | `app/services/api_tokens.py:37` | backend:valor | 30 dias | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | valor | `app/services/api_tokens.py:38` | backend:valor | 90 dias | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | valor | `app/services/api_tokens.py:39` | backend:valor | 1 ano | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | valor | `app/services/api_tokens.py:40` | backend:valor | Sem expiração | valor exibido (rótulo, opção, situação) | só passou pela padronização automática de termos | — | pendente de revisão manual |
| services/api_tokens.py | erro | `app/services/api_tokens.py:90` | backend:erro | Escolha ao menos um escopo válido. | mensagem de erro | só passou pela padronização automática de termos | — | pendente de revisão manual |

</details>
