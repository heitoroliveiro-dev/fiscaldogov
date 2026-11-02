-- FR-006: a página escolhe o deputado pela mesma ordem que o ETL (Python), que
-- compara por código de caractere. A collation do banco (en_US) ignora espaço e
-- pontuação no primeiro nível e poria "anabela" antes de "ana paula".
-- O Prisma não representa collation no schema.prisma: a regra vive só aqui.
ALTER TABLE "parlamentar" ALTER COLUMN "nome_ordenacao" TYPE text COLLATE "C";
