"""
app/premios.py
==============
Constantes e helpers (funções puras) relacionados a palpites de prêmios
individuais da Copa.

Não tem I/O - é só configuração e validação. Para acesso ao banco,
ver app/db_premios.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Premio:
    """Definição de um prêmio palpitável."""
    tipo: str        # identificador interno (vai pro banco)
    titulo: str      # rótulo exibido na UI
    emoji: str       # decoração visual
    descricao: str   # texto curto explicando


# Ordem aqui é a ordem de exibição na tela.
PREMIOS: list[Premio] = [
    Premio(
        tipo="campeao",
        titulo="Seleção Campeã",
        emoji="🏆",
        descricao="Qual seleção vai levar a Copa?",
    ),
    Premio(
        tipo="craque",
        titulo="Craque da Copa",
        emoji="⭐",
        descricao="Melhor jogador da competição (Bola de Ouro).",
    ),
    Premio(
        tipo="artilheiro",
        titulo="Artilheiro",
        emoji="⚽",
        descricao="Quem vai marcar mais gols?",
    ),
    Premio(
        tipo="assistencia",
        titulo="Maior Assistente",
        emoji="👟",
        descricao="Quem vai dar mais assistências?",
    ),
    Premio(
        tipo="luva_de_ouro",
        titulo="Luva de Ouro",
        emoji="🧤",
        descricao="Melhor goleiro da competição.",
    ),
    Premio(
        tipo="jogador_jovem",
        titulo="Jogador Jovem",
        emoji="🧒",
        descricao="Melhor jogador sub-21 da Copa.",
    ),
]

# Lookup rápido por tipo (uso interno)
PREMIOS_POR_TIPO: dict[str, Premio] = {p.tipo: p for p in PREMIOS}


# -------------------------------------------------------------------
# Deadline
# -------------------------------------------------------------------
# Palpites de prêmio são aceitos até 0h do dia 14/06/2026 (Brasília),
# o que equivale a 23:59:59 do dia 13/06. Antes do primeiro fim de
# semana da Copa, portanto.

DEADLINE_DATA = date(2026, 6, 14)
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")


def deadline_premios() -> datetime:
    """Datetime do deadline (0h de 14/06/2026, Brasília)."""
    return datetime.combine(DEADLINE_DATA, time(0, 0, 0), tzinfo=TZ_BRASIL)


def palpite_premios_permitido(agora: datetime | None = None) -> bool:
    """True se ainda dá tempo de palpitar/editar prêmios."""
    if agora is None:
        agora = datetime.now(TZ_BRASIL)
    return agora < deadline_premios()


# -------------------------------------------------------------------
# Validação de texto livre
# -------------------------------------------------------------------

def normalizar_palpite(s: str) -> str:
    """Limpa espaços extras do palpite (mas mantém o texto original).
    O case e os acentos NÃO são alterados aqui - o usuário decide
    como escrever. A apuração depois cuidará da comparação."""
    return " ".join((s or "").split())


def palpite_valido(s: str) -> bool:
    """Aceita qualquer texto não-vazio com pelo menos 2 caracteres."""
    return len(normalizar_palpite(s)) >= 2