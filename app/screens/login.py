"""
pages/login.py
==============
Tela de login e cadastro.

Fluxo:
1. Usuário digita o telefone (11 dígitos: DD9XXXXXXXX) e clica em Continuar.
2. Se o telefone já está cadastrado, mostramos o nome e pedimos a senha.
3. Se não está cadastrado, pedimos nome e senha (cria conta nova).
"""
from __future__ import annotations

import streamlit as st

from app import auth, db


# -------------------------------------------------------------------
# Estado intermediário da tela de login
# -------------------------------------------------------------------
# 'login_etapa': 'telefone' (inicial) ou 'senha' (após buscar)
# 'login_telefone': telefone digitado (já validado)
# 'login_usuario_existente': dict com usuário do banco ou None

def _reset_etapa() -> None:
    for k in ("login_etapa", "login_telefone", "login_usuario_existente"):
        if k in st.session_state:
            del st.session_state[k]


def render() -> None:
    st.title("⚽ Bolão da Copa do Mundo 2026")
    st.caption("Faça login ou cadastre-se para participar")

    etapa = st.session_state.get("login_etapa", "telefone")

    if etapa == "telefone":
        _render_etapa_telefone()
    elif etapa == "senha":
        _render_etapa_senha()


# -------------------------------------------------------------------
# Etapa 1: telefone
# -------------------------------------------------------------------

def _render_etapa_telefone() -> None:
    st.subheader("Identificação")
    st.markdown(
        "Digite seu **celular** no formato **DD9XXXXXXXX** "
        "(11 dígitos, sem espaços ou traços).  \n"
        "Exemplo: `47999998888`"
    )

    with st.form("form_telefone", clear_on_submit=False):
        telefone = st.text_input(
            "Celular",
            max_chars=11,
            placeholder="47999998888",
            key="input_telefone",
        )
        enviar = st.form_submit_button("Continuar", type="primary")

    if not enviar:
        return

    telefone = telefone.strip()
    if not auth.telefone_valido(telefone):
        st.error(
            "Telefone inválido. Use exatamente 11 dígitos no formato "
            "DD9XXXXXXXX."
        )
        return

    # Busca o usuário e avança para a etapa de senha
    try:
        usuario = db.buscar_usuario(telefone)
    except Exception as exc:
        st.error(f"Erro ao buscar usuário: {exc}")
        return

    st.session_state["login_telefone"] = telefone
    st.session_state["login_usuario_existente"] = usuario
    st.session_state["login_etapa"] = "senha"
    st.rerun()


# -------------------------------------------------------------------
# Etapa 2: senha (login se existente, cadastro completo se novo)
# -------------------------------------------------------------------

def _render_etapa_senha() -> None:
    telefone = st.session_state["login_telefone"]
    usuario = st.session_state["login_usuario_existente"]

    if usuario is not None:
        _form_login_existente(telefone, usuario)
    else:
        _form_cadastro_novo(telefone)

    st.divider()
    if st.button("← Usar outro telefone"):
        _reset_etapa()
        st.rerun()


def _form_login_existente(telefone: str, usuario: dict) -> None:
    st.subheader(f"Olá, {usuario['nome']}! 👋")
    st.caption(f"Telefone: {telefone}")
    st.markdown("Digite sua **senha** de 4 dígitos para entrar.")

    with st.form("form_login"):
        senha = st.text_input(
            "Senha (4 dígitos)",
            type="password",
            max_chars=4,
        )
        enviar = st.form_submit_button("Entrar", type="primary")

    if enviar:
        if not auth.senha_valida(senha):
            st.error("A senha deve ter exatamente 4 dígitos numéricos.")
            return
        ok, msg = auth.autenticar(telefone, senha)
        if ok:
            st.success(msg)
            _reset_etapa()
            st.rerun()
        else:
            st.error(msg)

    st.info(
        "🔑 **Esqueceu a senha?** Fale com o **Pedro (administrador)** "
        "para redefinir."
    )


def _form_cadastro_novo(telefone: str) -> None:
    st.subheader("Primeiro acesso 🆕")
    st.caption(f"Telefone: {telefone}")
    st.markdown(
        "Esse telefone ainda não está cadastrado. Vamos criar sua conta:"
    )

    with st.form("form_cadastro"):
        nome = st.text_input("Seu nome", max_chars=50)
        senha = st.text_input(
            "Crie uma senha de 4 dígitos",
            type="password",
            max_chars=4,
            help="Use 4 dígitos numéricos. Você usará essa senha para entrar.",
        )
        confirmar = st.text_input(
            "Confirme a senha",
            type="password",
            max_chars=4,
        )
        enviar = st.form_submit_button("Cadastrar e entrar", type="primary")

    if not enviar:
        return

    nome = nome.strip()
    if len(nome) < 2:
        st.error("Por favor, digite seu nome (pelo menos 2 caracteres).")
        return
    if not auth.senha_valida(senha):
        st.error("A senha deve ter exatamente 4 dígitos numéricos.")
        return
    if senha != confirmar:
        st.error("As senhas não coincidem.")
        return

    ok, msg = auth.cadastrar(telefone, nome, senha)
    if ok:
        st.success(msg)
        _reset_etapa()
        st.rerun()
    else:
        st.error(msg)
