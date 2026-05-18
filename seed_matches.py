"""
seed_matches.py
================
Popula a tabela `partidas` no Supabase com todas as 104 partidas da
Copa do Mundo 2026:

  - 72 partidas da fase de grupos (com times e datas reais oficiais)
  - 16 partidas dos 16-avos de final (placeholders)
  -  8 partidas das oitavas de final (placeholders)
  -  4 partidas das quartas de final (placeholders)
  -  2 partidas das semifinais (placeholders)
  -  1 partida da disputa de 3º lugar (placeholder)
  -  1 partida da final (placeholder)

As partidas do mata-mata são criadas com `time_a` e `time_b` nulos e
ficam `disponivel = FALSE` até serem habilitadas manualmente após a
fase de grupos.

Como rodar:
    1. Configure o .env com SUPABASE_URL e SUPABASE_KEY
    2. pip install -r requirements.txt
    3. python seed_matches.py
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client


# ============================================================
# Dados oficiais da Copa do Mundo 2026
# Fonte: sorteio FIFA de 5 de dezembro de 2025
# ============================================================

# Grupos: posição 1 a 4 conforme o sorteio
GRUPOS: dict[str, list[str]] = {
    "A": ["México", "África do Sul", "Coreia do Sul", "República Tcheca"],
    "B": ["Canadá", "Bósnia e Herzegovina", "Catar", "Suíça"],
    "C": ["Brasil", "Marrocos", "Haiti", "Escócia"],
    "D": ["Estados Unidos", "Paraguai", "Austrália", "Turquia"],
    "E": ["Alemanha", "Curaçao", "Costa do Marfim", "Equador"],
    "F": ["Holanda", "Japão", "Suécia", "Tunísia"],
    "G": ["Bélgica", "Egito", "Irã", "Nova Zelândia"],
    "H": ["Espanha", "Cabo Verde", "Arábia Saudita", "Uruguai"],
    "I": ["França", "Senegal", "Iraque", "Noruega"],
    "J": ["Argentina", "Argélia", "Áustria", "Jordânia"],
    "K": ["Portugal", "República Democrática do Congo", "Uzbequistão", "Colômbia"],
    "L": ["Inglaterra", "Croácia", "Gana", "Panamá"],
}

# Datas oficiais por grupo (Matchday 1, 2, 3) em junho de 2026
DATAS_GRUPOS: dict[str, tuple[date, date, date]] = {
    "A": (date(2026, 6, 11), date(2026, 6, 18), date(2026, 6, 24)),
    "B": (date(2026, 6, 12), date(2026, 6, 18), date(2026, 6, 24)),
    "C": (date(2026, 6, 13), date(2026, 6, 19), date(2026, 6, 24)),
    "D": (date(2026, 6, 12), date(2026, 6, 19), date(2026, 6, 25)),
    "E": (date(2026, 6, 14), date(2026, 6, 20), date(2026, 6, 25)),
    "F": (date(2026, 6, 14), date(2026, 6, 20), date(2026, 6, 25)),
    "G": (date(2026, 6, 15), date(2026, 6, 21), date(2026, 6, 26)),
    "H": (date(2026, 6, 15), date(2026, 6, 21), date(2026, 6, 26)),
    "I": (date(2026, 6, 16), date(2026, 6, 22), date(2026, 6, 26)),
    "J": (date(2026, 6, 16), date(2026, 6, 22), date(2026, 6, 27)),
    "K": (date(2026, 6, 17), date(2026, 6, 23), date(2026, 6, 27)),
    "L": (date(2026, 6, 17), date(2026, 6, 23), date(2026, 6, 27)),
}

# Padrão de emparelhamento dentro do grupo (índices 0-based dos times)
# Matchday 1: pos1 x pos2,  pos3 x pos4
# Matchday 2: pos1 x pos3,  pos4 x pos2
# Matchday 3: pos4 x pos1,  pos2 x pos3
EMPARELHAMENTOS = [
    [(0, 1), (2, 3)],
    [(0, 2), (3, 1)],
    [(3, 0), (1, 2)],
]


@dataclass
class Partida:
    numero: int
    fase: str
    grupo: Optional[str]
    time_a: Optional[str]
    time_b: Optional[str]
    placeholder_a: Optional[str]
    placeholder_b: Optional[str]
    data_jogo: str               # ISO string
    horario: Optional[str] = None
    disponivel: bool = True
    status: str = "agendado"


# ============================================================
# Geração das partidas
# ============================================================

def gerar_fase_grupos() -> list[Partida]:
    """Gera as 72 partidas da fase de grupos."""
    partidas: list[Partida] = []
    numero = 1
    # Itera por matchday e dentro dele por grupo, para casar com a
    # ordem oficial de numeração da FIFA (matchday 1 vem antes do 2).
    for md in range(3):
        for grupo, times in GRUPOS.items():
            data = DATAS_GRUPOS[grupo][md]
            for i_a, i_b in EMPARELHAMENTOS[md]:
                partidas.append(Partida(
                    numero=numero,
                    fase="grupos",
                    grupo=grupo,
                    time_a=times[i_a],
                    time_b=times[i_b],
                    placeholder_a=f"{i_a + 1}{grupo}",
                    placeholder_b=f"{i_b + 1}{grupo}",
                    data_jogo=data.isoformat(),
                ))
                numero += 1
    return partidas


def gerar_mata_mata() -> list[Partida]:
    """
    Gera as 32 partidas do mata-mata (números 73..104) com placeholders.
    As datas seguem o calendário oficial da FIFA. Após a fase de grupos,
    o admin atualiza `time_a`, `time_b` e marca `disponivel = TRUE`.
    """
    partidas: list[Partida] = []

    # 16-avos de final (Round of 32): partidas 73..88, 28/06 a 03/07
    datas_r32 = [
        date(2026, 6, 28), date(2026, 6, 28),
        date(2026, 6, 29), date(2026, 6, 29),
        date(2026, 6, 30), date(2026, 6, 30),
        date(2026, 7,  1), date(2026, 7,  1),
        date(2026, 7,  1), date(2026, 7,  1),
        date(2026, 7,  2), date(2026, 7,  2),
        date(2026, 7,  2), date(2026, 7,  2),
        date(2026, 7,  3), date(2026, 7,  3),
    ]
    for idx, data in enumerate(datas_r32):
        numero = 73 + idx
        partidas.append(Partida(
            numero=numero,
            fase="r32",
            grupo=None,
            time_a=None, time_b=None,
            placeholder_a=f"Vaga A da partida {numero}",
            placeholder_b=f"Vaga B da partida {numero}",
            data_jogo=data.isoformat(),
            disponivel=False,
        ))

    # Oitavas (Round of 16): 89..96, 04/07 a 07/07
    datas_r16 = [
        date(2026, 7, 4), date(2026, 7, 4),
        date(2026, 7, 5), date(2026, 7, 5),
        date(2026, 7, 6), date(2026, 7, 6),
        date(2026, 7, 7), date(2026, 7, 7),
    ]
    # Pares oficiais conforme FIFA (Sky Sports): m89 = vencedor M74 x vencedor M77, etc.
    # Como o usuário vai cadastrar manualmente, deixamos placeholders genéricos.
    for idx, data in enumerate(datas_r16):
        numero = 89 + idx
        partidas.append(Partida(
            numero=numero,
            fase="r16",
            grupo=None,
            time_a=None, time_b=None,
            placeholder_a=f"Vencedor 16-avos (M{73 + idx * 2})",
            placeholder_b=f"Vencedor 16-avos (M{74 + idx * 2})",
            data_jogo=data.isoformat(),
            disponivel=False,
        ))

    # Quartas: 97..100, 09/07 a 11/07
    datas_qf = [
        date(2026, 7,  9), date(2026, 7,  9),
        date(2026, 7, 10), date(2026, 7, 11),
    ]
    for idx, data in enumerate(datas_qf):
        numero = 97 + idx
        partidas.append(Partida(
            numero=numero,
            fase="quartas",
            grupo=None,
            time_a=None, time_b=None,
            placeholder_a=f"Vencedor oitavas (M{89 + idx * 2})",
            placeholder_b=f"Vencedor oitavas (M{90 + idx * 2})",
            data_jogo=data.isoformat(),
            disponivel=False,
        ))

    # Semifinais: 101 e 102, 14/07 e 15/07
    partidas.append(Partida(
        numero=101, fase="semi", grupo=None,
        time_a=None, time_b=None,
        placeholder_a="Vencedor M97", placeholder_b="Vencedor M98",
        data_jogo=date(2026, 7, 14).isoformat(),
        disponivel=False,
    ))
    partidas.append(Partida(
        numero=102, fase="semi", grupo=None,
        time_a=None, time_b=None,
        placeholder_a="Vencedor M99", placeholder_b="Vencedor M100",
        data_jogo=date(2026, 7, 15).isoformat(),
        disponivel=False,
    ))

    # Disputa de 3º lugar: 103, 18/07
    partidas.append(Partida(
        numero=103, fase="terceiro", grupo=None,
        time_a=None, time_b=None,
        placeholder_a="Perdedor M101", placeholder_b="Perdedor M102",
        data_jogo=date(2026, 7, 18).isoformat(),
        disponivel=False,
    ))

    # Final: 104, 19/07
    partidas.append(Partida(
        numero=104, fase="final", grupo=None,
        time_a=None, time_b=None,
        placeholder_a="Vencedor M101", placeholder_b="Vencedor M102",
        data_jogo=date(2026, 7, 19).isoformat(),
        disponivel=False,
    ))

    return partidas


# ============================================================
# Inserção no Supabase
# ============================================================

def conectar() -> Client:
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Defina SUPABASE_URL e SUPABASE_KEY no .env antes de rodar."
        )
    return create_client(url, key)


def inserir(client: Client, partidas: list[Partida]) -> None:
    payload = [asdict(p) for p in partidas]
    # upsert pelo `numero` para permitir rodar o script múltiplas vezes
    result = client.table("partidas").upsert(payload, on_conflict="numero").execute()
    print(f"  → {len(result.data)} linhas inseridas/atualizadas")


def main() -> None:
    partidas = gerar_fase_grupos() + gerar_mata_mata()

    assert len(partidas) == 104, f"Esperado 104 partidas, obtido {len(partidas)}"
    print(f"Geradas {len(partidas)} partidas:")
    print(f"  - Fase de grupos: {sum(1 for p in partidas if p.fase == 'grupos')}")
    print(f"  - 16-avos:        {sum(1 for p in partidas if p.fase == 'r32')}")
    print(f"  - Oitavas:        {sum(1 for p in partidas if p.fase == 'r16')}")
    print(f"  - Quartas:        {sum(1 for p in partidas if p.fase == 'quartas')}")
    print(f"  - Semifinais:     {sum(1 for p in partidas if p.fase == 'semi')}")
    print(f"  - 3º lugar:       {sum(1 for p in partidas if p.fase == 'terceiro')}")
    print(f"  - Final:          {sum(1 for p in partidas if p.fase == 'final')}")
    print()
    print("Conectando ao Supabase…")
    client = conectar()
    print("Enviando partidas…")
    inserir(client, partidas)
    print("Concluído.")


if __name__ == "__main__":
    main()
