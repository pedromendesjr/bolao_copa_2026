"""
utils.py
========
Utilidades gerais: cálculo de deadline, formatação de datas, leitura
de configurações (com suporte a Streamlit Cloud e .env local).
"""
from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st


# -------------------------------------------------------------------
# Leitura de configurações
# -------------------------------------------------------------------
# Ordem de prioridade:
#   1. st.secrets (Streamlit Cloud)
#   2. variáveis de ambiente / .env (rodando localmente)

def ler_segredo(chave: str, default: str | None = None) -> str | None:
    """Lê um segredo. None ou default se não encontrar."""
    try:
        if chave in st.secrets:
            return st.secrets[chave]
    except Exception:
        # st.secrets pode levantar quando não há arquivo secrets.toml
        # localmente. Tudo bem - caímos no fallback.
        pass
    return os.environ.get(chave, default)


# -------------------------------------------------------------------
# Timezone / deadlines
# -------------------------------------------------------------------

def _tz() -> ZoneInfo:
    """Retorna o ZoneInfo configurado (default America/Sao_Paulo)."""
    nome = ler_segredo("TIMEZONE", "America/Sao_Paulo")
    return ZoneInfo(nome)


def deadline_palpite(data_jogo: date) -> datetime:
    """
    Deadline para palpite: meia-noite (0h) do dia do jogo, no fuso configurado.

    Exemplo: jogo em 20/06/2026 → deadline 20/06/2026 00:00:00 (horário Brasília).
    Isso significa que os palpites são aceitos até 23:59:59 do dia anterior.
    """
    return datetime.combine(data_jogo, time(0, 0, 0), tzinfo=_tz())


def palpite_permitido(data_jogo: date, agora: datetime | None = None) -> bool:
    """Retorna True se ainda é permitido palpitar nessa partida."""
    if agora is None:
        agora = datetime.now(_tz())
    return agora < deadline_palpite(data_jogo)


def formatar_data(d: date) -> str:
    """Retorna data em formato 'dd/mm (dia da semana)'."""
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    return f"{d.strftime('%d/%m')} ({dias[d.weekday()]})"


def somente_digitos(s: str) -> str:
    """Mantém só dígitos da string. Útil para normalizar telefone."""
    return "".join(c for c in s if c.isdigit())


def admin_pin() -> str | None:
    """Retorna o PIN do admin, ou None se não configurado."""
    pin = (ler_segredo("ADMIN_PIN") or "").strip()
    return pin if pin else None