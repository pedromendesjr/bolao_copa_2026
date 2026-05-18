"""
db.py
=====
Cliente Supabase e funções de acesso ao banco. Toda I/O acontece aqui.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

from app.utils import ler_segredo


# Carrega variáveis do .env uma única vez quando o módulo é importado
load_dotenv()


# -------------------------------------------------------------------
# Cliente
# -------------------------------------------------------------------

@st.cache_resource
def get_client() -> Client:
    """
    Retorna o cliente Supabase, criado uma única vez por sessão.

    Lê credenciais com a seguinte ordem de prioridade:
        1. st.secrets (Streamlit Cloud)
        2. variáveis de ambiente / .env (rodando localmente)
    """
    url = ler_segredo("SUPABASE_URL")
    key = ler_segredo("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_KEY não configurados. "
            "Localmente: confira seu arquivo .env. "
            "No Streamlit Cloud: configure em Settings → Secrets."
        )
    return create_client(url, key)


# -------------------------------------------------------------------
# Usuários
# -------------------------------------------------------------------

def buscar_usuario(telefone: str) -> Optional[dict]:
    """Retorna o usuário (dict) ou None se não existir."""
    result = (
        get_client()
        .table("usuarios")
        .select("*")
        .eq("telefone", telefone)
        .execute()
    )
    return result.data[0] if result.data else None


def criar_usuario(telefone: str, nome: str, senha: str) -> dict:
    """Cria um novo usuário e retorna o registro inserido."""
    result = (
        get_client()
        .table("usuarios")
        .insert({"telefone": telefone, "nome": nome, "senha": senha})
        .execute()
    )
    return result.data[0]


def validar_senha(telefone: str, senha: str) -> bool:
    """Confere se o telefone existe e a senha bate."""
    usuario = buscar_usuario(telefone)
    return usuario is not None and usuario.get("senha") == senha


def resetar_senha(telefone: str, nova_senha: str) -> dict:
    """Atualiza a senha de um usuário (usado pela tela admin)."""
    result = (
        get_client()
        .table("usuarios")
        .update({"senha": nova_senha})
        .eq("telefone", telefone)
        .execute()
    )
    return result.data[0]


def listar_usuarios() -> list[dict]:
    """Lista todos os usuários cadastrados."""
    return get_client().table("usuarios").select("*").execute().data


# -------------------------------------------------------------------
# Partidas
# -------------------------------------------------------------------

@st.cache_data(ttl=60)
def listar_partidas(
    fase: Optional[str] = None,
    grupo: Optional[str] = None,
) -> list[dict]:
    """
    Lista partidas com filtros opcionais. Resultados cacheados por 60s
    para não martelar o banco a cada reload do Streamlit.
    """
    query = get_client().table("partidas").select("*")
    if fase:
        query = query.eq("fase", fase)
    if grupo:
        query = query.eq("grupo", grupo)
    result = query.order("numero").execute()
    return result.data


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
    """Lança o resultado oficial de uma partida (uso administrativo)."""
    payload = {
        "placar_a": placar_a,
        "placar_b": placar_b,
        "status": "finalizado",
    }
    if avanca is not None:
        payload["avanca"] = avanca
    result = (
        get_client()
        .table("partidas")
        .update(payload)
        .eq("id", partida_id)
        .execute()
    )
    # Invalida o cache para refletir a mudança imediatamente
    listar_partidas.clear()
    return result.data[0]


# -------------------------------------------------------------------
# Palpites
# -------------------------------------------------------------------

def buscar_palpites_usuario(telefone: str) -> list[dict]:
    """Lista todos os palpites de um usuário."""
    result = (
        get_client()
        .table("palpites")
        .select("*")
        .eq("telefone", telefone)
        .execute()
    )
    return result.data


def buscar_palpites_partida(partida_id: int) -> list[dict]:
    """Lista todos os palpites de uma partida (uso administrativo/ranking)."""
    result = (
        get_client()
        .table("palpites")
        .select("*")
        .eq("partida_id", partida_id)
        .execute()
    )
    return result.data


def salvar_palpite(
    telefone: str,
    partida_id: int,
    placar_a: int,
    placar_b: int,
    avanca: Optional[str] = None,
) -> dict:
    """Insere ou atualiza um palpite (upsert pela PK composta)."""
    payload = {
        "telefone": telefone,
        "partida_id": partida_id,
        "placar_a": placar_a,
        "placar_b": placar_b,
        "avanca": avanca,
    }
    result = (
        get_client()
        .table("palpites")
        .upsert(payload, on_conflict="telefone,partida_id")
        .execute()
    )
    return result.data[0]


def todos_palpites() -> list[dict]:
    """Retorna todos os palpites de todos os usuários (uso pelo ranking)."""
    return get_client().table("palpites").select("*").execute().data