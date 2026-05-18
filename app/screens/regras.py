"""
pages/regras.py
===============
Tela estática explicando o sistema de pontuação.
"""
import streamlit as st

from app import auth


def render() -> None:
    usuario = auth.usuario_logado()
    st.title("📜 Regras de pontuação")
    st.caption(f"Logado como **{usuario['nome']}**")

    st.markdown(
        """
        A pontuação é **excludente e hierárquica**: cada palpite cai em
        **uma única faixa**, sempre a mais alta que se encaixar.
        """
    )

    st.subheader("Fase de grupos")
    st.markdown(
        """
        | Pontos | Critério |
        |:------:|:---------|
        | 🟢 **18** | Placar exato |
        | 🟢 **15** | Acertou o vencedor e o número de gols de um dos times |
        | 🟢 **12** | Acertou apenas o vencedor (errando ambos os gols) **ou** acertou empate (não exato) |
        | 🟡 **3** | Errou o resultado, mas acertou o número de gols de um dos times |
        | 🔴 **0** | Demais casos |
        """
    )

    st.subheader("Mata-mata")
    st.markdown(
        """
        No mata-mata, além do placar, você palpita **quem avança** (relevante
        em caso de empate decidido nos pênaltis).

        - Se você palpitar um **vencedor**, valem as mesmas regras da fase
          de grupos (18 / 15 / 12 / 3 / 0). O campo "quem avança" fica
          implícito.
        - Se você palpitar **empate**, aplicam-se as regras abaixo:

        | Pontos | Critério (palpite de empate) |
        |:------:|:------------------------------|
        | 🟢 **18** | Empate exato **e** acertou quem avançou |
        | 🟢 **15** | Empate não exato **e** acertou quem avançou |
        | 🟢 **12** | Empate exato, mas errou quem avançou |
        | 🟡 **9** | Empate não exato e errou quem avançou |
        | 🟡 **3** | Real teve vencedor, mas você acertou quem avançou |
        | 🔴 **0** | Demais casos |
        """
    )

    st.subheader("Prazo dos palpites")
    st.markdown(
        """
        Os palpites para cada jogo são aceitos até **0h (meia-noite)
        do dia do jogo**, horário de Brasília.

        Exemplo: para um jogo no dia 20/06 às 15h, o prazo é até
        23:59:59 do dia **19/06**.
        """
    )

    st.subheader("Desempate no ranking")
    st.markdown(
        """
        Em caso de empate na pontuação total:
        1. Maior número de **placares exatos**
        2. Maior número de **vencedores acertados**
        3. Ordem **alfabética**
        """
    )
