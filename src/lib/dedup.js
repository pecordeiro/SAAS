function normalizeDomain(url) {
  if (!url) return '';
  let h = String(url).trim().toLowerCase();
  h = h.replace(/^[a-z]+:\/\//, '').replace(/^www\./, '').split(/[\/?#]/)[0].split(':')[0];
  return /^[a-z0-9.-]+\.[a-z]{2,}$/.test(h) ? h : '';
}

function normalizeCnpj(v) {
  const d = String(v || '').replace(/\D/g, '');
  return d.length === 14 ? d : '';
}

function validCnpj(v) {
  const d = normalizeCnpj(v);
  if (!d || /^(\d)\1+$/.test(d)) return false;
  const calc = len => {
    let sum = 0, pos = len - 7;
    for (let i = len; i >= 1; i--) { sum += d[len - i] * pos--; if (pos < 2) pos = 9; }
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return calc(12) === +d[12] && calc(13) === +d[13];
}

function normalizeName(n) {
  return String(n || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/\b(ltda|me|epp|eireli|s\/?a|sa|industria|comercio|e)\b/g, ' ')
    .replace(/[^a-z0-9]+/g, ' ').trim();
}

// Chaves fortes: CNPJ e domínio. Chave fraca (nome+UF) só sinaliza "possível duplicado".
function keysFor(lead) {
  return {
    cnpj: validCnpj(lead.cnpj) ? normalizeCnpj(lead.cnpj) : '',
    domain: normalizeDomain(lead.site),
    weak: normalizeName(lead.nome) && lead.uf ? normalizeName(lead.nome) + '|' + String(lead.uf).toUpperCase() : '',
  };
}

function findDuplicate(candidate, existing) {
  const k = keysFor(candidate);
  for (const e of existing) {
    const ek = keysFor(e);
    if (k.cnpj && k.cnpj === ek.cnpj) return { lead: e, match: 'cnpj', strong: true };
    if (k.domain && k.domain === ek.domain) return { lead: e, match: 'dominio', strong: true };
  }
  for (const e of existing) {
    const ek = keysFor(e);
    if (k.weak && k.weak === ek.weak) return { lead: e, match: 'nome_uf', strong: false };
  }
  return null;
}

// Preenche apenas campos vazios; nunca sobrescreve dado existente.
function mergeLead(existing, incoming) {
  const out = { ...existing };
  for (const [k, v] of Object.entries(incoming)) if (!out[k] && v) out[k] = v;
  return out;
}
