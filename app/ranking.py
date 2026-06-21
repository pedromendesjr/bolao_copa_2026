"""
ranking.py
==========
Cálculo do ranking de pontuação dos participantes do bolão.

Critérios de desempate (em ordem):
    1. Maior número de placares exatos
    2. Maior número de vencedores acertados
    3. Ordem alfabética do nome
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.scoring import Palpite, Resultado
from app.scoring_helpers import pontuar


@dataclass(frozen=True)
class LinhaRanking:
    posicao: int
    nome: str
    telefone: str
    pontos: int
    placares_exatos: int
    vencedores_acertados: int
    jogos_palpitados: int


def _vencedor(a: int, b: int) -> str | None:
    if a > b:
        return "A"
    if b > a:
        return "B"
    return None


def calcular_ranking(
    usuarios: list[dict],
    partidas: list[dict],
    palpites: list[dict],
    regras: Optional[str] = None,
) -> list[LinhaRanking]:
    """
    Calcula o ranking final.

    Se `regras` é None (uso normal pelas telas), descobre via
    bolao_id() do ambiente. Se for passado ('padrao' ou 'cartola'),
    força aquele regramento - útil em scripts que processam múltiplos
    bolões.
    """
    partidas_por_id = {p["id"]: p for p in partidas}

    stats: dict[str, dict] = {
        u["telefone"]: {
            "nome": u["nome"],
            "telefone": u["telefone"],
            "pontos": 0,
            "placares_exatos": 0,
            "vencedores_acertados": 0,
            "jogos_palpitados": 0,
        }
        for u in usuarios
    }

    for palp in palpites:
        tel = palp["telefone"]
        if tel not in stats:
            continue

        partida = partidas_por_id.get(palp["partida_id"])
        if partida is None:
            continue
        if partida["status"] != "finalizado":
            continue
        if partida["placar_a"] is None or partida["placar_b"] is None:
            continue

        stats[tel]["jogos_palpitados"] += 1

        resultado = Resultado(
            placar_a=partida["placar_a"],
            placar_b=partida["placar_b"],
            avanca=partida.get("avanca"),
        )
        pal = Palpite(
            placar_a=palp["placar_a"],
            placar_b=palp["placar_b"],
            avanca=palp.get("avanca"),
        )
        pont = pontuar(pal, resultado, fase=partida["fase"], regras=regras)
        stats[tel]["pontos"] += pont.pontos

        if (palp["placar_a"] == partida["placar_a"]
                and palp["placar_b"] == partida["placar_b"]):
            stats[tel]["placares_exatos"] += 1

        vp = _vencedor(palp["placar_a"], palp["placar_b"])
        vr = _vencedor(partida["placar_a"], partida["placar_b"])
        if vp == vr:
            stats[tel]["vencedores_acertados"] += 1

    ordenados = sorted(
        stats.values(),
        key=lambda s: (
            -s["pontos"],
            -s["placares_exatos"],
            -s["vencedores_acertados"],
            s["nome"].lower(),
        ),
    )

    ranking: list[LinhaRanking] = []
    for i, s in enumerate(ordenados, start=1):
        ranking.append(LinhaRanking(
            posicao=i,
            nome=s["nome"],
            telefone=s["telefone"],
            pontos=s["pontos"],
            placares_exatos=s["placares_exatos"],
            vencedores_acertados=s["vencedores_acertados"],
            jogos_palpitados=s["jogos_palpitados"],
        ))
    return ranking