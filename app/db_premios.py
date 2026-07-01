"""
app/db_premios.py
=================
Acesso ao Supabase para a tabela `premios_palpites`.
Todas as operações são escopadas pelo bolão atual (utils.bolao_id()).

Usa `_paginate` de `db.py` para contornar o limite padrão do PostgREST.
"""
from __future__ import annotations

from app.db import _paginate, get_client
from app.utils import bolao_id


def buscar_palpites_premios(telefone: str) -> dict[str, str]:
    """Dict {tipo_premio: palpite} do usuário no bolão atual."""
    result = (
        get_client()
        .table("premios_palpites")
        .select("tipo_premio, palpite")
        .eq("bolao_id", bolao_id())
        .eq("telefone", telefone)
        .execute()
    )
    return {row["tipo_premio"]: row["palpite"] for row in result.data}


def salvar_palpite_premio(
    telefone: str,
    tipo_premio: str,
    palpite: str,
) -> dict:
    payload = {
        "bolao_id": bolao_id(),
        "telefone": telefone,
        "tipo_premio": tipo_premio,
        "palpite": palpite,
    }
    result = (
        get_client()
        .table("premios_palpites")
        .upsert(payload, on_conflict="bolao_id,telefone,tipo_premio")
        .execute()
    )
    return result.data[0]


def listar_todos_palpites_premios() -> list[dict]:
    """TODOS os palpites de prêmio do bolão atual (paginado)."""
    return _paginate(
        lambda: get_client()
            .table("premios_palpites")
            .select("*")
            .eq("bolao_id", bolao_id())
    )