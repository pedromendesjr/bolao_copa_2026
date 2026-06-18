"""
screens/classificacao.py
========================
Página de Classificação Geral. Lista todos os participantes do bolão
ordenados por pontos, com critérios de desempate.

Detalhe visual: quem está em último lugar (pior pontuação) ganha um
emoji 🔦 (lanterna) antes do nome E é movido para o fim da tabela,
deixando linhas em branco entre o pelotão e a lanterna. A coluna "Pos"
mostra a posição real, não a linha visual.

Casos cobertos:
    - Se todos estão empatados (ex: início da Copa, todos com 0 pts),
      ninguém é marcado como lanterna (não faria sentido).
    - Se várias pessoas empatam na pior pontuação, todas viram lanterna
      e ficam juntas no fim da tabela.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app import auth, db, utils
from app.ranking import LinhaRanking, calcular_ranking


# Quantidade fixa de linhas visuais da tabela. Mantém a aparência
# consistente independente do número de participantes.
LINHAS_VISUAIS = 15
LANTERNA = "🔦"


def render() -> None:
    usuario = auth.usuario_logado()
    st.title("📊 Classificação Geral")
    st.caption(f"Bolão: **{utils.bolao_id()}**")

    try:
        usuarios = db.listar_usuarios()
        partidas = db.listar_partidas()
        palpites = db.todos_palpites()
    except Exception as exc:
        st.error(f"Erro ao buscar dados: {exc}")
        return

    if not usuarios:
        st.info("Nenhum participante cadastrado ainda.")
        return

    linhas = calcular_ranking(usuarios, partidas, palpites)

    # ---- Métricas do topo ----
    finalizadas = sum(1 for p in partidas if p["status"] == "finalizado")
    lider_nome = linhas[0].nome if linhas else "—"
    lider_pts = linhas[0].pontos if linhas else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Participantes", len(linhas))
    col2.metric("Partidas finalizadas", finalizadas)
    col3.metric("Líder", lider_nome, f"{lider_pts} pts")

    st.divider()

    # ---- Construção da tabela ----
    df = _construir_dataframe(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True, height=563)

    # ---- Balão "você está em Nº" ----
    minha_linha = next(
        (l for l in linhas if l.telefone == usuario["telefone"]),
        None,
    )
    if minha_linha is not None:
        st.info(
            f"📍 Você está em **{minha_linha.posicao}º lugar** "
            f"com **{minha_linha.pontos} pontos**."
        )

    # ---- Critérios de desempate ----
    with st.expander("ℹ️ Critérios de desempate"):
        st.markdown(
            """
            Em caso de empate na pontuação, a ordem é definida por:
            1. Maior número de **placares exatos**
            2. Maior número de **vencedores acertados**
            3. Ordem alfabética do nome
            """
        )


# -------------------------------------------------------------------
# Construção do DataFrame com lógica da lanterna
# -------------------------------------------------------------------

def _construir_dataframe(linhas: list[LinhaRanking]) -> pd.DataFrame:
    if not linhas:
        return pd.DataFrame(columns=[
            "Pos", "Nome", "Pontos",
            "Placares exatos", "Vencedores", "Jogos",
        ])

    # Decide se faz sentido ter lanterna nesta classificação.
    # Não faz sentido se todos têm a mesma pontuação (ex: 0 no começo).
    pior = min(l.pontos for l in linhas)
    melhor = max(l.pontos for l in linhas)
    tem_lanterna = pior != melhor

    if tem_lanterna:
        lanternas = [l for l in linhas if l.pontos == pior]
        nao_lanternas = [l for l in linhas if l.pontos != pior]
    else:
        lanternas = []
        nao_lanternas = list(linhas)

    registros: list[dict] = []

    # 1. Pelotão normal nas primeiras linhas
    for l in nao_lanternas:
        registros.append(_registro(l, eh_lanterna=False))

    # 2. Linhas em branco até abrir espaço para as lanternas no fim
    while len(registros) < LINHAS_VISUAIS - len(lanternas):
        registros.append({
            "Pos": "",
            "Nome": "",
            "Pontos": "",
            "Placares exatos": "",
            "Vencedores": "",
            "Jogos": "",
        })

    # 3. Lanterna(s) no fim, com 🔦 antes do nome e Pos real
    for l in lanternas:
        registros.append(_registro(l, eh_lanterna=True))

    return pd.DataFrame(registros)


def _registro(linha: LinhaRanking, eh_lanterna: bool) -> dict:
    nome = f"{LANTERNA} {linha.nome}" if eh_lanterna else linha.nome
    return {
        "Pos": linha.posicao,
        "Nome": nome,
        "Pontos": linha.pontos,
        "Placares exatos": linha.placares_exatos,
        "Vencedores": linha.vencedores_acertados,
        "Jogos": linha.jogos_palpitados,
    }