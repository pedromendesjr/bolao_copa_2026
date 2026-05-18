"""
auth.py
=======
Gerenciamento de sessão e autenticação.

Usa st.session_state com as chaves:
    - usuario_telefone: str | None
    - usuario_nome: str | None
"""
from __future__ import annotations

import re
from typing import Optional

import streamlit as st

from app import db


# -------------------------------------------------------------------
# Validações
# -------------------------------------------------------------------

TELEFONE_REGEX = re.compile(r"^\d{11}$")
SENHA_REGEX = re.compile(r"^\d{4}$")


def telefone_valido(t: str) -> bool:
    return bool(TELEFONE_REGEX.match(t))


def senha_valida(s: str) -> bool:
    return bool(SENHA_REGEX.match(s))


def nome_valido(s: str) -> bool:
    """Aceita qualquer nome com pelo menos 2 caracteres úteis (após strip)."""
    return len(s.strip()) >= 2


# -------------------------------------------------------------------
# Sessão
# -------------------------------------------------------------------

def usuario_logado() -> Optional[dict]:
    """Retorna {'telefone': ..., 'nome': ...} se houver sessão, senão None."""
    tel = st.session_state.get("usuario_telefone")
    nome = st.session_state.get("usuario_nome")
    if tel and nome:
        return {"telefone": tel, "nome": nome}
    return None


def fazer_login(telefone: str, nome: str) -> None:
    """Grava telefone e nome em session_state."""
    st.session_state["usuario_telefone"] = telefone
    st.session_state["usuario_nome"] = nome


def fazer_logout() -> None:
    """Limpa a sessão do usuário."""
    for k in ("usuario_telefone", "usuario_nome"):
        if k in st.session_state:
            del st.session_state[k]


# -------------------------------------------------------------------
# Operações de login/cadastro
# -------------------------------------------------------------------

def autenticar(telefone: str, senha: str) -> tuple[bool, str]:
    """
    Tenta autenticar usuário existente.
    Retorna (ok, mensagem). Em caso de sucesso, já grava a sessão.
    """
    usuario = db.buscar_usuario(telefone)
    if usuario is None:
        return False, "Usuário não encontrado."
    if usuario.get("senha") != senha:
        return False, "Senha incorreta."
    fazer_login(telefone, usuario["nome"])
    return True, f"Bem-vindo, {usuario['nome']}!"


def cadastrar(telefone: str, nome: str, senha: str) -> tuple[bool, str]:
    """
    Cria novo usuário. Retorna (ok, mensagem).
    Em caso de sucesso, já grava a sessão.
    """
    if db.buscar_usuario(telefone) is not None:
        return False, "Esse telefone já está cadastrado."
    try:
        db.criar_usuario(telefone, nome.strip(), senha)
    except Exception as exc:
        return False, f"Erro ao cadastrar: {exc}"
    fazer_login(telefone, nome.strip())
    return True, f"Cadastro realizado, {nome.strip()}!"


# -------------------------------------------------------------------
# Admin
# -------------------------------------------------------------------

def eh_admin() -> bool:
    """True se o usuário logado é o admin (telefone configurado em ADMIN_TELEFONE)."""
    from app.utils import ler_segredo
    usuario = usuario_logado()
    if not usuario:
        return False
    admin_phone = (ler_segredo("ADMIN_TELEFONE") or "").strip()
    return bool(admin_phone) and usuario["telefone"] == admin_phone