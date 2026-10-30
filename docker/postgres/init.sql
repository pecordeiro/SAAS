-- Roda uma vez, na criação do volume. Banco separado para os testes (o nome precisa
-- conter "test": a suíte recria o schema public dele a cada execução).
CREATE DATABASE controle_test OWNER controle;
