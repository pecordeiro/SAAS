const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', 'workflows');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

test('existem workflows exportados', () => assert.ok(files.length >= 4));

for (const f of files) {
  const wf = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  test(f + ': conexões válidas, nomes únicos', () => {
    const names = wf.nodes.map(n => n.name);
    assert.equal(new Set(names).size, names.length);
    for (const [from, c] of Object.entries(wf.connections)) {
      assert.ok(names.includes(from), 'origem ' + from);
      for (const t of c.main[0]) assert.ok(names.includes(t.node), 'destino ' + t.node);
    }
  });
  test(f + ': Code nodes têm sintaxe válida', () => {
    for (const n of wf.nodes.filter(n => n.type === 'n8n-nodes-base.code')) {
      assert.doesNotThrow(() => new AsyncFunction('$', '$input', '$env', n.parameters.jsCode), n.name);
    }
  });
  test(f + ': nenhum nó de envio de e-mail e nenhum segredo embutido', () => {
    const raw = JSON.stringify(wf);
    for (const n of wf.nodes) assert.ok(!/emailSend|gmail|smtp|sendgrid|mailgun|outlook/i.test(n.type), n.type);
    assert.ok(!/sk-ant-|AIza|Bearer [A-Za-z0-9]/.test(raw));
    for (const n of wf.nodes) if (n.credentials) for (const c of Object.values(n.credentials)) assert.equal(c.id, '');
  });
  test(f + ': webhooks exigem token no código', () => {
    const hooks = wf.nodes.filter(n => n.type === 'n8n-nodes-base.webhook');
    const codes = wf.nodes.filter(n => n.type === 'n8n-nodes-base.code').map(n => n.parameters.jsCode.split('\n').slice(-40).join('\n') + n.parameters.jsCode);
    assert.ok(hooks.length > 0);
    assert.ok(codes.some(c => /requireToken\(/.test(c.replace(/function requireToken[\s\S]*?\n}\n/, ''))));
  });
}

test('workflows commitados estão atualizados em relação ao gerador', () => {
  const { workflows } = require('../scripts/build-workflows');
  for (const [k, v] of Object.entries(workflows)) {
    assert.deepEqual(JSON.parse(fs.readFileSync(path.join(dir, k + '.json'), 'utf8')), v, k + ' desatualizado: rode npm run build');
  }
});
