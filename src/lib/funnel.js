const DEFAULT_STAGES = [
  'identificada', 'pesquisada', 'qualificado', 'aguardando_aprovacao', 'aprovada', 'contato_realizado',
  'resposta_recebida', 'reuniao_agendada', 'diagnostico_realizado', 'demonstracao_apresentada',
  'proposta_enviada', 'negociacao', 'cliente', 'perdido',
];
const PROMO_STAGES = ['aguardando_aprovacao', 'aprovada'];

// Transição: registra data/ator e aplica regras de interrupção.
function transition(lead, to, opts = {}) {
  const stages = opts.stages || DEFAULT_STAGES;
  if (!stages.includes(to)) throw new Error('Etapa inválida: ' + to);
  if (lead.nao_contatar && PROMO_STAGES.concat('contato_realizado').includes(to)) {
    throw new Error('Lead marcado como não contatar: ação promocional bloqueada');
  }
  const at = opts.at || new Date().toISOString();
  const entry = { de: lead.status, para: to, em: at, por: opts.by || 'usuario', motivo: opts.reason || '' };
  const next = { ...lead, status: to, atualizado_em: at, historico: [...(lead.historico || []), entry] };
  if (to === 'perdido' && !opts.reason) throw new Error('Informe o motivo da perda');
  if (to === 'resposta_recebida' || to === 'perdido') next.proxima_acao = next.proxima_acao || '';
  return next;
}

function markDoNotContact(lead, opts = {}) {
  const at = opts.at || new Date().toISOString();
  return {
    ...lead, nao_contatar: true, proxima_acao: '', atualizado_em: at,
    historico: [...(lead.historico || []), { de: lead.status, para: lead.status, em: at, por: opts.by || 'usuario', motivo: 'nao_contatar: ' + (opts.reason || '') }],
  };
}

function suggestNextAction(lead) {
  if (lead.nao_contatar) return 'Nenhuma (não contatar)';
  const m = {
    identificada: 'Pesquisar a empresa em fontes oficiais',
    pesquisada: 'Qualificar e revisar a pontuação',
    qualificado: 'Gerar rascunho de abordagem',
    aguardando_aprovacao: 'Revisar, editar e aprovar o rascunho',
    aprovada: 'Enviar manualmente e marcar como enviado',
    contato_realizado: 'Aguardar resposta; revisar manualmente após alguns dias úteis',
    resposta_recebida: 'Responder e propor 20 min de conversa',
    reuniao_agendada: 'Preparar roteiro de diagnóstico',
    diagnostico_realizado: 'Avaliar demonstração',
    demonstracao_apresentada: 'Avaliar proposta',
    proposta_enviada: 'Fazer acompanhamento manual',
    negociacao: 'Definir próximos passos com o decisor',
  };
  return m[lead.status] || '';
}
