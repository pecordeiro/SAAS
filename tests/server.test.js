const test = require('node:test');
const assert = require('node:assert');
const http = require('http'), fs = require('fs'), path = require('path');
const { createApp } = require('../server/index');
const dbm = require('../server/db');
const ai = require('../server/ai');

async function boot(opts = {}) {
  const db = dbm.open(':memory:');
  const server = http.createServer(createApp({ db, ai: opts.ai || ai.mock(), fetchSite: async () => { throw new Error('sem rede nos testes'); } }));
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  let csrf = '';
  const get = async p => { const r = await fetch(base + p, { redirect: 'manual' }); const t = await r.text(); const m = /name="_csrf" value="([^"]+)"/.exec(t); if (m) csrf = m[1]; return { status: r.status, text: t, loc: r.headers.get('location') }; };
  const post = async (p, body, referer) => { const r = await fetch(base + p, { method: 'POST', redirect: 'manual', headers: { 'content-type': 'application/x-www-form-urlencoded', referer: referer || base + '/' }, body: new URLSearchParams({ _csrf: csrf, ...body }) }); return { status: r.status, loc: r.headers.get('location') || '', msg: decodeURIComponent((r.headers.get('location') || '').split('m=')[1] || '') }; };
  await get('/');
  return { db, get, post, close: () => server.close() };
}
const csv = () => fs.readFileSync(path.join(__dirname, '..', 'data', 'exemplo_leads.csv'), 'utf8');
const cfg = { funcionalidades_existentes: 'acompanhamento de etapas de montagem; horas restantes; previsão de conclusão', remetente_nome: 'Fulano Teste', remetente_contato: 'teste@example.com' };

test('fluxo completo: importar, qualificar, aprovar, enviar manualmente, responder, exportar', async () => {
  const t = await boot();
  try {
    assert.match((await t.post('/import', { csv: csv() })).msg, /2 novos, 1 mesclados/);
    assert.equal(t.db.all('leads').length, 2);
    const alfa = t.db.all('leads').find(l => /Alfa/.test(l.nome));
    // sem funcionalidades configuradas, a geração é bloqueada
    const blocked = await t.post(`/lead/${alfa.id}/qualify`, {}, 'http://x/lead/' + alfa.id);
    assert.match(blocked.msg, /Funcionalidades existentes/);
    await t.post('/config', cfg);
    assert.match((await t.post(`/lead/${alfa.id}/qualify`, {})).msg, /Qualificado/);
    const q = t.db.all('fila');
    assert.ok(q.length >= 1);
    assert.equal(q[0].estado, 'pendente');
    assert.ok(t.db.get('leads', alfa.id).score > 50);
    assert.ok(t.db.get('leads', alfa.id).fatos.every(f => f.url));
    assert.match((await t.get('/queue')).text, /Modo simulado/);
    // aprovação
    assert.match((await t.post('/action', { action: 'approve', lead_id: alfa.id, draft_id: q[0].draft_id })).loc, /\/queue/);
    assert.equal(t.db.get('fila', q[0].draft_id).estado, 'aprovado');
    await t.post('/action', { action: 'sent', lead_id: alfa.id, draft_id: q[0].draft_id });
    assert.equal(t.db.get('leads', alfa.id).status, 'contato_realizado');
    await t.post('/action', { action: 'reply', lead_id: alfa.id, motivo: 'topou conversar' });
    assert.equal(t.db.get('leads', alfa.id).status, 'resposta_recebida');
    const dash = (await t.get('/dashboard')).text;
    assert.match(dash, /amostra insuficiente/);
    const exp = await t.get('/export?table=leads&format=csv');
    assert.match(exp.text, /Alfa Automacao/);
    assert.ok(t.db.all('historico').filter(h => h.lead_id === alfa.id).length >= 5);
  } finally { t.close(); }
});

test('aprovação bloqueada com texto inventado; edição revalida', async () => {
  const t = await boot();
  try {
    await t.post('/import', { csv: csv() }); await t.post('/config', cfg);
    const alfa = t.db.all('leads').find(l => /Alfa/.test(l.nome));
    await t.post(`/lead/${alfa.id}/qualify`, {});
    const d = t.db.all('fila')[0];
    const r = await t.post('/action', { action: 'approve', lead_id: alfa.id, draft_id: d.draft_id, corpo: 'Vocês sofrem com atrasos constantes e usam planilhas.', assunto: 'x' });
    assert.match(r.msg, /bloqueada/);
    assert.equal(t.db.get('fila', d.draft_id).estado, 'pendente');
  } finally { t.close(); }
});

test('não contatar: cancela fila, suprime e bloqueia nova qualificação', async () => {
  const t = await boot();
  try {
    await t.post('/import', { csv: csv() }); await t.post('/config', cfg);
    const alfa = t.db.all('leads').find(l => /Alfa/.test(l.nome));
    await t.post(`/lead/${alfa.id}/qualify`, {});
    await t.post('/action', { action: 'dnc', lead_id: alfa.id, motivo: 'pediu' });
    assert.ok(t.db.all('fila').every(f => f.estado === 'rejeitado'));
    assert.equal(t.db.all('supressao').length, 1);
    assert.match((await t.post(`/lead/${alfa.id}/qualify`, {})).msg, /supressão/);
    // reimportar não reativa nem duplica
    await t.post('/import', { csv: csv() });
    assert.equal(t.db.all('leads').length, 2);
    assert.equal(t.db.get('leads', alfa.id).nao_contatar, true);
  } finally { t.close(); }
});

test('IA real sem chave falha de forma explícita e não grava nada', async () => {
  const t2 = await boot({ ai: ai.anthropic({ apiKey: '', model: '' }) });
  try {
    await t2.post('/import', { csv: csv() }); await t2.post('/config', cfg);
    const alfa = t2.db.all('leads').find(l => /Alfa/.test(l.nome));
    assert.match((await t2.post(`/lead/${alfa.id}/qualify`, {})).msg, /ANTHROPIC_API_KEY/);
    assert.equal(t2.db.all('fila').length, 0);
    assert.equal(t2.db.get('leads', alfa.id).score, undefined);
  } finally { t2.close(); }
});

test('CSRF inválido é recusado', async () => {
  const db = dbm.open(':memory:');
  const server = http.createServer(createApp({ db, ai: ai.mock() }));
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const r = await fetch(base + '/import', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 'csv=nome%0Ax&_csrf=errado' });
  assert.equal(r.status, 403);
  const status = await new Promise(res => http.get({ host: '127.0.0.1', port: server.address().port, path: '/', headers: { host: 'evil.example' } }, r => { r.resume(); res(r.statusCode); }));
  assert.equal(status, 403, 'bloqueia Host desconhecido (DNS rebinding)');
  server.close();
});

test('provedor Anthropic: monta requisição sem vazar a chave e falha em HTTP de erro', async () => {
  let seen;
  const okFetch = async (u, o) => { seen = { u, o }; return { ok: true, json: async () => ({ content: [{ text: '{"x":1}' }] }) }; };
  const p = ai.anthropic({ apiKey: 'k-teste', model: 'm-teste', fetchImpl: okFetch });
  assert.deepEqual(await p.qualify({ material: 'm' }), { x: 1 });
  assert.equal(seen.u, 'https://api.anthropic.com/v1/messages');
  assert.equal(seen.o.headers['x-api-key'], 'k-teste');
  assert.ok(!seen.o.body.includes('k-teste'));
  const bad = ai.anthropic({ apiKey: 'k', model: 'm', fetchImpl: async () => ({ ok: false, status: 401 }) });
  await assert.rejects(bad.qualify({ material: 'm' }), /HTTP 401/);
});
