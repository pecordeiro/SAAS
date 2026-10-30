"""Tour de primeiro acesso (ADR-0021): os passos que cada papel vê e quando o tour abre.

O servidor decide os passos (ADR-0009); o tour.js só destaca na tela o item do menu de cada
passo (``alvo`` = valor do atributo ``data-tour``) e, sem o item visível (celular, menu Mais),
mostra o balão no meio da tela apontando para ``reserva``. Textos seguem a terminologia
(docs/teroz-terminologia.md): só o que a tela faz de verdade.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import ROLE_OWNER, ROLE_SUPERVISOR


@dataclass(frozen=True)
class Passo:
    titulo: str
    texto: str
    alvo: str = ""  # data-tour do item destacado ("" = balão no centro)
    reserva: str = ""  # data-tour usado quando o alvo não está visível (celular)

    @property
    def dica_reserva(self) -> str:
        """Frase somada ao texto quando o balão aponta para a reserva (celular)."""
        return "No celular, fica no menu Mais." if self.reserva == "more" else ""


def passos(membership) -> tuple[Passo, ...]:
    """Passos do tour para o papel da pessoa na empresa atual."""
    supervisor = membership.has_role(ROLE_SUPERVISOR)
    owner = membership.has_role(ROLE_OWNER)
    lista = [
        Passo(
            "Um giro rápido pela Teroz",
            "Em um minuto, mostramos para que serve cada parte. Você pode pular agora e rever quando "
            "quiser em Como funciona.",
        ),
        Passo(
            "Painel",
            "A situação de todos os projetos ativos: o que precisa de atenção, o progresso de cada "
            "etapa e o término previsto em relação ao prazo.",
            "dashboard",
        ),
        Passo(
            "Preencher etapas",
            (
                "Onde a produção é registrada: digite o total de peças prontas de cada subatividade, "
                "não só as de hoje. No modo Configurar, você monta etapas, subatividades e tempos."
            )
            if supervisor
            else (
                "Onde você registra a produção: digite o total de peças prontas de cada subatividade, "
                "não só as de hoje. Ao sair do campo, o valor é salvo e as contas se refazem."
            ),
            "fill",
        ),
        Passo(
            "Meta e equipe",
            (
                "Quantas unidades o projeto vai montar, quantas pessoas trabalham e quantas horas por dia. "
                "Daqui sai a previsão de término."
            )
            if supervisor
            else (
                "A meta do projeto, a equipe e as horas por dia. Daqui sai a previsão de término; "
                "quem muda esses números é o supervisor."
            ),
            "team",
        ),
        Passo(
            "Como funciona",
            "Escolha uma dúvida e veja a conta feita com os números do seu projeto: progresso, unidades "
            "prontas, horas que faltam e prazo.",
            "how",
        ),
        Passo(
            "Projetos",
            "Todos os projetos da empresa, ativos e concluídos."
            + (" Daqui você cria um projeto novo ou importa uma planilha." if supervisor else ""),
            "projects",
            "more",
        ),
        Passo(
            "Histórico",
            "Cada registro de peças, com quem lançou e quando.",
            "history",
            "more",
        ),
    ]
    if owner:
        lista.append(
            Passo(
                "Configurações",
                "Dados da empresa, usuários e convites, assinatura, módulos opcionais e importação de planilha.",
                "settings",
                "more",
            )
        )
    elif supervisor:
        lista.append(
            Passo(
                "Configurações",
                "Usuários e convites, modelos de etapas e importação de planilha.",
                "settings",
                "more",
            )
        )
    lista.append(
        Passo(
            "Sua conta",
            "Nome, senha, verificação em duas etapas e os avisos que você recebe por e-mail.",
            "account",
            "more",
        )
    )
    lista.append(
        Passo(
            "Pronto",
            "Para rever este giro, abra Como funciona e escolha “Rever o tour pelas telas”.",
        )
    )
    return tuple(lista)


def deve_abrir(user, pedido: bool) -> bool:
    """O tour abre sozinho até a pessoa ver uma vez; ``pedido`` = link “Rever o tour”."""
    return pedido or user.tour_seen_at is None


def marcar_visto(user) -> bool:
    """Marca o tour como visto (uma vez só). Devolve True se mudou."""
    if user.tour_seen_at is not None:
        return False
    user.tour_seen_at = datetime.now(timezone.utc)
    return True
