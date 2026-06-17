"""
scoring_helpers.py
==================
Pequena ponte entre o módulo puro `scoring.py` (que recebe `regras` como
parâmetro) e os callsites do app (que precisam descobrir qual regramento
usar conforme o bolão atual).

Mantemos `scoring.py` puro para ser testável. Esta ponte tem I/O leve
(lê `utils.bolao_id()` que pode ler secrets).
"""
from __future__ import annotations

from app.scoring import Palpite, Pontuacao, Resultado, calcular_pontuacao
from app.utils import bolao_id


def regras_do_bolao_atual() -> str:
    """Retorna 'cartola' se o bolão atual é o cartola; senão 'padrao'."""
    return "cartola" if bolao_id() == "cartola" else "padrao"


def pontuar(palpite: Palpite, resultado: Resultado, fase: str) -> Pontuacao:
    """Calcula a pontuação usando o regramento do bolão atual."""
    return calcular_pontuacao(
        palpite, resultado, fase, regras=regras_do_bolao_atual()
    )
