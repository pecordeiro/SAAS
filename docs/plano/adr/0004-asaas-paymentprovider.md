# ADR-0004 — Asaas atrás de uma interface PaymentProvider

- Status: proposto · Data: 2026-10-13

## Contexto
Clientes brasileiros pagam por Pix, boleto e cartão. O Asaas cobre os três com assinatura
recorrente e checkout hospedado. Não queremos acoplar regras de cobrança a um fornecedor.

## Decisão
Interface `PaymentProvider` com `create_customer`, `create_subscription`, `change_plan`,
`cancel`, `get_subscription`, `list_payments`. Implementações: `AsaasProvider` (produção e
sandbox, base URL por env) e `FakeProvider` (testes, determinística). O estado de assinatura
é nosso (`subscriptions.status`); o Asaas é fonte de verdade de pagamentos e é consultado
em dúvida e na reconciliação diária.

## Consequências
- (+) Testes sem rede; troca de provedor sem mexer em telas e regras.
- (+) Nenhum dado de cartão no nosso servidor (escopo PCI mínimo).
- (−) Uma camada a mais e mapeamento de status.

## Alternativas
Stripe (Pix limitado no Brasil, boleto via parceiros); Mercado Pago, Pagar.me, Iugu
(válidos; ficam como plano B pela mesma interface).
