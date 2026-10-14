"""Fábrica da aplicação Flask."""

from __future__ import annotations

import uuid

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from app.config import finalize_config, get_config
from app.extensions import csrf, db, limiter, login_manager, migrate


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)
    app.config.update(config.from_env())
    if overrides:
        app.config.update(overrides)
    finalize_config(app.config, config.ENV_NAME)
    app.config["ENV_NAME"] = config.ENV_NAME
    _init_proxy(app)

    from app import models  # noqa: F401  (registra os modelos no metadata)

    db.init_app(app)
    from app import rls

    rls.init_app(app)
    migrate.init_app(app, db, render_as_batch=True, compare_type=True)
    csrf.init_app(app)
    limiter.init_app(app)
    _init_login(app)

    from app.blueprints.account import bp as account_bp
    from app.blueprints.app import bp as app_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.dev import bp as dev_bp
    from app.blueprints.public import bp as public_bp
    from app.blueprints.team import bp as team_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(app_bp)
    app.register_blueprint(account_bp)  # Fase 5: /conta
    app.register_blueprint(team_bp)  # Fase 5: /app/usuarios e /convite
    app.register_blueprint(dev_bp)  # /estilo: responde 404 fora de development

    # Fase 4: modelos de etapas, edição de projeto (+ 402 e modo leitura), importar/exportar.
    from app.blueprints.dados import bp as dados_bp
    from app.blueprints.edicao import bp as edicao_bp
    from app.blueprints.modelos import bp as modelos_bp

    app.register_blueprint(modelos_bp)
    app.register_blueprint(edicao_bp)
    app.register_blueprint(dados_bp)

    # Fase 6: configurações da empresa (/app/empresa).
    from app.blueprints.empresa import bp as empresa_bp

    app.register_blueprint(empresa_bp)

    # Fase 9: API pública e tela de tokens só existem com FEATURE_PUBLIC_API (desligada → 404).
    if app.config.get("FEATURE_PUBLIC_API"):
        from app.blueprints.api_v1 import bp as api_v1_bp
        from app.blueprints.api_v1 import ui_bp as api_tokens_bp

        app.register_blueprint(api_v1_bp)
        app.register_blueprint(api_tokens_bp)

    # Fase 8: assinatura (owner) e webhook do Asaas (sem CSRF, token no header).
    from app.blueprints.billing import bp as billing_bp
    from app.blueprints.webhooks import bp as webhooks_bp

    app.register_blueprint(billing_bp)
    app.register_blueprint(webhooks_bp)

    from app.tenancy import load_company

    app.before_request(load_company)
    from app.blueprints.account import register_guards

    register_guards(app)  # depois de load_company: confirmação de e-mail e MFA obrigatório
    _register_errors(app)
    _register_security_headers(app)
    _register_template_helpers(app)
    from app import assets

    assets.init_app(app)

    from app.cli import register_cli

    register_cli(app)
    from app.services.billing.cli import register_cli as register_billing_cli

    register_billing_cli(app)
    return app


def _init_proxy(app: Flask) -> None:
    """ProxyFix só com proxies confiáveis declarados: o IP real (X-Forwarded-For) passa a
    valer em ``request.remote_addr`` antes do bloqueio de login e do Flask-Limiter."""
    count = int(app.config.get("TRUSTED_PROXY_COUNT") or 0)
    if count > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=count, x_proto=count)  # type: ignore[method-assign]


def _init_login(app: Flask) -> None:
    from app.models import User

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre para continuar."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "basic"

    @login_manager.user_loader
    def load_user(raw: str):
        try:
            user_id, version = raw.split(":", 1)
            user = db.session.get(User, uuid.UUID(user_id))
            version_int = int(version)
        except (ValueError, TypeError):
            return None
        if user is None or not user.active or user.session_version != version_int:
            return None
        return user


def _register_errors(app: Flask) -> None:
    def page(template: str, status: int, **ctx):
        return render_template(template, **ctx), status

    @app.errorhandler(CSRFError)
    def csrf_error(err):
        return page("errors/400.html", 400, message="Formulário expirado ou inválido. Recarregue a página e tente de novo.")

    @app.errorhandler(400)
    def bad_request(err):
        return page("errors/400.html", 400, message="Requisição inválida.")

    @app.errorhandler(403)
    def forbidden(err):
        return page("errors/403.html", 403)

    @app.errorhandler(404)
    def not_found(err):
        return page("errors/404.html", 404)

    @app.errorhandler(405)
    def method_not_allowed(err):
        return page("errors/400.html", 405, message="Método não permitido.")

    @app.errorhandler(429)
    def too_many(err):
        return page("errors/429.html", 429)

    @app.errorhandler(500)
    def server_error(err):
        db.session.rollback()
        return page("errors/500.html", 500)


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def headers(response):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def _register_template_helpers(app: Flask) -> None:
    from app.formatting import (
        br_date,
        br_date_short,
        br_datetime,
        br_day_label,
        br_hours,
        br_number,
        br_pct,
        br_time,
        br_workdays,
    )
    from app.models import ROLE_LABELS

    app.add_template_filter(br_number, "num")
    app.add_template_filter(br_pct, "pct")
    app.add_template_filter(br_date, "data")
    app.add_template_filter(br_datetime, "datahora")
    app.add_template_filter(br_date_short, "data_curta")
    app.add_template_filter(br_hours, "horas")
    app.add_template_filter(br_time, "hora")
    app.add_template_filter(br_day_label, "dia_rotulo")
    app.add_template_filter(br_workdays, "dias_semana")

    @app.context_processor
    def inject():
        from flask import g, request

        from app.blueprints.public import THEME_COOKIE, THEMES_FIXED
        from app.forms import LogoutForm

        theme = request.cookies.get(THEME_COOKIE)

        return {
            "current_company": getattr(g, "company", None),
            "current_membership": getattr(g, "membership", None),
            "role_labels": ROLE_LABELS,
            "logout_form": LogoutForm(formdata=None),
            # Tema fixado pelo usuário (cookie); ausente = segue o sistema.
            "theme": theme if theme in THEMES_FIXED else None,
        }
