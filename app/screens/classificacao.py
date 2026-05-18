"""
pages/classificacao.py
======================
Tela do ranking geral com pontuação e critérios de desempate.

Exibe:
    - Ranking completo (posição, nome, pontos, exatos, vencedores, jogos)
    - Destaque visual na linha do usuário logado
    - Explicação dos critérios de desempate
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app import auth, db, ranking


def render() -> None:
    usuario = auth.usuario_logado()
    st.title("🏆 Classificação Geral")
    st.caption(f"Logado como **{usuario['nome']}**")

    try:
        usuarios = db.listar_usuarios()
        partidas = db.listar_partidas()
        palpites = db.todos_palpites()
    except Exception as exc:
        st.error(f"Erro ao carregar dados: {exc}")
        return

    if not usuarios:
        st.info("Ainda não há usuários cadastrados.")
        return

    linhas = ranking.calcular_ranking(usuarios, partidas, palpites)

    # Métricas no topo
    finalizadas = sum(
        1 for p in partidas
        if p.get("status") == "finalizado" and p.get("placar_a") is not None
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Participantes", len(linhas))
    col2.metric("Partidas finalizadas", f"{finalizadas} / {len(partidas)}")
    if linhas:
        col3.metric("Líder", f"{linhas[0].nome} ({linhas[0].pontos} pts)")

    st.divider()

    # Monta o dataframe para exibição (sem personalização de cor para
    # respeitar tanto o tema claro quanto o escuro).
    df = pd.DataFrame([
        {
            "Pos": l.posicao,
            "Nome": l.nome,
            "Pontos": l.pontos,
            "Placares exatos": l.placares_exatos,
            "Vencedores": l.vencedores_acertados,
            "Jogos": l.jogos_palpitados,
        }
        for l in linhas
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Posição do usuário em destaque (caso ele não veja logo)
    minha_linha = next((l for l in linhas if l.telefone == usuario["telefone"]), None)
    if minha_linha:
        st.info(
            f"📍 Você está em **{minha_linha.posicao}º lugar** "
            f"com **{minha_linha.pontos} pontos** "
            f"({minha_linha.placares_exatos} placar(es) exato(s), "
            f"{minha_linha.vencedores_acertados} vencedor(es))."
        )

    st.divider()

    # Explicação dos critérios de desempate
    with st.expander("📜 Como funcionam os critérios de desempate"):
        st.markdown(
            """
            Em caso de empate na pontuação total, a ordem é decidida por:

            1. **Placares exatos** — quem tiver mais palpites com 18 pontos
               (placar exato cravado) fica à frente.
            2. **Vencedores acertados** — entre os ainda empatados, quem
               acertou o desfecho de mais jogos (vencedor correto ou
               empate quando o jogo foi empate) fica à frente.
            3. **Ordem alfabética** — se persistir o empate, ordena pelo
               nome.

            > **Observação:** "vencedor acertado" significa acertar o
            > desfecho do jogo (vitória A, vitória B ou empate). Inclui
            > qualquer palpite que valha 12 pontos ou mais.

            ### Sobre as colunas

            - **Pontos**: soma de todos os palpites em partidas finalizadas.
            - **Placares exatos**: quantidade de palpites com 18 pontos.
            - **Vencedores**: quantidade de palpites em que acertou o
              desfecho (≥ 12 pontos).
            - **Jogos**: número de jogos finalizados em que palpitou.

            Apenas partidas **finalizadas** entram no cálculo.
            """
        )