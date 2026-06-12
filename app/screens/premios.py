"""
screens/premios.py
==================
Tela onde a pessoa palpita os prêmios individuais da Copa.

Layout: um formulário único com um text_input por prêmio. Botão
"Salvar" no fim. Antes do deadline, todos os campos são editáveis;
depois, ficam congelados em modo somente-leitura.
"""
from __future__ import annotations

import streamlit as st

from app import auth, db_premios
from app.premios import (
    DEADLINE_DATA,
    PREMIOS,
    deadline_premios,
    normalizar_palpite,
    palpite_premios_permitido,
    palpite_valido,
)


def render() -> None:
    usuario = auth.usuario_logado()
    st.title("🏆 Palpites de Prêmios")
    st.caption(f"Logado como **{usuario['nome']}**")

    permitido = palpite_premios_permitido()
    dl = deadline_premios()

    if permitido:
        st.info(
            "💡 Palpite os prêmios individuais da Copa 2026.  \n"
            f"• Prazo final: **{DEADLINE_DATA.strftime('%d/%m/%Y')} "
            "às 00:00 (Brasília)**, ou seja, até o fim do dia 13/06.  \n"
            "• Texto livre - escreva o nome completo do jogador "
            "(ou da seleção, no caso da campeã)."
        )
    else:
        st.warning(
            "🔒 O prazo para palpites de prêmios já encerrou em "
            f"**{dl.strftime('%d/%m/%Y às %H:%M')}**. "
            "Seus palpites estão registrados e não podem mais ser alterados."
        )

    # Busca palpites já salvos
    try:
        salvos = db_premios.buscar_palpites_premios(usuario["telefone"])
    except Exception as exc:
        st.error(f"Erro ao buscar palpites: {exc}")
        return

    with st.form("form_premios", clear_on_submit=False):
        valores_novos: dict[str, str] = {}

        for premio in PREMIOS:
            valor_atual = salvos.get(premio.tipo, "")
            entrada = st.text_input(
                f"{premio.emoji} **{premio.titulo}**",
                value=valor_atual,
                key=f"premio_{premio.tipo}",
                help=premio.descricao,
                disabled=not permitido,
                placeholder="Nome do jogador / seleção",
            )
            valores_novos[premio.tipo] = entrada

        salvar = st.form_submit_button(
            "💾 Salvar palpites de prêmios",
            type="primary",
            use_container_width=True,
            disabled=not permitido,
        )

    if salvar:
        _salvar(usuario["telefone"], valores_novos, salvos)


def _salvar(
    telefone: str,
    valores_novos: dict[str, str],
    salvos: dict[str, str],
) -> None:
    """
    Salva palpites que mudaram ou são novos. Ignora campos vazios e
    palpites inválidos (com aviso).
    """
    # Verificação extra: o deadline pode ter expirado entre o load e o
    # submit do form (caso de borda, mas vale proteger).
    if not palpite_premios_permitido():
        st.error("⏰ Prazo encerrado durante o preenchimento. "
                 "Recarregue a página - palpites não foram salvos.")
        return

    salvos_count = 0
    vazios = 0
    invalidos: list[str] = []
    erros: list[str] = []

    for tipo, entrada in valores_novos.items():
        normalizado = normalizar_palpite(entrada)

        # Campo vazio: ignora (não apaga palpite anterior).
        if not normalizado:
            vazios += 1
            continue

        # Texto muito curto - provavelmente um descuido.
        if not palpite_valido(normalizado):
            invalidos.append(tipo)
            continue

        # Sem mudança - nada a fazer.
        if salvos.get(tipo) == normalizado:
            continue

        try:
            db_premios.salvar_palpite_premio(
                telefone=telefone,
                tipo_premio=tipo,
                palpite=normalizado,
            )
            salvos_count += 1
        except Exception as exc:
            erros.append(f"{tipo}: {exc}")

    if salvos_count > 0:
        st.success(f"✅ {salvos_count} palpite(s) de prêmio salvo(s).")
    elif not erros and not invalidos:
        st.info("Nenhuma alteração para salvar.")

    if invalidos:
        st.warning(
            "⚠ Palpites muito curtos (não salvos): "
            + ", ".join(invalidos)
        )

    if erros:
        st.error("Alguns palpites não foram salvos:")
        for e in erros:
            st.write(f"- {e}")