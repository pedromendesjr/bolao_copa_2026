"""Testes unitários da lógica de pontuação."""
import pytest

from app.scoring import Palpite, Pontuacao, Resultado, calcular_pontuacao


# ============================================================
# FASE DE GRUPOS
# ============================================================

class TestFaseDeGrupos:
    """Regras da fase de grupos (18 / 15 / 12 / 3 / 0)."""

    def test_placar_exato_vence_A(self):
        r = calcular_pontuacao(Palpite(3, 1), Resultado(3, 1), "grupos")
        assert r.pontos == 18
        assert r.cor == "verde"
        assert "exato" in r.motivo.lower()

    def test_placar_exato_vence_B(self):
        r = calcular_pontuacao(Palpite(0, 2), Resultado(0, 2), "grupos")
        assert r.pontos == 18
        assert r.cor == "verde"

    def test_placar_exato_empate(self):
        r = calcular_pontuacao(Palpite(1, 1), Resultado(1, 1), "grupos")
        assert r.pontos == 18
        assert r.cor == "verde"

    def test_acertou_vencedor_e_gols_do_vencedor(self):
        # Brasil 3x1, palpite 3x0 → acertou os 3 do vencedor
        r = calcular_pontuacao(Palpite(3, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 15
        assert r.cor == "verde"

    def test_acertou_vencedor_e_gols_do_perdedor(self):
        # Brasil 3x1, palpite 2x1 → acertou o 1 do perdedor
        r = calcular_pontuacao(Palpite(2, 1), Resultado(3, 1), "grupos")
        assert r.pontos == 15
        assert r.cor == "verde"

    def test_acertou_apenas_o_vencedor(self):
        # Real 3x1, palpite 2x0 → acertou só o vencedor
        r = calcular_pontuacao(Palpite(2, 0), Resultado(3, 1), "grupos")
        assert r.pontos == 12
        assert r.cor == "verde"

    def test_acertou_empate_nao_exato(self):
        r = calcular_pontuacao(Palpite(2, 2), Resultado(1, 1), "grupos")
        assert r.pontos == 12
        assert r.cor == "verde"

    def test_empate_zero_zero_acertou_empate(self):
        r = calcular_pontuacao(Palpite(0, 0), Resultado(1, 1), "grupos")
        assert r.pontos == 12

    def test_acertou_so_gols_de_um_lado_resultado_errado(self):
        # Real 3x1, palpite 3x3 → acertou os 3 mas errou o resultado
        r = calcular_pontuacao(Palpite(3, 3), Resultado(3, 1), "grupos")
        assert r.pontos == 3
        assert r.cor == "amarelo"

    def test_acertou_gols_empate_real_palpite_vencedor(self):
        # Real 1x1, palpite 1x0 → vencedor errado, mas gols A coincidem
        r = calcular_pontuacao(Palpite(1, 0), Resultado(1, 1), "grupos")
        assert r.pontos == 3
        assert r.cor == "amarelo"

    def test_vencedor_invertido_zero_pontos(self):
        # Real 3x1, palpite 1x3 → vencedor errado, sem gols comuns
        r = calcular_pontuacao(Palpite(1, 3), Resultado(3, 1), "grupos")
        assert r.pontos == 0
        assert r.cor == "vermelho"

    def test_palpite_completamente_errado(self):
        r = calcular_pontuacao(Palpite(0, 5), Resultado(3, 1), "grupos")
        assert r.pontos == 0
        assert r.cor == "vermelho"


# ============================================================
# MATA-MATA - palpite EMPATE
# ============================================================

class TestMataMataEmpate:
    """Regras específicas quando o usuário palpita empate."""

    def test_empate_exato_avanca_correto(self):
        # Real 1x1, A avança nos pênaltis; palpite 1x1 + A
        r = calcular_pontuacao(
            Palpite(1, 1, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 18
        assert r.cor == "verde"

    def test_empate_nao_exato_avanca_correto(self):
        # Real 1x1 A avança; palpite 2x2 + A
        r = calcular_pontuacao(
            Palpite(2, 2, avanca="A"),
            Resultado(1, 1, avanca="A"),
            "quartas",
        )
        assert r.pontos == 15
        assert r.cor == "verde"

    def test_empate_exato_avanca_errado(self):
        # Real 1x1 A avança; palpite 1x1 + B
        r = calcular_pontuacao(
            Palpite(1, 1, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 12
        assert r.cor == "verde"

    def test_empate_nao_exato_avanca_errado(self):
        # Real 1x1 A avança; palpite 2x2 + B
        r = calcular_pontuacao(
            Palpite(2, 2, avanca="B"),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 9
        assert r.cor == "amarelo"

    def test_palpite_empate_real_vencedor_acertou_quem_passou(self):
        # Real 2x1 A vence; palpite 1x1 + A
        r = calcular_pontuacao(
            Palpite(1, 1, avanca="A"),
            Resultado(2, 1, avanca="A"),
            "r32",
        )
        assert r.pontos == 3
        assert r.cor == "amarelo"

    def test_palpite_empate_real_vencedor_errou_quem_passou(self):
        # Real 2x1 A vence; palpite 1x1 + B
        r = calcular_pontuacao(
            Palpite(1, 1, avanca="B"),
            Resultado(2, 1, avanca="A"),
            "r32",
        )
        assert r.pontos == 0
        assert r.cor == "vermelho"


# ============================================================
# MATA-MATA - palpite com VENCEDOR
# ============================================================

class TestMataMataVencedor:
    """Quando o palpite tem vencedor, aplicam-se as regras de grupos
    (avanca é redundante com o vencedor do palpite)."""

    def test_placar_exato_jogo_normal(self):
        # Real 3x1 A vence; palpite 3x1
        r = calcular_pontuacao(
            Palpite(3, 1),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 18
        assert r.cor == "verde"

    def test_vencedor_certo_gols_um_lado(self):
        # Real 3x1; palpite 3x0
        r = calcular_pontuacao(
            Palpite(3, 0),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 15

    def test_vencedor_certo_sem_gols(self):
        # Real 3x1; palpite 2x0
        r = calcular_pontuacao(
            Palpite(2, 0),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 12

    def test_palpite_vencedor_real_empate_acertou_quem_passou(self):
        # Real 1x1, A passa nos pênaltis; palpite 2x1 (vencedor A)
        # Errou resultado (vencedor != real_vencedor None), mas acertou
        # quem passou. Também acerta gols_b (1=1). Cai em 3 pts.
        r = calcular_pontuacao(
            Palpite(2, 1),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3
        assert r.cor == "amarelo"

    def test_palpite_vencedor_real_empate_errou_quem_passou(self):
        # Real 1x1, A passa; palpite 0x2 (vencedor B), sem gols coincidentes
        r = calcular_pontuacao(
            Palpite(0, 2),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 0

    def test_palpite_vencedor_real_empate_errou_quem_passou_mas_gols_um_lado(self):
        # Real 1x1, A passa; palpite 0x1 (vencedor B, errou quem passou),
        # mas placar_b coincide (1=1) → 3 pts pela faixa "gols de um lado"
        r = calcular_pontuacao(
            Palpite(0, 1),
            Resultado(1, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 3

    def test_palpite_vencedor_invertido_zero(self):
        # Real 3x1, A passa; palpite 1x3, sem coincidência
        r = calcular_pontuacao(
            Palpite(1, 3),
            Resultado(3, 1, avanca="A"),
            "r16",
        )
        assert r.pontos == 0


# ============================================================
# Validações gerais
# ============================================================

class TestProprieadesGerais:
    """Invariantes que valem para qualquer caso."""

    @pytest.mark.parametrize("fase", ["grupos", "r32", "r16", "quartas", "semi", "final"])
    def test_palpite_igual_ao_resultado_sempre_18(self, fase):
        avanca = None if fase == "grupos" else "A"
        r = calcular_pontuacao(
            Palpite(2, 1, avanca=avanca),
            Resultado(2, 1, avanca=avanca),
            fase,
        )
        assert r.pontos == 18

    def test_cor_consistente_com_pontos(self):
        casos = [
            (Palpite(3, 1), Resultado(3, 1), "grupos", "verde"),     # 18
            (Palpite(2, 1), Resultado(3, 1), "grupos", "verde"),     # 15
            (Palpite(2, 0), Resultado(3, 1), "grupos", "verde"),     # 12
            (Palpite(3, 3), Resultado(3, 1), "grupos", "amarelo"),   # 3
            (Palpite(1, 3), Resultado(3, 1), "grupos", "vermelho"),  # 0
        ]
        for palpite, resultado, fase, cor_esperada in casos:
            r = calcular_pontuacao(palpite, resultado, fase)
            assert r.cor == cor_esperada, (
                f"Esperava cor {cor_esperada} mas obteve {r.cor} "
                f"({r.pontos} pts, motivo: {r.motivo})"
            )
