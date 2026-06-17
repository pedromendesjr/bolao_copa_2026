"""Testes das regras de pontuação 'cartola' (bolão cartola)."""
import pytest

from app.scoring import Palpite, Resultado, calcular_pontuacao


def pont(p, r, fase):
    """Atalho para chamar com regras=cartola."""
    return calcular_pontuacao(p, r, fase, regras="cartola")


# ============================================================
# Fase de Grupos - Cartola
# ============================================================

class TestCartolaGrupos:
    def test_placar_exato_dezoito(self):
        r = pont(Palpite(3, 1), Resultado(3, 1), "grupos")
        assert r.pontos == 18

    def test_empate_exato_dezoito(self):
        r = pont(Palpite(1, 1), Resultado(1, 1), "grupos")
        assert r.pontos == 18

    def test_vencedor_e_gols_doze(self):
        # Era 15 no padrão; agora 12
        r = pont(Palpite(3, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 12

    def test_vencedor_outro_lado_doze(self):
        r = pont(Palpite(2, 1), Resultado(3, 1), "grupos")
        assert r.pontos == 12

    def test_so_vencedor_nove(self):
        # Era 12 no padrão; agora 9
        r = pont(Palpite(2, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 9

    def test_empate_nao_exato_nove(self):
        # Era 12 no padrão; agora 9
        r = pont(Palpite(2, 2), Resultado(1, 1), "grupos")
        assert r.pontos == 9

    def test_gols_um_lado_resultado_errado_tres(self):
        # Palpite 3x3 (empate), real 3x1 (A vence). Acertou os 3 do A.
        r = pont(Palpite(3, 3), Resultado(3, 1), "grupos")
        assert r.pontos == 3

    def test_errou_tudo_zero(self):
        r = pont(Palpite(0, 5), Resultado(3, 1), "grupos")
        assert r.pontos == 0


# ============================================================
# Mata-mata Cartola - jogo real NÃO empatou
# ============================================================

class TestCartolaMataMataComVencedor:
    """Jogo real terminou com vencedor (tempo normal)."""

    def test_placar_exato_trinta(self):
        # Brasil 3x1, real 3x1
        r = pont(
            Palpite(3, 1),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 30

    def test_vencedor_e_gols_vinteum(self):
        # Palpite 3x0, real 3x1
        r = pont(
            Palpite(3, 0),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 21

    def test_so_vencedor_quinze(self):
        # Palpite 2x0, real 3x1
        r = pont(
            Palpite(2, 0),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 15

    def test_palpite_empate_real_teve_vencedor_acertou_quem_passou(self):
        # Palpite 1x1 avanca=A, real 2x1 (A venceu = A passou)
        r = pont(
            Palpite(1, 1, avanca="A"),
            Resultado(2, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_empate_real_teve_vencedor_acertou_so_gols(self):
        # Palpite 1x1 avanca=B (errou quem passa), real 2x1
        # mas placar_a coincide (... 1 != 2) e placar_b coincide (1 == 1)
        # acertou gols de um lado
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(2, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_empate_real_teve_vencedor_errou_tudo(self):
        # Palpite 1x1 avanca=B, real 3x0 (sem coincidência alguma)
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(3, 0, avanca="A"),
            "r16",
        )
        assert r.pontos == 0

    def test_palpite_vencedor_errado_acertou_gols(self):
        # Palpite 0x1 (B vence), real 3x1 (A venceu)
        # placar_b coincide → 3 pts
        r = pont(
            Palpite(0, 1),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_vencedor_errado_errou_tudo(self):
        # Palpite 1x3 (B vence), real 3x0 (A venceu), nada coincide
        r = pont(
            Palpite(1, 3),
            Resultado(3, 0, avanca="A"),
            "r16",
        )
        assert r.pontos == 0


# ============================================================
# Mata-mata Cartola - jogo real EMPATOU (foi pra pênaltis)
# ============================================================

class TestCartolaMataMataEmpate:
    """Jogo real terminou empate (decidido nos pênaltis)."""

    def test_palpite_empate_exato_acertou_avanca_34(self):
        # Palpite 1x1 avanca=A, real 1x1 A passou
        r = pont(
            Palpite(1, 1, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 34

    def test_palpite_empate_exato_errou_avanca_25(self):
        # Palpite 1x1 avanca=B, real 1x1 A passou
        r = pont(
            Palpite(1, 1, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 25

    def test_palpite_empate_nao_exato_acertou_avanca_22(self):
        # Palpite 2x2 avanca=A, real 1x1 A passou
        r = pont(
            Palpite(2, 2, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 22

    def test_palpite_empate_nao_exato_errou_avanca_15(self):
        # Palpite 2x2 avanca=B, real 1x1 A passou
        r = pont(
            Palpite(2, 2, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 15

    def test_palpite_vencedor_real_empate_acertou_quem_passou(self):
        # Palpite 2x1 (A vence), real 1x1, A passa nos pênaltis
        # palpite implica A passa, real diz A passou → acertou avanca
        r = pont(
            Palpite(2, 1),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_vencedor_real_empate_acertou_so_gols(self):
        # Palpite 2x1 (A vence), real 1x1 B passou nos pênaltis
        # Errou quem passa. Mas placar_b coincide (1==1) → 3 pts por gols
        r = pont(
            Palpite(2, 1),
            Resultado(1, 1, avanca="B"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_vencedor_real_empate_errou_tudo(self):
        # Palpite 3x0 (A vence), real 1x1 B passou. Nada coincide.
        r = pont(
            Palpite(3, 0),
            Resultado(1, 1, avanca="B"),
            "r16",
        )
        assert r.pontos == 0


# ============================================================
# Comparação padrão vs cartola
# ============================================================

class TestComparacaoEntreRegras:
    """Garante que mudar 'regras' realmente muda o resultado."""

    def test_grupos_vencedor_e_gols_diferentes(self):
        # Padrão = 15, Cartola = 12
        p, r = Palpite(3, 0), Resultado(3, 1)
        assert calcular_pontuacao(p, r, "grupos", regras="padrao").pontos == 15
        assert calcular_pontuacao(p, r, "grupos", regras="cartola").pontos == 12

    def test_grupos_so_vencedor_diferentes(self):
        # Padrão = 12, Cartola = 9
        p, r = Palpite(2, 0), Resultado(3, 1)
        assert calcular_pontuacao(p, r, "grupos", regras="padrao").pontos == 12
        assert calcular_pontuacao(p, r, "grupos", regras="cartola").pontos == 9

    def test_default_eh_padrao(self):
        # Sem passar 'regras', deve cair em padrao
        r = calcular_pontuacao(Palpite(3, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 15

    def test_mata_mata_placar_exato_dobra_quase(self):
        # Padrão = 18, Cartola = 30
        p, r = Palpite(3, 1), Resultado(3, 1, avanca="A")
        assert calcular_pontuacao(p, r, "r16", regras="padrao").pontos == 18
        assert calcular_pontuacao(p, r, "r16", regras="cartola").pontos == 30

    def test_mata_mata_empate_exato_avanca_certo(self):
        # Padrão = 18, Cartola = 34
        p = Palpite(1, 1, avanca="A")
        r = Resultado(1, 1, avanca="A")
        assert calcular_pontuacao(p, r, "r16", regras="padrao").pontos == 18
        assert calcular_pontuacao(p, r, "r16", regras="cartola").pontos == 34
