"""Modelos de etapas versionados (base da Fase 3; edição/comparação completa na Fase 4).

- ``create_template`` cria o modelo com a versão 1 e a marca como atual.
- ``stages_from_version`` devolve a CÓPIA das etapas/atividades da versão, no formato que
  ``services.projects.create_project`` recebe (snapshot: o projeto não muda quando o modelo
  ganha versão nova).
"""

from __future__ import annotations

import uuid

from app.extensions import db
from app.models import Company, Template, TemplateActivity, TemplateStage, TemplateVersion
from app.services.projects import NewActivity, NewStage


def create_template(
    company: Company, name: str, stages: list[NewStage], created_by_user_id: uuid.UUID | None = None
) -> Template:
    template = Template(company_id=company.id, name=name)
    db.session.add(template)
    db.session.flush()
    version = add_version(template, stages, created_by_user_id=created_by_user_id)
    template.current_version_id = version.id
    db.session.flush()
    return template


def add_version(
    template: Template, stages: list[NewStage], created_by_user_id: uuid.UUID | None = None
) -> TemplateVersion:
    number = max((v.number for v in template.versions), default=0) + 1
    version = TemplateVersion(
        company_id=template.company_id, template_id=template.id, number=number, created_by_user_id=created_by_user_id
    )
    db.session.add(version)
    db.session.flush()
    for s_pos, new_stage in enumerate(stages):
        stage = TemplateStage(
            company_id=template.company_id, template_version_id=version.id, name=new_stage.name, position=s_pos
        )
        db.session.add(stage)
        db.session.flush()
        for a_pos, new_activity in enumerate(new_stage.activities):
            db.session.add(
                TemplateActivity(
                    company_id=template.company_id,
                    template_stage_id=stage.id,
                    name=new_activity.name,
                    ideal_minutes=new_activity.ideal_minutes,
                    position=a_pos,
                )
            )
    db.session.flush()
    db.session.refresh(version)
    return version


def stages_from_version(version: TemplateVersion) -> list[NewStage]:
    return [
        NewStage(
            name=stage.name,
            activities=[NewActivity(name=a.name, ideal_minutes=a.ideal_minutes) for a in stage.activities],
        )
        for stage in version.stages
    ]
