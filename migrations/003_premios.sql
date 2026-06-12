-- =============================================================
-- Migration 003 - palpites de prêmios individuais da Copa
-- =============================================================
-- Cria a tabela `premios_palpites` para armazenar os palpites
-- dos usuários sobre prêmios individuais (Seleção Campeã,
-- Artilheiro, Assistência, Luva de Ouro, Jogador Jovem).
--
-- Modelagem: uma linha por (bolao_id, telefone, tipo_premio).
-- Texto livre no campo `palpite`. Pontuação será apurada depois.
-- =============================================================
-- Como rodar: Supabase → SQL Editor → New query → cole → Run.
-- =============================================================

DROP TABLE IF EXISTS premios_palpites CASCADE;
CREATE TABLE premios_palpites (
    bolao_id        TEXT NOT NULL,
    telefone        TEXT NOT NULL,
    tipo_premio     TEXT NOT NULL,        -- 'campeao', 'artilheiro', etc.
    palpite         TEXT NOT NULL,        -- texto livre digitado pela pessoa
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bolao_id, telefone, tipo_premio),
    FOREIGN KEY (bolao_id, telefone)
        REFERENCES usuarios (bolao_id, telefone) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_premios_bolao ON premios_palpites(bolao_id);

-- Trigger para manter atualizado_em sempre correto
CREATE OR REPLACE FUNCTION trg_premios_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS premios_atualizado_em ON premios_palpites;
CREATE TRIGGER premios_atualizado_em
BEFORE UPDATE ON premios_palpites
FOR EACH ROW EXECUTE FUNCTION trg_premios_atualizado_em();

-- Tabela criada com RLS desabilitado (mesmo padrão das outras)
ALTER TABLE premios_palpites DISABLE ROW LEVEL SECURITY;