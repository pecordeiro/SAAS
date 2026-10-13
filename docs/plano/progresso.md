# Progresso

Cada fase preenche um bloco abaixo ao terminar. A próxima só começa quando todos os
critérios de pronto da anterior estiverem marcados.

## Formato do bloco

```
### Fase N — Nome
- Status: não iniciada | em andamento | concluída
- Datas: início AAAA-MM-DD · fim AAAA-MM-DD
- Entregas: lista curta do que foi feito
- Critérios de pronto: [x] / [ ] um por linha, copiados do roadmap
- Testes: resultado de `python -m pytest -q` (n passaram, n falharam, cobertura se aplicável)
- /security-review: sem achados | achados abertos (listar)
- Telas conferidas (375/768/1280, claro/escuro): sim | não | n/a
- Commit: hash e mensagem
- ADRs criados: lista
- Pendências e dívidas: lista
```

## Fases

(vazio — nenhuma fase iniciada)
