"""
app/relatorio_palpites.py
=========================
Gera o texto formatado dos palpites de um dia, pronto para copiar e
colar no WhatsApp.

A função principal é pura: recebe dados e retorna string. Sem I/O.

Usa um dicionário próprio de bandeiras em formato EMOJI (não imagens),
porque o WhatsApp só renderiza emojis no texto - imagens SVG da tela
do app não funcionariam quando copiadas para o WhatsApp.
"""
from __future__ import annotations

from datetime import date


# Mapeamento país → emoji de bandeira (Unicode).
# Escócia e Inglaterra usam "tag sequences" especiais (bandeiras das
# nações constituintes do Reino Unido), que renderizam corretamente
# no WhatsApp mobile.
BANDEIRAS_EMOJI: dict[str, str] = {
    "México": "🇲🇽",
    "África do Sul": "🇿🇦",
    "Coreia do Sul": "🇰🇷",
    "República Tcheca": "🇨🇿",
    "Canadá": "🇨🇦",
    "Bósnia e Herzegovina": "🇧🇦",
    "Catar": "🇶🇦",
    "Suíça": "🇨🇭",
    "Brasil": "🇧🇷",
    "Marrocos": "🇲🇦",
    "Haiti": "🇭🇹",
    "Escócia": "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "Estados Unidos": "🇺🇸",
    "Paraguai": "🇵🇾",
    "Austrália": "🇦🇺",
    "Turquia": "🇹🇷",
    "Alemanha": "🇩🇪",
    "Curaçao": "🇨🇼",
    "Costa do Marfim": "🇨🇮",
    "Equador": "🇪🇨",
    "Holanda": "🇳🇱",
    "Japão": "🇯🇵",
    "Suécia": "🇸🇪",
    "Tunísia": "🇹🇳",
    "Bélgica": "🇧🇪",
    "Egito": "🇪🇬",
    "Irã": "🇮🇷",
    "Nova Zelândia": "🇳🇿",
    "Espanha": "🇪🇸",
    "Cabo Verde": "🇨🇻",
    "Arábia Saudita": "🇸🇦",
    "Uruguai": "🇺🇾",
    "França": "🇫🇷",
    "Senegal": "🇸🇳",
    "Iraque": "🇮🇶",
    "Noruega": "🇳🇴",
    "Argentina": "🇦🇷",
    "Argélia": "🇩🇿",
    "Áustria": "🇦🇹",
    "Jordânia": "🇯🇴",
    "Portugal": "🇵🇹",
    "República Democrática do Congo": "🇨🇩",
    "Uzbequistão": "🇺🇿",
    "Colômbia": "🇨🇴",
    "Inglaterra": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "Croácia": "🇭🇷",
    "Gana": "🇬🇭",
    "Panamá": "🇵🇦",
}

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def _bandeira(time: str) -> str:
    return BANDEIRAS_EMOJI.get(time, "🏳️")


def _formatar_data(d: date) -> str:
    return f"{d.strftime('%d/%m')} ({DIAS_SEMANA[d.weekday()]})"


def _parse_data(d) -> date:
    """Converte string ISO ('YYYY-MM-DD') ou date em date."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def gerar_relatorio_dia(
    data_jogo: date,
    partidas: list[dict],
    palpites: list[dict],
    usuarios: list[dict],
) -> str:
    """
    Gera o texto dos palpites do dia para envio no WhatsApp.

    Args:
        data_jogo: data dos jogos (date).
        partidas: partidas DESSA data (já filtradas pelo caller).
        palpites: palpites das partidas dessa data (já filtrados).
        usuarios: todos os usuários do bolão.

    Returns:
        String formatada, pronta para copiar e colar. Usuários ordenados
        alfabeticamente. Quem não palpitou aparece como "sem palpite".
    """
    if not partidas:
        return f"Nenhum jogo em {_formatar_data(data_jogo)}."

    # Indexa palpites por (telefone, partida_id) para lookup rápido.
    palpites_por = {(p["telefone"], p["partida_id"]): p for p in palpites}

    # Usuários ordenados alfabeticamente (case-insensitive).
    usuarios_ord = sorted(usuarios, key=lambda u: u["nome"].lower())

    linhas: list[str] = [f"Jogos do dia {_formatar_data(data_jogo)}", ""]

    # Partidas ordenadas pelo número oficial.
    for partida in sorted(partidas, key=lambda p: p["numero"]):
        time_a = partida.get("time_a")
        time_b = partida.get("time_b")
        if not time_a or not time_b:
            continue  # placeholder de mata-mata sem times definidos

        ba = _bandeira(time_a)
        bb = _bandeira(time_b)
        linhas.append(f"{ba} {time_a} x {bb} {time_b}")

        for usuario in usuarios_ord:
            nome = usuario["nome"]
            tel = usuario["telefone"]
            palp = palpites_por.get((tel, partida["id"]))

            if palp is None:
                linhas.append(f"{nome}: sem palpite")
                continue

            placar = f"{palp['placar_a']}x{palp['placar_b']}"
            # Mata-mata + palpite de empate: anexar quem avança.
            if (partida.get("fase") != "grupos"
                    and palp["placar_a"] == palp["placar_b"]
                    and palp.get("avanca")):
                nome_avanca = time_a if palp["avanca"] == "A" else time_b
                placar += f" ({nome_avanca} avança)"
            linhas.append(f"{nome}: {placar}")

        linhas.append("")  # linha em branco entre partidas

    return "\n".join(linhas).rstrip()


def datas_com_partidas(partidas: list[dict]) -> list[date]:
    """Retorna lista ordenada de datas distintas das partidas."""
    datas = {_parse_data(p["data_jogo"]) for p in partidas
             if p.get("time_a") and p.get("time_b")}
    return sorted(datas)
