# Auditoria de design e UX — 2026-10-27

Escopo: site público e área logada, a 1280 e 375 px (e claro/escuro nas telas tocadas), com Playwright
sobre a base de demonstração (`flask seed-demo`) e uma base de vitrine à parte, só para as capturas da página
inicial. Ferramentas: plugin Frontend Design (carregado), diretrizes do Impeccable lidas do repositório oficial
(o instalador e o motor dele dependem de impeccable.style, que a rede deste ambiente bloqueia) e Playwright.

## Inventário

Públicas: início, como funciona, preços, contato, termos, privacidade, entrar, cadastro, esqueci a senha.
Área logada: painel da operação, painel do projeto, projeto (detalhe), preencher etapas, meta e equipe,
como funciona, projetos, novo projeto, histórico (geral e do projeto), editar projeto, modelos, usuários,
empresa, módulos, assinatura e planos, importar planilha, perfil, privacidade. Alertas, unidades, pessoas e
identidade visual responderam 404 na demo por serem módulos ou recursos de plano desligados (esperado).

## Achados e situação

| Prioridade | Achado | Situação |
|---|---|---|
| P0 | Painel da operação: eixo de "Horas por projeto" mostrava "undefined" (regressão da troca para colunas) | Corrigido em `painel.js` |
| P0 | Sobreposição na lista de etapas de "Preencher etapas" (título e barras por cima do painel) | Corrigido (commit d776f01) |
| P1 | Página inicial e "Como funciona" com maquetes geométricas (aparelho desenhado com esteira, barras, teclas, interruptores) | Trocadas por capturas reais do produto com dados de exemplo, claro e escuro no herói |
| P1 | Interruptores de enfeite nos opcionais da página inicial (pareciam controles e não faziam nada) | Trocados por ícones do recurso |
| P1 | Abas de projeto usavam os caracteres ✎ e ✕ como ícones; o formulário "Novo projeto" vazava a 375 px | Barra segmentada com ícones do sprite; formulário quebra para a linha inteira |
| P1 | Campos com o mesmo id em dois formulários da mesma página (perfil: "Senha atual"; empresa: "Nome"), deixando um deles sem rótulo | Macro `field` aceita `id`; ids únicos |
| P1 | Esteira de etapas assumia processo linear | Removida dos dois painéis (pedido do dono) |
| P2 | Ícones com traços de 1,5 a 3 px, desenhados à mão | Sprite refeito com Lucide 0.460.0 (2 px em todos), mesmos nomes |
| P2 | Faixas coloridas à esquerda em alertas e nas caixas de progresso | Borda inteira fina; a cor da série virou marca de legenda no rótulo |
| P2 | Unidades soltas na quebra de linha ("86,7 / h") nos indicadores | Espaço inseparável entre número e unidade |
| P2 | Seleção de texto, cursor e caixas de marcar com as cores do navegador | Seguem o oliva da marca |
| P2 | Usuários: seletor de papel ocupava a largura toda e empilhava as ações | Seletor do tamanho do conteúdo, na mesma linha do botão |
| P3 | Rótulos em caixa-alta acima das seções da página inicial | Mantidos: o dono pediu para manter a estrutura |
| P3 | Rodapé e títulos ainda dizem "Controle de Produção" | Pendente: decisão do nome em texto (ADR-0020, item 5) |
| P3 | "Etapa atrasada" ainda usa a ordem das etapas como faixas do prazo | Pendente: critério novo depende do dono |

## Direção visual

Mantida a identidade oliva (ADR-0018) com o logotipo Teroz (ADR-0020): fundo papel, tinta quase preta, oliva
só em marca, links, foco e ação; dados sempre nas cores de situação e de série. Telas de operação continuam
tipográficas e densas; a página inicial mostra o produto real em vez de desenhos.
