# ADR-0016 — Identidade verde-oliva nas páginas públicas

- Nota: a ADR-0018 levou esta identidade para a área logada (`/app`), login e e-mails.
- Status: **aceito**. Aprovado pelo dono em 2026-10-23 (referência visual HTML “v6 oliva”). Aplicado na R10.
  Não substitui a ADR-0015: a área logada (`/app`) mantém o visual da base “Controle de Atividades”.

## Contexto
A R10 pedia a página pública no visual novo. O dono aprovou uma referência com título em serifa
centralizado, painel dentro de moldura de aparelho sobre um bloco oliva, faixa rolante de produtos, três
passos, mapeamento de colunas, opcionais como chaves, quatro planos, perguntas frequentes e chamada final.

## Decisão
1. **Paleta de marca** (tokens `--color-brand-*` em `app/static/css/tokens.css`, cópia idêntica em
   `docs/design/tokens.css`): off-white `#FBFBF6`, superfície `#FFFFFF`, cinza-oliva `#F0F1E6`, tinta
   `#14170D`, texto secundário `#5E6354`, linha `#E1E3D3`, marca oliva escuro `#455A0F` (hover `#2E3D08`),
   bloco oliva `#8F9F78`, moldura `#101208`. Tema escuro equivalente (marca `#B7D064`, fundo `#0F120A`,
   bloco `#3E4A2C`). Contrastos em `docs/design/contraste.md`.
2. **Onde vale:** só o site público (início, preços, como funciona com a sua planilha, termos, privacidade,
   contato), o logotipo e os links da marca. Essas páginas declaram `marca` no template e o `body` ganha
   `site--marca`; `publico.css` redefine os tokens semânticos (`--color-bg`, `--color-primary`…) só dentro
   dessa classe, então botões, tabelas e cartões existentes assumem a paleta sem retrabalho. Login, cadastro
   e a área logada não passam por ali.
3. **A marca nunca colore dado.** Anel, esteira, pontos e etiquetas de situação usam só os tokens de status
   (verde concluída, azul em andamento, cinza, amarelo, vermelho). Um teste confere isso.
4. **Tipografia:** Newsreader (títulos, itálico no destaque) e DM Sans (texto), licença OFL, servidas pelo
   próprio site em `app/static/fonts/` (latin; Newsreader 400 normal e itálico, DM Sans 400 e 700), com as
   licenças ao lado. A IBM Plex Sans segue na área logada. O navegador só baixa a fonte que a página usa.
5. **Movimento:** palavras do título subindo, bloco oliva subindo, aparelho flutuando, contadores, reveal ao
   rolar (IntersectionObserver), faixa rolante, três passos que se alternam. Tudo em `static/js/publico.js` e
   `publico.css` (passam por `scripts/build_assets.py`), sem biblioteca. Sem o script ou com
   `prefers-reduced-motion`, a página aparece inteira e parada.
6. **Preços e limites** continuam vindo da tabela `plans`; o `trial_days` entra no card de plano como
   argumento explícito (corrige o “14” que sumia em “14 dias grátis, sem cartão”, porque o macro importado não
   enxergava o contexto da página).
7. **Nova página** `/como-funciona` (“Como funciona com a sua planilha”) no sitemap e no menu. Descreve só o
   que o sistema faz (R7/R8).
8. **SEO:** título e descrição por página, Open Graph, canonical, sitemap, robots e `theme-color` claro/escuro
   (`THEME_COLORS` em `public.py`, conferido por teste contra `tokens.css`). Logotipo, favicon, apple-touch e
   imagem de compartilhamento refeitos na paleta.

## Consequências
- `--font-size-brand-hero` chega a 112 px: é a exceção ao teto de 32 px da ADR-0015, restrita às páginas
  públicas.
- Pendências: (a) o “Entrar/Cadastro” segue no visual da área logada; (b) revisar a imagem de compartilhamento
  com o dono; (c) a faixa de produtos (“Robôs industriais…”) é texto de exemplo para validar com clientes reais.
