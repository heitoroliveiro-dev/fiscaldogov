-- Dados fictícios para o build do E2E (T047): um parlamentar em exercício e uma
-- execução com sucesso. Só em banco descartável (CI ou banco local de E2E);
-- nunca em produção. Nome e sigla fictícios de propósito: a página de teste não
-- atribui dado inventado a uma pessoa ou partido reais.
BEGIN;

WITH parlamentar AS (
  INSERT INTO parlamentar (nome_parlamentar, nome_ordenacao, fonte_url, coletado_em)
  VALUES ('Parlamentar de Teste', 'parlamentar de teste',
          'https://dadosabertos.camara.leg.br/api/v2/deputados?itens=100&pagina=1', now())
  RETURNING id
), identificador AS (
  INSERT INTO identificador_externo (parlamentar_id, sistema, valor)
  SELECT id, 'camara_v2', '999001' FROM parlamentar
), partido AS (
  INSERT INTO partido (sigla) VALUES ('TESTE') RETURNING id
), filiacao AS (
  INSERT INTO filiacao (parlamentar_id, partido_id, inicio, fonte_url, coletado_em)
  SELECT parlamentar.id, partido.id, '2023-02-01T03:00:00Z',
         'https://dadosabertos.camara.leg.br/api/v2/deputados/999001/historico', now()
  FROM parlamentar, partido
), mandato AS (
  INSERT INTO mandato (parlamentar_id, casa_id, legislatura_numero, uf)
  SELECT parlamentar.id, casa.id, 57, 'DF'
  FROM parlamentar, casa_legislativa casa WHERE casa.sigla = 'CD'
  RETURNING id
)
INSERT INTO periodo_exercicio (mandato_id, inicio, condicao, motivo_inicio, fonte_url, coletado_em)
SELECT id, '2023-02-01T15:05:00Z', 'titular', 'Posse',
       'https://dadosabertos.camara.leg.br/api/v2/deputados/999001/historico', now()
FROM mandato;

INSERT INTO execucao_etl (status, gatilho, versao_codigo, terminada_em)
VALUES ('sucesso', 'manual', 'seed-e2e', now());

COMMIT;
