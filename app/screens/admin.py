"""
screens/admin.py
================
Tela administrativa (protegida por PIN).

Funcionalidades:
    - Lançar/editar resultado oficial de partidas (fase de grupos e mata-mata)
    - Definir quem avançou (mata-mata)
    - Resetar a senha de um usuário
    - Gerar relatório de palpites do dia para copiar/colar no WhatsApp
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from app import auth, db, utils
from app.placar_parser import formatar_placar, parse_placar
from app.relatorio_palpites import (
    datas_com_partidas,
    gerar_relatorio_dia,
)


def render() -> None:
    st.title("⚙️ Administração")

    pin_configurado = utils.admin_pin()

    if pin_configurado is None:
        st.error(
            "⚠ Nenhum PIN administrativo está configurado. "
            "Defina `ADMIN_PIN` no `.env` (local) ou nos Secrets "
            "(Streamlit Cloud) e reinicie o app."
        )
        return

    pin_digitado = st.text_input("PIN administrativo", type="password")

    if not pin_digitado:
        st.caption("Digite o PIN administrativo para acessar.")
        return

    if pin_digitado.strip() != pin_configurado.strip():
        st.error("PIN incorreto.")
        return

    # ----- Acesso liberado -----
    usuario = auth.usuario_logado()
    st.success(f"Acesso liberado, {usuario['nome']}.")

    aba_resultados, aba_senhas, aba_palpites = st.tabs(
        ["📋 Lançar resultados", "🔑 Resetar senha", "📱 Palpites do dia"]
    )

    with aba_resultados:
        _aba_resultados()

    with aba_senhas:
        _aba_resetar_senha()

    with aba_palpites:
        _aba_palpites_do_dia()


# -------------------------------------------------------------------
# Aba: lançar resultados
# -------------------------------------------------------------------

def _aba_resultados() -> None:
    st.subheader("Lançar / editar resultado oficial")

    try:
        partidas = db.listar_partidas()
    except Exception as exc:
        st.error(f"Erro ao buscar partidas: {exc}")
        return

    partidas_validas = [
        p for p in partidas if p.get("time_a") and p.get("time_b")
    ]

    if not partidas_validas:
        st.info("Nenhuma partida com times definidos ainda.")
        return

    def _rotulo(p: dict) -> str:
        status_icone = "✅" if p["status"] == "finalizado" else "⏳"
        placar = ""
        if p["placar_a"] is not None and p["placar_b"] is not None:
            placar = f" [{p['placar_a']}x{p['placar_b']}]"
        return (
            f"{status_icone} M{p['numero']} · {p['time_a']} × {p['time_b']}"
            f"{placar}"
        )

    opcoes = {_rotulo(p): p for p in partidas_validas}
    rotulo_escolhido = st.selectbox(
        "Selecione a partida",
        options=list(opcoes.keys()),
    )
    partida = opcoes[rotulo_escolhido]

    eh_mata_mata = partida["fase"] != "grupos"

    if partida["placar_a"] is not None and partida["placar_b"] is not None:
        valor_atual = formatar_placar(partida["placar_a"], partida["placar_b"])
    else:
        valor_atual = ""

    with st.form("form_resultado"):
        st.markdown(
            f"**{partida['time_a']}** × **{partida['time_b']}**  \n"
            f"📅 {partida['data_jogo']} · Fase: {partida['fase']}"
        )

        placar_str = st.text_input(
            "Placar oficial (formato 2x1)",
            value=valor_atual,
            max_chars=5,
            placeholder="ex: 2x1",
        )

        avanca = None
        if eh_mata_mata:
            st.caption(
                "Jogo de mata-mata: indique quem avançou "
                "(usado quando o jogo termina empatado)."
            )
            escolha = st.radio(
                "Quem avançou?",
                options=[
                    f"{partida['time_a']} (A)",
                    f"{partida['time_b']} (B)",
                ],
                horizontal=True,
                index=None,
            )
            if escolha:
                avanca = "A" if escolha.endswith("(A)") else "B"

        col1, col2 = st.columns(2)
        salvar = col1.form_submit_button(
            "💾 Salvar resultado", type="primary", use_container_width=True
        )
        limpar = col2.form_submit_button(
            "↩ Reabrir (limpar resultado)", use_container_width=True
        )

    if salvar:
        resultado = parse_placar(placar_str)
        if resultado is None:
            st.error("Placar inválido. Use o formato 2x1.")
            return
        if eh_mata_mata and resultado[0] == resultado[1] and avanca is None:
            st.error(
                "Jogo de mata-mata empatado: você precisa indicar "
                "quem avançou."
            )
            return
        try:
            db.atualizar_resultado(
                partida_id=partida["id"],
                placar_a=resultado[0],
                placar_b=resultado[1],
                avanca=avanca,
            )
            st.success(
                f"✅ Resultado salvo: {partida['time_a']} "
                f"{resultado[0]} × {resultado[1]} {partida['time_b']}."
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Erro ao salvar: {exc}")

    if limpar:
        try:
            _reabrir_partida(partida["id"])
            st.success("Resultado limpo. A partida voltou a 'agendada'.")
            st.rerun()
        except Exception as exc:
            st.error(f"Erro ao reabrir: {exc}")


def _reabrir_partida(partida_id: int) -> None:
    """Limpa o resultado de uma partida (volta para 'agendado')."""
    client = db.get_client()
    client.table("partidas").update({
        "placar_a": None,
        "placar_b": None,
        "avanca": None,
        "status": "agendado",
    }).eq("id", partida_id).execute()
    db.listar_partidas.clear()


# -------------------------------------------------------------------
# Aba: resetar senha
# -------------------------------------------------------------------

def _aba_resetar_senha() -> None:
    st.subheader("Resetar senha de um participante")
    st.caption(
        "Use quando alguém esquecer o PIN de 4 dígitos. "
        "Defina uma senha temporária e avise a pessoa."
    )

    try:
        usuarios = db.listar_usuarios()
    except Exception as exc:
        st.error(f"Erro ao buscar usuários: {exc}")
        return

    if not usuarios:
        st.info("Nenhum participante cadastrado ainda.")
        return

    opcoes = {
        f"{u['nome']} · {u['telefone']}": u for u in sorted(
            usuarios, key=lambda x: x["nome"].lower()
        )
    }
    rotulo = st.selectbox("Participante", options=list(opcoes.keys()))
    usuario_sel = opcoes[rotulo]

    with st.form("form_senha"):
        nova = st.text_input(
            "Nova senha (4 dígitos)", max_chars=4, type="password"
        )
        confirmar = st.form_submit_button("🔑 Redefinir senha", type="primary")

    if confirmar:
        if not auth.senha_valida(nova):
            st.error("A senha deve ter exatamente 4 dígitos numéricos.")
            return
        try:
            db.resetar_senha(usuario_sel["telefone"], nova)
            st.success(
                f"✅ Senha de {usuario_sel['nome']} redefinida. "
                "Avise a pessoa da nova senha."
            )
        except Exception as exc:
            st.error(f"Erro ao redefinir: {exc}")


# -------------------------------------------------------------------
# Aba: palpites do dia (para WhatsApp)
# -------------------------------------------------------------------

def _aba_palpites_do_dia() -> None:
    st.subheader("Relatório de palpites do dia")
    st.caption(
        "Escolha uma data com jogos. O texto gerado pode ser copiado "
        "e colado no WhatsApp do grupo."
    )

    try:
        partidas = db.listar_partidas()
        usuarios = db.listar_usuarios()
        palpites = db.todos_palpites()
    except Exception as exc:
        st.error(f"Erro ao buscar dados: {exc}")
        return

    if not usuarios:
        st.info("Nenhum participante cadastrado ainda.")
        return

    datas = datas_com_partidas(partidas)
    if not datas:
        st.info("Nenhuma partida com times definidos.")
        return

    # Tenta pré-selecionar a data de hoje se houver jogos; senão, a primeira.
    hoje = date.today()
    index_default = 0
    if hoje in datas:
        index_default = datas.index(hoje)

    data_escolhida = st.selectbox(
        "Data",
        options=datas,
        index=index_default,
        format_func=lambda d: d.strftime("%d/%m/%Y (%a)"),
    )

    # Filtra partidas e palpites pela data escolhida.
    partidas_dia = [
        p for p in partidas
        if str(p["data_jogo"]) == data_escolhida.isoformat()
    ]
    ids_dia = {p["id"] for p in partidas_dia}
    palpites_dia = [p for p in palpites if p["partida_id"] in ids_dia]

    texto = gerar_relatorio_dia(
        data_jogo=data_escolhida,
        partidas=partidas_dia,
        palpites=palpites_dia,
        usuarios=usuarios,
    )

    # Calcula altura aproximada (linhas + folga).
    n_linhas = texto.count("\n") + 1
    altura = max(200, min(600, n_linhas * 22))

    st.text_area(
        "Texto pronto para copiar (use o ícone 📋 no canto superior direito)",
        value=texto,
        height=altura,
    )
