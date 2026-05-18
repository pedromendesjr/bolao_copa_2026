"""pages/admin.py - Em construção (Entrega 5)."""
import streamlit as st

from app import auth, utils


def render() -> None:
    st.title("⚙️ Administração")
    pin = st.text_input("PIN administrativo", type="password")
    if pin and pin == utils.admin_pin():
        usuario = auth.usuario_logado()
        st.success(f"Acesso liberado, {usuario['nome']}.")
        st.info(
            "🚧 Tela em construção. Será desenvolvida na **Entrega 5** "
            "(lançar resultados oficiais, definir quem avançou, "
            "liberar fase do mata-mata, resetar senhas)."
        )
    elif pin:
        st.error("PIN incorreto.")
    else:
        st.caption("Digite o PIN administrativo (definido no `.env`).")
