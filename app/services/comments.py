"""Etapa G — comentários por atividade (evidência de montagem / não conformidade).

- Operador+ comenta (só membros da empresa da sessão; a rota resolve a atividade com
  ``tenancy.get_or_404``). Texto limpo de espaços nas pontas, 1..``COMMENT_MAX_CHARS``.
- Comentário não se edita. Supervisor+ apaga: a linha sai e fica ``activity.comment_deleted``
  na auditoria com autor, data e tamanho — SEM o texto (o motivo de apagar costuma ser o
  conteúdo: dado pessoal, ofensa, engano).
"""

from __future__ import annotations

import uuid

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import Activity
from app.models.quality import COMMENT_MAX_CHARS, ActivityComment
from app.services import audit


class CommentError(Exception):
    """Comentário recusado (mensagem pronta para a tela)."""


def max_chars() -> int:
    return min(int(current_app.config.get("COMMENT_MAX_CHARS", COMMENT_MAX_CHARS)), COMMENT_MAX_CHARS)


def list_for(activity: Activity) -> list[ActivityComment]:
    return list(
        db.session.execute(
            select(ActivityComment)
            .where(ActivityComment.company_id == activity.company_id, ActivityComment.activity_id == activity.id)
            .order_by(ActivityComment.created_at.desc(), ActivityComment.id)
        ).scalars()
    )


def counts_by_activity(company_id: uuid.UUID, activity_ids) -> dict[uuid.UUID, int]:
    ids = list(activity_ids)
    if not ids:
        return {}
    rows = db.session.execute(
        select(ActivityComment.activity_id, func.count())
        .where(ActivityComment.company_id == company_id, ActivityComment.activity_id.in_(ids))
        .group_by(ActivityComment.activity_id)
    ).all()
    return {aid: n for aid, n in rows}


def add_comment(activity: Activity, body: str | None, user_id: uuid.UUID | None) -> ActivityComment:
    text = (body or "").strip()
    limit = max_chars()
    if not text:
        raise CommentError("Escreva o comentário.")
    if len(text) > limit:
        raise CommentError(f"O comentário tem no máximo {limit} caracteres.")
    comment = ActivityComment(company_id=activity.company_id, activity_id=activity.id, body=text, author_id=user_id)
    db.session.add(comment)
    db.session.flush()
    return comment


def delete_comment(comment: ActivityComment, user_id: uuid.UUID | None) -> None:
    activity = comment.activity
    audit.record(
        audit.COMMENT_DELETED,
        company_id=comment.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=activity.stage.project_id,
        details={
            "comment_id": str(comment.id),
            "activity_id": str(activity.id),
            "activity": activity.name,
            "author_id": str(comment.author_id) if comment.author_id else None,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "chars": len(comment.body),
        },
    )
    db.session.delete(comment)
    db.session.flush()
