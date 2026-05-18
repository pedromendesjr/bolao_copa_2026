"""pages/palpites_mata_mata.py - Em construção (Entrega 3)."""
import streamlit as st

from app import auth


def render() -> None:
    usuario = auth.usuario_logado()
    st.title("Palpites · Mata-mata")
    st.caption(f"Logado como **{usuario['nome']}**")
    st.warning(
        "🔒 Esta fase ficará disponível apenas após o término da fase de grupos."
    )
    st.info(
        "🚧 Tela em construção. Será desenvolvida na **Entrega 3**."
    )
