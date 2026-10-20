const L = require('../scripts/bundle').load();

const DEFAULTS = { min_amostra_conversao: '20', funcionalidades_existentes: '', funcionalidades_inexistentes: '', link_apresentacao: '', link_site: '', link_formulario: '', remetente_nome: '', remetente_contato: '', etapas: '' };
const now = () => new Date().toISOString();
const list = s => String(s || '').split(';').map(x => x.trim()).filter(Boolean);
const hashId = s => { let h = 5381; for (const c of s) h = ((h * 33) ^ c.charCodeAt(0)) >>> 0; return 'L' + h.toString(36); };
const cfgOf = db => ({ ...DEFAULTS, ...db.config() });
const weightsOf = cfg => Object.fromEntries(Object.keys(L.DEFAULT_WEIGHTS).map(k => [k, Number(cfg['peso_' + k]) || L.DEFAULT_WEIGHTS[k]]));
const vcfg = (db, cfg) => ({ allowedLinks: ['link_apresentacao', 'link_site', 'link_formulario'].map(k => cfg[k]).filter(Boolean), nonExistingFeatures: list(cfg.funcionalidades_inexistentes), suppression: db.all('supressao') });
const sourceUrls = (db, id) => db.all('fontes').filter(f => f.lead_id === id).map(f => f.url);
const log = (db, o) => db.add('historico', { em: now(), por: 'usuario', ...o });

function importCsv(db, text) {
  const rows = L.parseCsv(text);
  if (!rows.length) throw new Error('CSV vazio ou sem cabeçalho');
  if (!rows.some(r => r.nome)) throw new Error('CSV precisa da coluna "nome"');
  const res = { novos: 0, mesclados: 0, possiveis_duplicados: 0, ignorados: 0, cnpj_invalido: 0 };
  db.tx(() => {
    const base = db.all('leads');
    for (const r of rows) {
      if (!r.nome) { res.ignorados++; continue; }
      if (r.cnpj && !L.validCnpj(r.cnpj)) { r.cnpj = ''; res.cnpj_invalido++; }
      const { fonte_url, fonte_trecho, ...data } = r;
      const t = now(), d = L.findDuplicate(data, base);
      let lead;
      if (d && d.strong) { lead = { ...L.mergeLead(d.lead, data), atualizado_em: t }; base[base.indexOf(d.lead)] = lead; res.mesclados++; log(db, { lead_id: lead.id, evento: 'mesclado_por_' + d.match, de: lead.status, para: lead.status, detalhes: data.nome, por: 'import' }); }
      else {
        lead = { ...data, id: hashId(L.normalizeDomain(data.site) || L.normalizeCnpj(data.cnpj) || L.normalizeName(data.nome) + (data.uf || '')), status: 'identificada', nao_contatar: false, fonte_aquisicao: data.fonte_aquisicao || 'csv', criado_em: t, atualizado_em: t };
        if (base.some(b => b.id === lead.id)) lead.id += '-' + (base.length + 1);
        if (d) { lead.justificativa = 'Possível duplicado de ' + d.lead.id + ' (mesmo nome+UF)'; res.possiveis_duplicados++; }
        base.push(lead); res.novos++;
        log(db, { lead_id: lead.id, evento: 'criado', de: '', para: 'identificada', por: 'import' });
      }
      db.put('leads', lead.id, lead);
      if (fonte_url && !db.all('fontes').some(f => f.lead_id === lead.id && f.url === fonte_url)) db.add('fontes', { lead_id: lead.id, url: fonte_url, data_pesquisa: t, tipo: lead.fonte_aquisicao, trecho: fonte_trecho || '', nivel: 'fato' });
    }
  });
  return res;
}

const htmlToText = h => String(h).replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 8000);

// fetchSite(url) -> html. Apenas o site oficial cadastrado do lead; falha de rede não derruba o processo.
async function qualify(db, ai, leadId, fetchSite) {
  const raw = db.get('leads', leadId);
  if (!raw) throw new Error('Lead não encontrado');
  if (raw.nao_contatar || L.isSuppressed(raw, db.all('supressao'))) throw new Error('Lead em lista de supressão: nada será gerado');
  const cfg = cfgOf(db);
  const fe = list(cfg.funcionalidades_existentes);
  if (!fe.length) throw new Error('Defina "Funcionalidades existentes" em Config antes de gerar e-mails');
  const t = now(), notes = [];
  const sources = db.all('fontes').filter(f => f.lead_id === leadId).map(f => ({ url: f.url, text: f.trecho || '' }));
  const dom = L.normalizeDomain(raw.site);
  if (dom && fetchSite) {
    const url = /^https?:/i.test(raw.site) ? raw.site : 'https://' + raw.site;
    try {
      const text = htmlToText(await fetchSite(url));
      if (text) { sources.push({ url, text }); if (!db.all('fontes').some(f => f.lead_id === leadId && f.url === url && f.tipo === 'site_oficial')) db.add('fontes', { lead_id: leadId, url, data_pesquisa: t, tipo: 'site_oficial', trecho: text.slice(0, 500), nivel: 'fato' }); }
    } catch (e) { notes.push('Site oficial não acessível (' + e.message + '): usando apenas fontes registradas'); }
  }
  if (!sources.some(s => s.text)) throw new Error('Sem texto de fonte para analisar. Cadastre uma fonte com trecho (coluna fonte_trecho) ou um site acessível. ' + notes.join(' '));
  const material = '<fontes>\n' + sources.map(s => `[${s.url}]\n${s.text}`).join('\n\n') + '\n</fontes>\nEmpresa: ' + raw.nome + ' (' + (raw.cidade || '') + '/' + (raw.uf || '') + ')';
  const q = await ai.qualify({ material, sources, lead: raw });
  for (const f of Object.values(q.factors || {})) if (!f.evidence || !f.evidence.length) { f.value = null; f.level = 'hipotese'; }
  const known = new Set(sources.map(s => s.url));
  q.fatos = (q.fatos || []).filter(f => f.url && known.has(f.url));
  const s = L.computeScore(q.factors || {}, weightsOf(cfg));
  const e = await ai.draft({ payload: { empresa: raw.nome, segmento: q.segmento, fatos: q.fatos, gancho: q.gancho, funcionalidades_existentes: fe,
    links_permitidos: ['link_apresentacao', 'link_site', 'link_formulario'].map(k => cfg[k]).filter(Boolean), remetente: { nome: cfg.remetente_nome, contato: cfg.remetente_contato } } });
  const ctx = { ...raw, fontes: sourceUrls(db, leadId) };
  const fila = (e.versoes || []).slice(0, 2).map((v, i) => { const r = L.validateDraft(v, ctx, vcfg(db, cfg));
    return { draft_id: leadId + '-' + Date.now() + '-' + (i + 1), lead_id: leadId, versao: i + 1, assunto: v.assunto, corpo: v.corpo, validacao: r.ok ? 'ok' + (r.warnings.length ? ' (' + r.warnings.join('; ') + ')' : '') : 'BLOQUEADO: ' + r.errors.join(' | '), estado: r.ok ? 'pendente' : 'rejeitado', simulado: !!ai.simulated, criado_em: t, atualizado_em: t }; });
  const status = fila.some(f => f.estado === 'pendente') ? 'aguardando_aprovacao' : 'qualificado';
  const lead = { ...raw, segmento: q.segmento || raw.segmento, produtos: (q.produtos || []).join('; ') || raw.produtos, score: s.score, confianca: s.confidence, breakdown: s.breakdown,
    fatos: q.fatos, inferencias: q.inferencias || [], hipoteses: q.hipoteses || [], desconhecido: (q.desconhecido || []).concat(s.unknown.map(k => 'fator ' + k + ' (' + L.FACTORS[k] + ')')),
    hipotese_problema: q.hipotese_problema || '', gancho: q.gancho || '', ultima_pesquisa: t, qualificacao_simulada: !!ai.simulated, status, atualizado_em: t, aviso: notes.join(' ') };
  db.tx(() => {
    db.put('leads', leadId, lead);
    fila.forEach(f => db.put('fila', f.draft_id, f));
    log(db, { lead_id: leadId, evento: 'qualificacao_ia' + (ai.simulated ? '_simulada' : ''), de: raw.status, para: status, por: 'ia', detalhes: 'score=' + s.score + '; rascunhos=' + fila.length });
  });
  return { lead, fila };
}

// Ações do usuário na fila/funil. Lança erro se bloqueada; nada é enviado externamente.
function act(db, b) {
  const t = now(), a = b.action;
  const draft = b.draft_id ? db.get('fila', b.draft_id) : null;
  const raw = db.get('leads', b.lead_id);
  if (!raw) throw new Error('Lead não encontrado');
  let lead = { ...raw };
  const cfg = cfgOf(db), hist = [];
  const H = (evento, detalhes, de, para) => hist.push({ lead_id: lead.id, evento, de: de || lead.status, para: para || lead.status, detalhes: detalhes || '' });
  const go = (to, reason) => { const n = L.transition(lead, to, { at: t, reason }); delete n.historico; H('transicao', reason, lead.status, to); lead = n; };
  const check = d => L.validateDraft(d, { ...lead, fontes: sourceUrls(db, lead.id) }, vcfg(db, cfg));
  let fila = null, sup = null;
  const setFila = (estado, extra) => { fila = { ...draft, ...extra, estado, atualizado_em: t }; };
  const need = () => { if (!draft) throw new Error('Rascunho não encontrado'); };
  switch (a) {
    case 'edit': { need(); H('edicao', 'antes: ' + draft.assunto + ' | ' + draft.corpo + ' => depois: ' + b.assunto + ' | ' + b.corpo);
      const r = check({ assunto: b.assunto, corpo: b.corpo }); setFila('pendente', { assunto: b.assunto, corpo: b.corpo, validacao: r.ok ? 'ok (editado)' : 'ATENÇÃO: ' + r.errors.join(' | ') }); break; }
    case 'approve': { need(); const d = { assunto: b.assunto || draft.assunto, corpo: b.corpo || draft.corpo };
      const r = check(d); if (!r.ok) throw new Error('Aprovação bloqueada: ' + r.errors.join(' | '));
      setFila('aprovado', { ...d, validacao: 'ok (aprovado)' }); H('aprovacao', 'rascunho ' + draft.draft_id); go('aprovada'); break; }
    case 'reject': need(); setFila('rejeitado', {}); H('rejeicao', b.motivo); break;
    case 'sent': go('contato_realizado', 'enviado manualmente'); if (draft) setFila('enviado', {}); lead.proxima_acao = b.proxima_acao || L.suggestNextAction(lead); break;
    case 'reply': go('resposta_recebida', b.motivo); lead.proxima_acao = b.proxima_acao || L.suggestNextAction(lead); break;
    case 'stage': if (!b.para) throw new Error('Escolha a etapa'); go(b.para, b.motivo); if (b.para === 'perdido') lead.motivo_perda = b.motivo; lead.proxima_acao = b.proxima_acao || L.suggestNextAction(lead); break;
    case 'schedule': lead.proxima_acao = b.proxima_acao || ''; lead.proxima_acao_data = b.proxima_acao_data || ''; H('agendamento', lead.proxima_acao + ' ' + lead.proxima_acao_data); break;
    case 'override': { const sc = Number(b.score); if (!(sc >= 0 && sc <= 100)) throw new Error('Pontuação deve ser 0–100'); H('ajuste_manual_score', `de ${lead.score} para ${sc}: ${b.motivo || ''}`); lead.score = sc; lead.score_manual = true; break; }
    case 'dnc': lead = L.markDoNotContact(lead, { at: t, reason: b.motivo }); delete lead.historico; H('nao_contatar', b.motivo);
      sup = { lead_id: lead.id, email: lead.email || '', dominio: L.normalizeDomain(lead.site), motivo: b.motivo || '', em: t };
      for (const f of db.all('fila').filter(f => f.lead_id === lead.id && ['pendente', 'aprovado'].includes(f.estado))) db.put('fila', f.draft_id, { ...f, estado: 'rejeitado', validacao: 'cancelado: não contatar', atualizado_em: t });
      fila = null; break;
    case 'erase': lead = { ...lead, contato_nome: '', contato_cargo: '', email: '', email_fonte: '', telefone: '', nao_contatar: true, proxima_acao: '' }; H('exclusao_dados_pessoais', b.motivo);
      sup = { lead_id: lead.id, email: '', dominio: L.normalizeDomain(lead.site), motivo: 'exclusão: ' + (b.motivo || ''), em: t };
      for (const f of db.all('fila').filter(f => f.lead_id === lead.id && ['pendente', 'aprovado'].includes(f.estado))) db.put('fila', f.draft_id, { ...f, estado: 'rejeitado', validacao: 'cancelado: dados excluídos', atualizado_em: t });
      fila = null; break;
    case 'delete_lead': throw new Error('Exclusão completa do lead: use "Excluir dados pessoais"; o registro mínimo é mantido para a supressão');
    default: throw new Error('Ação desconhecida: ' + a);
  }
  db.tx(() => {
    if (fila) db.put('fila', fila.draft_id, fila);
    db.put('leads', lead.id, { ...lead, atualizado_em: t });
    hist.forEach(h => log(db, h));
    if (sup) db.add('supressao', sup);
  });
  return lead;
}

function metrics(db) {
  const cfg = cfgOf(db), hist = {};
  for (const h of db.all('historico')) (hist[h.lead_id] = hist[h.lead_id] || []).push(h);
  const leads = db.all('leads').map(l => ({ ...l, historico: hist[l.id] || [] }));
  return L.computeMetrics(leads, { minSample: Number(cfg.min_amostra_conversao) || 20, stages: cfg.etapas ? cfg.etapas.split(',').map(s => s.trim()) : L.DEFAULT_STAGES });
}
module.exports = { L, DEFAULTS, cfgOf, importCsv, qualify, act, metrics, list };
