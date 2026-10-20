const fs = require('fs'), path = require('path');
const prompt = n => fs.readFileSync(path.join(__dirname, '..', 'src', 'prompts', n + '.md'), 'utf8');

function parseJson(txt) {
  const a = txt.indexOf('{'), b = txt.lastIndexOf('}');
  if (a < 0 || b < a) throw new Error('Resposta da IA sem JSON');
  try { return JSON.parse(txt.slice(a, b + 1)); } catch (e) { throw new Error('Resposta da IA não é JSON válido'); }
}

function anthropic({ apiKey, model, fetchImpl = fetch }) {
  const call = async (system, user, maxTokens) => {
    if (!apiKey) throw new Error('ANTHROPIC_API_KEY não configurada: a qualificação por IA não pode rodar (use AI_MODE=mock apenas para testar a interface)');
    if (!model) throw new Error('ANTHROPIC_MODEL não configurado');
    let lastErr;
    for (let i = 0; i < 2; i++) {
      try {
        const r = await fetchImpl('https://api.anthropic.com/v1/messages', {
          method: 'POST', signal: AbortSignal.timeout(60000),
          headers: { 'content-type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
          body: JSON.stringify({ model, max_tokens: maxTokens, system, messages: [{ role: 'user', content: user }] }),
        });
        if (!r.ok) throw new Error('Anthropic API HTTP ' + r.status);
        const j = await r.json();
        return parseJson(((j.content || [])[0] || {}).text || '');
      } catch (e) { lastErr = e; if (/HTTP 4(0[0-3]|04)/.test(e.message)) break; }
    }
    throw lastErr;
  };
  return {
    simulated: false,
    qualify: input => call(prompt('qualificacao'), input.material, 2000),
    draft: input => call(prompt('email'), JSON.stringify(input.payload), 1500),
  };
}

// Provedor SIMULADO: heurística por palavras-chave sobre o texto fornecido. Serve para testar o fluxo, não para vender.
function mock() {
  const KEY = {
    A: /fabric|monta(gem|mos)|produz/i, B: /automa[cç]|rob[oô]|mecatr|painéis?|paineis?|m[aá]quina|equipamento/i,
    C: /encomenda|sob medida|sob projeto|personaliz/i, D: /etapas|linhas? de|diversos|vari(ad|ed)/i,
    G: /f[aá]brica|parque fabril|produ[cç][aã]o pr[oó]pria|nossa planta/i,
  };
  return {
    simulated: true,
    async qualify({ sources }) {
      const factors = {}, fatos = [];
      for (const k of Object.keys(KEY)) {
        for (const s of sources) {
          const sent = (s.text || '').split(/(?<=[.!?\n])\s+/).find(x => KEY[k].test(x));
          if (sent) { factors[k] = { value: 0.8, level: 'fato', evidence: [s.url], note: '' }; fatos.push({ texto: sent.trim().slice(0, 200), url: s.url }); break; }
        }
        if (!factors[k]) factors[k] = { value: null, level: 'hipotese', evidence: [], note: '' };
      }
      factors.E = { value: null, level: 'hipotese', evidence: [], note: '' };
      factors.F = { value: null, level: 'hipotese', evidence: [], note: '' };
      const uniq = []; for (const f of fatos) if (!uniq.some(u => u.texto === f.texto)) uniq.push(f);
      return { factors, segmento: factors.B.value ? 'Máquinas e equipamentos' : '', produtos: [], fatos: uniq, inferencias: [], hipoteses: ['Como a empresa acompanha etapas e previsões de entrega hoje (confirmar em conversa)'],
        desconhecido: ['porte da empresa', 'canal comercial'], gancho: uniq[0] ? uniq[0].texto : '', hipotese_problema: '' };
    },
    async draft({ payload }) {
      const { empresa, fatos, funcionalidades_existentes: fe, remetente } = payload;
      const sig = `Obrigado,\n${remetente.nome || ''}\n${remetente.contato || ''}`.trim();
      const mk = (fato) => ({ assunto: `Acompanhamento dos prazos de montagem na ${empresa}`,
        corpo: `Olá, tudo bem?\n\nEncontrei a ${empresa}${fato ? ' e vi que ' + fato.texto.replace(/[.]+$/, '').replace(/^./, c => c.toLowerCase()) : ''}.\n\nEstou desenvolvendo a Montco, uma solução que oferece: ${fe.join(', ')}.\n\nEstou conversando com empresas do setor para entender como organizam esse acompanhamento hoje. Você teria 20 minutos para conversarmos sobre como isso funciona aí na ${empresa}?\n\n${sig}` });
      return { versoes: fatos.length >= 2 ? [mk(fatos[0]), mk(fatos[1])] : [mk(fatos[0])] };
    },
  };
}

function fromEnv(env = process.env) {
  const mode = env.AI_MODE || 'anthropic';
  if (mode === 'mock') return mock();
  return anthropic({ apiKey: env.ANTHROPIC_API_KEY, model: env.ANTHROPIC_MODEL });
}
module.exports = { anthropic, mock, fromEnv, parseJson };
