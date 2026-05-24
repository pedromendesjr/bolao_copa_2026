-- =============================================================
-- Bolão Copa do Mundo 2026 - Schema Supabase / Postgres
-- =============================================================
-- Como usar:
--   1. Acesse seu projeto no Supabase
--   2. Vá em "SQL Editor" e cole este arquivo inteiro
--   3. Clique em "Run"
-- =============================================================

-- Tipos enumerados ---------------------------------------------------
DROP TYPE IF EXISTS fase_torneio CASCADE;
CREATE TYPE fase_torneio AS ENUM (
    'grupos',     -- fase de grupos
    'r32',        -- 16-avos de final (Round of 32)
    'r16',        -- oitavas de final (Round of 16)
    'quartas',    -- quartas de final
    'semi',       -- semifinal
    'terceiro',   -- disputa de 3º lugar
    'final'       -- final
);

DROP TYPE IF EXISTS status_partida CASCADE;
CREATE TYPE status_partida AS ENUM (
    'agendado',
    'em_andamento',
    'finalizado'
);

-- Tabela: usuarios ---------------------------------------------------
DROP TABLE IF EXISTS usuarios CASCADE;
CREATE TABLE usuarios (
    bolao_id      TEXT NOT NULL,                -- ex: 'lavaprato', 'cartola'
    telefone      TEXT NOT NULL,                -- 11 dígitos: DD9XXXXXXXX
    nome          TEXT NOT NULL,
    senha         TEXT NOT NULL,                -- 4 dígitos numéricos
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bolao_id, telefone),
    CONSTRAINT senha_quatro_digitos CHECK (senha ~ '^[0-9]{4}$'),
    CONSTRAINT telefone_onze_digitos CHECK (telefone ~ '^[0-9]{11}$')
);

-- Tabela: partidas ---------------------------------------------------
DROP TABLE IF EXISTS partidas CASCADE;
CREATE TABLE partidas (
    id                SERIAL PRIMARY KEY,
    numero            INTEGER UNIQUE NOT NULL,  -- número oficial da partida (1..104)
    fase              fase_torneio NOT NULL,
    grupo             CHAR(1),                  -- 'A'..'L' na fase de grupos; NULL no mata-mata
    time_a            TEXT,                     -- NULL no mata-mata enquanto não definido
    time_b            TEXT,
    placeholder_a     TEXT,                     -- descrição do slot, ex: '1A', '2B', 'Vencedor M73'
    placeholder_b     TEXT,
    data_jogo         DATE NOT NULL,
    horario           TIME,                     -- opcional; usado apenas para exibição
    placar_a          INTEGER,                  -- placar oficial (após o jogo)
    placar_b          INTEGER,
    avanca            CHAR(1),                  -- 'A' ou 'B': quem avançou (só mata-mata)
    status            status_partida NOT NULL DEFAULT 'agendado',
    disponivel        BOOLEAN NOT NULL DEFAULT TRUE,  -- se aceita palpites
    CONSTRAINT placar_consistente CHECK (
        (placar_a IS NULL AND placar_b IS NULL) OR
        (placar_a IS NOT NULL AND placar_b IS NOT NULL)
    ),
    CONSTRAINT avanca_valido CHECK (avanca IS NULL OR avanca IN ('A', 'B'))
);

CREATE INDEX idx_partidas_fase  ON partidas(fase);
CREATE INDEX idx_partidas_data  ON partidas(data_jogo);
CREATE INDEX idx_partidas_grupo ON partidas(grupo);

-- Tabela: palpites ---------------------------------------------------
DROP TABLE IF EXISTS palpites CASCADE;
CREATE TABLE palpites (
    bolao_id        TEXT NOT NULL,
    telefone        TEXT NOT NULL,
    partida_id      INTEGER NOT NULL REFERENCES partidas(id) ON DELETE CASCADE,
    placar_a        INTEGER NOT NULL CHECK (placar_a >= 0),
    placar_b        INTEGER NOT NULL CHECK (placar_b >= 0),
    avanca          CHAR(1) CHECK (avanca IS NULL OR avanca IN ('A', 'B')),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bolao_id, telefone, partida_id),
    FOREIGN KEY (bolao_id, telefone)
        REFERENCES usuarios (bolao_id, telefone) ON DELETE CASCADE
);

CREATE INDEX idx_palpites_partida ON palpites(partida_id);
CREATE INDEX idx_palpites_bolao   ON palpites(bolao_id);
CREATE INDEX idx_usuarios_bolao   ON usuarios(bolao_id);

-- Trigger para manter atualizado_em sempre correto -------------------
CREATE OR REPLACE FUNCTION trg_palpites_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS palpites_atualizado_em ON palpites;
CREATE TRIGGER palpites_atualizado_em
BEFORE UPDATE ON palpites
FOR EACH ROW EXECUTE FUNCTION trg_palpites_atualizado_em();

-- Tabela: admins -----------------------------------------------------
DROP TABLE IF EXISTS admins CASCADE;
CREATE TABLE admins (
    telefone TEXT PRIMARY KEY REFERENCES usuarios(telefone) ON DELETE CASCADE
);

-- =============================================================
-- Observação sobre Row Level Security (RLS)
-- =============================================================
-- Para um bolão entre amigos (~30 pessoas), recomendo deixar
-- RLS DESATIVADO e proteger no app via Streamlit. Isso simplifica
-- o desenvolvimento. Mais tarde, se quiser endurecer, ative RLS e
-- crie policies por telefone. As linhas abaixo deixam explícito:
ALTER TABLE usuarios  DISABLE ROW LEVEL SECURITY;
ALTER TABLE partidas  DISABLE ROW LEVEL SECURITY;
ALTER TABLE palpites  DISABLE ROW LEVEL SECURITY;
ALTER TABLE admins    DISABLE ROW LEVEL SECURITY;