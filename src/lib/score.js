const FACTORS = {
  A: 'Compatibilidade com fabricação/montagem',
  B: 'Complexidade aparente dos equipamentos',
  C: 'Indícios de produção sob encomenda',
  D: 'Número de etapas/tipos de produto',
  E: 'Porte e público-alvo',
  F: 'Canal comercial apropriado',
  G: 'Operação produtiva própria',
};
const DEFAULT_WEIGHTS = { A: 25, B: 15, C: 20, D: 10, E: 10, F: 10, G: 10 };

// factors: { A: { value: 0..1 | null, level: 'fato'|'inferencia'|'hipotese', evidence: [urls] } }
// Fator desconhecido (value null) NÃO penaliza: entra com valor neutro e fica listado em "unknown".
function computeScore(factors, weights = DEFAULT_WEIGHTS, neutral = 0.5) {
  const total = Object.values(weights).reduce((a, b) => a + b, 0) || 1;
  let sum = 0;
  const breakdown = {}, unknown = [];
  for (const k of Object.keys(weights)) {
    const f = factors[k] || {};
    const known = typeof f.value === 'number' && !isNaN(f.value);
    const v = known ? Math.min(1, Math.max(0, f.value)) : neutral;
    if (!known) unknown.push(k);
    const pts = (v * weights[k] * 100) / total;
    breakdown[k] = { points: Math.round(pts * 10) / 10, weight: weights[k], known, level: f.level || (known ? 'inferencia' : 'desconhecido'), evidence: f.evidence || [] };
    sum += pts;
  }
  const knownWeight = Object.keys(weights).filter(k => !unknown.includes(k)).reduce((a, k) => a + weights[k], 0);
  return { score: Math.round(sum), breakdown, unknown, confidence: Math.round((knownWeight / total) * 100) / 100 };
}
