const { L, cfgOf, list } = require('./pipeline');
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const STAGE_LABEL = { identificada: 'Empresa identificada', pesquisada: 'Empresa pesquisada', qualificado: 'Lead qualificado', aguardando_aprovacao: 'Abordagem aguardando aprovação', aprovada: 'Abordagem aprovada', contato_realizado: 'Contato realizado', resposta_recebida: 'Resposta recebida', reuniao_agendada: 'Reunião agendada', diagnostico_realizado: 'Diagnóstico realizado', demonstracao_apresentada: 'Demonstração apresentada', proposta_enviada: 'Proposta enviada', negociacao: 'Negociação', cliente: 'Cliente conquistado', perdido: 'Perdido / sem interesse' };
const label = s => STAGE_LABEL[s] || s;

const CSS = `body{font-family:system-ui,sans-serif;max-width:1000px;margin:0 auto;padding:16px;color:#1d2433;background:#fff}
nav a{margin-right:14px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:6px;text-align:left;vertical-align:top}
.card{border:1px solid #ccd;border-radius:8px;padding:12px;margin:12px 0}.warn{background:#fff4d6;padding:8px;border-radius:6px}.err{background:#ffe0e0;padding:8px;border-radius:6px}
textarea,input[type=text],input:not([type]),select{width:100%;box-sizing:border-box;padding:6px;margin:2px 0}button{padding:6px 10px;margin:2px;cursor:pointer}small{color:#556}
@media(prefers-color-scheme:dark){body{background:#12151c;color:#e6e9f0}td,th,.card{border-color:#445}.warn{background:#4a3b10}.err{background:#4a1c1c}input,textarea,select{background:#1c212c;color:inherit}}`;

function page(title, body, ctx) {
  const banner = ctx.simulated ? '<p class="warn"><b>Modo simulado (AI_MODE=mock):</b> a qualificação e os e-mails são gerados por regras simples, não pela IA. Use só para testar o fluxo.</p>' : '';
  const flash = ctx.flash ? `<p class="${ctx.flash.err ? 'err' : 'warn'}">${esc(ctx.flash.msg)}</p>` : '';
  return `<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · Montco</title><style>${CSS}</style><body>
<h1>Montco · Prospecção</h1><nav><a href="/">Leads</a><a href="/queue">Fila de revisão</a><a href="/dashboard">Dashboard</a><a href="/config">Config</a><a href="/export">Exportar</a></nav>
<p><small>Nada é enviado por este sistema: você copia o texto aprovado e envia manualmente.</small></p>${banner}${flash}${body}</body></html>`;
}
const csrf = ctx => `<input type="hidden" name="_csrf" value="${esc(ctx.csrf)}">`;
const btn = (a, t, extra = '') => `<button name="action" value="${a}" ${extra}>${t}</button>`;

function leadsPage(db, ctx) {
  const leads = db.all('leads').sort((a, b) => (b.score || -1) - (a.score || -1));
  const rows = leads.map(l => `<tr><td><a href="/lead/${esc(l.id)}">${esc(l.nome)}</a>${l.nao_contatar ? ' 🚫' : ''}</td><td>${esc(l.cidade)}/${esc(l.uf)}</td><td>${esc(l.segmento)}</td><td>${l.score == null ? '—' : esc(l.score)}</td><td>${esc(label(l.status))}</td><td>${esc(l.proxima_acao)}</td></tr>`).join('');
  return page('Leads', `<div class="card"><h2>Importar CSV</h2><form method="POST" action="/import">${csrf(ctx)}
<p><small>Colunas: nome, cnpj, site, cidade, uf, segmento, produtos, fonte_url, fonte_trecho, fonte_aquisicao. Use fonte_trecho para colar o texto público que sustenta os fatos.</small></p>
<input type="file" accept=".csv,text/csv" onchange="const f=this.files[0];if(f){f.text().then(t=>document.getElementById('csv').value=t)}"><textarea id="csv" name="csv" rows="6" placeholder="nome,site,uf,..."></textarea><button>Importar</button></form></div>
<h2>Leads (${leads.length})</h2><table><tr><th>Empresa</th><th>Local</th><th>Segmento</th><th>Score</th><th>Etapa</th><th>Próxima ação</th></tr>${rows || '<tr><td colspan=6>Nenhum lead. Importe um CSV.</td></tr>'}</table>`, ctx);
}

function leadPage(db, id, ctx) {
  const l = db.get('leads', id); if (!l) return null;
  const fontes = db.all('fontes').filter(f => f.lead_id === id), hist = db.all('historico').filter(h => h.lead_id === id).reverse();
  const bd = l.breakdown ? Object.entries(l.breakdown).map(([k, v]) => `<tr><td>${k} ${esc(L.FACTORS[k])}</td><td>${v.points}/${v.weight}</td><td>${v.known ? esc(v.level) : 'desconhecido'}</td><td>${(v.evidence || []).map(u => `<a href="${esc(u)}" rel="noopener noreferrer">${esc(u)}</a>`).join('<br>')}</td></tr>`).join('') : '';
  const ul = a => '<ul>' + (a || []).map(x => `<li>${esc(x)}</li>`).join('') + '</ul>';
  return page(l.nome, `<h2>${esc(l.nome)} <small>${esc(label(l.status))}</small></h2>
<p>${esc(l.site)} · ${esc(l.cidade)}/${esc(l.uf)} · ${esc(l.segmento)} ${l.qualificacao_simulada ? '<b>(qualificação simulada)</b>' : ''}</p>
<form method="POST" action="/lead/${esc(id)}/qualify">${csrf(ctx)}<button>Pesquisar e qualificar${l.score != null ? ' novamente' : ''}</button></form>
${l.score != null ? `<div class="card"><h3>Score ${esc(l.score)}/100 <small>confiança nas informações: ${Math.round((l.confianca || 0) * 100)}%${l.score_manual ? ' · ajustado manualmente' : ''}</small></h3>
<table><tr><th>Fator</th><th>Pontos</th><th>Nível</th><th>Fontes</th></tr>${bd}</table>
<h4>Fatos verificados (com fonte)</h4><ul>${(l.fatos || []).map(f => `<li>${esc(f.texto)} — <a href="${esc(f.url)}" rel="noopener noreferrer">${esc(f.url)}</a></li>`).join('') || '<li>Nenhum</li>'}</ul>
<h4>Inferências razoáveis</h4>${ul(l.inferencias)}<h4>Hipóteses a confirmar em conversa</h4>${ul(l.hipoteses)}<h4>Informações ainda desconhecidas</h4>${ul(l.desconhecido)}
<form method="POST" action="/action">${csrf(ctx)}<input type="hidden" name="lead_id" value="${esc(id)}">Ajustar score: <input name="score" size=4 style="width:80px" value="${esc(l.score)}"> motivo: <input name="motivo">${btn('override', 'Salvar ajuste')}</form></div>` : ''}
<div class="card"><h3>Etapa e ações</h3><form method="POST" action="/action">${csrf(ctx)}<input type="hidden" name="lead_id" value="${esc(id)}">
Etapa: <select name="para">${L.DEFAULT_STAGES.map(s => `<option value="${s}" ${s === l.status ? 'selected' : ''}>${esc(label(s))}</option>`).join('')}</select> Motivo (obrigatório se perdido): <input name="motivo">
Próxima ação: <input name="proxima_acao" value="${esc(l.proxima_acao)}"> Data: <input name="proxima_acao_data" type="date" value="${esc(l.proxima_acao_data)}">
${btn('stage', 'Mudar etapa')}${btn('schedule', 'Agendar ação')}${btn('reply', 'Registrar resposta')}${btn('dnc', 'Não contatar', 'onclick="return confirm(\'Marcar como não contatar?\')"')}${btn('erase', 'Excluir dados pessoais', 'onclick="return confirm(\'Apagar contato/e-mail/telefone?\')"')}</form>
<p><small>Sugestão: ${esc(L.suggestNextAction(l))}</small></p></div>
<div class="card"><h3>Fontes (${fontes.length})</h3><ul>${fontes.map(f => `<li><a href="${esc(f.url)}" rel="noopener noreferrer">${esc(f.url)}</a> · ${esc(f.tipo)} · ${esc(f.data_pesquisa)}</li>`).join('')}</ul></div>
<div class="card"><h3>Contato publicado</h3><p>${esc(l.contato_nome)} ${esc(l.contato_cargo)} ${esc(l.email)} ${esc(l.telefone)} ${esc(l.pagina_contato)}</p></div>
<div class="card"><h3>Histórico</h3><table>${hist.map(h => `<tr><td>${esc(h.em)}</td><td>${esc(h.evento)}</td><td>${esc(h.de)} → ${esc(h.para)}</td><td>${esc(h.por)}</td><td>${esc(h.detalhes)}</td></tr>`).join('')}</table></div>`, ctx);
}

function queuePage(db, ctx) {
  const leads = Object.fromEntries(db.all('leads').map(l => [l.id, l]));
  const items = db.all('fila').filter(f => ['pendente', 'aprovado'].includes(f.estado));
  const cards = items.map(f => { const l = leads[f.lead_id] || {}; const mail = l.email ? `mailto:${encodeURIComponent(l.email).replace('%40', '@')}?subject=${encodeURIComponent(f.assunto)}&body=${encodeURIComponent(f.corpo)}` : '';
    return `<form class="card" method="POST" action="/action">${csrf(ctx)}<input type="hidden" name="draft_id" value="${esc(f.draft_id)}"><input type="hidden" name="lead_id" value="${esc(f.lead_id)}">
<h3><a href="/lead/${esc(l.id)}">${esc(l.nome)}</a> · score ${esc(l.score)} · ${esc(f.estado)} ${f.simulado ? '<small>(simulado)</small>' : ''}</h3>
<p><small>Validação: <b>${esc(f.validacao)}</b></small></p><input name="assunto" value="${esc(f.assunto)}"><textarea name="corpo" rows="10">${esc(f.corpo)}</textarea>
<p>Motivo/obs: <input name="motivo"> Próxima ação: <input name="proxima_acao"></p>
${btn('approve', 'Aprovar')}${btn('edit', 'Salvar edição')}${btn('reject', 'Rejeitar')}
${f.estado === 'aprovado' ? `<button type="button" onclick="navigator.clipboard.writeText(this.form.assunto.value+'\\n\\n'+this.form.corpo.value)">Copiar e-mail</button>${mail ? `<a href="${mail}">Abrir no meu e-mail</a>` : '<small>sem e-mail publicado cadastrado</small>'} ${btn('sent', 'Marquei como enviado')}` : ''}
${btn('dnc', 'Não contatar')}</form>`; }).join('');
  return page('Fila', `<h2>Fila de revisão (${items.length})</h2>${cards || '<p>Fila vazia. Qualifique um lead para gerar rascunhos.</p>'}`, ctx);
}

function dashboardPage(m, ctx) {
  const tbl = o => '<table>' + (Object.entries(o).map(([k, v]) => `<tr><td>${esc(label(k))}</td><td>${esc(v)}</td></tr>`).join('') || '<tr><td>—</td></tr>') + '</table>';
  const conv = m.conversoes.map(c => `<tr><td>${esc(label(c.de))} → ${esc(label(c.para))}</td><td>${c.atingiram}/${c.base}</td><td>${c.taxa == null ? '—' : c.taxa + '%'}</td><td>${esc(c.nota)}</td></tr>`).join('');
  return page('Dashboard', `<h2>Dashboard</h2><p>Total de empresas: <b>${m.total}</b>. Todos os números são <b>observados</b>; não há estimativas.</p>
<h3>Leads que atingiram cada etapa</h3>${tbl(m.porEtapa)}<h3>Conversão entre etapas</h3><table><tr><th>Passo</th><th>Casos</th><th>Taxa</th><th>Nota</th></tr>${conv}</table>
<h3>Segmentos</h3>${tbl(m.porSegmento)}<h3>Fontes de aquisição</h3>${tbl(m.porFonte)}<h3>Motivos de perda</h3>${tbl(m.motivosPerda)}
<h3>Próximas ações</h3><ul>${m.proximasAcoes.map(a => `<li>${esc(a.nome)}: ${esc(a.acao)} ${esc(a.data)}</li>`).join('') || '<li>Nenhuma</li>'}</ul>`, ctx);
}

function configPage(db, ctx) {
  const c = cfgOf(db);
  const keys = ['funcionalidades_existentes', 'funcionalidades_inexistentes', 'link_apresentacao', 'link_site', 'link_formulario', 'remetente_nome', 'remetente_contato', 'min_amostra_conversao', 'etapas', ...Object.keys(L.DEFAULT_WEIGHTS).map(k => 'peso_' + k)];
  const hints = { funcionalidades_existentes: 'O que a Montco realmente faz hoje, separado por ; (obrigatório para gerar e-mails)', funcionalidades_inexistentes: 'Termos proibidos nos e-mails, separados por ;', etapas: 'Etapas personalizadas separadas por vírgula (vazio = padrão)' };
  return page('Config', `<h2>Configuração</h2><form method="POST" action="/config">${csrf(ctx)}${keys.map(k => `<p><label><b>${k}</b><br><small>${esc(hints[k] || (k.startsWith('peso_') ? L.FACTORS[k.slice(5)] + ' (padrão ' + L.DEFAULT_WEIGHTS[k.slice(5)] + ')' : 'Vazio = não usado'))}</small><input name="${k}" value="${esc(c[k] || '')}"></label></p>`).join('')}<button>Salvar</button></form>`, ctx);
}

function exportPage(ctx) {
  return page('Exportar', `<h2>Exportar</h2><ul>${['leads', 'fontes', 'fila', 'historico', 'supressao'].map(t => `<li>${t}: <a href="/export?table=${t}&format=csv">CSV</a> · <a href="/export?table=${t}&format=json">JSON</a></li>`).join('')}</ul>`, ctx);
}
module.exports = { page, leadsPage, leadPage, queuePage, dashboardPage, configPage, exportPage, esc };
