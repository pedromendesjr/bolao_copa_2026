-- =============================================================
-- Guia: cadastrar confrontos do mata-mata
-- =============================================================
-- As partidas 73 a 104 já existem no banco (criadas pelo seed),
-- mas com time_a e time_b NULL (placeholders). Conforme os times
-- forem definidos, atualize cada partida com este modelo.
--
-- Rode no Supabase: SQL Editor → New query → cole → Run.
-- =============================================================

-- EXEMPLO 1: definir os times de uma partida dos 16-avos (M73)
-- Assim que souber quem joga, preencha time_a e time_b.
UPDATE partidas
SET time_a = 'Brasil',
    time_b = 'Noruega'
WHERE numero = 73;

-- EXEMPLO 2: definir vários confrontos de uma vez
-- (repita o bloco para cada partida)
UPDATE partidas SET time_a = 'Argentina', time_b = 'Suíça'   WHERE numero = 74;
UPDATE partidas SET time_a = 'França',    time_b = 'Senegal' WHERE numero = 75;

-- =============================================================
-- IMPORTANTE sobre os nomes dos times
-- =============================================================
-- Use EXATAMENTE os mesmos nomes da fase de grupos, para que as
-- bandeiras apareçam. A lista completa de nomes válidos:
--
--   México, África do Sul, Coreia do Sul, República Tcheca,
--   Canadá, Bósnia e Herzegovina, Catar, Suíça, Brasil, Marrocos,
--   Haiti, Escócia, Estados Unidos, Paraguai, Austrália, Turquia,
--   Alemanha, Curaçao, Costa do Marfim, Equador, Holanda, Japão,
--   Suécia, Tunísia, Bélgica, Egito, Irã, Nova Zelândia, Espanha,
--   Cabo Verde, Arábia Saudita, Uruguai, França, Senegal, Iraque,
--   Noruega, Argentina, Argélia, Áustria, Jordânia, Portugal,
--   República Democrática do Congo, Uzbequistão, Colômbia,
--   Inglaterra, Croácia, Gana, Panamá
--
-- (Acentos e maiúsculas importam: 'brasil' ≠ 'Brasil'.)

-- =============================================================
-- Conferir o estado atual das partidas do mata-mata
-- =============================================================
SELECT numero, fase, time_a, time_b, data_jogo, status
FROM partidas
WHERE fase <> 'grupos'
ORDER BY numero;

-- =============================================================
-- Reverter uma partida para placeholder (se errar o cadastro)
-- =============================================================
-- UPDATE partidas SET time_a = NULL, time_b = NULL WHERE numero = 73;