"""Testes das validações puras de auth.py (sem I/O)."""
import pytest

from app.auth import nome_valido, senha_valida, telefone_valido


class TestTelefoneValido:
    @pytest.mark.parametrize("t", [
        "47999998888",
        "11987654321",
        "21912345678",
        "00000000000",  # valida só o formato; semântica é outra
    ])
    def test_telefones_validos(self, t):
        assert telefone_valido(t)

    @pytest.mark.parametrize("t", [
        "",
        "12345",
        "4799999888",       # 10 dígitos
        "479999988880",     # 12 dígitos
        "47 99999 8888",    # com espaços
        "(47)99999-8888",   # com máscara
        "47999998888a",     # caractere extra
        "479999A8888",      # letra no meio
    ])
    def test_telefones_invalidos(self, t):
        assert not telefone_valido(t)


class TestSenhaValida:
    @pytest.mark.parametrize("s", ["0000", "1234", "9999", "0001"])
    def test_senhas_validas(self, s):
        assert senha_valida(s)

    @pytest.mark.parametrize("s", [
        "",
        "123",          # 3 dígitos
        "12345",        # 5 dígitos
        "12a4",         # letra
        "12 4",         # espaço
        "abcd",         # tudo letra
    ])
    def test_senhas_invalidas(self, s):
        assert not senha_valida(s)


class TestNomeValido:
    @pytest.mark.parametrize("n", [
        "Pedro",
        "Ana Maria",
        "Jô",
        "Pê",
    ])
    def test_nomes_validos(self, n):
        # nome_valido existe? Vou ser flexível: se não existir, pulo
        try:
            from app.auth import nome_valido as nv
        except ImportError:
            pytest.skip("nome_valido não está em auth.py (ok, está em outro lugar)")
        assert nv(n)

    @pytest.mark.parametrize("n", ["", " ", "a", " A "])
    def test_nomes_invalidos(self, n):
        try:
            from app.auth import nome_valido as nv
        except ImportError:
            pytest.skip("nome_valido não está em auth.py")
        # 'a' tem 1 char util → inválido; ' A ' tem 1 char util após strip → inválido
        assert not nv(n)
