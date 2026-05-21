"""
pages/palpites_grupos.py
========================
Tela de palpites da fase de grupos.

Layout: abas por grupo (A-L). Dentro de cada aba, os 6 jogos do grupo
aparecem agrupados por rodada (1, 2, 3), dentro de um único st.form
com um botão "Salvar palpites deste grupo" no rodapé.

Lógica de exibição de cada jogo:
    - Jogo finalizado (placar oficial lançado): mostra inputs desabilitados
      com o palpite registrado, mais um card colorido (verde/amarelo/vermelho)
      com a pontuação obtida e o motivo.
    - Deadline expirado mas sem resultado oficial: inputs desabilitados,
      aviso "Prazo encerrado, aguardando o jogo".
    - Antes do deadline: inputs habilitados, pre-preenchidos com palpite
      salvo (se existir).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import streamlit as st

from app import auth, db, utils
from app.placar_parser import formatar_placar, parse_placar
from app.scoring import Palpite, Pontuacao, Resultado, calcular_pontuacao


GRUPOS_FASE = list("ABCDEFGHIJKL")

# Mapeamento país → código ISO 3166-1 alpha-2 (formato do flagcdn).
# Para Escócia e Inglaterra, usamos códigos especiais suportados pelo CDN
# (`gb-sct` e `gb-eng`), que renderizam as bandeiras das nações britânicas.
CODIGO_PAIS: dict[str, str] = {
    "México": "mx", "África do Sul": "za", "Coreia do Sul": "kr",
    "República Tcheca": "cz", "Canadá": "ca", "Bósnia e Herzegovina": "ba",
    "Catar": "qa", "Suíça": "ch", "Brasil": "br", "Marrocos": "ma",
    "Haiti": "ht", "Escócia": "gb-sct", "Estados Unidos": "us",
    "Paraguai": "py", "Austrália": "au", "Turquia": "tr",
    "Alemanha": "de", "Curaçao": "cw", "Costa do Marfim": "ci",
    "Equador": "ec", "Holanda": "nl", "Japão": "jp", "Suécia": "se",
    "Tunísia": "tn", "Bélgica": "be", "Egito": "eg", "Irã": "ir",
    "Nova Zelândia": "nz", "Espanha": "es", "Cabo Verde": "cv",
    "Arábia Saudita": "sa", "Uruguai": "uy", "França": "fr",
    "Senegal": "sn", "Iraque": "iq", "Noruega": "no",
    "Argentina": "ar", "Argélia": "dz", "Áustria": "at",
    "Jordânia": "jo", "Portugal": "pt",
    "República Democrática do Congo": "cd", "Uzbequistão": "uz",
    "Colômbia": "co", "Inglaterra": "gb-eng", "Croácia": "hr",
    "Gana": "gh", "Panamá": "pa",
}


def _bandeira_img(time: str, altura_px: int = 18) -> str:
    """Retorna tag <img> de bandeira via flagcdn (SVG, ~1KB cada)."""
    codigo = CODIGO_PAIS.get(time)
    if not codigo:
        return ""
    url = f"https://flagcdn.com/{codigo}.svg"
    return (
        f'<img src="{url}" alt="{time}" '
        f'style="height:{altura_px}px; border-radius:2px; flex-shrink:0;">'
    )


def _parse_data(d) -> date:
    """Converte string ISO ('YYYY-MM-DD') ou date em date."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _agrupar_por_rodada(partidas: list[dict]) -> dict[int, list[dict]]:
    """
    Agrupa partidas do grupo por rodada (1, 2, 3) usando a data do jogo.
    A primeira data → Rodada 1, segunda → Rodada 2, terceira → Rodada 3.
    """
    por_rodada: dict[int, list[dict]] = defaultdict(list)
    datas_ordenadas = sorted(set(p["data_jogo"] for p in partidas))
    data_para_rodada = {d: i + 1 for i, d in enumerate(datas_ordenadas)}
    for p in partidas:
        rodada = data_para_rodada[p["data_jogo"]]
        por_rodada[rodada].append(p)
    return dict(sorted(por_rodada.items()))


def _calcular_resultado(partida: dict) -> Resultado | None:
    """Retorna Resultado se a partida foi finalizada, senão None."""
    if partida["status"] != "finalizado":
        return None
    if partida["placar_a"] is None or partida["placar_b"] is None:
        return None
    return Resultado(
        placar_a=partida["placar_a"],
        placar_b=partida["placar_b"],
        avanca=partida.get("avanca"),
    )


def _card_pontuacao(pont: Pontuacao, placar_a: int, placar_b: int) -> None:
    """Renderiza o card colorido com a pontuação obtida no jogo."""
    cor_para_func = {
        "verde": st.success,
        "amarelo": st.warning,
        "vermelho": st.error,
    }
    cor_para_func[pont.cor](
        f"**{pont.pontos} pts** · {pont.motivo}  \n"
        f"Placar real: **{placar_a} × {placar_b}**"
    )


def _renderizar_jogo_form(
    partida: dict,
    palpite_existente: dict | None,
    pode_editar: bool,
) -> tuple[int | None, int | None]:
    """
    Renderiza um jogo dentro de um st.form e retorna (placar_a, placar_b)
    do valor atual do input. Retorna (None, None) se em branco/inválido.

    Usa um único campo de texto por jogo, onde a pessoa digita o placar
    no formato "2x1", "2-1" ou "2 1". Isso ocupa pouco espaço e funciona
    bem no celular.
    """
    time_a = partida["time_a"]
    time_b = partida["time_b"]
    bandeira_a = _bandeira_img(time_a)
    bandeira_b = _bandeira_img(time_b)
    data_fmt = utils.formatar_data(_parse_data(partida["data_jogo"]))

    # Default: se existe palpite, mostra no formato "AxB"; senão, vazio.
    if palpite_existente:
        valor_default = formatar_placar(
            palpite_existente["placar_a"], palpite_existente["placar_b"]
        )
    else:
        valor_default = ""

    # Confronto numa linha HTML única (não usa st.columns, então não
    # empilha no celular): Time A 🏳  ×  🏳 Time B, com a data ao lado.
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

    # Campo de palpite: estreito e centralizado, usando colunas só para
    # limitar a largura (a do meio é o input). Como há 1 input por jogo,
    # mesmo empilhando no mobile fica organizado.
    _, col_meio, _ = st.columns([1, 1, 1])
    placar_str = col_meio.text_input(
        "Placar",
        value=valor_default,
        max_chars=5,
        key=f"placar_{partida['id']}",
        label_visibility="collapsed",
        disabled=not pode_editar,
        placeholder="ex: 2x1",
    )

    resultado = parse_placar(placar_str)
    if resultado is None:
        if placar_str and placar_str.strip():
            col_meio.caption("⚠ formato inválido")
        return (None, None)
    return resultado


def _renderizar_jogo(
    partida: dict,
    palpite_existente: dict | None,
) -> tuple[int | None, int | None] | None:
    """
    Renderiza um jogo no modo apropriado (editável / finalizado / expirado).
    Retorna (pa, pb) se editável (cada um pode ser None se em branco),
    ou None se não é editável (finalizado ou prazo expirado).
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
                ),
                resultado,
                fase="grupos",
            )
            _card_pontuacao(pont, resultado.placar_a, resultado.placar_b)
        else:
            st.info(
                f"Você não palpitou neste jogo. Placar real: "
                f"**{resultado.placar_a} × {resultado.placar_b}**"
            )
        return None

    if not palpite_permitido:
        _renderizar_jogo_form(partida, palpite_existente, pode_editar=False)
        if palpite_existente:
            st.caption(
                f"⏰ Prazo encerrado · seu palpite: "
                f"**{palpite_existente['placar_a']} × {palpite_existente['placar_b']}** "
                "· aguardando o resultado"
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
    st.title("⚽ Palpites · Fase de Grupos")
    st.caption(f"Logado como **{usuario['nome']}**")

    # CSS leve: apenas deixa os inputs de placar centralizados e mais
    # estreitos. NÃO mexemos no comportamento de empilhamento das colunas
    # (forçar nowrap causava overflow horizontal no celular).
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
        "• Digite o placar no formato **2x1** (também aceita 2-1 ou 2 1).  \n"
        "• Cada grupo tem um botão **Salvar** próprio. "
        "Lembre de clicar antes de trocar de aba.  \n"
        "• Você pode editar os palpites até **0h (Brasília) do dia do jogo**.  \n"
        "• Após o jogo finalizado, sua pontuação aparece em destaque."
    )

    try:
        partidas = db.listar_partidas(fase="grupos")
    except Exception as exc:
        st.error(f"Erro ao buscar partidas: {exc}")
        return

    try:
        palpites = db.buscar_palpites_usuario(usuario["telefone"])
    except Exception as exc:
        st.error(f"Erro ao buscar palpites: {exc}")
        return

    palpites_por_partida = {p["partida_id"]: p for p in palpites}

    abas = st.tabs([f"Grupo {g}" for g in GRUPOS_FASE])
    for aba, grupo in zip(abas, GRUPOS_FASE):
        with aba:
            _renderizar_aba_grupo(
                grupo=grupo,
                partidas=[p for p in partidas if p["grupo"] == grupo],
                palpites_por_partida=palpites_por_partida,
                telefone=usuario["telefone"],
            )


def _renderizar_aba_grupo(
    grupo: str,
    partidas: list[dict],
    palpites_por_partida: dict[int, dict],
    telefone: str,
) -> None:
    """Renderiza o conteúdo de uma aba (um grupo)."""
    por_rodada = _agrupar_por_rodada(partidas)

    with st.form(f"form_grupo_{grupo}", clear_on_submit=False):
        valores_novos: dict[int, tuple[int | None, int | None]] = {}

        for rodada, jogos_rodada in por_rodada.items():
            st.subheader(f"Rodada {rodada}")
            for jogo in sorted(jogos_rodada, key=lambda j: j["numero"]):
                palp = palpites_por_partida.get(jogo["id"])
                valores = _renderizar_jogo(jogo, palp)
                if valores is not None:
                    valores_novos[jogo["id"]] = valores
                st.divider()

        salvar = st.form_submit_button(
            f"💾 Salvar palpites do Grupo {grupo}",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        _salvar_palpites(telefone, valores_novos, palpites_por_partida)


def _salvar_palpites(
    telefone: str,
    valores_novos: dict[int, tuple[int | None, int | None]],
    palpites_existentes: dict[int, dict],
) -> None:
    """
    Salva palpites preenchidos (ambos os placares) que mudaram em
    relação ao que já está no banco.

    Pula:
        - jogos com algum campo vazio (palpite incompleto)
        - jogos cujo palpite no banco já é exatamente igual ao digitado
    """
    salvos = 0
    incompletos = 0
    erros: list[str] = []

    for partida_id, (pa, pb) in valores_novos.items():
        # Palpite incompleto (algum campo vazio ou inválido)
        if pa is None or pb is None:
            # Se a pessoa tinha um palpite e apagou um dos campos, NÃO
            # apagamos do banco - apenas ignoramos, mantendo o palpite
            # anterior. Para apagar de fato, seria preciso uma ação
            # explícita ("limpar palpite"), que pode ficar pra depois.
            incompletos += 1
            continue

        existente = palpites_existentes.get(partida_id)
        if existente is not None:
            if existente["placar_a"] == pa and existente["placar_b"] == pb:
                continue
        try:
            db.salvar_palpite(
                telefone=telefone,
                partida_id=partida_id,
                placar_a=pa,
                placar_b=pb,
                avanca=None,
            )
            salvos += 1
        except Exception as exc:
            erros.append(f"Partida {partida_id}: {exc}")

    if salvos > 0:
        st.success(f"✅ {salvos} palpite(s) salvo(s) com sucesso.")
    elif not erros and incompletos == 0:
        st.info("Nenhuma alteração para salvar.")

    if incompletos > 0 and salvos == 0:
        st.warning(
            f"⚠ {incompletos} jogo(s) sem palpite válido "
            "(em branco ou formato incorreto). Use o formato 2x1."
        )

    if erros:
        st.error("Alguns palpites não foram salvos:")
        for e in erros:
            st.write(f"- {e}")