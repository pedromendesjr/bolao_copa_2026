"""
scoring.py
==========
Lógica de pontuação do bolão. Funções puras (sem I/O), 100% testáveis.

Suporta DOIS conjuntos de regras:
    - "padrao"  → regras originais (bolão lavaprato / branch main)
    - "cartola" → regras do bolão cartola, mais favoráveis ao mata-mata

A função pública `calcular_pontuacao` recebe o nome do regramento como
parâmetro e despacha para a implementação correta. Os callsites passam
"padrao" ou "cartola" baseado em utils.bolao_id().

=============================================================
REGRAS PADRÃO (lavaprato / main)
=============================================================

Fase de grupos:
    18 → placar exato
    15 → vencedor + gols de UM dos times
    12 → vencedor (errando ambos) OU empate não-exato
     3 → errou resultado, mas acertou gols de um lado
     0 → caso contrário

Mata-mata, palpite EMPATE:
    18 → empate exato + acertou quem avançou
    15 → empate não-exato + acertou quem avançou
    12 → empate exato + errou quem avançou
     9 → empate não-exato + errou quem avançou
     3 → real teve vencedor, mas acertou quem passou
     0 → caso contrário

Mata-mata, palpite com VENCEDOR:
    Aplicam-se as regras da fase de grupos. Casos especiais:
    - Real terminou empate (pênaltis): se errou placar mas acertou quem
      avançou, ganha 3 pontos.

=============================================================
REGRAS CARTOLA
=============================================================

Fase de grupos:
    18 → placar exato                                    (igual)
    12 → vencedor + gols de UM dos times                 (era 15)
     9 → vencedor (errando ambos) OU empate não-exato    (era 12)
     3 → errou resultado, mas acertou gols de um lado    (igual)
     0 → caso contrário

Mata-mata, jogo real NÃO empatou (tempo normal teve vencedor):
    30 → placar exato
    21 → acertou vencedor + gols de um dos times
    15 → acertou apenas o vencedor
     3 → palpite empate, mas acertou quem passou OU acertou gols de um lado
     0 → caso contrário

Mata-mata, jogo real EMPATOU (foi pra pênaltis):
    34 → palpitou empate exato + acertou quem avançou nos pênaltis
    25 → palpitou empate exato + errou quem avançou
    22 → palpitou empate não-exato + acertou quem avançou
    15 → palpitou empate não-exato + errou quem avançou
     3 → palpitou vencedor, mas acertou quem passou OU acertou gols de um lado
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


# -------------------------------------------------------------------
# Helpers internos
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Função pública (despacha para a implementação certa)
# -------------------------------------------------------------------

def calcular_pontuacao(
    palpite: Palpite,
    resultado: Resultado,
    fase: str,
    regras: Regras = "padrao",
) -> Pontuacao:
    """
    Calcula pontos do palpite contra o resultado oficial.

    Args:
        palpite: palpite do usuário.
        resultado: resultado oficial.
        fase: 'grupos' ou uma das fases de mata-mata
              ('r32', 'r16', 'quartas', 'semi', 'terceiro', 'final').
        regras: 'padrao' (lavaprato/main) ou 'cartola'.
    """
    if regras == "cartola":
        return _calcular_cartola(palpite, resultado, fase)
    return _calcular_padrao(palpite, resultado, fase)


# -------------------------------------------------------------------
# REGRAS PADRÃO (lavaprato / main)
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

    # Mata-mata, palpite empate
    if eh_mata_mata and palpite_v is None:
        acertou_avanca = palpite.avanca == resultado.avanca
        if placar_exato and acertou_avanca:
            return _pont(18, "Placar exato e acertou quem avançou")
        if real_v is None and acertou_avanca:
            return _pont(15, "Acertou o empate e quem avançou")
        if placar_exato and not acertou_avanca:
            return _pont(12, "Placar exato, mas errou quem avançou")
        if real_v is None and not acertou_avanca:
            return _pont(9, "Acertou o empate, mas errou quem avançou")
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        return _pont(0, "Errou tudo")

    # Mata-mata, palpite com vencedor
    if eh_mata_mata:
        if placar_exato:
            return _pont(18, "Placar exato")
        if palpite_v == real_v:
            if acertou_algum_gol:
                return _pont(15, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(12, "Acertou apenas o vencedor")
        acertou_avanca = palpite_v == resultado.avanca
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    # Fase de grupos
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

    # ========== FASE DE GRUPOS ==========
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

    # ========== MATA-MATA ==========
    # Determina quem o palpite acha que passa e quem realmente passou.
    palpite_avanca = palpite_v if palpite_v is not None else palpite.avanca
    real_avanca = real_v if real_v is not None else resultado.avanca
    acertou_avanca = palpite_avanca == real_avanca

    # --- Palpite empate ---
    if palpite_v is None:
        if real_v is None:  # jogo terminou empate (foi pra pênaltis)
            if placar_exato and acertou_avanca:
                return _pont(34, "Placar exato e acertou quem avançou nos pênaltis")
            if placar_exato and not acertou_avanca:
                return _pont(25, "Placar exato, mas errou quem avançou nos pênaltis")
            if acertou_avanca:
                return _pont(22, "Acertou o empate e quem avançou nos pênaltis")
            return _pont(15, "Acertou o empate, mas errou quem avançou nos pênaltis")
        # Palpite empate, mas jogo real teve vencedor
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    # --- Palpite com vencedor ---
    if real_v is not None:  # jogo real teve vencedor
        if placar_exato:
            return _pont(30, "Placar exato")
        if palpite_v == real_v:
            if acertou_algum_gol:
                return _pont(21, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(15, "Acertou apenas o vencedor")
        # Palpite errou o vencedor
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    # Palpite com vencedor, mas jogo real foi empate (foi pra pênaltis)
    if acertou_avanca:
        return _pont(3, "Acertou apenas quem avançou (decidido nos pênaltis)")
    if acertou_algum_gol:
        return _pont(3, "Acertou apenas o número de gols de um dos times")
    return _pont(0, "Errou tudo")
