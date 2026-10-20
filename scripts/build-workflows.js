// Gera workflows/*.json (n8n) a partir de src/lib e src/prompts. Uso: npm run build
const fs = require('fs'), path = require('path');
const { bundleSource } = require('./bundle');
const root = path.join(__dirname, '..');
const prompt = n => fs.readFileSync(path.join(root, 'src', 'prompts', n + '.md'), 'utf8');

const PRELUDE = bundleSource() + `
const STAGES = DEFAULT_STAGES;
const bool = v => ['true', 'sim', '1', 'x'].includes(String(v || '').toLowerCase());
const normLead = l => ({ ...l, nao_contatar: bool(l.nao_contatar) });
const cfgMap = rows => Object.fromEntries(rows.filter(r => r.json && r.json.chave).map(r => [r.json.chave, String(r.json.valor || '')]));
const list = s => String(s || '').split(';').map(x => x.trim()).filter(Boolean);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const now = () => new Date().toISOString();
function requireToken(token) {
  const t = $env.REVIEW_UI_TOKEN;
  if (!t) throw new Error('REVIEW_UI_TOKEN não configurado: recusando requisição');
  if (token !== t) throw new Error('Não autorizado');
}
function hashId(s) { let h = 5381; for (const c of s) h = ((h * 33) ^ c.charCodeAt(0)) >>> 0; return 'L' + h.toString(36); }
`;

let nid = 0;
const pos = i => [240 * i, 300];
const sheetDoc = { __rl: true, mode: 'id', value: '={{$env.GOOGLE_SHEET_ID}}' };
const sheetName = n => ({ __rl: true, mode: 'name', value: n });
const cred = { googleSheetsOAuth2Api: { id: '', name: 'Google Sheets account' } };

const webhook = (name, p, method, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.webhook', typeVersion: 2, position: pos(i),
  parameters: { path: p, httpMethod: method, responseMode: 'responseNode', options: {} }, webhookId: 'montco-' + p });
const code = (name, body, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.code', typeVersion: 2, position: pos(i),
  parameters: { mode: 'runOnceForAllItems', language: 'javaScript', jsCode: PRELUDE + '\n' + body } });
const sheetGet = (name, sheet, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.googleSheets', typeVersion: 4.5, position: pos(i), alwaysOutputData: true, credentials: cred,
  parameters: { resource: 'sheet', operation: 'getAll', documentId: sheetDoc, sheetName: sheetName(sheet), options: {} } });
const sheetWrite = (name, sheet, op, match, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.googleSheets', typeVersion: 4.5, position: pos(i), credentials: cred,
  parameters: { resource: 'sheet', operation: op, documentId: sheetDoc, sheetName: sheetName(sheet),
    columns: { mappingMode: 'autoMapInputData', value: null, matchingColumns: match ? [match] : [] }, options: {} } });
const respond = (name, i, type) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.respondToWebhook', typeVersion: 1.1, position: pos(i),
  parameters: { respondWith: 'text', responseBody: '={{$json.body}}', options: { responseHeaders: { entries: [{ name: 'Content-Type', value: type || 'text/html; charset=utf-8' }] } } } });
const anthropic = (name, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.httpRequest', typeVersion: 4.2, position: pos(i), retryOnFail: true, maxTries: 2, waitBetweenTries: 3000,
  credentials: { httpHeaderAuth: { id: '', name: 'Anthropic (header x-api-key)' } },
  parameters: { method: 'POST', url: 'https://api.anthropic.com/v1/messages', authentication: 'genericCredentialType', genericAuthType: 'httpHeaderAuth',
    sendHeaders: true, headerParameters: { parameters: [{ name: 'anthropic-version', value: '2023-06-01' }] },
    sendBody: true, specifyBody: 'json', jsonBody: '={{ JSON.stringify($json.request) }}', options: { timeout: 60000 } } });
const fetchSite = (name, i) => ({ id: 'n' + ++nid, name, type: 'n8n-nodes-base.httpRequest', typeVersion: 4.2, position: pos(i), onError: 'continueRegularOutput',
  parameters: { method: 'GET', url: '={{$json.site_url}}', options: { timeout: 15000, response: { response: { responseFormat: 'text' } } } } });

const wf = (name, nodes, chains) => {
  const connections = {};
  for (const ch of chains) for (let k = 0; k < ch.length - 1; k++) {
    const a = ch[k]; connections[a] = connections[a] || { main: [[]] };
    if (!connections[a].main[0].some(c => c.node === ch[k + 1])) connections[a].main[0].push({ node: ch[k + 1], type: 'main', index: 0 });
  }
  return { name, nodes, connections, active: false, settings: { executionOrder: 'v1' }, meta: { nota: 'Gerado por scripts/build-workflows.js. NÃO contém nó de envio de e-mail.' } };
};

const workflows = {};

// 01 — Importação CSV + deduplicação
workflows['01-import-csv'] = (() => {
  const n = [
    webhook('Webhook', 'montco-import', 'POST', 0),
    sheetGet('Ler Leads', 'Leads', 1),
    code('Dedup', `
const inp = $('Webhook').first().json;
requireToken(inp.headers && inp.headers['x-token'] || (inp.query || {}).token);
const rows = parseCsv(String((inp.body || {}).csv || ''));
if (!rows.length) throw new Error('CSV vazio ou sem cabeçalho');
const base = $input.all().map(i => i.json).filter(l => l.id).map(l => ({ ...l }));
const out = [], resumo = { novos: 0, mesclados: 0, possiveis_duplicados: 0 };
for (const r of rows) {
  if (!r.nome) continue;
  if (r.cnpj && !validCnpj(r.cnpj)) r.cnpj = '';
  const d = findDuplicate(r, base);
  const t = now();
  let lead;
  if (d && d.strong) { lead = mergeLead(d.lead, r); resumo.mesclados++; base[base.indexOf(d.lead)] = lead; lead.atualizado_em = t; }
  else {
    lead = { id: hashId(normalizeDomain(r.site) || normalizeCnpj(r.cnpj) || normalizeName(r.nome) + r.uf), ...r, status: 'identificada', criado_em: t, atualizado_em: t };
    if (d) { lead.justificativa = 'Possível duplicado de ' + d.lead.id + ' (nome+UF)'; resumo.possiveis_duplicados++; }
    resumo.novos++; base.push(lead);
  }
  out.push({ json: { kind: 'lead', lead_row: { ...lead, produtos: lead.produtos || '', fonte_aquisicao: lead.fonte_aquisicao || 'csv' } } });
  if (r.fonte_url) out.push({ json: { kind: 'fonte', fonte_row: { lead_id: lead.id, url: r.fonte_url, data_pesquisa: now(), tipo: r.fonte_aquisicao || 'csv', trecho: '', nivel: 'fato' } } });
}
out.push({ json: { kind: 'resumo', resumo } });
return out;`, 2),
    code('Só leads', `return $input.all().filter(i => i.json.kind === 'lead').map(i => ({ json: i.json.lead_row }));`, 3),
    sheetWrite('Gravar Leads', 'Leads', 'appendOrUpdate', 'id', 4),
    code('Só fontes', `return $('Dedup').all().filter(i => i.json.kind === 'fonte').map(i => ({ json: i.json.fonte_row }));`, 5),
    sheetWrite('Gravar Fontes', 'Fontes', 'append', null, 6),
    code('Resposta', `const r = $('Dedup').all().find(i => i.json.kind === 'resumo').json.resumo; return [{ json: { body: JSON.stringify(r) } }];`, 7),
    respond('Responder', 8, 'application/json'),
  ];
  return wf('Montco 01 — Importar CSV', n, [['Webhook', 'Ler Leads', 'Dedup'], ['Dedup', 'Só leads', 'Gravar Leads'], ['Dedup', 'Só fontes', 'Gravar Fontes'], ['Dedup', 'Resposta', 'Responder']]);
})();

// 02 — Pesquisa (site oficial), qualificação e rascunho
workflows['02-qualificacao-e-rascunho'] = (() => {
  const qp = JSON.stringify(prompt('qualificacao')), ep = JSON.stringify(prompt('email'));
  const n = [
    webhook('Webhook', 'montco-qualify', 'POST', 0),
    sheetGet('Leads', 'Leads', 1), sheetGet('Fontes', 'Fontes', 2), sheetGet('Config', 'Config', 3), sheetGet('Supressao', 'Supressao', 4),
    code('Selecionar lead', `
const inp = $('Webhook').first().json;
requireToken((inp.headers || {})['x-token'] || (inp.query || {}).token);
const id = (inp.body || {}).lead_id;
const lead = $('Leads').all().map(i => i.json).find(l => l.id === id);
if (!lead) throw new Error('Lead não encontrado: ' + id);
const L = normLead(lead);
if (L.nao_contatar || isSuppressed(L, $('Supressao').all().map(i => i.json))) throw new Error('Lead em supressão: nada será gerado');
if (!normalizeDomain(L.site)) throw new Error('Lead sem site oficial válido: cadastre o site ou adicione fontes manualmente');
return [{ json: { site_url: /^https?:/i.test(L.site) ? L.site : 'https://' + L.site } }];`, 5),
    fetchSite('Buscar site oficial', 6),
    code('Montar qualificação', `
if (!$env.ANTHROPIC_MODEL) throw new Error('ANTHROPIC_MODEL não configurado');
const id = $('Webhook').first().json.body.lead_id;
const lead = normLead($('Leads').all().map(i => i.json).find(l => l.id === id));
const html = String(($input.first() || { json: {} }).json.data || ($input.first() || { json: {} }).json.body || '');
const text = html.replace(/<script[\\s\\S]*?<\\/script>|<style[\\s\\S]*?<\\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim().slice(0, 8000);
const siteUrl = $('Selecionar lead').first().json.site_url;
const fontes = $('Fontes').all().map(i => i.json).filter(f => f.lead_id === id);
const fetched = !!text;
const cfg = cfgMap($('Config').all());
const weights = Object.fromEntries(Object.keys(DEFAULT_WEIGHTS).map(k => [k, Number(cfg['peso_' + k]) || DEFAULT_WEIGHTS[k]]));
const material = '<fontes>\\n' + (fetched ? '[' + siteUrl + ' | consultado em ' + now() + ']\\n' + text + '\\n' : '') +
  fontes.map(f => '[' + f.url + ']\\n' + (f.trecho || '')).join('\\n') + '\\n</fontes>\\nEmpresa: ' + lead.nome + ' (' + (lead.cidade || '') + '/' + (lead.uf || '') + ')';
return [{ json: { id, fetched, siteUrl, weights, cfg, request: { model: $env.ANTHROPIC_MODEL, max_tokens: 2000, system: ${qp}, messages: [{ role: 'user', content: material }] } } }];`, 7),
    anthropic('Claude: qualificar', 8),
    code('Pontuar e montar e-mail', `
const prev = $('Montar qualificação').first().json;
const txt = (($input.first().json.content || [])[0] || {}).text || '';
let q; try { q = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1)); } catch (e) { throw new Error('Resposta da IA não é JSON válido'); }
// Mantém apenas evidências com URL: sem URL, o fator vira desconhecido.
for (const k of Object.keys(q.factors || {})) { const f = q.factors[k]; if (!f.evidence || !f.evidence.length) { f.value = null; f.level = 'hipotese'; } }
const s = computeScore(q.factors || {}, prev.weights);
const cfg = prev.cfg;
const links = ['link_apresentacao', 'link_site', 'link_formulario'].map(k => cfg[k]).filter(Boolean);
const fatos = (q.fatos || []).filter(f => f.url);
const emailReq = { model: $env.ANTHROPIC_MODEL, max_tokens: 1500, system: ${ep},
  messages: [{ role: 'user', content: JSON.stringify({ empresa: $('Leads').all().map(i => i.json).find(l => l.id === prev.id).nome, segmento: q.segmento, fatos, gancho: q.gancho,
    funcionalidades_existentes: list(cfg.funcionalidades_existentes), links_permitidos: links, remetente: { nome: cfg.remetente_nome || $env.SENDER_NAME, contato: cfg.remetente_contato || $env.SENDER_CONTACT } }) }] };
if (!list(cfg.funcionalidades_existentes).length) throw new Error('Config.funcionalidades_existentes vazio: defina o que a Montco realmente faz antes de gerar e-mails');
return [{ json: { request: emailReq, q, s } }];`, 9),
    anthropic('Claude: rascunho', 10),
    code('Validar e preparar gravações', `
const id = $('Montar qualificação').first().json.id;
const prev = $('Montar qualificação').first().json, { q, s } = $('Pontuar e montar e-mail').first().json;
const txt = (($input.first().json.content || [])[0] || {}).text || '';
let e; try { e = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1)); } catch (x) { throw new Error('Rascunho da IA não é JSON válido'); }
const lead = normLead($('Leads').all().map(i => i.json).find(l => l.id === id));
const cfg = prev.cfg, t = now();
const fontesAll = $('Fontes').all().map(i => i.json).filter(f => f.lead_id === id).map(f => f.url).concat(prev.fetched ? [prev.siteUrl] : []);
const vctx = { ...lead, fontes: fontesAll };
const vcfg = { allowedLinks: ['link_apresentacao', 'link_site', 'link_formulario'].map(k => cfg[k]).filter(Boolean), nonExistingFeatures: list(cfg.funcionalidades_inexistentes), suppression: $('Supressao').all().map(i => i.json) };
const fila = (e.versoes || []).slice(0, 2).map((v, i) => { const r = validateDraft(v, vctx, vcfg);
  return { draft_id: id + '-' + t + '-' + (i + 1), lead_id: id, versao: i + 1, assunto: v.assunto, corpo: v.corpo, validacao: r.ok ? 'ok' + (r.warnings.length ? ' (' + r.warnings.join('; ') + ')' : '') : 'BLOQUEADO: ' + r.errors.join(' | '), estado: r.ok ? 'pendente' : 'rejeitado', criado_em: t, atualizado_em: t }; });
const temPendente = fila.some(f => f.estado === 'pendente');
const status = temPendente ? 'aguardando_aprovacao' : 'qualificado';
const updated = { ...lead, nao_contatar: lead.nao_contatar ? 'TRUE' : '', segmento: q.segmento || lead.segmento, produtos: (q.produtos || []).join('; ') || lead.produtos, score: s.score,
  justificativa: 'Fatos: ' + (q.fatos || []).map(f => f.texto + ' (' + f.url + ')').join(' | ') + ' || Inferências: ' + (q.inferencias || []).join(' | ') + ' || Hipóteses (confirmar em conversa): ' + (q.hipoteses || []).join(' | ') + ' || Confiança: ' + s.confidence,
  desconhecido: (q.desconhecido || []).concat(s.unknown.map(k => 'fator ' + k)).join('; '), hipotese_problema: q.hipotese_problema || '', gancho: q.gancho || '',
  ultima_pesquisa: t, status, atualizado_em: t };
const hist = { em: t, lead_id: id, evento: 'qualificacao_ia', de: lead.status, para: status, por: 'ia', detalhes: 'score=' + s.score + '; rascunhos=' + fila.length };
const fonteRow = prev.fetched ? [{ lead_id: id, url: prev.siteUrl, data_pesquisa: t, tipo: 'site_oficial', trecho: '', nivel: 'fato' }] : [];
return [{ json: { lead: updated, fila, hist, fonteRow } }];`, 11),
    code('Item lead', `return [{ json: $input.first().json.lead }];`, 12),
    sheetWrite('Atualizar lead', 'Leads', 'update', 'id', 13),
    code('Itens fila', `return $('Validar e preparar gravações').first().json.fila.map(f => ({ json: f }));`, 14),
    sheetWrite('Gravar fila', 'Fila', 'append', null, 15),
    code('Item histórico', `return [{ json: $('Validar e preparar gravações').first().json.hist }];`, 16),
    sheetWrite('Gravar histórico', 'Historico', 'append', null, 17),
    code('Itens fonte', `return $('Validar e preparar gravações').first().json.fonteRow.map(f => ({ json: f }));`, 18),
    sheetWrite('Gravar fonte', 'Fontes', 'append', null, 19),
    code('Resposta', `const v = $('Validar e preparar gravações').first().json; return [{ json: { body: JSON.stringify({ score: v.lead.score, rascunhos: v.fila.map(f => f.validacao) }) } }];`, 20),
    respond('Responder', 21, 'application/json'),
  ];
  const V = 'Validar e preparar gravações';
  return wf('Montco 02 — Qualificar e gerar rascunho', n, [
    ['Webhook', 'Leads', 'Fontes', 'Config', 'Supressao', 'Selecionar lead', 'Buscar site oficial', 'Montar qualificação', 'Claude: qualificar', 'Pontuar e montar e-mail', 'Claude: rascunho', V],
    [V, 'Item lead', 'Atualizar lead'], [V, 'Itens fila', 'Gravar fila'], [V, 'Item histórico', 'Gravar histórico'], [V, 'Itens fonte', 'Gravar fonte'], [V, 'Resposta', 'Responder']]);
})();

// 03 — Fila de revisão humana + funil
workflows['03-revisao-e-funil'] = (() => {
  const view = [
    webhook('Revisão (GET)', 'montco-review', 'GET', 0),
    sheetGet('Fila', 'Fila', 1), sheetGet('Leads', 'Leads', 2),
    code('Renderizar fila', `
requireToken(($('Revisão (GET)').first().json.query || {}).token);
const token = $('Revisão (GET)').first().json.query.token;
const leads = Object.fromEntries($('Leads').all().map(i => [i.json.id, i.json]));
const items = $('Fila').all().map(i => i.json).filter(f => f.draft_id && ['pendente', 'aprovado'].includes(f.estado));
const stageOpts = STAGES.map(s => '<option>' + esc(s) + '</option>').join('');
const cards = items.map(f => { const l = leads[f.lead_id] || {}; return '<form method="POST" action="/webhook/montco-action" style="border:1px solid #888;padding:12px;margin:12px 0">' +
  '<input type="hidden" name="token" value="' + esc(token) + '"><input type="hidden" name="draft_id" value="' + esc(f.draft_id) + '"><input type="hidden" name="lead_id" value="' + esc(f.lead_id) + '">' +
  '<h3>' + esc(l.nome) + ' — score ' + esc(l.score) + ' — ' + esc(f.estado) + '</h3><p><small>' + esc(l.justificativa) + '</small></p><p><small>Desconhecido: ' + esc(l.desconhecido) + '</small></p>' +
  '<p>Validação: <b>' + esc(f.validacao) + '</b></p><input name="assunto" style="width:100%" value="' + esc(f.assunto) + '"><textarea name="corpo" rows="9" style="width:100%">' + esc(f.corpo) + '</textarea>' +
  '<p>Etapa: <select name="para"><option value="">(manter)</option>' + stageOpts + '</select> Motivo/obs: <input name="motivo"> Próxima ação: <input name="proxima_acao"> Data: <input name="proxima_acao_data" type="date"></p>' +
  ['approve:Aprovar (pronto p/ envio manual)', 'edit:Salvar edição', 'reject:Rejeitar', 'sent:Marcei como enviado', 'reply:Registrar resposta', 'stage:Mudar etapa', 'schedule:Agendar ação', 'dnc:Não contatar', 'erase:Excluir dados pessoais']
    .map(a => { const [k, v] = a.split(':'); return '<button name="action" value="' + k + '">' + v + '</button>'; }).join(' ') + '</form>'; }).join('');
return [{ json: { body: '<!doctype html><meta charset="utf-8"><title>Fila de revisão</title><body style="font-family:sans-serif;max-width:900px;margin:auto"><h1>Fila de revisão</h1><p>Nada é enviado por este sistema. Copie o texto aprovado e envie manualmente.</p>' + (cards || '<p>Fila vazia.</p>') + '</body>' } }];`, 3),
    respond('Responder fila', 4),
  ];
  const act = [
    webhook('Ação (POST)', 'montco-action', 'POST', 0),
    sheetGet('Fila', 'Fila', 1), sheetGet('Leads', 'Leads', 2), sheetGet('Config', 'Config', 3), sheetGet('Fontes', 'Fontes', 4), sheetGet('Supressao', 'Supressao', 5),
    code('Aplicar ação', `
const b = $('Ação (POST)').first().json.body || {};
requireToken(b.token);
const t = now(), act = b.action;
const draft = $('Fila').all().map(i => i.json).find(f => f.draft_id === b.draft_id);
const raw = $('Leads').all().map(i => i.json).find(l => l.id === b.lead_id);
if (!raw) throw new Error('Lead não encontrado');
let lead = normLead(raw);
const out = { fila: null, lead: null, hist: [], supressao: null }, cfg = cfgMap($('Config').all());
const H = (evento, detalhes, de, para) => out.hist.push({ em: t, lead_id: lead.id, evento, de: de || lead.status, para: para || lead.status, por: 'usuario', detalhes: detalhes || '' });
const go = (to, reason) => { const n = transition(lead, to, { at: t, reason }); H('transicao', reason, lead.status, to); lead = n; };
const check = (d) => validateDraft(d, { ...lead, fontes: $('Fontes').all().map(i => i.json).filter(f => f.lead_id === lead.id).map(f => f.url) },
  { allowedLinks: ['link_apresentacao', 'link_site', 'link_formulario'].map(k => cfg[k]).filter(Boolean), nonExistingFeatures: list(cfg.funcionalidades_inexistentes), suppression: $('Supressao').all().map(i => i.json) });
const setFila = (estado, extra) => { out.fila = { ...draft, ...extra, estado, atualizado_em: t }; };
switch (act) {
  case 'edit': { if (!draft) throw new Error('Rascunho não encontrado'); H('edicao', 'antes: ' + draft.assunto + ' | ' + draft.corpo + ' => depois: ' + b.assunto + ' | ' + b.corpo);
    const r = check({ assunto: b.assunto, corpo: b.corpo }); setFila('pendente', { assunto: b.assunto, corpo: b.corpo, validacao: r.ok ? 'ok (editado)' : 'ATENÇÃO: ' + r.errors.join(' | ') }); break; }
  case 'approve': { if (!draft) throw new Error('Rascunho não encontrado');
    const r = check({ assunto: b.assunto || draft.assunto, corpo: b.corpo || draft.corpo }); if (!r.ok) throw new Error('Aprovação bloqueada: ' + r.errors.join(' | '));
    setFila('aprovado', { assunto: b.assunto || draft.assunto, corpo: b.corpo || draft.corpo, validacao: 'ok (aprovado)' }); H('aprovacao', 'rascunho ' + draft.draft_id); go('aprovada'); break; }
  case 'reject': setFila('rejeitado', {}); H('rejeicao', b.motivo); break;
  case 'sent': go('contato_realizado', 'enviado manualmente'); if (draft) setFila('enviado', {}); lead.proxima_acao = b.proxima_acao || suggestNextAction(lead); break;
  case 'reply': go('resposta_recebida', b.motivo); lead.proxima_acao = b.proxima_acao || suggestNextAction(lead); break;
  case 'stage': if (!b.para) throw new Error('Escolha a etapa'); go(b.para, b.motivo); if (b.para === 'perdido') lead.motivo_perda = b.motivo; lead.proxima_acao = b.proxima_acao || suggestNextAction(lead); break;
  case 'schedule': lead.proxima_acao = b.proxima_acao; lead.proxima_acao_data = b.proxima_acao_data; H('agendamento', b.proxima_acao + ' ' + b.proxima_acao_data); break;
  case 'dnc': lead = markDoNotContact(lead, { at: t, reason: b.motivo }); H('nao_contatar', b.motivo); out.supressao = { lead_id: lead.id, email: lead.email || '', dominio: normalizeDomain(lead.site), motivo: b.motivo || '', em: t };
    if (draft && ['pendente', 'aprovado'].includes(draft.estado)) setFila('rejeitado', { validacao: 'cancelado: não contatar' }); break;
  case 'erase': lead = { ...lead, contato_nome: '', contato_cargo: '', email: '', email_fonte: '', telefone: '', nao_contatar: true, proxima_acao: '' }; H('exclusao_dados_pessoais', b.motivo);
    out.supressao = { lead_id: lead.id, email: '', dominio: normalizeDomain(lead.site), motivo: 'exclusão: ' + (b.motivo || ''), em: t };
    if (draft) setFila('rejeitado', { validacao: 'cancelado: dados excluídos' }); break;
  default: throw new Error('Ação desconhecida: ' + act);
}
if (act !== 'reject' && act !== 'edit') out.lead = { ...lead, nao_contatar: lead.nao_contatar ? 'TRUE' : '', atualizado_em: t }; else if (!out.lead) out.lead = null;
return [{ json: out }];`, 6),
    code('Item fila', `const f = $input.first().json.fila; return f ? [{ json: f }] : [];`, 7),
    sheetWrite('Atualizar fila', 'Fila', 'update', 'draft_id', 8),
    code('Item lead', `const l = $('Aplicar ação').first().json.lead; return l ? [{ json: l }] : [];`, 9),
    sheetWrite('Atualizar lead', 'Leads', 'update', 'id', 10),
    code('Itens histórico', `return $('Aplicar ação').first().json.hist.map(h => ({ json: h }));`, 11),
    sheetWrite('Gravar histórico', 'Historico', 'append', null, 12),
    code('Item supressão', `const s = $('Aplicar ação').first().json.supressao; return s ? [{ json: s }] : [];`, 13),
    sheetWrite('Gravar supressão', 'Supressao', 'append', null, 14),
    code('Resposta', `return [{ json: { body: '<!doctype html><meta charset="utf-8"><p>Ação registrada. <a href="javascript:history.go(-1)">Voltar</a></p>' } }];`, 15),
    respond('Responder ação', 16),
  ];
  const nodes = [...view, ...act];
  const names = a => a.map(x => x.name);
  // nós com mesmo nome nos dois ramos precisam ser únicos
  const rename = (arr, suf) => arr.map(x => ({ ...x, name: x.name + suf }));
  // simplificação: renomeia todo o ramo de ação para evitar colisões e reescreve referências $('...')
  const sufx = ' [ação]';
  const actNames = names(act);
  const renamed = act.map(x => {
    let js = x.parameters && x.parameters.jsCode;
    if (js) actNames.forEach(nm => { js = js.split("$('" + nm + "')").join("$('" + nm + sufx + "')"); });
    return { ...x, name: x.name + sufx, parameters: js ? { ...x.parameters, jsCode: js } : x.parameters };
  });
  const all = [...view, ...renamed];
  const S = x => x + sufx, A = S('Aplicar ação');
  return wf('Montco 03 — Revisão humana e funil', all, [names(view),
    [S('Ação (POST)'), S('Fila'), S('Leads'), S('Config'), S('Fontes'), S('Supressao'), A],
    [A, S('Item fila'), S('Atualizar fila')], [A, S('Item lead'), S('Atualizar lead')], [A, S('Itens histórico'), S('Gravar histórico')],
    [A, S('Item supressão'), S('Gravar supressão')], [A, S('Resposta'), S('Responder ação')]]);
})();

// 04 — Dashboard e exportação
workflows['04-dashboard-e-exportacao'] = (() => {
  const dash = [
    webhook('Dashboard (GET)', 'montco-dashboard', 'GET', 0), sheetGet('Leads', 'Leads', 1), sheetGet('Historico', 'Historico', 2), sheetGet('Config', 'Config', 3),
    code('Calcular', `
requireToken(($('Dashboard (GET)').first().json.query || {}).token);
const cfg = cfgMap($('Config').all());
const hist = {};
for (const h of $('Historico').all().map(i => i.json)) if (h.lead_id) (hist[h.lead_id] = hist[h.lead_id] || []).push(h);
const leads = $('Leads').all().map(i => i.json).filter(l => l.id).map(l => ({ ...normLead(l), historico: hist[l.id] || [] }));
const m = computeMetrics(leads, { minSample: Number(cfg.min_amostra_conversao) || 20, stages: cfg.etapas ? cfg.etapas.split(',').map(s => s.trim()) : STAGES });
const tbl = (o) => '<table border="1" cellpadding="4">' + Object.entries(o).map(([k, v]) => '<tr><td>' + esc(k) + '</td><td>' + esc(v) + '</td></tr>').join('') + '</table>';
const conv = m.conversoes.map(c => '<tr><td>' + esc(c.de + ' → ' + c.para) + '</td><td>' + c.atingiram + '/' + c.base + '</td><td>' + (c.taxa == null ? '—' : c.taxa + '%') + '</td><td>' + esc(c.nota) + '</td></tr>').join('');
const html = '<!doctype html><meta charset="utf-8"><title>Dashboard</title><body style="font-family:sans-serif;max-width:900px;margin:auto"><h1>Dashboard</h1><p>Total de empresas: <b>' + m.total + '</b>. Todos os números são <b>observados</b> na planilha; nenhuma estimativa é calculada.</p>' +
  '<h2>Leads por etapa (atingiram a etapa)</h2>' + tbl(m.porEtapa) + '<h2>Conversão entre etapas</h2><table border="1" cellpadding="4">' + conv + '</table>' +
  '<h2>Segmentos</h2>' + tbl(m.porSegmento) + '<h2>Fontes de aquisição</h2>' + tbl(m.porFonte) + '<h2>Motivos de perda</h2>' + tbl(m.motivosPerda) +
  '<h2>Próximas ações</h2><ul>' + m.proximasAcoes.map(a => '<li>' + esc(a.nome + ': ' + a.acao + ' ' + a.data) + '</li>').join('') + '</ul></body>';
return [{ json: { body: html } }];`, 4),
    respond('Responder dashboard', 5),
  ];
  const exp = [
    webhook('Exportar (GET)', 'montco-export', 'GET', 0), sheetGet('Leads', 'Leads', 1), sheetGet('Historico', 'Historico', 2), sheetGet('Fontes', 'Fontes', 3), sheetGet('Supressao', 'Supressao', 4),
    code('Montar exportação', `
const q = $('Exportar (GET)').first().json.query || {};
requireToken(q.token);
const sheets = { Leads: 'Leads', Historico: 'Historico', Fontes: 'Fontes', Supressao: 'Supressao' };
const name = sheets[q.sheet || 'Leads']; if (!name) throw new Error('Aba inválida');
const rows = $(name + ' [exp]').all().map(i => i.json).filter(r => Object.values(r).some(Boolean));
return [{ json: { body: q.format === 'json' ? JSON.stringify(rows) : toCsv(rows), ct: q.format === 'json' ? 'application/json' : 'text/csv; charset=utf-8' } }];`, 5),
    respond('Responder exportação', 6, '={{$json.ct}}'),
  ];
  const expR = exp.map(x => {
    const nm = ['Leads', 'Historico', 'Fontes', 'Supressao'].includes(x.name) ? x.name + ' [exp]' : x.name;
    return { ...x, name: nm };
  });
  const all = [...dash, ...expR];
  return wf('Montco 04 — Dashboard e exportação', all, [dash.map(x => x.name), expR.map(x => x.name)]);
})();

if (require.main === module) {
  fs.mkdirSync(path.join(root, 'workflows'), { recursive: true });
  for (const [k, v] of Object.entries(workflows)) {
    fs.writeFileSync(path.join(root, 'workflows', k + '.json'), JSON.stringify(v, null, 2) + '\n');
    console.log('gerado workflows/' + k + '.json');
  }
}
module.exports = { workflows };
