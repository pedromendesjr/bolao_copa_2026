"""
scoring.py
==========
Lógica de pontuação do bolão. Funções puras (sem I/O), 100% testáveis.

Regras (excludente e hierárquica - sempre a faixa mais alta):

Fase de grupos:
    18 → placar exato
    15 → acertou vencedor e o número de gols de UM dos times
    12 → acertou apenas o vencedor (errando ambos os gols) OU acertou empate (não exato)
     3 → errou o resultado, mas acertou o número de gols de um dos times
     0 → caso contrário

Mata-mata, palpite EMPATE:
    18 → empate exato + acertou quem avançou
    15 → empate não exato + acertou quem avançou
    12 → empate exato + errou quem avançou
     9 → empate não exato + errou quem avançou
     3 → real foi vencedor, mas acertou quem avançou
     0 → caso contrário

Mata-mata, palpite com VENCEDOR:
    Aplicam-se as regras da fase de grupos. O campo "quem avança" é
    redundante com o palpite do vencedor. Casos especiais:
    - Real terminou empate (decidido nos pênaltis): se errou o placar
      mas acertou quem avançou, ganha 3 pontos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Cor = Literal["verde", "amarelo", "vermelho"]


@dataclass(frozen=True)
class Palpite:
    placar_a: int
    placar_b: int
    avanca: Optional[str] = None  # 'A' ou 'B'; só relevante no mata-mata com empate


@dataclass(frozen=True)
class Resultado:
    placar_a: int
    placar_b: int
    avanca: Optional[str] = None  # 'A' ou 'B'; quem efetivamente avançou no mata-mata


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
    return None  # empate


def _cor_pontos(p: int) -> Cor:
    if p >= 12:
        return "verde"
    if p > 0:
        return "amarelo"
    return "vermelho"


def _pont(pontos: int, motivo: str) -> Pontuacao:
    return Pontuacao(pontos=pontos, motivo=motivo, cor=_cor_pontos(pontos))


# -------------------------------------------------------------------
# Função principal
# -------------------------------------------------------------------

def calcular_pontuacao(
    palpite: Palpite,
    resultado: Resultado,
    fase: str,
) -> Pontuacao:
    """
    Calcula pontos do palpite contra o resultado oficial.

    Args:
        palpite: palpite do usuário.
        resultado: resultado oficial.
        fase: 'grupos' para a fase de grupos; qualquer outro valor
              ('r32', 'r16', 'quartas', 'semi', 'terceiro', 'final')
              é tratado como mata-mata.

    Returns:
        Pontuacao com pontos, motivo e cor para exibição.
    """
    eh_mata_mata = fase != "grupos"
    palpite_vencedor = _vencedor(palpite.placar_a, palpite.placar_b)
    real_vencedor = _vencedor(resultado.placar_a, resultado.placar_b)
    placar_exato = (
        palpite.placar_a == resultado.placar_a
        and palpite.placar_b == resultado.placar_b
    )
    acertou_gols_a = palpite.placar_a == resultado.placar_a
    acertou_gols_b = palpite.placar_b == resultado.placar_b
    acertou_algum_gol = acertou_gols_a or acertou_gols_b

    # ============================================================
    # MATA-MATA, palpite de EMPATE
    # ============================================================
    if eh_mata_mata and palpite_vencedor is None:
        acertou_avanca = palpite.avanca == resultado.avanca

        if placar_exato and acertou_avanca:
            return _pont(18, "Placar exato e acertou quem avançou")
        if real_vencedor is None and acertou_avanca:
            return _pont(15, "Acertou o empate e quem avançou")
        if placar_exato and not acertou_avanca:
            return _pont(12, "Placar exato, mas errou quem avançou")
        if real_vencedor is None and not acertou_avanca:
            return _pont(9, "Acertou o empate, mas errou quem avançou")
        # Real teve vencedor; palpite foi empate
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        return _pont(0, "Errou tudo")

    # ============================================================
    # MATA-MATA, palpite com VENCEDOR
    # (quem o palpite acha que avança = vencedor do palpite)
    # ============================================================
    if eh_mata_mata:
        if placar_exato:
            return _pont(18, "Placar exato")
        if palpite_vencedor == real_vencedor:  # acertou vencedor (real teve vencedor também)
            if acertou_algum_gol:
                return _pont(15, "Acertou o vencedor e o número de gols de um dos times")
            return _pont(12, "Acertou apenas o vencedor")
        # Errou o vencedor (ou real foi empate com decisão por pênaltis)
        acertou_avanca = palpite_vencedor == resultado.avanca
        if acertou_avanca:
            return _pont(3, "Acertou apenas quem avançou")
        if acertou_algum_gol:
            return _pont(3, "Acertou apenas o número de gols de um dos times")
        return _pont(0, "Errou tudo")

    # ============================================================
    # FASE DE GRUPOS
    # ============================================================
    if placar_exato:
        return _pont(18, "Placar exato")
    if palpite_vencedor == real_vencedor and real_vencedor is not None:
        if acertou_algum_gol:
            return _pont(15, "Acertou o vencedor e o número de gols de um dos times")
        return _pont(12, "Acertou apenas o vencedor")
    if palpite_vencedor is None and real_vencedor is None:
        # ambos empates, mas placar diferente (exato já tratado acima)
        return _pont(12, "Acertou o empate")
    # Errou o resultado
    if acertou_algum_gol:
        return _pont(3, "Acertou apenas o número de gols de um dos times")
    return _pont(0, "Errou tudo")
