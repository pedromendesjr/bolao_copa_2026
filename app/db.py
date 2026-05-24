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

from app.utils import bolao_id, ler_segredo


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
# Todas as operações de usuário são escopadas pelo bolão atual
# (utils.bolao_id()), lido dos secrets/.env do deploy.

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
    """Cria um novo usuário no bolão atual e retorna o registro."""
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
    """Confere se o telefone existe no bolão atual e a senha bate."""
    usuario = buscar_usuario(telefone)
    return usuario is not None and usuario.get("senha") == senha


def resetar_senha(telefone: str, nova_senha: str) -> dict:
    """Atualiza a senha de um usuário do bolão atual (tela admin)."""
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
    """Lista todos os usuários do bolão atual."""
    return (
        get_client()
        .table("usuarios")
        .select("*")
        .eq("bolao_id", bolao_id())
        .execute()
        .data
    )


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
# Todas as operações são escopadas pelo bolão atual (utils.bolao_id()).

def buscar_palpites_usuario(telefone: str) -> list[dict]:
    """Lista todos os palpites de um usuário no bolão atual."""
    result = (
        get_client()
        .table("palpites")
        .select("*")
        .eq("bolao_id", bolao_id())
        .eq("telefone", telefone)
        .execute()
    )
    return result.data


def buscar_palpites_partida(partida_id: int) -> list[dict]:
    """Lista palpites de uma partida no bolão atual (admin/ranking)."""
    result = (
        get_client()
        .table("palpites")
        .select("*")
        .eq("bolao_id", bolao_id())
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
    """Insere ou atualiza um palpite no bolão atual (upsert pela PK composta)."""
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
    """Retorna todos os palpites do bolão atual (uso pelo ranking)."""
    return (
        get_client()
        .table("palpites")
        .select("*")
        .eq("bolao_id", bolao_id())
        .execute()
        .data
    )
    