-- Papéis de acesso para DESENVOLVIMENTO e CI (banco local ou efêmero).
-- Senhas de teste, conhecidas de propósito. Em produção os papéis são criados
-- pelo runbook docs/05-runbooks/banco-papeis.md, com senhas que só existem nos cofres.
-- As permissões (GRANT) vêm da migration 0001_fundacao, não daqui.
CREATE ROLE etl_escrita LOGIN PASSWORD 'dev_etl_escrita';
CREATE ROLE site_leitura LOGIN PASSWORD 'dev_site_leitura';
