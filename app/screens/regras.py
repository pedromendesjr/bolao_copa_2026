"""
screens/regras.py
=================
Tela estática explicando as regras de pontuação. O conteúdo muda
conforme o bolão atual (lavaprato/padrão vs cartola).
"""
from __future__ import annotations

import streamlit as st

from app import utils
from app.scoring_helpers import regras_do_bolao_atual


def render() -> None:
    st.title("📜 Regras de Pontuação")

    regras = regras_do_bolao_atual()
    st.caption(f"Bolão: **{utils.bolao_id()}** · "
               f"Regramento: **{regras}**")

    if regras == "cartola":
        _renderizar_cartola()
    else:
        _renderizar_padrao()

    st.divider()
    _renderizar_comuns()


# -------------------------------------------------------------------
# REGRAS PADRÃO (lavaprato / main)
# -------------------------------------------------------------------

def _renderizar_padrao() -> None:
    st.subheader("Fase de grupos")
    st.markdown(
        """
        | Pontos | Critério |
        |---:|---|
        | **18** | Placar exato |
        | **15** | Acertou vencedor e número de gols de um dos times |
        | **12** | Acertou vencedor (errando ambos os gols) **ou** empate não-exato |
        | **3** | Errou o resultado, mas acertou número de gols de um dos times |
        | **0** | Demais casos |
        """
    )

    st.subheader("Mata-mata · palpite com VENCEDOR")
    st.markdown(
        """
        Aplicam-se as mesmas regras da fase de grupos (18/15/12/3).
        O campo "quem avança" é ignorado pois já está implícito no vencedor.

        **Caso especial:** se o jogo termina empatado e vai para os pênaltis,
        e você errou o placar mas acertou quem avançou, ganha **3 pontos**.
        """
    )

    st.subheader("Mata-mata · palpite EMPATE")
    st.markdown(
        """
        | Pontos | Critério |
        |---:|---|
        | **18** | Placar exato + acertou quem avançou |
        | **15** | Empate não-exato + acertou quem avançou |
        | **12** | Placar exato + errou quem avançou |
        | **9** | Empate não-exato + errou quem avançou |
        | **3** | Real teve vencedor, mas você acertou quem passou |
        | **0** | Demais casos |
        """
    )


# -------------------------------------------------------------------
# REGRAS CARTOLA
# -------------------------------------------------------------------

def _renderizar_cartola() -> None:
    st.subheader("Fase de grupos")
    st.markdown(
        """
        | Pontos | Critério |
        |---:|---|
        | **18** | Placar exato |
        | **12** | Acertou vencedor e número de gols de um dos times |
        | **9** | Acertou vencedor (errando ambos os gols) **ou** empate não-exato |
        | **3** | Errou o resultado, mas acertou número de gols de um dos times |
        | **0** | Demais casos |
        """
    )

    st.subheader("Mata-mata · jogo termina no tempo normal (com vencedor)")
    st.markdown(
        """
        | Pontos | Critério |
        |---:|---|
        | **30** | Placar exato |
        | **21** | Acertou vencedor e número de gols de um dos times |
        | **15** | Acertou apenas o vencedor |
        | **3** | Palpite empate, mas acertou quem passou (ou acertou gols de um lado) |
        | **0** | Demais casos |
        """
    )

    st.subheader("Mata-mata · jogo termina empatado (decidido nos pênaltis)")
    st.markdown(
        """
        | Pontos | Critério |
        |---:|---|
        | **34** | Empate exato + acertou quem avançou nos pênaltis |
        | **25** | Empate exato + errou quem avançou nos pênaltis |
        | **22** | Empate não-exato + acertou quem avançou |
        | **15** | Empate não-exato + errou quem avançou |
        | **3** | Palpite com vencedor, mas acertou quem passou (ou acertou gols de um lado) |
        | **0** | Demais casos |
        """
    )

    st.info(
        "💡 No mata-mata, em caso de empate **você precisa selecionar** "
        "quem você acha que avança nos pênaltis ao fazer o palpite."
    )


# -------------------------------------------------------------------
# Seção comum (vale pros dois bolões)
# -------------------------------------------------------------------

def _renderizar_comuns() -> None:
    st.subheader("Prazo dos palpites")
    st.markdown(
        "Você pode editar seus palpites até **meio-dia (12h, horário de Brasília) "
        "do dia do jogo**. Depois disso o palpite trava."
    )

    st.subheader("Critério de desempate no ranking")
    st.markdown(
        """
        1. Maior número de **placares exatos**
        2. Maior número de **vencedores acertados**
        3. Ordem alfabética do nome
        """
    )
