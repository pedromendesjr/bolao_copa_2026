"""Testes do parser de placar em texto único."""
import pytest

from app.placar_parser import formatar_placar, parse_placar


class TestParsePlacarValido:
    @pytest.mark.parametrize("texto,esperado", [
        ("2x1", (2, 1)),
        ("2X1", (2, 1)),
        ("2-1", (2, 1)),
        ("2:1", (2, 1)),
        ("2 1", (2, 1)),
        ("2 x 1", (2, 1)),
        ("2 - 1", (2, 1)),
        (" 2x1 ", (2, 1)),
        ("0x0", (0, 0)),
        ("10x0", (10, 0)),
        ("3x12", (3, 12)),
        ("20x20", (20, 20)),
    ])
    def test_formatos_aceitos(self, texto, esperado):
        assert parse_placar(texto) == esperado


class TestParsePlacarInvalido:
    @pytest.mark.parametrize("texto", [
        "",
        "   ",
        "2",
        "x",
        "abc",
        "2x",
        "x1",
        "2xx1",
        "2x1x3",
        "-1x2",
        "2x-1",
        "21x0",     # acima de 20
        "0x21",
        "2.5x1",
        "dois x um",
    ])
    def test_formatos_rejeitados(self, texto):
        assert parse_placar(texto) is None

    def test_none_retorna_none(self):
        assert parse_placar(None) is None


class TestFormatarPlacar:
    def test_formato_canonico(self):
        assert formatar_placar(2, 1) == "2x1"
        assert formatar_placar(0, 0) == "0x0"
        assert formatar_placar(10, 3) == "10x3"

    def test_roundtrip(self):
        # formatar e re-parsear deve dar o mesmo resultado
        for a, b in [(0, 0), (2, 1), (10, 5), (20, 20)]:
            assert parse_placar(formatar_placar(a, b)) == (a, b)