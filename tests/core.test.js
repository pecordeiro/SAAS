const test = require('node:test');
const assert = require('node:assert');
const L = require('./helpers');

test('CSV: parse e export com proteção contra fórmulas', () => {
  const rows = L.parseCsv('nome,site\n"Acme, Ficticia",x.example\n');
  assert.equal(rows[0].nome, 'Acme, Ficticia');
  assert.match(L.toCsv([{ a: '=1+1' }]), /'=1\+1/);
});

test('dedup: mesmo domínio em fontes diferentes não cria novo lead', () => {
  const a = { id: 'L1', nome: 'Alfa Ltda', site: 'https://www.alfa.example/x', uf: 'SP' };
  const b = { nome: 'Alfa', site: 'alfa.example', uf: 'SP' };
  const d = L.findDuplicate(b, [a]);
  assert.equal(d.match, 'dominio');
  assert.ok(d.strong);
});

test('dedup: CNPJ válido casa; inválido é ignorado; nome+UF é só sinal fraco', () => {
  assert.ok(L.validCnpj('11.222.333/0001-81'));
  assert.ok(!L.validCnpj('11.222.333/0001-82'));
  const e = { id: 'L1', nome: 'Beta Paineis Ltda', uf: 'SP', cnpj: '11222333000181' };
  assert.equal(L.findDuplicate({ nome: 'X', cnpj: '11.222.333/0001-81' }, [e]).match, 'cnpj');
  const weak = L.findDuplicate({ nome: 'Beta Paineis', uf: 'sp' }, [e]);
  assert.equal(weak.strong, false);
});

test('merge não sobrescreve dados existentes', () => {
  const m = L.mergeLead({ nome: 'A', cidade: '' }, { nome: 'B', cidade: 'Campinas' });
  assert.equal(m.nome, 'A');
  assert.equal(m.cidade, 'Campinas');
});

test('score: fator desconhecido é neutro e listado; pesos configuráveis', () => {
  const all1 = Object.fromEntries(Object.keys(L.DEFAULT_WEIGHTS).map(k => [k, { value: 1 }]));
  assert.equal(L.computeScore(all1).score, 100);
  const none = L.computeScore({});
  assert.equal(none.score, 50);
  assert.equal(none.unknown.length, 7);
  assert.equal(none.confidence, 0);
  const custom = L.computeScore({ A: { value: 1 }, B: { value: 0 } }, { A: 50, B: 50 });
  assert.equal(custom.score, 50);
});

test('funil: transição registra histórico; perdido exige motivo; não contatar bloqueia', () => {
  let lead = { id: 'L1', status: 'qualificado' };
  lead = L.transition(lead, 'aguardando_aprovacao', { at: '2026-01-01T00:00:00Z' });
  assert.equal(lead.historico[0].para, 'aguardando_aprovacao');
  assert.throws(() => L.transition(lead, 'perdido'));
  assert.throws(() => L.transition(lead, 'inexistente'));
  const dnc = L.markDoNotContact(lead, { reason: 'pedido do contato' });
  assert.equal(dnc.proxima_acao, '');
  assert.throws(() => L.transition(dnc, 'aprovada'));
});

test('supressão por lead, domínio e e-mail', () => {
  const list = [{ dominio: 'alfa.example' }, { email: 'x@y.example' }];
  assert.ok(L.isSuppressed({ site: 'https://alfa.example' }, list));
  assert.ok(L.isSuppressed({ email: 'X@Y.example' }, list));
  assert.ok(!L.isSuppressed({ site: 'https://ok.example' }, list));
});

test('validador de rascunho bloqueia invenção, links e funcionalidades inexistentes', () => {
  const lead = { id: 'L1', site: 'https://alfa.example', fontes: ['https://alfa.example/p'] };
  const ok = { assunto: 'Prazos de montagem na Alfa', corpo: 'Olá, vi que a Alfa fabrica linhas de montagem. Teria 20 minutos para conversarmos?' };
  assert.ok(L.validateDraft(ok, lead).ok);
  const bad = { assunto: 'x', corpo: 'Vocês usam planilhas e sofrem com atrasos constantes. Veja https://falso.example e nosso módulo de IoT [Nome]' };
  const r = L.validateDraft(bad, lead, { nonExistingFeatures: ['IoT'] });
  assert.ok(!r.ok);
  assert.ok(r.errors.length >= 4);
  assert.ok(!L.validateDraft(ok, { ...lead, fontes: [] }).ok);
  assert.ok(!L.validateDraft(ok, { ...lead, email: 'a@alfa.example' }).ok, 'e-mail sem origem');
  assert.ok(!L.validateDraft(ok, lead, { suppression: [{ dominio: 'alfa.example' }] }).ok);
  const link = { assunto: 'a', corpo: 'Veja https://montco.example/apresentacao' };
  assert.ok(L.validateDraft(link, lead, { allowedLinks: ['https://montco.example/apresentacao'] }).ok);
});

test('métricas: amostra insuficiente não gera taxa', () => {
  const leads = [{ status: 'qualificado', historico: [{ para: 'identificada' }, { para: 'qualificado' }], segmento: 'A' }];
  const m = L.computeMetrics(leads, { minSample: 20 });
  assert.equal(m.total, 1);
  assert.equal(m.conversoes[0].taxa, null);
  assert.match(m.conversoes[0].nota, /insuficiente/);
  const many = Array.from({ length: 20 }, (_, i) => ({ status: i < 10 ? 'pesquisada' : 'identificada', historico: [] }));
  const m2 = L.computeMetrics(many, { minSample: 20 });
  assert.equal(m2.conversoes[0].taxa, 50);
});

test('exemplo CSV importa sem duplicar (fluxo de importação)', () => {
  const rows = L.parseCsv(require('fs').readFileSync(__dirname + '/../data/exemplo_leads.csv', 'utf8'));
  const base = [];
  for (const r of rows) {
    const d = L.findDuplicate(r, base);
    if (d && d.strong) base[base.indexOf(d.lead)] = L.mergeLead(d.lead, r);
    else base.push({ id: 'L' + (base.length + 1), ...r });
  }
  assert.equal(rows.length, 3);
  assert.equal(base.length, 2);
});
