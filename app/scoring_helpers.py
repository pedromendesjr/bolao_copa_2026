"""
scoring_helpers.py
==================
Pequena ponte entre o módulo puro `scoring.py` e os callsites do app.

Tem duas formas de descobrir o regramento:
    1. `pontuar(palpite, resultado, fase)` (sem parâmetro `regras`):
       descobre automaticamente pelo `bolao_id()` do ambiente (lê secrets).
       Uso normal: pelas telas do app.

    2. `pontuar(palpite, resultado, fase, regras="cartola")` (com parâmetro):
       força o regramento. Uso: scripts que processam múltiplos bolões
       (ex: bootstrap de snapshots) onde o `bolao_id()` ambiente é fixo
       mas precisamos calcular pra cada bolão separadamente.
"""
from __future__ import annotations

from typing import Optional

from app.scoring import Palpite, Pontuacao, Resultado, calcular_pontuacao
from app.utils import bolao_id


def regras_para_bolao(bid: str) -> str:
    """Retorna 'cartola' ou 'padrao' baseado no id do bolão."""
    return "cartola" if bid == "cartola" else "padrao"


def regras_do_bolao_atual() -> str:
    """Retorna o regramento do bolão atual (lido de bolao_id())."""
    return regras_para_bolao(bolao_id())


def pontuar(
    palpite: Palpite,
    resultado: Resultado,
    fase: str,
    regras: Optional[str] = None,
) -> Pontuacao:
    """
    Calcula a pontuação. Se `regras` não é passado, usa o regramento
    do bolão atual (lido de bolao_id()).
    """
    if regras is None:
        regras = regras_do_bolao_atual()
    return calcular_pontuacao(palpite, resultado, fase, regras=regras)