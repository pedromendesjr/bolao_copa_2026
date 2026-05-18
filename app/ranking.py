"""
ranking.py
==========
Cálculo do ranking agregado dos usuários, incluindo critérios de desempate.

Critérios de desempate na ordem:
    1. Maior número de PLACARES EXATOS (palpites com 18 pts)
    2. Maior número de VENCEDORES acertados (qualquer pontuação > 0
       em jogos onde o usuário acertou quem ganhou ou o empate)
    3. Ordem ALFABÉTICA do nome

Os palpites de partidas ainda não finalizadas são ignorados.
"""
from __future__ import annotations

from dataclasses import dataclass

from app import scoring


@dataclass
class LinhaRanking:
    posicao: int
    telefone: str
    nome: str
    pontos: int
    placares_exatos: int
    vencedores_acertados: int
    jogos_palpitados: int  # número de partidas finalizadas em que palpitou


def _eh_placar_exato(p: scoring.Pontuacao) -> bool:
    return p.pontos == 18


def _acertou_vencedor(p: scoring.Pontuacao) -> bool:
    """
    'Vencedor' aqui significa: o palpite acertou o desfecho do jogo
    (quem ganhou ou que foi empate). Qualquer pontuação ≥ 12 conta:
    - 18: placar exato → acertou o desfecho
    - 15: vencedor + 1 gol  → acertou o desfecho
    - 12: só vencedor OU empate → acertou o desfecho
    Pontuações 9, 3 e 0 não acertaram o desfecho (acertaram apenas
    quem avançou ou gols isolados).
    """
    return p.pontos >= 12


def calcular_ranking(
    usuarios: list[dict],
    partidas: list[dict],
    palpites: list[dict],
) -> list[LinhaRanking]:
    """
    Computa o ranking dos usuários a partir dos dados brutos do banco.

    Args:
        usuarios: lista de dicts {telefone, nome, ...}
        partidas: lista de dicts {id, fase, status, placar_a, placar_b, avanca, ...}
        palpites: lista de dicts {telefone, partida_id, placar_a, placar_b, avanca}

    Returns:
        Lista de LinhaRanking ordenada (posição 1 primeiro).
    """
    # Indexa partidas finalizadas por id
    partidas_finalizadas: dict[int, dict] = {
        p["id"]: p
        for p in partidas
        if p.get("status") == "finalizado" and p.get("placar_a") is not None
    }

    # Inicializa estatísticas zeradas para cada usuário
    stats: dict[str, dict] = {
        u["telefone"]: {
            "nome": u["nome"],
            "pontos": 0,
            "placares_exatos": 0,
            "vencedores_acertados": 0,
            "jogos_palpitados": 0,
        }
        for u in usuarios
    }

    # Itera pelos palpites somando estatísticas
    for palpite in palpites:
        tel = palpite["telefone"]
        if tel not in stats:
            continue  # palpite órfão (usuário removido?), ignora
        partida = partidas_finalizadas.get(palpite["partida_id"])
        if partida is None:
            continue  # jogo ainda não finalizado

        pont = scoring.calcular_pontuacao(
            palpite=scoring.Palpite(
                placar_a=palpite["placar_a"],
                placar_b=palpite["placar_b"],
                avanca=palpite.get("avanca"),
            ),
            resultado=scoring.Resultado(
                placar_a=partida["placar_a"],
                placar_b=partida["placar_b"],
                avanca=partida.get("avanca"),
            ),
            fase=partida["fase"],
        )

        stats[tel]["pontos"] += pont.pontos
        stats[tel]["jogos_palpitados"] += 1
        if _eh_placar_exato(pont):
            stats[tel]["placares_exatos"] += 1
        if _acertou_vencedor(pont):
            stats[tel]["vencedores_acertados"] += 1

    # Ordena pela tripla de critérios e atribui posição
    linhas_brutas = [
        {"telefone": tel, **s}
        for tel, s in stats.items()
    ]
    linhas_brutas.sort(
        key=lambda x: (
            -x["pontos"],
            -x["placares_exatos"],
            -x["vencedores_acertados"],
            x["nome"].lower(),
        )
    )

    return [
        LinhaRanking(
            posicao=i + 1,
            telefone=l["telefone"],
            nome=l["nome"],
            pontos=l["pontos"],
            placares_exatos=l["placares_exatos"],
            vencedores_acertados=l["vencedores_acertados"],
            jogos_palpitados=l["jogos_palpitados"],
        )
        for i, l in enumerate(linhas_brutas)
    ]
