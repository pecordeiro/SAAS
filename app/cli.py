"""Comandos de linha (flask ...)."""

from __future__ import annotations

import os
import secrets
from datetime import date, timedelta
from decimal import Decimal

import click
from flask import Flask, current_app
from sqlalchemy import select

from app.extensions import db
from app.models import ROLE_OPERATOR, ROLE_OWNER, ROLE_SUPERVISOR, Company, Holiday, Membership, ProgressEntry, User
from app.services import projects as svc
from app.services.passwords import hash_password

# Etapas GENÉRICAS e fictícias (decisão D15: nada de nomes reais de clientes no seed).
DEMO_STAGES: list[tuple[str, list[tuple[str, int, int]]]] = [
    # (etapa, [(atividade, minutos por unidade, peças já concluídas)])
    ("1. Preparação da base", [("Separar componentes", 10, 10), ("Limpar e conferir a base", 5, 10)]),
    ("2. Montagem da estrutura", [("Posicionar a estrutura", 15, 6), ("Conferir esquadro", 20, 5), ("Apertar fixações", 10, 4)]),
    ("3. Instalação mecânica", [("Instalar eixos", 25, 3), ("Instalar correias", 15, 2)]),
    ("4. Instalação elétrica", [("Passar chicote", 30, 1), ("Ligar painel", 20, 0)]),
    ("5. Fechamento", [("Fixar tampas", 10, 0), ("Etiquetar", 5, 0)]),
    ("6. Teste final", [("Teste funcional", 30, 0)]),
]

DEMO_COMPANIES = [
    ("Metalúrgica Exemplo A (demo)", "a"),
    ("Montadora Exemplo B (demo)", "b"),
]


def register_cli(app: Flask) -> None:
    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Cria 2 empresas fictícias com 1 projeto de 10 equipamentos cada (só dev/test)."""
        if current_app.config.get("ENV_NAME") not in {"development", "test"}:
            raise click.ClickException("seed-demo só roda em development ou test.")
        password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12)
        created = []
        for company_name, suffix in DEMO_COMPANIES:
            exists = db.session.execute(select(Company).where(Company.name == company_name)).scalar_one_or_none()
            if exists:
                click.echo(f"Já existe: {company_name} (nada feito)")
                continue
            company = Company(name=company_name)
            db.session.add(company)
            db.session.flush()
            users = {}
            for role in (ROLE_OWNER, ROLE_SUPERVISOR, ROLE_OPERATOR):
                email = f"{role}.{suffix}@demo.invalid"
                user = User(email=email, name=f"{role.capitalize()} {suffix.upper()}", password_hash=hash_password(password))
                db.session.add(user)
                db.session.flush()
                db.session.add(Membership(company_id=company.id, user_id=user.id, role=role))
                users[role] = user
                created.append(email)
            today = date.today()
            project = svc.create_project(
                company,
                name="Lote 10 equipamentos",
                quantity=10,
                start_date=today - timedelta(days=7),
                due_date=today + timedelta(days=30),
                people=2,
                hours_per_day=Decimal("8"),
                stages=[
                    svc.NewStage(
                        name=stage_name,
                        activities=[svc.NewActivity(name=n, ideal_minutes=Decimal(m)) for n, m, _ in acts],
                    )
                    for stage_name, acts in DEMO_STAGES
                ],
            )
            for stage, (_, acts) in zip(project.stages, DEMO_STAGES):
                for activity, (_, _, done) in zip(stage.activities, acts):
                    if done:
                        activity.units_done = done
                        activity.version += 1
                        db.session.add(
                            ProgressEntry(
                                company_id=company.id,
                                activity_id=activity.id,
                                user_id=users[ROLE_OPERATOR].id,
                                delta=done,
                            )
                        )
            db.session.add(Holiday(company_id=company.id, day=date(today.year, 12, 25), name="Natal"))
        db.session.commit()
        if created:
            click.echo("Usuários criados (e-mails .invalid, só para desenvolvimento):")
            for email in created:
                click.echo(f"  {email}")
            if os.environ.get("DEMO_PASSWORD"):
                click.echo("Senha: a definida em DEMO_PASSWORD.")
            else:
                click.echo(f"Senha gerada para todos: {password}")
