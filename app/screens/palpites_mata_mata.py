"""
screens/palpites_mata_mata.py
=============================
Tela de palpites do mata-mata (16-avos até a final).

Estrutura: abas por fase (16-avos, Oitavas, Quartas, Semis, 3º lugar, Final).
Cada jogo tem:
    - campo de placar (formato "2x1")
    - seletor de "quem avança" (sempre visível; só pontua em caso de empate)

Partidas sem times definidos (placeholders) aparecem como
"aguardando definição" e não são palpitáveis ainda. Conforme o admin
cadastra os times no banco, elas passam a aceitar palpites.

O deadline e a renderização de jogos finalizados seguem a mesma lógica
da fase de grupos.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from app import auth, db, utils
from app.placar_parser import formatar_placar, parse_placar
from app.scoring import Palpite, Pontuacao, Resultado, calcular_pontuacao

# Importa o dicionário de bandeiras já definido na tela de grupos
from app.screens.palpites_grupos import _bandeira_img, _parse_data


# Fases do mata-mata, na ordem, com rótulos amigáveis
FASES_MATA_MATA = [
    ("r32", "16-avos"),
    ("r16", "Oitavas"),
    ("quartas", "Quartas"),
    ("semi", "Semifinais"),
    ("terceiro", "3º lugar"),
    ("final", "Final"),
]

MSG_AVANCA = "Em caso de empate, quem você acredita que avançará:"


def _calcular_resultado(partida: dict) -> Resultado | None:
    if partida["status"] != "finalizado":
        return None
    if partida["placar_a"] is None or partida["placar_b"] is None:
        return None
    return Resultado(
        placar_a=partida["placar_a"],
        placar_b=partida["placar_b"],
        avanca=partida.get("avanca"),
    )


def _card_pontuacao(pont: Pontuacao, placar_a: int, placar_b: int,
                    avanca_real: str | None, time_a: str, time_b: str) -> None:
    cor_para_func = {
        "verde": st.success,
        "amarelo": st.warning,
        "vermelho": st.error,
    }
    texto_avanca = ""
    if avanca_real:
        nome = time_a if avanca_real == "A" else time_b
        texto_avanca = f"  \nAvançou: **{nome}**"
    cor_para_func[pont.cor](
        f"**{pont.pontos} pts** · {pont.motivo}  \n"
        f"Placar real: **{placar_a} × {placar_b}**{texto_avanca}"
    )


def _tem_times_definidos(partida: dict) -> bool:
    return bool(partida.get("time_a")) and bool(partida.get("time_b"))


def _renderizar_jogo_form(
    partida: dict,
    palpite_existente: dict | None,
    pode_editar: bool,
) -> tuple[int | None, int | None, str | None]:
    """
    Renderiza um jogo do mata-mata. Retorna (placar_a, placar_b, avanca).
    Retorna (None, None, ...) se placar em branco/inválido.
    """
    time_a = partida["time_a"]
    time_b = partida["time_b"]
    bandeira_a = _bandeira_img(time_a)
    bandeira_b = _bandeira_img(time_b)
    data_fmt = utils.formatar_data(_parse_data(partida["data_jogo"]))

    if palpite_existente:
        valor_default = formatar_placar(
            palpite_existente["placar_a"], palpite_existente["placar_b"]
        )
        avanca_default = palpite_existente.get("avanca")
    else:
        valor_default = ""
        avanca_default = None

    # Confronto em linha HTML única (não empilha no celular)
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; justify-content:center;
                    gap:8px; flex-wrap:nowrap; margin-bottom:4px;'>
            <span style='flex:1; text-align:right; font-weight:600;
                         line-height:1.2;'>{time_a}</span>
            {bandeira_a}
            <span style='opacity:0.6; font-weight:bold;'>×</span>
            {bandeira_b}
            <span style='flex:1; text-align:left; font-weight:600;
                         line-height:1.2;'>{time_b}</span>
        </div>
        <div style='text-align:center; font-size:0.75rem; opacity:0.6;
                    margin-bottom:2px;'>📅 {data_fmt}</div>
        """,
        unsafe_allow_html=True,
    )

    # Campo de placar centralizado
    _, col_meio, _ = st.columns([1, 1, 1])
    placar_str = col_meio.text_input(
        "Placar",
        value=valor_default,
        max_chars=5,
        key=f"placar_mm_{partida['id']}",
        label_visibility="collapsed",
        disabled=not pode_editar,
        placeholder="ex: 2x1",
    )

    # Seletor de quem avança (sempre visível, com aviso)
    st.caption(MSG_AVANCA)
    opcoes = [f"{time_a}", f"{time_b}"]
    idx_default = None
    if avanca_default == "A":
        idx_default = 0
    elif avanca_default == "B":
        idx_default = 1
    escolha = st.radio(
        "avanca",
        options=opcoes,
        index=idx_default,
        horizontal=True,
        key=f"avanca_mm_{partida['id']}",
        label_visibility="collapsed",
        disabled=not pode_editar,
    )
    avanca = None
    if escolha == time_a:
        avanca = "A"
    elif escolha == time_b:
        avanca = "B"

    resultado = parse_placar(placar_str)
    if resultado is None:
        if placar_str and placar_str.strip():
            col_meio.caption("⚠ formato inválido")
        return (None, None, avanca)
    return (resultado[0], resultado[1], avanca)


def _renderizar_jogo(
    partida: dict,
    palpite_existente: dict | None,
) -> tuple[int | None, int | None, str | None] | None:
    """
    Renderiza um jogo no modo apropriado. Retorna (pa, pb, avanca) se
    editável, None caso contrário.
    """
    resultado = _calcular_resultado(partida)
    palpite_permitido = utils.palpite_permitido(_parse_data(partida["data_jogo"]))

    if resultado is not None:
        _renderizar_jogo_form(partida, palpite_existente, pode_editar=False)
        if palpite_existente is not None:
            pont = calcular_pontuacao(
                Palpite(
                    placar_a=palpite_existente["placar_a"],
                    placar_b=palpite_existente["placar_b"],
                    avanca=palpite_existente.get("avanca"),
                ),
                resultado,
                fase=partida["fase"],
            )
            _card_pontuacao(
                pont, resultado.placar_a, resultado.placar_b,
                resultado.avanca, partida["time_a"], partida["time_b"],
            )
        else:
            st.info(
                f"Você não palpitou neste jogo. Placar real: "
                f"**{resultado.placar_a} × {resultado.placar_b}**"
            )
        return None

    if not palpite_permitido:
        _renderizar_jogo_form(partida, palpite_existente, pode_editar=False)
        if palpite_existente:
            av = palpite_existente.get("avanca")
            nome_av = ""
            if av:
                nome = partida["time_a"] if av == "A" else partida["time_b"]
                nome_av = f" · avança: {nome}"
            st.caption(
                f"⏰ Prazo encerrado · seu palpite: "
                f"**{palpite_existente['placar_a']} × "
                f"{palpite_existente['placar_b']}**{nome_av}"
            )
        else:
            st.caption("⏰ Prazo encerrado · você não palpitou neste jogo")
        return None

    return _renderizar_jogo_form(partida, palpite_existente, pode_editar=True)


# -------------------------------------------------------------------
# Render principal
# -------------------------------------------------------------------

def render() -> None:
    usuario = auth.usuario_logado()
    st.title("🏆 Palpites · Mata-mata")
    st.caption(f"Logado como **{usuario['nome']}**")

    st.markdown(
        """
        <style>
        div[data-testid="stTextInput"] input {
            text-align: center;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "💡 **Dicas:**  \n"
        "• Digite o placar no formato **2x1**.  \n"
        "• O campo *quem avança* só pontua em caso de **empate** no seu palpite.  \n"
        "• Cada fase tem um botão **Salvar** próprio.  \n"
        "• Palpites liberados até **0h (Brasília) do dia do jogo**."
    )

    try:
        partidas = db.listar_partidas()
    except Exception as exc:
        st.error(f"Erro ao buscar partidas: {exc}")
        return

    try:
        palpites = db.buscar_palpites_usuario(usuario["telefone"])
    except Exception as exc:
        st.error(f"Erro ao buscar palpites: {exc}")
        return

    palpites_por_partida = {p["partida_id"]: p for p in palpites}

    # Abas por fase do mata-mata
    rotulos = [rotulo for _, rotulo in FASES_MATA_MATA]
    abas = st.tabs(rotulos)

    for aba, (fase, rotulo) in zip(abas, FASES_MATA_MATA):
        with aba:
            partidas_fase = [p for p in partidas if p["fase"] == fase]
            _renderizar_aba_fase(
                fase=fase,
                rotulo=rotulo,
                partidas=partidas_fase,
                palpites_por_partida=palpites_por_partida,
                telefone=usuario["telefone"],
            )


def _renderizar_aba_fase(
    fase: str,
    rotulo: str,
    partidas: list[dict],
    palpites_por_partida: dict[int, dict],
    telefone: str,
) -> None:
    if not partidas:
        st.info(f"Nenhuma partida cadastrada para {rotulo} ainda.")
        return

    # Separa as que têm times definidos das que ainda são placeholders
    definidas = [p for p in partidas if _tem_times_definidos(p)]
    pendentes = [p for p in partidas if not _tem_times_definidos(p)]

    if not definidas:
        st.warning(
            f"🔒 Os confrontos de **{rotulo}** ainda não foram definidos. "
            "Esta fase será liberada quando os times forem cadastrados."
        )
        return

    with st.form(f"form_fase_{fase}", clear_on_submit=False):
        valores_novos: dict[int, tuple[int | None, int | None, str | None]] = {}

        for jogo in sorted(definidas, key=lambda j: j["numero"]):
            palp = palpites_por_partida.get(jogo["id"])
            valores = _renderizar_jogo(jogo, palp)
            if valores is not None:
                valores_novos[jogo["id"]] = valores
            st.divider()

        salvar = st.form_submit_button(
            f"💾 Salvar palpites · {rotulo}",
            type="primary",
            use_container_width=True,
        )

    # Aviso sobre partidas ainda não definidas nesta fase
    if pendentes:
        st.caption(
            f"⏳ {len(pendentes)} confronto(s) de {rotulo} ainda aguardando "
            "definição dos times."
        )

    if salvar:
        _salvar_palpites(telefone, valores_novos, palpites_por_partida)


def _salvar_palpites(
    telefone: str,
    valores_novos: dict[int, tuple[int | None, int | None, str | None]],
    palpites_existentes: dict[int, dict],
) -> None:
    salvos = 0
    invalidos = 0
    erros: list[str] = []

    for partida_id, (pa, pb, avanca) in valores_novos.items():
        if pa is None or pb is None:
            invalidos += 1
            continue
        # Em caso de empate, exige "quem avança"
        if pa == pb and avanca is None:
            invalidos += 1
            continue

        existente = palpites_existentes.get(partida_id)
        if existente is not None:
            if (existente["placar_a"] == pa
                    and existente["placar_b"] == pb
                    and existente.get("avanca") == avanca):
                continue
        try:
            db.salvar_palpite(
                telefone=telefone,
                partida_id=partida_id,
                placar_a=pa,
                placar_b=pb,
                avanca=avanca,
            )
            salvos += 1
        except Exception as exc:
            erros.append(f"Partida {partida_id}: {exc}")

    if salvos > 0:
        st.success(f"✅ {salvos} palpite(s) salvo(s) com sucesso.")
    elif not erros and invalidos == 0:
        st.info("Nenhuma alteração para salvar.")

    if invalidos > 0 and salvos == 0:
        st.warning(
            f"⚠ {invalidos} jogo(s) não salvos: placar em branco/inválido, "
            "ou empate sem indicar quem avança."
        )

    if erros:
        st.error("Alguns palpites não foram salvos:")
        for e in erros:
            st.write(f"- {e}")