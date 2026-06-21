"""
scripts/bootstrap_snapshots.py
==============================
Script de execução única (idempotente) que popula a tabela
`ranking_snapshots` com o histórico de dias que já passaram.

Como funciona:
    1. Lista todas as datas que tiveram jogos finalizados.
    2. Pra cada data, calcula o ranking simulando "todos os jogos
       finalizados até essa data" (cumulativo).
    3. Insere os snapshots correspondentes na tabela.

Roda os snapshots para AMBOS os bolões (lavaprato e cartola).

Como executar:
    Local:
        $ python scripts/bootstrap_snapshots.py

    Pré-requisitos: variáveis SUPABASE_URL e SUPABASE_KEY no .env.
    A variável BOLAO_ID é ignorada aqui - o script processa os dois.

Idempotência:
    Pode rodar várias vezes sem problema. Cada execução APAGA os
    snapshots existentes e recria a partir do zero. Isso garante
    que se alguma regra mudou (ex: pontuação cartola), o histórico
    é regerado coerentemente.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Garante que `from app import ...` funcione independente de onde chamou
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    # Garante que SUPABASE_URL/KEY estão definidos
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
        print("ERRO: SUPABASE_URL e SUPABASE_KEY precisam estar definidos no .env")
        return 1

    from app.snapshots import _parse_data, criar_snapshot
    from app.db import get_client

    client = get_client()

    BOLOES = ["lavaprato", "cartola"]

    # Datas distintas com pelo menos 1 jogo finalizado
    partidas = client.table("partidas").select("data_jogo, status").execute().data
    datas_com_jogos = sorted({
        _parse_data(p["data_jogo"]) for p in partidas
        if p["status"] == "finalizado"
    })

    if not datas_com_jogos:
        print("Nenhuma partida finalizada ainda. Nada a fazer.")
        return 0

    print(f"Encontradas {len(datas_com_jogos)} datas com jogos finalizados:")
    for d in datas_com_jogos:
        print(f"  - {d.isoformat()}")
    print()

    # Filtra apenas datas onde TODOS os jogos da data estão finalizados.
    # (Datas com jogos pendentes não geram snapshot - regra do gatilho.)
    datas_validas = []
    for d in datas_com_jogos:
        jogos_da_data = [p for p in partidas if _parse_data(p["data_jogo"]) == d]
        if all(p["status"] == "finalizado" for p in jogos_da_data):
            datas_validas.append(d)
        else:
            print(f"  ⏳ Pulando {d}: alguns jogos ainda não finalizados.")

    if not datas_validas:
        print("Nenhuma data tem TODOS os jogos finalizados. Nada a fazer.")
        return 0

    print(f"\nGerando snapshots para {len(datas_validas)} data(s):")

    total = 0
    for bid in BOLOES:
        print(f"\n  Bolão: {bid}")
        for d in datas_validas:
            n = criar_snapshot(d, bid=bid)
            print(f"    {d.isoformat()} → {n} linha(s)")
            total += n

    print(f"\n✅ Concluído. {total} linha(s) inseridas no total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())