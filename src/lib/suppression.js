function norm(v) { return String(v || '').trim().toLowerCase(); }

function isSuppressed(lead, list) {
  const emails = new Set(), domains = new Set(), ids = new Set();
  for (const s of list || []) {
    if (s.email) emails.add(norm(s.email));
    if (s.dominio) domains.add(norm(s.dominio));
    if (s.lead_id) ids.add(s.lead_id);
  }
  const d = normalizeDomain(lead.site);
  const em = norm(lead.email);
  if (ids.has(lead.id)) return true;
  if (d && domains.has(d)) return true;
  if (em && (emails.has(em) || domains.has(em.split('@')[1]))) return true;
  return false;
}
