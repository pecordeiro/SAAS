// CSV mínimo (RFC 4180): aspas, vírgulas e quebras de linha dentro de campos.
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', inQ = false;
  const s = String(text || '').replace(/^﻿/, '');
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (inQ) {
      if (c === '"' && s[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') inQ = false;
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ',' || c === ';') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && s[i + 1] === '\n') i++;
      row.push(field); field = '';
      if (row.some(v => v !== '')) rows.push(row);
      row = [];
    } else field += c;
  }
  row.push(field);
  if (row.some(v => v !== '')) rows.push(row);
  if (!rows.length) return [];
  const head = rows[0].map(h => h.trim());
  return rows.slice(1).map(r => Object.fromEntries(head.map((h, i) => [h, (r[i] || '').trim()])));
}

function toCsv(records, columns) {
  const cols = columns || [...new Set(records.flatMap(r => Object.keys(r)))];
  const esc = v => {
    v = v == null ? '' : String(v);
    // evita injeção de fórmulas ao abrir no Excel/Sheets
    if (/^[=+\-@]/.test(v)) v = "'" + v;
    return /[",\n\r;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  };
  return [cols.join(','), ...records.map(r => cols.map(c => esc(r[c])).join(','))].join('\n');
}
