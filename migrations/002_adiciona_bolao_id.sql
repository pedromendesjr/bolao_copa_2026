-- =============================================================
-- Migration 002 - adiciona suporte a múltiplos bolões (bolao_id)
-- =============================================================
-- O que faz:
--   - Adiciona a coluna `bolao_id` em `usuarios` e `palpites`
--   - Migra os dados existentes para o bolão 'lavaprato'
--   - Reconfigura as chaves primárias para serem compostas:
--       usuarios: (bolao_id, telefone)
--       palpites: (bolao_id, telefone, partida_id)
--
-- As tabelas `partidas` e `admins` NÃO mudam: partidas/resultados são
-- compartilhados entre todos os bolões.
--
-- Como rodar: Supabase → SQL Editor → New query → cole → Run.
-- É seguro rodar uma vez. Rodar de novo pode falhar nas constraints
-- (tudo bem, significa que já foi aplicada).
-- =============================================================

-- ---- usuarios ----

-- 1. Adiciona a coluna com default temporário 'lavaprato'
ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS bolao_id TEXT NOT NULL DEFAULT 'lavaprato';

-- 2. Remove o default (novos cadastros devem informar explicitamente)
ALTER TABLE usuarios
    ALTER COLUMN bolao_id DROP DEFAULT;

-- 3. Troca a PK de (telefone) para (bolao_id, telefone)
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_pkey CASCADE;
ALTER TABLE usuarios ADD PRIMARY KEY (bolao_id, telefone);

-- ---- palpites ----

-- 1. Adiciona a coluna com default temporário 'lavaprato'
ALTER TABLE palpites
    ADD COLUMN IF NOT EXISTS bolao_id TEXT NOT NULL DEFAULT 'lavaprato';

ALTER TABLE palpites
    ALTER COLUMN bolao_id DROP DEFAULT;

-- 2. Troca a PK de (telefone, partida_id) para (bolao_id, telefone, partida_id)
ALTER TABLE palpites DROP CONSTRAINT IF EXISTS palpites_pkey CASCADE;
ALTER TABLE palpites ADD PRIMARY KEY (bolao_id, telefone, partida_id);

-- 3. Recria a foreign key de palpites -> usuarios com a chave composta
ALTER TABLE palpites DROP CONSTRAINT IF EXISTS palpites_telefone_fkey;
ALTER TABLE palpites
    ADD CONSTRAINT palpites_usuario_fkey
    FOREIGN KEY (bolao_id, telefone)
    REFERENCES usuarios (bolao_id, telefone)
    ON DELETE CASCADE;

-- ---- índices úteis ----
CREATE INDEX IF NOT EXISTS idx_usuarios_bolao ON usuarios(bolao_id);
CREATE INDEX IF NOT EXISTS idx_palpites_bolao ON palpites(bolao_id);

-- =============================================================
-- Conferir o resultado
-- =============================================================
-- SELECT bolao_id, COUNT(*) FROM usuarios GROUP BY bolao_id;
-- SELECT bolao_id, COUNT(*) FROM palpites GROUP BY bolao_id;