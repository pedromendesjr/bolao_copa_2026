"""Testes do módulo de prêmios (funções puras)."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.premios import (
    DEADLINE_DATA,
    PREMIOS,
    PREMIOS_POR_TIPO,
    deadline_premios,
    normalizar_palpite,
    palpite_premios_permitido,
    palpite_valido,
)


TZ = ZoneInfo("America/Sao_Paulo")


class TestConstantes:
    def test_tem_seis_premios(self):
        assert len(PREMIOS) == 6

    def test_tipos_unicos(self):
        tipos = [p.tipo for p in PREMIOS]
        assert len(tipos) == len(set(tipos))

    def test_premios_esperados(self):
        tipos = {p.tipo for p in PREMIOS}
        assert tipos == {
            "campeao", "craque", "artilheiro", "assistencia",
            "luva_de_ouro", "jogador_jovem",
        }

    def test_lookup_por_tipo(self):
        assert PREMIOS_POR_TIPO["campeao"].titulo == "Seleção Campeã"


class TestDeadline:
    def test_deadline_eh_14_06_2026(self):
        dl = deadline_premios()
        assert dl.year == 2026
        assert dl.month == 6
        assert dl.day == 14
        assert dl.hour == 0
        assert dl.minute == 0

    def test_permitido_antes_do_deadline(self):
        agora = datetime(2026, 6, 13, 23, 59, tzinfo=TZ)
        assert palpite_premios_permitido(agora)

    def test_nao_permitido_depois_do_deadline(self):
        agora = datetime(2026, 6, 14, 0, 0, 1, tzinfo=TZ)
        assert not palpite_premios_permitido(agora)

    def test_nao_permitido_exatamente_no_deadline(self):
        # 0h em ponto: deadline já passou (regra "antes" de 0h)
        agora = datetime(2026, 6, 14, 0, 0, 0, tzinfo=TZ)
        assert not palpite_premios_permitido(agora)

    def test_permitido_muito_antes(self):
        agora = datetime(2025, 1, 1, 12, 0, tzinfo=TZ)
        assert palpite_premios_permitido(agora)


class TestNormalizar:
    def test_remove_espaco_duplo(self):
        assert normalizar_palpite("Vinicius  Junior") == "Vinicius Junior"

    def test_remove_espacos_extremos(self):
        assert normalizar_palpite("  Brasil  ") == "Brasil"

    def test_mantem_acentos_e_case(self):
        assert normalizar_palpite("Mbappé") == "Mbappé"
        assert normalizar_palpite("ARGENTINA") == "ARGENTINA"

    def test_vazio_vira_vazio(self):
        assert normalizar_palpite("") == ""
        assert normalizar_palpite("   ") == ""

    def test_none_seguro(self):
        # Tipagem é str, mas defensivamente o código aceita None
        assert normalizar_palpite(None) == ""  # type: ignore[arg-type]


class TestValidacao:
    @pytest.mark.parametrize("s", [
        "Vinicius Junior",
        "Brasil",
        "Mbappé",
        "ab",         # 2 chars: limite mínimo
    ])
    def test_palpites_validos(self, s):
        assert palpite_valido(s)

    @pytest.mark.parametrize("s", [
        "",
        " ",
        "a",          # 1 char
        "  a  ",      # 1 char depois de normalizar
    ])
    def test_palpites_invalidos(self, s):
        assert not palpite_valido(s)