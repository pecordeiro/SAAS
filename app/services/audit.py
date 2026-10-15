"""Trilha de auditoria (``audit_logs``, append-only).

Ponto único para registrar ações administrativas: mudança de papel, convite, plano,
exclusão, aplicar versão de modelo, desfazer registro, arquivar etc. A Fase 5 (usuários,
convites) chama ``record`` do mesmo jeito:

    from app.services import audit
    audit.record(audit.ROLE_CHANGED, company_id=c.id, actor_user_id=current_user.id,
                 object_type="membership", object_id=m.id, details={"de": "operator", "para": "supervisor"})

A linha entra na transação corrente (sem commit): grava junto com a mudança ou some junto.
O IP vem da requisição (``request.remote_addr``; atrás de proxy, configure ProxyFix no
deploy). Nunca passe senha, token ou payload de pagamento em ``details``.
"""

from __future__ import annotations

import uuid

from flask import has_request_context, request
from sqlalchemy import select

from app.extensions import db
from app.models import AuditLog

# Ações conhecidas (texto curto e estável; a tela traduz com ACTION_LABELS).
ROLE_CHANGED = "membership.role_changed"
MEMBER_REMOVED = "membership.removed"
INVITATION_CREATED = "invitation.created"
INVITATION_REVOKED = "invitation.revoked"
INVITATION_RESENT = "invitation.resent"
INVITATION_ACCEPTED = "invitation.accepted"
MEMBER_DEACTIVATED = "membership.deactivated"
MEMBER_REACTIVATED = "membership.reactivated"
MFA_REQUIREMENT_CHANGED = "company.mfa_required"
PLAN_CHANGED = "subscription.plan_changed"
COMPANY_DELETION_REQUESTED = "company.deletion_requested"
PROJECT_UPDATED = "project.updated"
PROJECT_ARCHIVED = "project.archived"
PROJECT_DUPLICATED = "project.duplicated"
PROJECT_IMPORTED = "project.imported"
STAGE_ARCHIVED = "stage.archived"
ACTIVITY_ARCHIVED = "activity.archived"
# Etapa D — colaboração.
STAGE_RENAMED = "stage.renamed"
ACTIVITY_UPDATED = "activity.updated"
ACTIVITY_ASSIGNED = "activity.assigned"
ACTIVITY_MOVED = "activity.moved"
STAGES_REORDERED = "stages.reordered"
TEMPLATE_VERSION_APPLIED = "template.version_applied"
TEMPLATE_ARCHIVED = "template.archived"
PROGRESS_UNDONE = "progress.undone"
COMPANY_UPDATED = "company.updated"
HOLIDAY_ADDED = "holiday.added"
HOLIDAY_REMOVED = "holiday.removed"
# Fase 7 — LGPD e suporte (constantes usadas por app/services/lgpd.py e support.py).
COMPANY_DELETION_CANCELLED = "company.deletion_cancelled"
COMPANY_DATA_EXPORTED = "company.data_exported"
SUPPORT_ACCESS_GRANTED = "support.access_granted"
SUPPORT_ACCESS_REVOKED = "support.access_revoked"
SUPPORT_ACCESS_EXPIRED = "support.access_expired"
ACCOUNT_CLAIMED_BY_RESET = "account.claimed_by_reset"

ACTION_LABELS = {
    ROLE_CHANGED: "Papel alterado",
    MEMBER_REMOVED: "Pessoa removida",
    INVITATION_CREATED: "Convite enviado",
    INVITATION_REVOKED: "Convite revogado",
    INVITATION_RESENT: "Convite reenviado",
    INVITATION_ACCEPTED: "Convite aceito",
    MEMBER_DEACTIVATED: "Pessoa desativada",
    MEMBER_REACTIVATED: "Pessoa reativada",
    MFA_REQUIREMENT_CHANGED: "Exigência de MFA alterada",
    PLAN_CHANGED: "Plano alterado",
    COMPANY_DELETION_REQUESTED: "Exclusão da empresa pedida",
    PROJECT_UPDATED: "Projeto editado",
    PROJECT_ARCHIVED: "Projeto arquivado",
    PROJECT_DUPLICATED: "Projeto duplicado",
    PROJECT_IMPORTED: "Projeto importado",
    STAGE_ARCHIVED: "Etapa arquivada",
    ACTIVITY_ARCHIVED: "Atividade arquivada",
    STAGE_RENAMED: "Etapa renomeada",
    ACTIVITY_UPDATED: "Atividade editada",
    ACTIVITY_ASSIGNED: "Responsável da atividade alterado",
    ACTIVITY_MOVED: "Atividade movida",
    STAGES_REORDERED: "Etapas reordenadas",
    TEMPLATE_VERSION_APPLIED: "Versão do modelo aplicada",
    TEMPLATE_ARCHIVED: "Modelo arquivado",
    PROGRESS_UNDONE: "Registro desfeito",
    COMPANY_UPDATED: "Dados da empresa alterados",
    HOLIDAY_ADDED: "Feriado incluído",
    HOLIDAY_REMOVED: "Feriado removido",
    COMPANY_DELETION_CANCELLED: "Exclusão da empresa cancelada",
    COMPANY_DATA_EXPORTED: "Dados da empresa exportados",
    SUPPORT_ACCESS_GRANTED: "Acesso de suporte concedido",
    SUPPORT_ACCESS_REVOKED: "Acesso de suporte revogado",
    SUPPORT_ACCESS_EXPIRED: "Acesso de suporte expirado",
    ACCOUNT_CLAIMED_BY_RESET: "Conta retomada pelo dono do e-mail",
}


def client_ip() -> str | None:
    if not has_request_context():
        return None
    ip = request.remote_addr
    return ip[:45] if ip else None


def record(
    action: str,
    *,
    company_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    object_type: str | None = None,
    object_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Adiciona uma linha de auditoria à transação corrente (sem commit)."""
    entry = AuditLog(
        company_id=company_id,
        actor_user_id=actor_user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        ip=ip if ip is not None else client_ip(),
        details=details or None,
    )
    db.session.add(entry)
    return entry


def for_object(company_id: uuid.UUID, object_type: str, object_id: uuid.UUID, limit: int = 50) -> list[AuditLog]:
    """Ações registradas sobre um objeto da empresa (mais recentes primeiro)."""
    return list(
        db.session.execute(
            select(AuditLog)
            .where(
                AuditLog.company_id == company_id,
                AuditLog.object_type == object_type,
                AuditLog.object_id == object_id,
            )
            .order_by(AuditLog.at.desc())
            .limit(limit)
        ).scalars()
    )
