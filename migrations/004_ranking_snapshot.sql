-- =============================================================
-- Migration 004 - snapshots históricos do ranking
-- =============================================================
-- Cria a tabela `ranking_snapshots` que armazena a posição e os
-- pontos de cada participante ao final de cada dia que teve jogos
-- finalizados. Usada para o gráfico de evolução temporal.
--
-- Granularidade: 1 linha por (bolao_id, telefone, data_snapshot).
-- O snapshot só é criado quando TODOS os jogos da data
-- estão com status='finalizado'.
-- =============================================================

DROP TABLE IF EXISTS ranking_snapshots CASCADE;
CREATE TABLE ranking_snapshots (
    bolao_id            TEXT NOT NULL,
    telefone            TEXT NOT NULL,
    data_snapshot       DATE NOT NULL,
    posicao             INTEGER NOT NULL,
    pontos              INTEGER NOT NULL,
    placares_exatos     INTEGER NOT NULL DEFAULT 0,
    vencedores_acertados INTEGER NOT NULL DEFAULT 0,
    jogos_palpitados    INTEGER NOT NULL DEFAULT 0,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bolao_id, telefone, data_snapshot),
    FOREIGN KEY (bolao_id, telefone)
        REFERENCES usuarios (bolao_id, telefone) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_bolao_data
    ON ranking_snapshots(bolao_id, data_snapshot);

ALTER TABLE ranking_snapshots DISABLE ROW LEVEL SECURITY;