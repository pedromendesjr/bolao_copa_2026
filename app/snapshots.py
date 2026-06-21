"""
app/snapshots.py
================
Snapshots históricos do ranking.

Importante: ao calcular ranking pro snapshot, o regramento correto
do bolão alvo é passado EXPLICITAMENTE (via `regras`), pra evitar que
o cálculo dependa do `bolao_id()` ambiente. Crucial no bootstrap,
que processa múltiplos bolões em sequência.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.db import get_client
from app.ranking import calcular_ranking
from app.scoring_helpers import regras_para_bolao
from app.utils import bolao_id


def _parse_data(d) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _todos_jogos_da_data_finalizados(data_jogo: date) -> bool:
    iso = data_jogo.isoformat()
    result = (
        get_client()
        .table("partidas")
        .select("id, status")
        .eq("data_jogo", iso)
        .execute()
    )
    if not result.data:
        return False
    return all(p["status"] == "finalizado" for p in result.data)


def _ranking_para_data(
    data_corte: date,
    usuarios: list[dict],
    partidas: list[dict],
    palpites: list[dict],
    regras: str,
) -> list:
    partidas_ate_data = [
        p for p in partidas
        if p["status"] == "finalizado"
        and _parse_data(p["data_jogo"]) <= data_corte
    ]
    ids_validos = {p["id"] for p in partidas_ate_data}
    palpites_filtrados = [p for p in palpites if p["partida_id"] in ids_validos]
    return calcular_ranking(
        usuarios, partidas_ate_data, palpites_filtrados, regras=regras
    )


def criar_snapshot(data_snapshot: date, bid: Optional[str] = None) -> int:
    """
    Cria/sobrescreve o snapshot do bolão para a data dada.
    O regramento aplicado é o do bolão alvo (não o do ambiente).
    """
    bid = bid or bolao_id()
    regras = regras_para_bolao(bid)
    client = get_client()

    usuarios = (
        client.table("usuarios").select("*").eq("bolao_id", bid).execute().data
    )
    if not usuarios:
        return 0

    partidas = client.table("partidas").select("*").execute().data
    palpites = (
        client.table("palpites").select("*").eq("bolao_id", bid).execute().data
    )

    linhas_ranking = _ranking_para_data(
        data_snapshot, usuarios, partidas, palpites, regras=regras
    )

    client.table("ranking_snapshots").delete().eq(
        "bolao_id", bid
    ).eq("data_snapshot", data_snapshot.isoformat()).execute()

    if not linhas_ranking:
        return 0

    registros = [
        {
            "bolao_id": bid,
            "telefone": linha.telefone,
            "data_snapshot": data_snapshot.isoformat(),
            "posicao": linha.posicao,
            "pontos": linha.pontos,
            "placares_exatos": linha.placares_exatos,
            "vencedores_acertados": linha.vencedores_acertados,
            "jogos_palpitados": linha.jogos_palpitados,
        }
        for linha in linhas_ranking
    ]
    client.table("ranking_snapshots").insert(registros).execute()
    return len(registros)


def criar_snapshot_se_dia_completo(data_jogo: date) -> Optional[int]:
    """Dispara snapshot em todos os bolões se o dia ficou completo."""
    if not _todos_jogos_da_data_finalizados(data_jogo):
        return None
    total = 0
    for bid in _listar_boloes_existentes():
        total += criar_snapshot(data_jogo, bid=bid)
    return total


def deletar_snapshot_da_data(
    data_snapshot: date, bid: Optional[str] = None
) -> int:
    """Apaga snapshot. Sem bid=None, apaga em todos os bolões."""
    client = get_client()
    iso = data_snapshot.isoformat()

    if bid is not None:
        result = (
            client.table("ranking_snapshots")
            .delete()
            .eq("bolao_id", bid)
            .eq("data_snapshot", iso)
            .execute()
        )
        return len(result.data) if result.data else 0

    total = 0
    for b in _listar_boloes_existentes():
        result = (
            client.table("ranking_snapshots")
            .delete()
            .eq("bolao_id", b)
            .eq("data_snapshot", iso)
            .execute()
        )
        total += len(result.data) if result.data else 0
    return total


def _listar_boloes_existentes() -> list[str]:
    result = get_client().table("usuarios").select("bolao_id").execute()
    return sorted({row["bolao_id"] for row in result.data})


def listar_snapshots() -> list[dict]:
    """Lista todos os snapshots do bolão atual."""
    return (
        get_client()
        .table("ranking_snapshots")
        .select("*")
        .eq("bolao_id", bolao_id())
        .order("data_snapshot")
        .order("posicao")
        .execute()
        .data
    )