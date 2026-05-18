"""Testes do cálculo de ranking."""
import pytest

from app.ranking import calcular_ranking


def _u(tel, nome):
    return {"telefone": tel, "nome": nome}


def _partida(pid, fase, placar_a, placar_b, avanca=None, status="finalizado"):
    return {
        "id": pid,
        "fase": fase,
        "status": status,
        "placar_a": placar_a,
        "placar_b": placar_b,
        "avanca": avanca,
    }


def _palpite(tel, pid, a, b, avanca=None):
    return {
        "telefone": tel,
        "partida_id": pid,
        "placar_a": a,
        "placar_b": b,
        "avanca": avanca,
    }


# ============================================================
# Caso simples
# ============================================================

class TestRankingBasico:

    def test_ranking_vazio(self):
        """Sem usuários, retorna lista vazia."""
        assert calcular_ranking([], [], []) == []

    def test_sem_partidas_finalizadas_todos_zerados(self):
        """Se nenhum jogo terminou, todos com 0 pts."""
        usuarios = [_u("1", "Alice"), _u("2", "Bob")]
        partidas = [_partida(1, "grupos", None, None, status="agendado")]
        palpites = [_palpite("1", 1, 2, 1)]

        r = calcular_ranking(usuarios, partidas, palpites)
        assert len(r) == 2
        assert all(linha.pontos == 0 for linha in r)
        # Desempate por nome alfabético
        assert r[0].nome == "Alice"
        assert r[1].nome == "Bob"

    def test_um_usuario_acerta_placar_exato(self):
        usuarios = [_u("1", "Alice"), _u("2", "Bob")]
        partidas = [_partida(1, "grupos", 2, 1)]
        palpites = [
            _palpite("1", 1, 2, 1),   # Alice acertou exato (18)
            _palpite("2", 1, 0, 5),   # Bob errou tudo (0)
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].nome == "Alice"
        assert r[0].pontos == 18
        assert r[0].placares_exatos == 1
        assert r[0].vencedores_acertados == 1
        assert r[1].nome == "Bob"
        assert r[1].pontos == 0


# ============================================================
# Critérios de desempate
# ============================================================

class TestDesempate:

    def test_desempate_por_placares_exatos(self):
        """Mesmos pontos, mais placares exatos vence."""
        usuarios = [_u("1", "Alice"), _u("2", "Bob")]
        # Alice: 1 exato (18). Bob: 18 = 15+3 sem exato.
        partidas = [
            _partida(1, "grupos", 2, 1),
            _partida(2, "grupos", 1, 0),
        ]
        palpites = [
            _palpite("1", 1, 2, 1),   # Alice: 18 (exato)
            _palpite("1", 2, 5, 5),   # Alice: 0
            _palpite("2", 1, 2, 0),   # Bob: 15 (vencedor+gols A)
            _palpite("2", 2, 1, 2),   # Bob: 3 (gols B coincidem)
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].pontos == 18
        assert r[1].pontos == 18
        # Alice ganha o desempate (1 exato vs 0)
        assert r[0].nome == "Alice"
        assert r[0].placares_exatos == 1
        assert r[1].placares_exatos == 0

    def test_desempate_por_vencedores_acertados(self):
        """Mesmos pontos e mesmos exatos, mais vencedores vence."""
        usuarios = [_u("1", "Alice"), _u("2", "Bob")]
        partidas = [
            _partida(1, "grupos", 2, 1),
            _partida(2, "grupos", 0, 3),
        ]
        palpites = [
            # Alice: 12 + 3 = 15, 0 exatos, 1 vencedor (jogo 1: 1x0 acertou A vencer)
            _palpite("1", 1, 1, 0),
            _palpite("1", 2, 0, 0),  # gols A coincidem → 3 pts
            # Bob: 15 + 0 = 15, 0 exatos, 1 vencedor (jogo 1 acertou A)
            _palpite("2", 1, 2, 0),  # vencedor + gols A
            _palpite("2", 2, 5, 5),  # errou
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].pontos == 15
        assert r[1].pontos == 15
        assert r[0].placares_exatos == 0
        assert r[1].placares_exatos == 0
        # Ambos têm 1 vencedor; desempate vai pra alfabético
        assert r[0].nome == "Alice"

    def test_desempate_final_alfabetico(self):
        """Tudo igual, ordem alfabética."""
        usuarios = [_u("1", "Carlos"), _u("2", "Ana")]
        partidas = []  # ninguém pontuou
        palpites = []
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].nome == "Ana"
        assert r[1].nome == "Carlos"


# ============================================================
# Casos de borda
# ============================================================

class TestBordas:

    def test_palpite_orfao_ignorado(self):
        """Palpite de usuário inexistente é ignorado, não causa erro."""
        usuarios = [_u("1", "Alice")]
        partidas = [_partida(1, "grupos", 2, 1)]
        palpites = [
            _palpite("1", 1, 2, 1),
            _palpite("99", 1, 0, 0),  # usuário não cadastrado
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert len(r) == 1
        assert r[0].pontos == 18

    def test_palpite_de_jogo_agendado_ignorado(self):
        """Palpite de partida ainda não finalizada não pontua."""
        usuarios = [_u("1", "Alice")]
        partidas = [_partida(1, "grupos", None, None, status="agendado")]
        palpites = [_palpite("1", 1, 2, 1)]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].pontos == 0
        assert r[0].jogos_palpitados == 0

    def test_usuario_sem_palpites_aparece_zerado(self):
        """Cadastrado mas não palpitou aparece no ranking com 0 pts."""
        usuarios = [_u("1", "Alice"), _u("2", "Bob")]
        partidas = [_partida(1, "grupos", 2, 1)]
        palpites = [_palpite("1", 1, 2, 1)]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert len(r) == 2
        assert r[0].nome == "Alice" and r[0].pontos == 18
        assert r[1].nome == "Bob" and r[1].pontos == 0

    def test_mata_mata_conta_no_ranking(self):
        """Pontos de jogos do mata-mata também entram no ranking."""
        usuarios = [_u("1", "Alice")]
        partidas = [
            _partida(1, "grupos", 2, 1),
            _partida(2, "r16", 1, 1, avanca="A"),
        ]
        palpites = [
            _palpite("1", 1, 2, 1),                    # 18
            _palpite("1", 2, 1, 1, avanca="A"),        # 18 (mata-mata)
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].pontos == 36
        assert r[0].placares_exatos == 2
        assert r[0].jogos_palpitados == 2

    def test_jogos_palpitados_conta_so_finalizados(self):
        """Contador de jogos palpitados só inclui partidas finalizadas."""
        usuarios = [_u("1", "Alice")]
        partidas = [
            _partida(1, "grupos", 2, 1),
            _partida(2, "grupos", None, None, status="agendado"),
        ]
        palpites = [
            _palpite("1", 1, 2, 1),
            _palpite("1", 2, 0, 0),
        ]
        r = calcular_ranking(usuarios, partidas, palpites)
        assert r[0].jogos_palpitados == 1
