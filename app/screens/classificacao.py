"""
screens/classificacao.py
========================
Página de Classificação Geral. Tem duas seções:

1. **Tabela de pontuação** — listagem ordenada com critério de desempate.
   A pessoa com menor pontuação (lanterna 🔦) é movida para a última linha
   visual, deixando espaço em branco entre o pelotão e ela.

2. **Gráfico de evolução temporal** — linhas mostrando como a posição de
   cada participante mudou ao longo dos dias do bolão. Eixo X é "Dia 1,
   Dia 2..." (sequência de dias com snapshot), eixo Y é a posição
   (invertido, 1º em cima). Tooltip mostra a data real. Por padrão exibe
   apenas a linha do usuário logado, com toggle para mostrar todos.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import auth, db, snapshots as snapshots_mod, utils
from app.ranking import LinhaRanking, calcular_ranking


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

    # ---- Tabela ----
    df = _construir_dataframe(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True, height=563)

    minha_linha = next(
        (l for l in linhas if l.telefone == usuario["telefone"]),
        None,
    )
    if minha_linha is not None:
        st.info(
            f"📍 Você está em **{minha_linha.posicao}º lugar** "
            f"com **{minha_linha.pontos} pontos**."
        )

    st.divider()

    # ---- Gráfico de evolução ----
    _render_grafico_evolucao(linhas, usuario["telefone"])

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
# Tabela (lógica da lanterna)
# -------------------------------------------------------------------

def _construir_dataframe(linhas: list[LinhaRanking]) -> pd.DataFrame:
    if not linhas:
        return pd.DataFrame(columns=[
            "Pos", "Nome", "Pontos",
            "Placares exatos", "Vencedores", "Jogos",
        ])

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

    for l in nao_lanternas:
        registros.append(_registro(l, eh_lanterna=False))

    while len(registros) < LINHAS_VISUAIS - len(lanternas):
        registros.append({
            "Pos": "",
            "Nome": "",
            "Pontos": "",
            "Placares exatos": "",
            "Vencedores": "",
            "Jogos": "",
        })

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


# -------------------------------------------------------------------
# Gráfico de evolução
# -------------------------------------------------------------------

def _parse_data(d) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _render_grafico_evolucao(
    linhas_ranking: list[LinhaRanking],
    usuario_telefone: str,
) -> None:
    st.subheader("📈 Evolução do ranking")

    try:
        snapshots = snapshots_mod.listar_snapshots()
    except Exception as exc:
        st.error(f"Erro ao buscar histórico: {exc}")
        return

    if not snapshots:
        st.info(
            "Quando os primeiros dias de jogos terminarem, aqui aparecerá "
            "um gráfico mostrando como sua posição evoluiu ao longo do bolão."
        )
        return

    # Mapeamento telefone → nome (pra exibir no tooltip e legenda)
    nomes_por_telefone = {l.telefone: l.nome for l in linhas_ranking}

    # Datas únicas ordenadas → vira "Dia 1, Dia 2..."
    datas_unicas = sorted({
        _parse_data(s["data_snapshot"]) for s in snapshots
    })
    dia_label = {d: f"Dia {i + 1}" for i, d in enumerate(datas_unicas)}
    data_real_str = {d: d.strftime("%d/%m/%Y") for d in datas_unicas}

    # Toggle "só eu" / "todos"
    mostrar_todos = st.toggle(
        "Mostrar todos os participantes",
        value=False,
        help="Por padrão, só sua linha aparece. Ative para comparar com os demais.",
    )

    if not mostrar_todos:
        snapshots_uso = [
            s for s in snapshots if s["telefone"] == usuario_telefone
        ]
        if not snapshots_uso:
            st.info(
                "Você ainda não tem histórico registrado. Quando o primeiro "
                "dia de jogos do bolão terminar, sua linha aparecerá aqui."
            )
            return
    else:
        snapshots_uso = snapshots

    # Agrupa snapshots por participante
    por_pessoa: dict[str, list[tuple[date, int]]] = defaultdict(list)
    for s in snapshots_uso:
        d = _parse_data(s["data_snapshot"])
        por_pessoa[s["telefone"]].append((d, s["posicao"]))

    # Constrói as linhas do gráfico
    fig = go.Figure()

    # Ordena participantes alfabeticamente pra legenda ficar estável,
    # mas garantindo que o usuário logado entre por ÚLTIMO (linha por cima)
    telefones_ordenados = sorted(
        por_pessoa.keys(),
        key=lambda t: (
            t == usuario_telefone,  # False primeiro, True por último
            nomes_por_telefone.get(t, "").lower(),
        ),
    )

    for telefone in telefones_ordenados:
        pontos = sorted(por_pessoa[telefone], key=lambda x: x[0])
        nome = nomes_por_telefone.get(telefone, "?")
        eh_voce = telefone == usuario_telefone

        x = [dia_label[d] for d, _ in pontos]
        y = [pos for _, pos in pontos]
        custom = [data_real_str[d] for d, _ in pontos]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=f"⭐ {nome}" if eh_voce and mostrar_todos else nome,
            line=dict(
                width=4 if eh_voce else 2,
                color="#FF4B4B" if eh_voce else None,
            ),
            marker=dict(size=10 if eh_voce else 6),
            opacity=1.0 if eh_voce else 0.55,
            customdata=custom,
            hovertemplate=(
                f"<b>{nome}</b><br>"
                "Posição: %{y}º<br>"
                "Data: %{customdata}"
                "<extra></extra>"
            ),
        ))

    # Determina amplitude do eixo Y para dtick=1 (uma marca por posição)
    n_total = len(linhas_ranking) or 1

    fig.update_layout(
        yaxis=dict(
            title="Posição",
            autorange="reversed",
            dtick=1,
            range=[n_total + 0.5, 0.5],
        ),
        xaxis=dict(title=None),
        showlegend=mostrar_todos,
        margin=dict(l=20, r=20, t=10, b=20),
        height=420,
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)