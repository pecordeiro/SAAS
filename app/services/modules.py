"""R6 — módulos opcionais por empresa (ADR-0017, plano de reestruturação §4.5).

O núcleo do produto é acompanhar ETAPAS. Todo o resto é opcional, DESLIGADO por padrão e ligado
pelo proprietário em Configurações › Módulos. Este arquivo é o ponto único da regra:

- ``CATALOG``: cada módulo, o nome em português e as ROTAS (endpoints) que pertencem a ele.
- ``guard_endpoint``: chamado por ``tenancy.tenant_required`` em toda rota da área logada, logo
  depois de resolver a empresa. Rota de módulo desligado → 404 (para todos os papéis), como se
  não existisse. A API (token, sem sessão) faz a mesma checagem em ``api_v1.authenticate``.
- ``enabled_keys``/``is_enabled``: o que templates (variável ``modules``), serviços e o worker
  consultam para não mostrar menu/fragmento nem gerar alerta ou e-mail de módulo desligado.

Esconder botão nunca substitui a recusa da rota (ADR-0009): os templates só leem ``modules``,
quem recusa é ``guard_endpoint``. Limites de plano continuam valendo à parte (``entitlements``):
ligar um módulo não libera recurso que o plano não tem.

Sem linha em ``company_modules`` = desligado. A migration f1a7c3e9b2d4 liga, nas empresas que
já existiam, os módulos em que elas já tinham dados (ninguém perde acesso ao que já usava).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Mapping

from flask import abort, current_app, g, has_app_context, has_request_context, request
from sqlalchemy import select

from app.extensions import db
from app.models.base import utcnow
from app.models.modules import CompanyModule

# Chaves estáveis (gravadas no banco e usadas nos templates como texto).
ATRIBUICAO = "atribuicao"
ALERTAS = "alertas"
AGUARDANDO_PECA = "aguardando_peca"
FOTOS = "fotos"
CHECKLIST = "checklist"
UNIDADES = "unidades"
API = "api"

@dataclass(frozen=True)
class Module:
    key: str
    name: str
    description: str
    # O que some quando está desligado (texto da tela de Módulos).
    where: str
    endpoints: tuple[str, ...] = ()
    endpoint_prefixes: tuple[str, ...] = ()
    # Só aparece em Configurações › Módulos com esta flag de configuração ligada.
    requires_config: str | None = None
    # Recurso do plano exigido para USAR (a checagem continua em entitlements, à parte).
    plan_feature: str | None = None


CATALOG: tuple[Module, ...] = (
    Module(
        ATRIBUICAO,
        "Responsáveis e progresso por pessoa",
        "Escolha quem cuida de cada atividade, avise a pessoa por e-mail e veja quantas peças cada um lançou.",
        "Campo “Responsável”, quadro “Pessoas” e a tela de progresso por pessoa.",
        endpoints=("app.project_people", "edicao.activity_assign"),
    ),
    Module(
        ALERTAS,
        "Alertas e relatório semanal por e-mail",
        "Avisa quando um prazo está em risco ou uma etapa parou, e manda um resumo toda segunda-feira.",
        "Tela de alertas e os e-mails de alerta e do relatório semanal.",
        endpoints=("app.alerts",),
    ),
    Module(
        AGUARDANDO_PECA,
        "Aguardando peça",
        "Marque a etapa que parou por falta de peça, com a data prevista de chegada.",
        "Marca “Aguardando peça” nas etapas, no painel e na lista de projetos.",
        endpoints=("app.stage_waiting_part",),
    ),
    Module(
        FOTOS,
        "Fotos e comentários",
        "Guarde fotos e comentários em cada atividade, como registro do que foi feito.",
        "Botão “Fotos e comentários” nas etapas e a tela de cada atividade.",
        endpoints=(
            "qualidade.evidence",
            "qualidade.comment_create",
            "qualidade.comment_delete",
            "qualidade.photo_upload",
            "qualidade.photo_view",
            "qualidade.photo_delete",
        ),
    ),
    Module(
        CHECKLIST,
        "Checklist de inspeção",
        "Lista de conferência por etapa, preenchida e assinada por quem inspecionou.",
        "Checklist nas etapas e nos modelos, e as telas de inspeção.",
        endpoints=(
            "qualidade.checklist",
            "qualidade.checklist_item_add",
            "qualidade.checklist_item_archive",
            "qualidade.checklist_required",
            "qualidade.inspection_start",
            "qualidade.inspection",
            "qualidade.inspection_save",
            "qualidade.inspection_correct",
        ),
    ),
    Module(
        UNIDADES,
        "Número de série por unidade",
        "Cadastre o número de série de cada unidade e veja o histórico de cada uma.",
        "Telas de unidades e a busca por número de série.",
        endpoints=(
            "qualidade.units",
            "qualidade.units_generate",
            "qualidade.units_import",
            "qualidade.units_search",
            "qualidade.unit_detail",
            "qualidade.unit_status",
            "qualidade.unit_register",
        ),
    ),
    Module(
        API,
        "API de integração",
        "Ligue outros sistemas ao Controle de Produção com tokens de acesso.",
        "Tela de tokens e o endereço /api/v1.",
        endpoint_prefixes=("api_tokens_ui.", "api_v1."),
        requires_config="FEATURE_PUBLIC_API",
        plan_feature="api",
    ),
)

BY_KEY: dict[str, Module] = {m.key: m for m in CATALOG}
KEYS: tuple[str, ...] = tuple(BY_KEY)

_ENDPOINTS: dict[str, str] = {endpoint: m.key for m in CATALOG for endpoint in m.endpoints}
_PREFIXES: tuple[tuple[str, str], ...] = tuple((p, m.key) for m in CATALOG for p in m.endpoint_prefixes)


class ModuleError(ValueError):
    """Chave de módulo desconhecida ou indisponível neste ambiente."""


def module_for_endpoint(endpoint: str | None) -> str | None:
    """Chave do módulo dono da rota (None = núcleo ou rota fora dos módulos)."""
    if not endpoint:
        return None
    key = _ENDPOINTS.get(endpoint)
    if key is not None:
        return key
    for prefix, module_key in _PREFIXES:
        if endpoint.startswith(prefix):
            return module_key
    return None


def available() -> list[Module]:
    """Módulos que existem neste ambiente (a API só com FEATURE_PUBLIC_API)."""
    config = current_app.config if has_app_context() else {}
    return [m for m in CATALOG if m.requires_config is None or config.get(m.requires_config)]


def _query(company_id: uuid.UUID) -> frozenset[str]:
    rows = db.session.execute(
        select(CompanyModule.module).where(CompanyModule.company_id == company_id, CompanyModule.enabled.is_(True))
    ).scalars()
    return frozenset(k for k in rows if k in BY_KEY)


def enabled_keys(company_or_id) -> frozenset[str]:
    """Módulos ligados da empresa. Em requisição, guarda o resultado em ``g`` (uma consulta por
    requisição); fora dela (worker) consulta sempre — o laço do worker é longo."""
    if company_or_id is None:
        return frozenset()
    company_id = getattr(company_or_id, "id", company_or_id)
    if not has_request_context():
        return _query(company_id)
    cache = g.setdefault("_modules_cache", {})
    if company_id not in cache:
        cache[company_id] = _query(company_id)
    return cache[company_id]


def is_enabled(company_or_id, key: str) -> bool:
    if key not in BY_KEY:
        raise ModuleError(key)
    return key in enabled_keys(company_or_id)


def _forget(company_id: uuid.UUID) -> None:
    if has_request_context():
        g.setdefault("_modules_cache", {}).pop(company_id, None)


def guard_endpoint(company) -> None:
    """Rota de módulo desligado → 404 (chamado por ``tenant_required`` depois de achar a empresa)."""
    key = module_for_endpoint(request.endpoint) if has_request_context() else None
    if key is not None and not is_enabled(company, key):
        abort(404)


def set_modules(company, wanted: Mapping[str, bool], actor_user_id: uuid.UUID | None) -> list[tuple[str, bool]]:
    """Grava o estado pedido (só módulos disponíveis; chave desconhecida → ``ModuleError``).
    Cada mudança vira uma linha em ``audit_logs``. Devolve ``[(chave, ligado), …]`` do que mudou.
    Sem commit."""
    from app.services import audit

    allowed = {m.key for m in available()}
    unknown = set(wanted) - allowed
    if unknown:
        raise ModuleError(", ".join(sorted(unknown)))
    rows = {
        r.module: r
        for r in db.session.execute(select(CompanyModule).where(CompanyModule.company_id == company.id)).scalars()
    }
    changed: list[tuple[str, bool]] = []
    now = utcnow()
    for key in [m.key for m in CATALOG if m.key in wanted]:
        on = bool(wanted[key])
        row = rows.get(key)
        if row is not None and bool(row.enabled) == on:
            continue
        if row is None:
            if not on:
                continue  # sem linha já é desligado
            row = CompanyModule(company_id=company.id, module=key)
            db.session.add(row)
        row.enabled = on
        row.updated_at = now
        row.updated_by_id = actor_user_id
        audit.record(
            audit.MODULE_ENABLED if on else audit.MODULE_DISABLED,
            company_id=company.id,
            actor_user_id=actor_user_id,
            object_type="module",
            details={"modulo": key, "nome": BY_KEY[key].name},
        )
        changed.append((key, on))
    db.session.flush()
    _forget(company.id)
    return changed


def init_app(app) -> None:
    @app.context_processor
    def inject_modules():
        company = getattr(g, "company", None)
        return {"modules": enabled_keys(company) if company is not None else frozenset()}
