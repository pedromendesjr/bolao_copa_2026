"""
Testes específicos das novas regras de mata-mata do bolão lavaprato
(regramento 'padrao').

Note: a fase de grupos do padrão NÃO mudou - esses testes cobrem só
o mata-mata, que ganhou pontuações novas.
"""
import pytest

from app.scoring import Palpite, Resultado, calcular_pontuacao


def pont(p, r, fase):
    """Atalho: chama com regras=padrao (default, mas explícito)."""
    return calcular_pontuacao(p, r, fase, regras="padrao")


# ============================================================
# Mata-mata padrão · jogo real teve vencedor (120 min)
# ============================================================

class TestPadraoMataMataComVencedor:
    def test_placar_exato_vinte_cinco(self):
        # Palpite 3x1, real 3x1
        r = pont(Palpite(3, 1), Resultado(3, 1, avanca="A"), "r16")
        assert r.pontos == 25

    def test_vencedor_e_gols_vinte(self):
        # Palpite 3x0, real 3x1 → acertou vencedor A e o "3"
        r = pont(Palpite(3, 0), Resultado(3, 1, avanca="A"), "r16")
        assert r.pontos == 20

    def test_so_vencedor_quinze(self):
        # Palpite 2x0, real 3x1 → acertou só que A vence, errou ambos gols
        r = pont(Palpite(2, 0), Resultado(3, 1, avanca="A"), "r16")
        assert r.pontos == 15

    def test_palpite_empate_real_teve_vencedor_acertou_avanca_tres(self):
        # Palpite 1x1 avanca=A, real 2x1 (A venceu = A passou)
        r = pont(
            Palpite(1, 1, avanca="A"),
            Resultado(2, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_empate_real_teve_vencedor_acertou_gols_mas_errou_avanca_zero(self):
        # Importante: lavaprato_v2 NÃO dá ponto por "gols soltos" no mata-mata.
        # Palpite 1x1 avanca=B (errou quem passa), real 2x1 → 0 pontos
        # (mesmo com placar_b coincidindo!)
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(2, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 0

    def test_palpite_empate_errou_tudo_zero(self):
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(3, 0, avanca="A"),
            "r16",
        )
        assert r.pontos == 0

    def test_palpite_vencedor_errado_acertou_gols_eh_zero(self):
        # Aqui também: gols coincidindo NÃO pontuam mais.
        # Palpite 0x1 (B vence), real 3x1 → 0 pontos mesmo com placar_b igual
        r = pont(
            Palpite(0, 1),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 0

    def test_palpite_vencedor_errado_errou_tudo_zero(self):
        r = pont(Palpite(1, 3), Resultado(3, 0, avanca="A"), "r16")
        assert r.pontos == 0


# ============================================================
# Mata-mata padrão · jogo real foi empate (pênaltis)
# ============================================================

class TestPadraoMataMataEmpate:
    def test_empate_exato_acertou_avanca_27(self):
        r = pont(
            Palpite(1, 1, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 27

    def test_empate_exato_errou_avanca_22(self):
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 22

    def test_empate_nao_exato_acertou_avanca_18(self):
        r = pont(
            Palpite(2, 2, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 18

    def test_empate_nao_exato_errou_avanca_15(self):
        r = pont(
            Palpite(2, 2, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 15

    def test_palpite_vencedor_real_empate_acertou_quem_passou_tres(self):
        # Palpite 2x1 (A vence), real 1x1, A ganhou nos pênaltis
        r = pont(Palpite(2, 1), Resultado(1, 1, avanca="A"), "r16")
        assert r.pontos == 3

    def test_palpite_vencedor_real_empate_errou_quem_passou_zero(self):
        # Palpite 2x1 (A vence), real 1x1, B ganhou nos pênaltis
        # placar_b coincide mas isso NÃO pontua → 0
        r = pont(Palpite(2, 1), Resultado(1, 1, avanca="B"), "r16")
        assert r.pontos == 0


# ============================================================
# Garantir que fase de grupos padrão NÃO mudou
# ============================================================

class TestPadraoGruposIntacto:
    def test_grupos_placar_exato_dezoito(self):
        r = pont(Palpite(2, 1), Resultado(2, 1), "grupos")
        assert r.pontos == 18

    def test_grupos_vencedor_e_gols_quinze(self):
        r = pont(Palpite(3, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 15

    def test_grupos_so_vencedor_doze(self):
        r = pont(Palpite(2, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 12

    def test_grupos_gols_um_lado_tres(self):
        r = pont(Palpite(3, 3), Resultado(3, 1), "grupos")
        assert r.pontos == 3