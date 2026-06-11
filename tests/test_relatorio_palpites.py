"""Testes da geração de relatório de palpites do dia."""
from datetime import date

import pytest

from app.relatorio_palpites import (
    datas_com_partidas,
    gerar_relatorio_dia,
)


# ---- Helpers para fixtures ----

def _p(id_, numero, time_a, time_b, data_jogo, fase="grupos"):
    return {
        "id": id_, "numero": numero, "fase": fase,
        "time_a": time_a, "time_b": time_b,
        "data_jogo": data_jogo,
    }


def _u(tel, nome):
    return {"telefone": tel, "nome": nome}


def _palp(tel, partida_id, pa, pb, avanca=None):
    return {
        "telefone": tel, "partida_id": partida_id,
        "placar_a": pa, "placar_b": pb, "avanca": avanca,
    }


class TestRelatorioBasico:
    def test_sem_partidas(self):
        texto = gerar_relatorio_dia(date(2026, 6, 11), [], [], [])
        assert "Nenhum jogo" in texto
        assert "11/06" in texto

    def test_um_jogo_um_palpite(self):
        partidas = [_p(1, 1, "México", "África do Sul", date(2026, 6, 11))]
        usuarios = [_u("111", "Renato")]
        palpites = [_palp("111", 1, 1, 2)]
        texto = gerar_relatorio_dia(date(2026, 6, 11), partidas, palpites, usuarios)
        assert "Jogos do dia 11/06 (qui)" in texto
        assert "México" in texto
        assert "África do Sul" in texto
        assert "Renato: 1x2" in texto

    def test_usuario_sem_palpite(self):
        partidas = [_p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13))]
        usuarios = [_u("111", "Pedro")]
        texto = gerar_relatorio_dia(date(2026, 6, 13), partidas, [], usuarios)
        assert "Pedro: sem palpite" in texto


class TestOrdenacao:
    def test_usuarios_em_ordem_alfabetica(self):
        partidas = [_p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13))]
        usuarios = [
            _u("333", "Renato"),
            _u("111", "André"),
            _u("222", "Pedro"),
        ]
        palpites = [
            _palp("333", 1, 1, 0),
            _palp("111", 1, 2, 2),
            _palp("222", 1, 0, 1),
        ]
        texto = gerar_relatorio_dia(
            date(2026, 6, 13), partidas, palpites, usuarios
        )
        # Pega só as linhas com nome:placar
        linhas = [l for l in texto.split("\n") if ":" in l and "x" in l]
        nomes = [l.split(":")[0] for l in linhas]
        assert nomes == ["André", "Pedro", "Renato"]

    def test_partidas_em_ordem_de_numero(self):
        partidas = [
            _p(5, 5, "Brasil", "Marrocos", date(2026, 6, 13)),
            _p(6, 6, "Haiti", "Escócia", date(2026, 6, 13)),
        ]
        usuarios = [_u("111", "Ana")]
        # Passa partidas fora de ordem
        texto = gerar_relatorio_dia(
            date(2026, 6, 13), list(reversed(partidas)), [], usuarios
        )
        # Brasil deve aparecer antes de Haiti
        pos_brasil = texto.find("Brasil")
        pos_haiti = texto.find("Haiti")
        assert pos_brasil < pos_haiti


class TestMataMata:
    def test_empate_com_avanca_mostra_quem_avanca(self):
        partidas = [_p(73, 73, "Brasil", "Marrocos", date(2026, 6, 28),
                       fase="r32")]
        usuarios = [_u("111", "Ana")]
        palpites = [_palp("111", 73, 1, 1, avanca="A")]
        texto = gerar_relatorio_dia(
            date(2026, 6, 28), partidas, palpites, usuarios
        )
        assert "Ana: 1x1 (Brasil avança)" in texto

    def test_empate_avanca_B(self):
        partidas = [_p(73, 73, "Brasil", "Marrocos", date(2026, 6, 28),
                       fase="r32")]
        usuarios = [_u("111", "Ana")]
        palpites = [_palp("111", 73, 0, 0, avanca="B")]
        texto = gerar_relatorio_dia(
            date(2026, 6, 28), partidas, palpites, usuarios
        )
        assert "Ana: 0x0 (Marrocos avança)" in texto

    def test_mata_mata_com_vencedor_nao_mostra_avanca(self):
        # Palpite tem vencedor: o "quem avança" é redundante, não mostramos.
        partidas = [_p(73, 73, "Brasil", "Marrocos", date(2026, 6, 28),
                       fase="r32")]
        usuarios = [_u("111", "Ana")]
        palpites = [_palp("111", 73, 2, 1, avanca="A")]
        texto = gerar_relatorio_dia(
            date(2026, 6, 28), partidas, palpites, usuarios
        )
        assert "Ana: 2x1" in texto
        assert "avança" not in texto.split("Ana")[1]

    def test_grupos_ignora_avanca_mesmo_se_tiver(self):
        # Fase de grupos não usa avanca mesmo se palpite for empate.
        partidas = [_p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13),
                       fase="grupos")]
        usuarios = [_u("111", "Ana")]
        palpites = [_palp("111", 1, 1, 1, avanca="A")]  # não deveria ter avanca
        texto = gerar_relatorio_dia(
            date(2026, 6, 13), partidas, palpites, usuarios
        )
        assert "Ana: 1x1" in texto
        assert "avança" not in texto


class TestPartidasIncompletas:
    def test_partidas_sem_times_definidos_sao_ignoradas(self):
        partidas = [
            _p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13)),
            _p(2, 73, None, None, date(2026, 6, 13), fase="r32"),
        ]
        usuarios = [_u("111", "Ana")]
        texto = gerar_relatorio_dia(date(2026, 6, 13), partidas, [], usuarios)
        assert "Brasil" in texto
        # A partida com times None não deve gerar bloco
        assert texto.count("Ana: ") == 1


class TestDatasComPartidas:
    def test_retorna_datas_unicas_ordenadas(self):
        partidas = [
            _p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13)),
            _p(2, 2, "Haiti", "Escócia", date(2026, 6, 13)),
            _p(3, 3, "México", "África do Sul", date(2026, 6, 11)),
        ]
        datas = datas_com_partidas(partidas)
        assert datas == [date(2026, 6, 11), date(2026, 6, 13)]

    def test_ignora_partidas_sem_times(self):
        partidas = [
            _p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13)),
            _p(2, 73, None, None, date(2026, 7, 4), fase="r32"),
        ]
        datas = datas_com_partidas(partidas)
        assert datas == [date(2026, 6, 13)]

    def test_aceita_data_como_string(self):
        # Supabase retorna data como string ISO
        partidas = [_p(1, 1, "Brasil", "Marrocos", "2026-06-13")]
        datas = datas_com_partidas(partidas)
        assert datas == [date(2026, 6, 13)]


class TestFormatoTexto:
    def test_estrutura_geral(self):
        partidas = [_p(1, 1, "Brasil", "Marrocos", date(2026, 6, 13))]
        usuarios = [_u("111", "Ana"), _u("222", "Bia")]
        palpites = [_palp("111", 1, 2, 1)]
        texto = gerar_relatorio_dia(
            date(2026, 6, 13), partidas, palpites, usuarios
        )
        # Estrutura: cabeçalho, linha em branco, jogo, palpites
        linhas = texto.split("\n")
        assert linhas[0] == "Jogos do dia 13/06 (sáb)"
        assert linhas[1] == ""
        assert "Brasil" in linhas[2] and "Marrocos" in linhas[2]
        # Ana antes de Bia (alfabético)
        assert linhas[3] == "Ana: 2x1"
        assert linhas[4] == "Bia: sem palpite"