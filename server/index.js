const http = require('http'), crypto = require('crypto');
const dbm = require('./db'), P = require('./pipeline'), V = require('./views'), { fromEnv } = require('./ai');
const { L } = P;

function createApp({ db, ai, fetchSite, appToken = '' }) {
  const csrf = crypto.randomBytes(16).toString('hex');
  const ctx = (flash) => ({ csrf, simulated: ai.simulated, flash });
  const defaultFetch = async url => { const r = await fetch(url, { signal: AbortSignal.timeout(15000), headers: { 'user-agent': 'MontcoProspeccao/0.1 (consulta pontual ao site oficial)' } }); if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); };
  fetchSite = fetchSite || defaultFetch;

  const readBody = req => new Promise((res, rej) => { let d = ''; req.on('data', c => { d += c; if (d.length > 5e6) { rej(new Error('Corpo grande demais')); req.destroy(); } }); req.on('end', () => res(d)); });
  const send = (res, code, body, type = 'text/html; charset=utf-8', extra = {}) => { res.writeHead(code, { 'content-type': type, 'x-content-type-options': 'nosniff', 'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'self'; base-uri 'none'", 'referrer-policy': 'no-referrer', ...extra }); res.end(body); };
  const back = (res, path, flash) => send(res, 303, '', 'text/plain', { location: path + (flash ? (path.includes('?') ? '&' : '?') + 'm=' + encodeURIComponent((flash.err ? '!' : '') + flash.msg) : '') });

  return async (req, res) => {
    try {
      const url = new URL(req.url, 'http://x'), host = (req.headers.host || '').split(':')[0];
      if (!['localhost', '127.0.0.1', '[::1]'].includes(host) && !process.env.ALLOW_REMOTE_HOST) return send(res, 403, 'Host não permitido', 'text/plain');
      if (appToken) {
        const cookie = /(?:^|; )montco=([^;]*)/.exec(req.headers.cookie || '');
        if (url.searchParams.get('token') === appToken) return send(res, 303, '', 'text/plain', { location: url.pathname, 'set-cookie': `montco=${appToken}; HttpOnly; SameSite=Strict; Path=/` });
        if (!cookie || cookie[1] !== appToken) return send(res, 401, 'Acesse com ?token=APP_TOKEN', 'text/plain');
      }
      const m = url.searchParams.get('m'); const flash = m ? { err: m[0] === '!', msg: m.replace(/^!/, '') } : null;
      const c = ctx(flash), path = url.pathname;
      if (req.method === 'GET') {
        if (path === '/health') return send(res, 200, JSON.stringify({ ok: true, ia: ai.simulated ? 'simulada' : 'anthropic' }), 'application/json');
        if (path === '/') return send(res, 200, V.leadsPage(db, c));
        if (path.startsWith('/lead/')) { const h = V.leadPage(db, decodeURIComponent(path.slice(6)), c); return h ? send(res, 200, h) : send(res, 404, 'Lead não encontrado', 'text/plain'); }
        if (path === '/queue') return send(res, 200, V.queuePage(db, c));
        if (path === '/dashboard') return send(res, 200, V.dashboardPage(P.metrics(db), c));
        if (path === '/config') return send(res, 200, V.configPage(db, c));
        if (path === '/export' && !url.searchParams.get('table')) return send(res, 200, V.exportPage(c));
        if (path === '/export') {
          const t = url.searchParams.get('table'); if (!['leads', 'fontes', 'fila', 'historico', 'supressao'].includes(t)) return send(res, 400, 'Tabela inválida', 'text/plain');
          const rows = db.all(t).map(r => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, typeof v === 'object' && v !== null ? JSON.stringify(v) : v])));
          return url.searchParams.get('format') === 'json' ? send(res, 200, JSON.stringify(db.all(t), null, 2), 'application/json', { 'content-disposition': `attachment; filename=${t}.json` })
            : send(res, 200, L.toCsv(rows), 'text/csv; charset=utf-8', { 'content-disposition': `attachment; filename=${t}.csv` });
        }
        return send(res, 404, 'Não encontrado', 'text/plain');
      }
      if (req.method === 'POST') {
        const b = Object.fromEntries(new URLSearchParams(await readBody(req)));
        if (b._csrf !== csrf) return send(res, 403, 'Token CSRF inválido: recarregue a página', 'text/plain');
        try {
          if (path === '/import') { const r = P.importCsv(db, b.csv || ''); return back(res, '/', { msg: `Importado: ${r.novos} novos, ${r.mesclados} mesclados, ${r.possiveis_duplicados} possíveis duplicados, ${r.cnpj_invalido} CNPJ inválidos descartados` }); }
          if (/^\/lead\/[^/]+\/qualify$/.test(path)) { const id = decodeURIComponent(path.split('/')[2]); await P.qualify(db, ai, id, fetchSite); return back(res, '/queue', { msg: 'Qualificado. Revise os rascunhos.' }); }
          if (path === '/action') { const l = P.act(db, b); return back(res, ['approve', 'edit', 'reject'].includes(b.action) ? '/queue' : '/lead/' + encodeURIComponent(l.id), { msg: 'Ação registrada: ' + b.action }); }
          if (path === '/config') { for (const [k, v] of Object.entries(b)) if (k !== '_csrf') db.setConfig(k, v.trim()); return back(res, '/config', { msg: 'Configuração salva' }); }
        } catch (e) { return back(res, req.headers.referer ? new URL(req.headers.referer).pathname : '/', { err: true, msg: e.message }); }
      }
      send(res, 404, 'Não encontrado', 'text/plain');
    } catch (e) { console.error('[erro]', e.message); send(res, 500, 'Erro interno', 'text/plain'); }
  };
}

if (require.main === module) {
  process.removeAllListeners('warning');
  const port = Number(process.env.PORT) || 3000;
  const db = dbm.open(process.env.DB_PATH || 'data/montco.sqlite');
  const ai = fromEnv();
  http.createServer(createApp({ db, ai, appToken: process.env.APP_TOKEN || '' })).listen(port, '127.0.0.1', () => {
    console.log(`Montco rodando em http://localhost:${port}  (IA: ${ai.simulated ? 'SIMULADA' : process.env.ANTHROPIC_API_KEY ? 'Anthropic' : 'Anthropic SEM CHAVE — configure ANTHROPIC_API_KEY'})`);
  });
}
module.exports = { createApp };
