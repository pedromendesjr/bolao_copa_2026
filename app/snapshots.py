"""
app/snapshots.py
================
Snapshots históricos do ranking. Cada snapshot guarda a posição e os
pontos de cada participante ao final de um dia que teve jogos.

Gatilhos:
    - Quando o admin lança um resultado E todos os jogos da data daquela
      partida estão finalizados, dispara `criar_snapshot_se_dia_completo`.
    - Quando o admin reabre uma partida (limpa resultado), dispara
      `deletar_snapshot_da_data` para invalidar o snapshot daquele dia.
      (Ele será recriado quando todos voltarem a ficar finalizados.)

Modo "histórico" do bootstrap:
    O script `scripts/bootstrap_snapshots.py` reconstrói os snapshots
    de dias passados simulando "quais jogos estavam finalizados ao
    fim de cada data". Reutiliza `_calcular_ranking_para_data` daqui.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.db import get_client
from app.ranking import calcular_ranking
from app.utils import bolao_id


def _parse_data(d) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _todos_jogos_da_data_finalizados(data_jogo: date) -> bool:
    """True se TODAS as partidas com aquela data estão finalizadas."""
    iso = data_jogo.isoformat()
    result = (
        get_client()
        .table("partidas")
        .select("id, status")
        .eq("data_jogo", iso)
        .execute()
    )
    if not result.data:
        return False  # nenhum jogo naquela data
    return all(p["status"] == "finalizado" for p in result.data)


def _ranking_para_data(
    data_corte: date,
    usuarios: list[dict],
    partidas: list[dict],
    palpites: list[dict],
) -> list:
    """
    Calcula o ranking considerando APENAS jogos com data_jogo <= data_corte
    E que estejam finalizados.
    """
    partidas_ate_data = [
        p for p in partidas
        if p["status"] == "finalizado"
        and _parse_data(p["data_jogo"]) <= data_corte
    ]
    ids_validos = {p["id"] for p in partidas_ate_data}
    palpites_filtrados = [p for p in palpites if p["partida_id"] in ids_validos]

    return calcular_ranking(usuarios, partidas_ate_data, palpites_filtrados)


def criar_snapshot(data_snapshot: date, bid: Optional[str] = None) -> int:
    """
    Cria/sobrescreve o snapshot do bolão para a data dada.
    Retorna o número de linhas inseridas.
    """
    bid = bid or bolao_id()
    client = get_client()

    # Coleta dados do bolão
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
        data_snapshot, usuarios, partidas, palpites
    )

    # Apaga snapshot anterior dessa data (se existir) antes de gravar.
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
    """
    Cria snapshot em TODOS os bolões SE todos os jogos do dia estão
    finalizados.

    Chamado depois de cada lançamento de resultado. Como resultados são
    compartilhados entre bolões (tabela `partidas` é única), o gatilho
    dispara o snapshot em todos os bolões existentes, garantindo histórico
    coerente sem depender de qual app fez o lançamento.

    Retorna a soma de linhas inseridas em todos os bolões, ou None se
    o gatilho não foi atingido.
    """
    if not _todos_jogos_da_data_finalizados(data_jogo):
        return None

    total = 0
    for bid in _listar_boloes_existentes():
        total += criar_snapshot(data_jogo, bid=bid)
    return total


def _listar_boloes_existentes() -> list[str]:
    """Lista os bolao_id distintos presentes na tabela usuarios."""
    result = (
        get_client()
        .table("usuarios")
        .select("bolao_id")
        .execute()
    )
    return sorted({row["bolao_id"] for row in result.data})


def deletar_snapshot_da_data(data_snapshot: date, bid: Optional[str] = None) -> int:
    """
    Remove o snapshot de uma data específica.

    Se `bid` é None (caso padrão, quando chamado pelo gatilho do admin ao
    reabrir uma partida): deleta em TODOS os bolões existentes, já que
    resultados são compartilhados.

    Se `bid` é fornecido (uso interno/programático): deleta só naquele bolão.

    Retorna o total de linhas removidas.
    """
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


def listar_snapshots() -> list[dict]:
    """Lista todos os snapshots do bolão atual (uso do gráfico)."""
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