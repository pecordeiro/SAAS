const DEFAULT_RULES = {
  maxWords: 180,
  // Afirmações de dor que exigem evidência; o rascunho não pode afirmá-las.
  bannedClaims: [/vocês? (usa|usam|trabalha|trabalham) com planilhas?/i, /sofre[mr]?\b/i, /atrasos? (constantes|frequentes)/i, /desperd[ií]cio/i, /falta de estoque/i, /garantimos?/i, /aumente .* em \d+%/i, /resultados? garantidos?/i],
  placeholders: /\[[^\]]+\]|\{\{[^}]+\}\}/,
};

// cfg: { allowedLinks:[urls configuradas], nonExistingFeatures:[termos], suppression:[...] }
function validateDraft(draft, lead, cfg = {}) {
  const errors = [], warnings = [];
  const body = String(draft.corpo || ''), subject = String(draft.assunto || '');
  const rules = { ...DEFAULT_RULES, ...(cfg.rules || {}) };
  if (!subject.trim()) errors.push('Assunto vazio');
  if (!body.trim()) errors.push('Corpo vazio');
  if (rules.placeholders.test(subject + body)) errors.push('Placeholders não preenchidos');
  if (body.split(/\s+/).filter(Boolean).length > rules.maxWords) warnings.push('Mensagem longa');
  for (const re of rules.bannedClaims) if (re.test(body)) errors.push('Afirmação sem evidência: ' + re);
  for (const t of cfg.nonExistingFeatures || []) if (t && body.toLowerCase().includes(t.toLowerCase())) errors.push('Menciona funcionalidade inexistente: ' + t);
  const allowed = new Set((cfg.allowedLinks || []).map(u => u.replace(/\/$/, '')));
  for (const u of body.match(/https?:\/\/[^\s)>"]+/g) || []) {
    if (!allowed.has(u.replace(/[.,;]$/, '').replace(/\/$/, ''))) errors.push('Link não configurado: ' + u);
  }
  if (!lead.fontes || !lead.fontes.length) errors.push('Lead sem fonte registrada');
  if (lead.email && !lead.email_fonte) errors.push('E-mail sem URL de origem');
  if (lead.nao_contatar || isSuppressed(lead, cfg.suppression)) errors.push('Lead em lista de supressão');
  return { ok: errors.length === 0, errors, warnings };
}
