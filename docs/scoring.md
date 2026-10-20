# Pontuação (0–100)
Fatores e pesos padrão (editáveis em `Config.peso_A..G`): A fabricação/montagem 25 · B complexidade 15 · C sob encomenda 20 · D etapas/tipos 10 · E porte/público 10 · F canal comercial 10 · G operação própria 10.
- Cada fator vem da IA com `value` 0–1 **ou null**, `level` (fato / inferência / hipótese) e URLs de evidência. Sem URL, o fator vira desconhecido.
- Desconhecido recebe valor neutro (0,5) e é listado em `desconhecido`; falta de informação não derruba o score. A resposta informa a confiança (peso dos fatores conhecidos).
- `justificativa` separa **Fatos**, **Inferências** e **Hipóteses a confirmar**. Dores (atrasos, planilhas, desperdício) só entram como hipótese.
- Ajuste manual: edite `score`/`status` na planilha; mudanças pela UI ficam em `Historico`.
