"""Modelos. Importar daqui garante que todos estejam registrados no metadata."""

from app.models.accounts import (  # noqa: F401
    ROLE_LABELS,
    ROLE_LEVEL,
    ROLE_OPERATOR,
    ROLE_OWNER,
    ROLE_SUPERVISOR,
    ROLES,
    Company,
    EmailConfirmation,
    Invitation,
    Membership,
    MfaRecoveryCode,
    PasswordReset,
    User,
)
from app.models.billing import (  # noqa: F401
    PAYMENT_STATUSES,
    SUBSCRIPTION_STATUSES,
    Payment,
    Plan,
    Subscription,
    WebhookEvent,
)
from app.models.platform import ApiClient, ApiToken, AuditLog, DomainEvent  # noqa: F401
from app.models.production import (  # noqa: F401
    PROGRESS_DETAILED,
    PROGRESS_MODES,
    PROGRESS_SIMPLE,
    PROJECT_ACTIVE,
    PROJECT_DONE,
    Activity,
    Holiday,
    Project,
    ProgressEntry,
    Stage,
)
from app.models.templates import Template, TemplateActivity, TemplateStage, TemplateVersion  # noqa: F401
from app.models.security import THROTTLE_ACCOUNT, THROTTLE_IP, LoginThrottle  # noqa: F401
from app.models.privacy import PlatformAuditLog  # noqa: F401,E402  (Fase 7)
from app.models.staff import (  # noqa: F401,E402  (Etapa C)
    VISUAL_BRIEFING_FILLED,
    VISUAL_DELIVERED,
    VISUAL_IN_PROGRESS,
    VISUAL_NEW,
    VISUAL_STATUSES,
    VisualRequest,
)
from app.models.notifications import (  # noqa: F401,E402  (Etapa F)
    ALERT_DEADLINE_RISK,
    ALERT_FORECAST_LATE,
    ALERT_KINDS,
    ALERT_PART_OVERDUE,
    ALERT_STAGE_STALLED,
    Alert,
    JobRun,
)
from app.models.quality import (  # noqa: F401,E402  (Etapa G)
    ActivityComment,
    ActivityPhoto,
    InspectionAnswer,
    StageChecklistItem,
    StageInspection,
    TemplateChecklistItem,
    Unit,
)
from app.models.modules import CompanyModule  # noqa: F401,E402  (R6: módulos opcionais)
from app.models.visual import (  # noqa: F401,E402  (ADR-0019: briefing e agendamento)
    CallBooking,
    CallSlot,
    VisualBriefing,
    VisualBriefingFile,
)
