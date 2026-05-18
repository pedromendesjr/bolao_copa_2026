"""
streamlit_app.py
================
Ponto de entrada da aplicação Streamlit.

Para rodar (a partir da raiz do projeto):
    streamlit run app/streamlit_app.py

Notas sobre o roteamento:
    - As "telas" estão em `app/screens/` (não `pages/`). Esse nome foi
      escolhido de propósito: se a pasta se chamar `pages/`, o Streamlit
      cria uma navegação automática a partir dos arquivos, que duplica
      o menu manual da sidebar. Mantendo `screens/`, a navegação é toda
      controlada por este arquivo.
"""
from __future__ import annotations

# -------------------------------------------------------------------
# Garante que a raiz do projeto esteja no sys.path para que
# `from app import ...` funcione independente de como o script é
# executado (CLI, Streamlit Cloud, etc.).
# -------------------------------------------------------------------
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app import auth
from app.screens import (
    admin,
    classificacao,
    login,
    palpites_grupos,
    palpites_mata_mata,
    regras,
)


# -------------------------------------------------------------------
# Configuração da página
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# Páginas disponíveis (label exibido -> função render)
# -------------------------------------------------------------------

PAGINAS_BASE = {
    "⚽ Palpites · Fase de grupos": palpites_grupos.render,
    "🏆 Palpites · Mata-mata":      palpites_mata_mata.render,
    "📊 Classificação geral":       classificacao.render,
    "📜 Regras de pontuação":       regras.render,
}

PAGINA_ADMIN = "⚙️ Administração"


# -------------------------------------------------------------------
# Roteamento baseado no estado de login
# -------------------------------------------------------------------

usuario = auth.usuario_logado()

if usuario is None:
    login.render()
else:
    paginas = dict(PAGINAS_BASE)
    if auth.eh_admin():
        paginas[PAGINA_ADMIN] = admin.render

    with st.sidebar:
        st.markdown(f"### 👤 {usuario['nome']}")
        st.caption(f"📱 {usuario['telefone']}")
        st.divider()

        pagina_escolhida = st.radio(
            "Navegação",
            options=list(paginas.keys()),
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            auth.fazer_logout()
            st.rerun()

    paginas[pagina_escolhida]()