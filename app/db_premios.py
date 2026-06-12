"""
app/db_premios.py
=================
Funções de acesso ao Supabase para a tabela `premios_palpites`.
Mantido separado de db.py para não inflar o módulo principal.

Todas as operações são escopadas pelo bolão atual (utils.bolao_id()).
"""
from __future__ import annotations

from app.db import get_client
from app.utils import bolao_id


def buscar_palpites_premios(telefone: str) -> dict[str, str]:
    """
    Retorna um dict {tipo_premio: palpite} com os palpites do usuário
    no bolão atual. Tipos sem palpite simplesmente não aparecem no dict.
    """
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
    """Insere ou atualiza um palpite de prêmio (upsert pela PK composta)."""
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
    """Retorna todos os palpites de prêmio do bolão atual (uso pelo admin)."""
    return (
        get_client()
        .table("premios_palpites")
        .select("*")
        .eq("bolao_id", bolao_id())
        .execute()
        .data
    )