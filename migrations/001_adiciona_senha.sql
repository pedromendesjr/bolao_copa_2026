-- =============================================================
-- Migration 001 - adiciona campo `senha` em `usuarios`
-- =============================================================
-- Quando rodar: SOMENTE se você já rodou o schema.sql original
-- (sem o campo senha) no Supabase. Se for fazer setup do zero,
-- basta rodar schema.sql atualizado.
-- =============================================================
-- Como rodar:
--   1. Supabase → SQL Editor → New query
--   2. Cole este arquivo e clique Run
-- =============================================================

-- Adiciona o campo `senha` à tabela `usuarios`.
-- Como pode haver registros pré-existentes sem senha, usamos
-- DEFAULT '0000' para preencher e depois removemos o DEFAULT.
ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS senha TEXT NOT NULL DEFAULT '0000';

ALTER TABLE usuarios
    ALTER COLUMN senha DROP DEFAULT;

-- Constraint: senha deve ter exatamente 4 dígitos numéricos
ALTER TABLE usuarios
    DROP CONSTRAINT IF EXISTS senha_quatro_digitos;

ALTER TABLE usuarios
    ADD CONSTRAINT senha_quatro_digitos CHECK (senha ~ '^[0-9]{4}$');

-- Constraint: telefone deve ter exatamente 11 dígitos
ALTER TABLE usuarios
    DROP CONSTRAINT IF EXISTS telefone_onze_digitos;

ALTER TABLE usuarios
    ADD CONSTRAINT telefone_onze_digitos CHECK (telefone ~ '^[0-9]{11}$');
