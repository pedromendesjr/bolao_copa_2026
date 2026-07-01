"""
db.py
=====
Cliente Supabase e funções de acesso ao banco.

Nota sobre paginação:
    O PostgREST (usado pelo Supabase) limita cada query a 1000 linhas
    por padrão. Passando desse limite, os resultados são cortados
    silenciosamente. Para tabelas que crescem (palpites, principalmente),
    usamos `_paginate` que busca em lotes até esgotar.
"""
from __future__ import annotations

from typing import Callable, Optional

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

from app.utils import bolao_id, ler_segredo


load_dotenv()


TAMANHO_LOTE = 1000


# -------------------------------------------------------------------
# Cliente
# -------------------------------------------------------------------

@st.cache_resource
def get_client() -> Client:
    url = ler_segredo("SUPABASE_URL")
    key = ler_segredo("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_KEY não configurados. "
            "Localmente: confira seu .env. "
            "No deploy: configure em Settings → Secrets/Variables."
        )
    return create_client(url, key)


def _paginate(
    fabrica_query: Callable, tamanho_lote: int = TAMANHO_LOTE
) -> list[dict]:
    """
    Executa uma query em lotes, contornando o limite padrão do PostgREST.

    `fabrica_query` é uma função sem argumentos que retorna um query
    builder (com filtros já aplicados, mas SEM .range() ainda). É invocada
    a cada iteração para gerar uma nova query — necessário porque
    supabase-py não permite reusar o mesmo objeto múltiplas vezes.

    Exemplo:
        def todos_palpites():
            return _paginate(
                lambda: get_client()
                    .table("palpites")
                    .select("*")
                    .eq("bolao_id", bolao_id())
            )
    """
    resultados: list[dict] = []
    offset = 0
    while True:
        pagina = (
            fabrica_query()
            .range(offset, offset + tamanho_lote - 1)
            .execute()
            .data
        )
        if not pagina:
            break
        resultados.extend(pagina)
        if len(pagina) < tamanho_lote:
            break
        offset += tamanho_lote
    return resultados


# -------------------------------------------------------------------
# Usuários
# -------------------------------------------------------------------

def buscar_usuario(telefone: str) -> Optional[dict]:
    """Retorna o usuário (dict) do bolão atual, ou None se não existir."""
    result = (
        get_client()
        .table("usuarios")
        .select("*")
        .eq("bolao_id", bolao_id())
        .eq("telefone", telefone)
        .execute()
    )
    return result.data[0] if result.data else None


def criar_usuario(telefone: str, nome: str, senha: str) -> dict:
    result = (
        get_client()
        .table("usuarios")
        .insert({
            "bolao_id": bolao_id(),
            "telefone": telefone,
            "nome": nome,
            "senha": senha,
        })
        .execute()
    )
    return result.data[0]


def validar_senha(telefone: str, senha: str) -> bool:
    usuario = buscar_usuario(telefone)
    return usuario is not None and usuario.get("senha") == senha


def resetar_senha(telefone: str, nova_senha: str) -> dict:
    result = (
        get_client()
        .table("usuarios")
        .update({"senha": nova_senha})
        .eq("bolao_id", bolao_id())
        .eq("telefone", telefone)
        .execute()
    )
    return result.data[0]


def listar_usuarios() -> list[dict]:
    """Lista todos os usuários do bolão atual (paginado)."""
    return _paginate(
        lambda: get_client()
            .table("usuarios")
            .select("*")
            .eq("bolao_id", bolao_id())
    )


# -------------------------------------------------------------------
# Partidas
# -------------------------------------------------------------------

@st.cache_data(ttl=60)
def listar_partidas(
    fase: Optional[str] = None,
    grupo: Optional[str] = None,
) -> list[dict]:
    """Lista partidas com filtros opcionais. Cacheia por 60s."""
    def fabrica():
        q = get_client().table("partidas").select("*")
        if fase:
            q = q.eq("fase", fase)
        if grupo:
            q = q.eq("grupo", grupo)
        return q.order("numero")

    return _paginate(fabrica)


def buscar_partida(partida_id: int) -> Optional[dict]:
    result = (
        get_client()
        .table("partidas")
        .select("*")
        .eq("id", partida_id)
        .execute()
    )
    return result.data[0] if result.data else None


def atualizar_resultado(
    partida_id: int,
    placar_a: int,
    placar_b: int,
    avanca: Optional[str] = None,
) -> dict:
    result = (
        get_client()
        .table("partidas")
        .update({
            "placar_a": placar_a,
            "placar_b": placar_b,
            "avanca": avanca,
            "status": "finalizado",
        })
        .eq("id", partida_id)
        .execute()
    )
    listar_partidas.clear()

    # Dispara snapshot se todos os jogos da data finalizaram (best-effort).
    try:
        from app.snapshots import (
            _parse_data,
            criar_snapshot_se_dia_completo,
        )
        partida_atualizada = result.data[0]
        data_jogo = _parse_data(partida_atualizada["data_jogo"])
        criar_snapshot_se_dia_completo(data_jogo)
    except Exception as exc:
        import logging
        logging.warning("Falha ao gerar snapshot: %s", exc)

    return result.data[0]


# -------------------------------------------------------------------
# Palpites
# -------------------------------------------------------------------

def buscar_palpites_usuario(telefone: str) -> list[dict]:
    """Palpites de um usuário no bolão atual (paginado)."""
    return _paginate(
        lambda: get_client()
            .table("palpites")
            .select("*")
            .eq("bolao_id", bolao_id())
            .eq("telefone", telefone)
    )


def buscar_palpites_partida(partida_id: int) -> list[dict]:
    """Palpites de uma partida no bolão atual (paginado)."""
    return _paginate(
        lambda: get_client()
            .table("palpites")
            .select("*")
            .eq("bolao_id", bolao_id())
            .eq("partida_id", partida_id)
    )


def salvar_palpite(
    telefone: str,
    partida_id: int,
    placar_a: int,
    placar_b: int,
    avanca: Optional[str] = None,
) -> dict:
    payload = {
        "bolao_id": bolao_id(),
        "telefone": telefone,
        "partida_id": partida_id,
        "placar_a": placar_a,
        "placar_b": placar_b,
        "avanca": avanca,
    }
    result = (
        get_client()
        .table("palpites")
        .upsert(payload, on_conflict="bolao_id,telefone,partida_id")
        .execute()
    )
    return result.data[0]


def todos_palpites() -> list[dict]:
    """
    Retorna TODOS os palpites do bolão atual (paginado).

    Usado por ranking, admin (relatório do dia), e snapshots.
    A paginação é ESSENCIAL: com ~11 participantes × 104 jogos = ~1144
    palpites, sem paginação os últimos ~144 seriam cortados
    silenciosamente pelo limite padrão do PostgREST.
    """
    return _paginate(
        lambda: get_client()
            .table("palpites")
            .select("*")
            .eq("bolao_id", bolao_id())
    )