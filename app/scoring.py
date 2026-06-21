"""
scoring.py
==========
Lógica de pontuação do bolão. Funções puras (sem I/O), 100% testáveis.

Suporta DOIS conjuntos de regras:
    - "padrao"  → regras do bolão lavaprato
    - "cartola" → regras do bolão cartola

=============================================================
REGRAS PADRÃO (lavaprato)
=============================================================

Fase de grupos:
    18 → placar exato
    15 → vencedor + gols de UM dos times
    12 → vencedor (errando ambos) OU empate não-exato
     3 → errou resultado, mas acertou gols de um lado
     0 → caso contrário

Mata-mata, jogo real NÃO empatou (vencedor em 120 min):
    25 → placar exato
    20 → acertou vencedor + gols de um dos times
    15 → acertou apenas o vencedor
     3 → palpite empate, mas acertou quem passou
     0 → caso contrário

Mata-mata, jogo real EMPATOU (decidido nos pênaltis):
    27 → empate exato + acertou quem ganhou nos pênaltis
    22 → empate exato + errou quem ganhou nos pênaltis
    18 → empate não-exato + acertou quem ganhou nos pênaltis
    15 → empate não-exato + errou quem ganhou nos pênaltis
     3 → palpite com vencedor, mas acertou quem ganhou nos pênaltis
     0 → caso contrário

=============================================================
REGRAS CARTOLA
=============================================================

Fase de grupos:
    18 → placar exato
    12 → vencedor + gols de UM dos times
     9 → vencedor (errando ambos) OU empate não-exato
     3 → errou resultado, mas acertou gols de um lado
     0 → caso contrário

Mata-mata, jogo real NÃO empatou (vencedor em 120 min):
    30 → placar exato
    21 → acertou vencedor + gols de um dos times
    15 → acertou apenas o vencedor
     3 → palpite empate, mas acertou quem passou OU gols de um lado
     0 → caso contrário

Mata-mata, jogo real EMPATOU (decidido nos pênaltis):
    34 → empate exato + acertou quem avançou
    25 → empate exato + errou quem avançou
    22 → empate não-exato + acertou quem avançou
    15 → empate não-exato + errou quem avançou
     3 → palpite com vencedor, mas acertou quem passou OU gols de um lado
     0 → caso contrário
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Cor = Literal["verde", "amarelo", "vermelho"]
Regras = Literal["padrao", "cartola"]


@dataclass(frozen=True)
class Palpite:
    placar_a: int
    placar_b: int
    avanca: Optional[str] = None


@dataclass(frozen=True)
class Resultado:
    placar_a: int
    placar_b: int
    avanca: Optional[str] = None


@dataclass(frozen=True)
class Pontuacao:
    pontos: int
    motivo: str
    cor: Cor


def _vencedor(placar_a: int, placar_b: int) -> Optional[str]:
    if placar_a > placar_b:
        return "A"
    if placar_b > placar_a:
        return "B"
    return None


def _cor_pontos(p: int) -> Cor:
    if p >= 12:
        return "verde"
    if p > 0:
        return "amarelo"
    return "vermelho"


def _pont(pontos: int, motivo: str) -> Pontuacao:
    return Pontuacao(pontos=pontos, motivo=motivo, cor=_cor_pontos(pontos))


def calcular_pontuacao(
    palpite: Palpite,
    resultado: Resultado,
    fase: str,
    regras: Regras = "padrao",
) -> Pontuacao:
    if regras == "cartola":
        return _calcular_cartola(palpite, resultado, fase)
    return _calcular_padrao(palpite, resultado, fase)


# -------------------------------------------------------------------
# REGRAS PADRÃO (lavaprato)
# -------------------------------------------------------------------

def _calcular_padrao(
    palpite: Palpite, resultado: Resultado, fase: str
) -> Pontuacao:
    eh_mata_mata = fase != "grupos"
    palpite_v = _vencedor(palpite.placar_a, palpite.placar_b)
    real_v = _vencedor(resultado.placar_a, resultado.placar_b)
    placar_exato = (
        palpite.placar_a == resultado.placar_a
        and palpite.placar_b == resultado.placar_b
    )
    acertou_algum_gol = (
        palpite.placar_a == resultado.placar_a
        or palpite.placar_b == resultado.placar_b
    )

    # ===== FASE DE GRUPOS (sem mudança) =====
    if not eh_mata_mata:
        if placar_exato:
            return _pont(18, "Placar exato")
        if palpite_v == real_v and real_v is not None:
            if acertou_algum_gol:
                return _pont(15, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(12, "Acertou apenas o vencedor")
        if palpite_v is None and real_v is None:
            return _pont(12, "Acertou o empate")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    # ===== MATA-MATA (regras novas) =====
    palpite_avanca = palpite_v if palpite_v is not None else palpite.avanca
    real_avanca = real_v if real_v is not None else resultado.avanca
    acertou_avanca = palpite_avanca == real_avanca

    # --- Palpite com EMPATE ---
    if palpite_v is None:
        if real_v is None:  # jogo terminou empate (pênaltis)
            if placar_exato and acertou_avanca:
                return _pont(27, "Placar exato e acertou quem ganhou nos pênaltis")
            if placar_exato and not acertou_avanca:
                return _pont(22, "Placar exato, mas errou quem ganhou nos pênaltis")
            if acertou_avanca:
                return _pont(18, "Acertou o empate e quem ganhou nos pênaltis")
            return _pont(15, "Acertou o empate, mas errou quem ganhou nos pênaltis")
        # Palpitou empate, mas jogo real teve vencedor
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        return _pont(0, "Errou tudo")

    # --- Palpite com VENCEDOR ---
    if real_v is not None:  # jogo real teve vencedor
        if placar_exato:
            return _pont(25, "Placar exato")
        if palpite_v == real_v:
            if acertou_algum_gol:
                return _pont(20, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(15, "Acertou apenas o vencedor")
        return _pont(0, "Errou tudo")

    # Palpite com vencedor, mas jogo real foi empate (pênaltis)
    if acertou_avanca:
        return _pont(3, "Acertou apenas quem ganhou nos pênaltis")
    return _pont(0, "Errou tudo")


# -------------------------------------------------------------------
# REGRAS CARTOLA
# -------------------------------------------------------------------

def _calcular_cartola(
    palpite: Palpite, resultado: Resultado, fase: str
) -> Pontuacao:
    eh_mata_mata = fase != "grupos"
    palpite_v = _vencedor(palpite.placar_a, palpite.placar_b)
    real_v = _vencedor(resultado.placar_a, resultado.placar_b)
    placar_exato = (
        palpite.placar_a == resultado.placar_a
        and palpite.placar_b == resultado.placar_b
    )
    acertou_algum_gol = (
        palpite.placar_a == resultado.placar_a
        or palpite.placar_b == resultado.placar_b
    )

    if not eh_mata_mata:
        if placar_exato:
            return _pont(18, "Placar exato")
        if palpite_v == real_v and real_v is not None:
            if acertou_algum_gol:
                return _pont(12, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(9, "Acertou apenas o vencedor")
        if palpite_v is None and real_v is None:
            return _pont(9, "Acertou o empate")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    palpite_avanca = palpite_v if palpite_v is not None else palpite.avanca
    real_avanca = real_v if real_v is not None else resultado.avanca
    acertou_avanca = palpite_avanca == real_avanca

    if palpite_v is None:
        if real_v is None:
            if placar_exato and acertou_avanca:
                return _pont(34, "Placar exato e acertou quem avançou nos pênaltis")
            if placar_exato and not acertou_avanca:
                return _pont(25, "Placar exato, mas errou quem avançou nos pênaltis")
            if acertou_avanca:
                return _pont(22, "Acertou o empate e quem avançou nos pênaltis")
            return _pont(15, "Acertou o empate, mas errou quem avançou nos pênaltis")
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    if real_v is not None:
        if placar_exato:
            return _pont(30, "Placar exato")
        if palpite_v == real_v:
            if acertou_algum_gol:
                return _pont(21, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(15, "Acertou apenas o vencedor")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    if acertou_avanca:
        return _pont(3, "Acertou apenas quem avançou (decidido nos pênaltis)")
    if acertou_algum_gol:
        return _pont(3, "Acertou apenas o número de gols de um dos times")
    return _pont(0, "Errou tudo")