const test = require('node:test');
const assert = require('node:assert');
const { workflows } = require('../scripts/build-workflows');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

// Executa um Code node com $/$input/$env simulados (sem rede, sem n8n).
async function run(wfKey, nodeName, { nodes = {}, input = [], env = { REVIEW_UI_TOKEN: 't' } }) {
  const node = workflows[wfKey].nodes.find(n => n.name === nodeName);
  const wrap = items => ({ all: () => items.map(json => ({ json })), first: () => ({ json: items[0] }) });
  const $ = name => { if (!nodes[name]) throw new Error('nó não simulado: ' + name); return wrap(nodes[name]); };
  return new AsyncFunction('$', '$input', '$env', node.parameters.jsCode)($, wrap(input), env).then(r => r.map(i => i.json));
}

const csv = 'nome,site,uf,fonte_url\nAlfa Ficticia,alfa.example,SP,https://alfa.example/p\nAlfa Ficticia Ltda,https://www.alfa.example,SP,https://dir.example/a\n';

test('import: dedup por domínio e token obrigatório', async () => {
  const wh = { body: { csv }, query: { token: 't' }, headers: {} };
  const out = await run('01-import-csv', 'Dedup', { nodes: { Webhook: [wh] }, input: [] });
  assert.equal(out.filter(o => o.kind === 'lead').length, 2);
  assert.equal(new Set(out.filter(o => o.kind === 'lead').map(o => o.lead_row.id)).size, 1);
  assert.equal(out.find(o => o.kind === 'resumo').resumo.novos, 1);
  await assert.rejects(run('01-import-csv', 'Dedup', { nodes: { Webhook: [{ ...wh, query: { token: 'x' } }] } }), /autorizado/);
  await assert.rejects(run('01-import-csv', 'Dedup', { nodes: { Webhook: [wh] }, env: {} }), /REVIEW_UI_TOKEN/);
});

const base = (body, lead = {}, draft = {}) => ({ nodes: {
  'Ação (POST) [ação]': [{ body: { token: 't', lead_id: 'L1', draft_id: 'D1', ...body } }],
  'Fila [ação]': [{ draft_id: 'D1', lead_id: 'L1', assunto: 'Prazos', corpo: 'Olá, vi que a Alfa fabrica linhas de montagem. Teria 20 minutos?', estado: 'pendente', ...draft }],
  'Leads [ação]': [{ id: 'L1', nome: 'Alfa', site: 'https://alfa.example', status: 'aguardando_aprovacao', ...lead }],
  'Config [ação]': [{ chave: 'funcionalidades_inexistentes', valor: 'IoT' }], 'Fontes [ação]': [{ lead_id: 'L1', url: 'https://alfa.example/p' }], 'Supressao [ação]': [],
} });

test('ação aprovar: valida, registra histórico e muda etapa', async () => {
  const [o] = await run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'approve' }));
  assert.equal(o.fila.estado, 'aprovado');
  assert.equal(o.lead.status, 'aprovada');
  assert.ok(o.hist.some(h => h.evento === 'aprovacao'));
});

test('ação aprovar é bloqueada se o texto inventa dor ou cita recurso inexistente', async () => {
  await assert.rejects(run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'approve', corpo: 'Vocês sofrem com atrasos e nosso IoT resolve' })), /bloqueada/);
});

test('não contatar: cancela rascunho, grava supressão e impede nova aprovação', async () => {
  const [o] = await run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'dnc', motivo: 'pediu' }));
  assert.equal(o.fila.estado, 'rejeitado');
  assert.equal(o.supressao.dominio, 'alfa.example');
  assert.equal(o.lead.nao_contatar, 'TRUE');
  await assert.rejects(run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'approve' }, { nao_contatar: 'TRUE' })), /bloqueada|bloqueada|contatar/);
});

test('enviado manualmente → contato_realizado; perdido exige motivo; erase limpa dados pessoais', async () => {
  const [s] = await run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'sent' }, { status: 'aprovada' }));
  assert.equal(s.lead.status, 'contato_realizado');
  assert.equal(s.fila.estado, 'enviado');
  await assert.rejects(run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'stage', para: 'perdido' })), /motivo/);
  const [e] = await run('03-revisao-e-funil', 'Aplicar ação [ação]', base({ action: 'erase' }, { email: 'a@alfa.example', telefone: '1' }));
  assert.equal(e.lead.email, '');
  assert.equal(e.lead.telefone, '');
});
