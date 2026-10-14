"""Assinaturas e pagamento (Fase 8, ADR-0004).

- ``provider``: interface ``PaymentProvider`` e tipos.
- ``asaas`` / ``fake``: implementações (Asaas real, sandbox ou produção; fake em memória).
- ``service``: regras (teste grátis, assinar, trocar plano, cancelar, webhook, carência,
  reconciliação, ações do admin da plataforma). Telas e CLI só chamam o serviço.
- ``documents``: CPF/CNPJ.  ``notify``: aviso de atraso por e-mail.
"""

from app.services.billing.provider import PaymentProvider, PaymentProviderError  # noqa: F401
