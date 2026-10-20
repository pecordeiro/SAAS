// Conversão só é exibida quando o denominador atinge minSample; senão, "amostra insuficiente".
function computeMetrics(leads, opts = {}) {
  const stages = opts.stages || DEFAULT_STAGES;
  const minSample = opts.minSample || 20;
  const reached = Object.fromEntries(stages.map(s => [s, 0]));
  const idx = s => stages.indexOf(s);
  for (const l of leads) {
    const visited = new Set((l.historico || []).map(h => h.para).concat(l.status));
    // etapa atingida = visitada ou posterior à maior visitada (exceto "perdido")
    const max = Math.max(-1, ...[...visited].filter(s => s !== 'perdido').map(idx));
    stages.forEach((s, i) => { if (s !== 'perdido' && (i <= max || visited.has(s))) reached[s]++; });
    if (visited.has('perdido')) reached['perdido']++;
  }
  const conversions = [];
  const chain = stages.filter(s => s !== 'perdido');
  for (let i = 1; i < chain.length; i++) {
    const from = reached[chain[i - 1]], to = reached[chain[i]];
    conversions.push({ de: chain[i - 1], para: chain[i], base: from, atingiram: to,
      taxa: from >= minSample ? Math.round((to / from) * 1000) / 10 : null,
      nota: from >= minSample ? 'observado' : 'amostra insuficiente (<' + minSample + ')' });
  }
  const count = (key, f = x => x) => {
    const o = {};
    for (const l of leads) { const v = f(l[key]) || 'não informado'; o[v] = (o[v] || 0) + 1; }
    return o;
  };
  const lost = {};
  for (const l of leads) if (l.status === 'perdido') { const m = l.motivo_perda || 'não informado'; lost[m] = (lost[m] || 0) + 1; }
  return {
    total: leads.length, porEtapa: reached, conversoes: conversions,
    porSegmento: count('segmento'), porFonte: count('fonte_aquisicao'), motivosPerda: lost,
    proximasAcoes: leads.filter(l => l.proxima_acao && !l.nao_contatar).map(l => ({ id: l.id, nome: l.nome, acao: l.proxima_acao, data: l.proxima_acao_data || '' })),
    tipo: 'observado',
  };
}
