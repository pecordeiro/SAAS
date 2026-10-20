// Armazenamento SQLite (node:sqlite, embutido no Node 22). Cada tabela guarda um documento JSON por chave.
const { DatabaseSync } = require('node:sqlite');
const TABLES = ['leads', 'fontes', 'fila', 'historico', 'supressao', 'config'];
let seq = 0;

function open(file = ':memory:') {
  const db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode=WAL');
  for (const t of TABLES) db.exec(`CREATE TABLE IF NOT EXISTS ${t} (k TEXT PRIMARY KEY, v TEXT NOT NULL, n INTEGER)`);
  const api = {
    raw: db,
    all: t => db.prepare(`SELECT v FROM ${chk(t)} ORDER BY n`).all().map(r => JSON.parse(r.v)),
    get: (t, k) => { const r = db.prepare(`SELECT v FROM ${chk(t)} WHERE k=?`).get(String(k)); return r ? JSON.parse(r.v) : null; },
    put: (t, k, o) => { db.prepare(`INSERT INTO ${chk(t)}(k,v,n) VALUES(?,?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v`).run(String(k), JSON.stringify(o), Date.now() * 1000 + (seq++ % 1000)); return o; },
    add: (t, o) => api.put(t, Date.now() + '-' + (seq++) + '-' + Math.random().toString(36).slice(2, 7), o),
    del: (t, k) => db.prepare(`DELETE FROM ${chk(t)} WHERE k=?`).run(String(k)),
    tx: fn => { db.exec('BEGIN'); try { const r = fn(); db.exec('COMMIT'); return r; } catch (e) { db.exec('ROLLBACK'); throw e; } },
    config: () => Object.fromEntries(api.all('config').map(c => [c.chave, c.valor])),
    setConfig: (chave, valor) => api.put('config', chave, { chave, valor: String(valor == null ? '' : valor) }),
  };
  return api;
}
function chk(t) { if (!TABLES.includes(t)) throw new Error('Tabela inválida'); return t; }
module.exports = { open };
