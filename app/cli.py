"""Comandos de linha (flask ...)."""

from __future__ import annotations

import os
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import click
from flask import Flask, current_app
from flask.cli import AppGroup
from sqlalchemy import select

from app import rls
from app.extensions import db
from app.models import (
    ROLE_OPERATOR,
    ROLE_OWNER,
    ROLE_SUPERVISOR,
    Company,
    Holiday,
    Membership,
    ProgressEntry,
    Subscription,
    User,
)
from app.models.billing import SUB_TRIALING
from app.services import projects as svc
from app.services import templates as templates_svc
from app.services.holidays import seed_national_holidays
from app.services.passwords import hash_password
from app.services.plans import PROFISSIONAL, get_plan, seed_plans

TRIAL_DAYS = 14

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


def _demo_progress(project, users: dict, scale: float, days: int) -> None:
    """Histórico realista: as peças de cada atividade chegam em até 3 registros, espalhados
    pelos dias desde o início, por operador e supervisor."""
    now = datetime.now(timezone.utc)
    authors = (users[ROLE_OPERATOR], users[ROLE_SUPERVISOR])
    step = 0
    for stage, (_, acts) in zip(project.stages, DEMO_STAGES):
        for activity, (_, _, done) in zip(stage.activities, acts):
            target = min(project.quantity, round(done * scale))
            remaining = target
            parts = []
            while remaining > 0:
                piece = max(1, (target + 2) // 3)
                piece = min(piece, remaining)
                parts.append(piece)
                remaining -= piece
            for delta in parts:
                step += 1
                db.session.add(
                    ProgressEntry(
                        company_id=project.company_id,
                        activity_id=activity.id,
                        user_id=authors[step % 2].id,
                        delta=delta,
                        at=now - timedelta(days=max(days - step % (days + 1), 0), hours=step % 8),
                    )
                )
                activity.version += 1
            activity.units_done = target


def register_cli(app: Flask) -> None:
    @app.cli.command("seed-plans")
    def seed_plans_command() -> None:
        """Cria/atualiza os planos Essencial, Profissional e Empresa (idempotente)."""
        created, updated = seed_plans()
        db.session.commit()
        click.echo(f"Planos: {created} criado(s), {updated} atualizado(s).")

    @app.cli.command("seed-holidays")
    @click.option("--de", "first_year", type=int, default=None, help="Primeiro ano (padrão: ano atual).")
    @click.option("--ate", "last_year", type=int, default=None, help="Último ano (padrão: ano atual + 4).")
    def seed_holidays_command(first_year: int | None, last_year: int | None) -> None:
        """Grava os feriados nacionais (company_id NULL) dos anos pedidos (idempotente)."""
        first_year = first_year or date.today().year
        last_year = last_year or first_year + 4
        if last_year < first_year or last_year - first_year > 50:
            raise click.ClickException("Intervalo de anos inválido.")
        created = seed_national_holidays(first_year, last_year)
        db.session.commit()
        click.echo(f"Feriados nacionais {first_year}–{last_year}: {created} criado(s).")

    rls_cli = AppGroup("rls", help="Row Level Security do PostgreSQL (ADR-0003).")

    def _postgres_connection():
        if db.engine.dialect.name != "postgresql":
            raise click.ClickException("RLS só existe no PostgreSQL.")
        return db.engine.begin()

    @rls_cli.command("enable")
    def rls_enable() -> None:
        """Liga ENABLE + FORCE ROW LEVEL SECURITY nas tabelas de cliente (exige RLS_ENABLED=1)."""
        if not current_app.config.get("RLS_ENABLED"):
            raise click.ClickException(
                "Defina RLS_ENABLED=1 (no app e aqui) antes: sem ele o app não informa a empresa ao banco "
                "e toda consulta voltaria vazia."
            )
        with _postgres_connection() as conn:
            rls.enable(conn)
        click.echo(f"RLS ligado e forçado em {len(rls.RLS_TABLES)} tabelas.")

    @rls_cli.command("disable")
    def rls_disable() -> None:
        """Desliga a cobrança do RLS (as políticas continuam criadas)."""
        with _postgres_connection() as conn:
            rls.disable(conn)
        click.echo("RLS desligado (políticas mantidas).")

    @rls_cli.command("status")
    def rls_status() -> None:
        """Mostra, por tabela de cliente, se o RLS está ligado/forçado e as políticas."""
        with _postgres_connection() as conn:
            info = rls.status(conn)
            superuser, bypass = conn.exec_driver_sql(
                "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
            ).one()
        for table in rls.RLS_TABLES:
            row = info.get(table, {"enabled": False, "forced": False, "policies": []})
            click.echo(
                f"{table:22} ligado={'sim' if row['enabled'] else 'não':3} "
                f"forçado={'sim' if row['forced'] else 'não':3} políticas={', '.join(row['policies']) or '-'}"
            )
        if superuser or bypass:
            click.echo("Atenção: o papel atual é superusuário ou tem BYPASSRLS; para ele o RLS não vale.")

    app.cli.add_command(rls_cli)

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Cria 2 empresas fictícias com modelo de etapas, 1 projeto de 10 equipamentos e
        assinatura em teste (trial) cada (só dev/test)."""
        if current_app.config.get("ENV_NAME") not in {"development", "test"}:
            raise click.ClickException("seed-demo só roda em development ou test.")
        password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12)
        created = []
        seed_plans()
        today = date.today()
        seed_national_holidays(today.year, today.year + 1)
        plan = get_plan(PROFISSIONAL)
        for company_name, suffix in DEMO_COMPANIES:
            exists = db.session.execute(select(Company).where(Company.name == company_name)).scalar_one_or_none()
            if exists:
                click.echo(f"Já existe: {company_name} (nada feito)")
                continue
            company = Company(name=company_name)
            db.session.add(company)
            db.session.flush()
            # Com RLS ligado, as linhas desta empresa só podem ser gravadas no contexto dela.
            rls.set_context(company_id=company.id)
            users = {}
            for role in (ROLE_OWNER, ROLE_SUPERVISOR, ROLE_OPERATOR):
                email = f"{role}.{suffix}@demo.invalid"
                user = User(email=email, name=f"{role.capitalize()} {suffix.upper()}", password_hash=hash_password(password))
                db.session.add(user)
                db.session.flush()
                db.session.add(Membership(company_id=company.id, user_id=user.id, role=role))
                users[role] = user
                created.append(email)
            template = templates_svc.create_template(
                company,
                "Montagem padrão (demo)",
                [
                    svc.NewStage(
                        name=stage_name,
                        activities=[svc.NewActivity(name=n, ideal_minutes=Decimal(m)) for n, m, _ in acts],
                    )
                    for stage_name, acts in DEMO_STAGES
                ],
                created_by_user_id=users[ROLE_OWNER].id,
            )
            version = template.current_version
            # Dois lotes do mesmo modelo: um adiantado e um recém-iniciado.
            for name, quantity, started_days_ago, due_in_days, scale in (
                ("Lote 10 equipamentos", 10, 7, 30, 1.0),
                ("Lote 4 equipamentos", 4, 2, 45, 0.25),
            ):
                project = svc.create_project(
                    company,
                    name=name,
                    quantity=quantity,
                    start_date=today - timedelta(days=started_days_ago),
                    due_date=today + timedelta(days=due_in_days),
                    people=2,
                    hours_per_day=Decimal("8"),
                    stages=templates_svc.stages_from_version(version),
                    template_version_id=version.id,
                )
                _demo_progress(project, users, scale, started_days_ago)
            db.session.add(
                Subscription(
                    company_id=company.id,
                    plan_id=plan.id,
                    provider="fake",
                    status=SUB_TRIALING,
                    trial_ends_at=datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS),
                )
            )
            # Feriado PRÓPRIO da empresa (os nacionais são linhas globais, sem company_id).
            db.session.add(Holiday(company_id=company.id, day=date(today.year, 12, 24), name="Recesso de fim de ano"))
        db.session.commit()
        if created:
            click.echo("Usuários criados (e-mails .invalid, só para desenvolvimento):")
            for email in created:
                click.echo(f"  {email}")
            if os.environ.get("DEMO_PASSWORD"):
                click.echo("Senha: a definida em DEMO_PASSWORD.")
            else:
                click.echo(f"Senha gerada para todos: {password}")

    # ------------------------------------------------------------------ worker (Etapa F)
    from app.services import worker as worker_svc

    worker_cli = AppGroup("worker", help="Worker: outbox e tarefas agendadas (ADR-0010).")

    @worker_cli.command("run")
    @click.option("--once", is_flag=True, help="Roda um ciclo (todas as tarefas pedidas) e sai — cron e testes.")
    @click.option(
        "--task",
        "tasks",
        multiple=True,
        type=click.Choice(worker_svc.TASKS),
        help="Tarefa a rodar (repita para várias). Padrão: todas.",
    )
    @click.option("--interval", type=float, default=None, help="Segundos entre ciclos (padrão WORKER_INTERVAL_SECONDS).")
    def worker_run(once: bool, tasks: tuple[str, ...], interval: float | None) -> None:
        """Consome domain_events pendentes e roda as tarefas agendadas, empresa a empresa."""
        chosen = tuple(tasks) or worker_svc.TASKS
        if once:
            results = worker_svc.run_once(chosen)
            for name, result in results.items():
                click.echo(f"{name}: {result}")
            if any("error" in r for r in results.values()):
                raise SystemExit(1)
            return
        loop = worker_svc.Loop(
            tasks=chosen, interval=interval or float(current_app.config.get("WORKER_INTERVAL_SECONDS", 30))
        )
        loop.install_signals()
        loop.run()

    @worker_cli.command("status")
    @click.option("--check", is_flag=True, help="Imprime métricas e sai com 1 se há eventos esgotados ou fila parada.")
    @click.option(
        "--max-idade-min", "max_age_min", type=int, default=15, show_default=True,
        help="Com --check: idade máxima (min) do evento pendente mais antigo.",
    )
    def worker_status(check: bool, max_age_min: int) -> None:
        """Eventos pendentes e esgotados (tentativas no limite), por empresa."""
        if check:
            metrics = worker_svc.queue_metrics()
            click.echo(
                "worker_queue pending={pending} dead={dead} companies={companies} "
                "oldest_pending_seconds={oldest_pending_seconds}".format(**metrics)
            )
            if metrics["dead"] > 0:
                click.echo("PROBLEMA: há evento esgotado (sai da fila sem ser entregue).", err=True)
                raise SystemExit(1)
            if metrics["oldest_pending_seconds"] > max_age_min * 60:
                click.echo(f"PROBLEMA: evento pendente há mais de {max_age_min} min (worker parado?).", err=True)
                raise SystemExit(1)
            return
        rows = worker_svc.queue_status()
        if not rows:
            click.echo("Fila vazia: nenhum evento pendente.")
            return
        for row in rows:
            click.echo(f"empresa {row['company_id']}: pendentes={row['pending']} esgotados={row['dead']}")

    app.cli.add_command(worker_cli)

    from app.ops_cli import register_ops_cli

    register_ops_cli(app)
