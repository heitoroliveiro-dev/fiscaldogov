# Runbook — papéis do banco em produção

Cria e mantém os dois papéis de acesso do Postgres de produção (Railway). Base: FR-019, princípio V e research §3 da spec 001.

| Papel | Quem usa | Pode | Não pode |
|---|---|---|---|
| dono (usuário administrador da Railway) | só o pré-deploy do ETL (`prisma migrate deploy`) | tudo | — |
| `etl_escrita` | a coleta (`DATABASE_URL_ESCRITA`) e o `pg_dump` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | DDL, `TRUNCATE`, criar no schema |
| `site_leitura` | o build do site (`DATABASE_URL_LEITURA`) | `SELECT` | qualquer escrita |

As permissões vêm da migration `0001_fundacao` (`GRANT` e `ALTER DEFAULT PRIVILEGES`). Este runbook só **cria os papéis e as senhas**. Senha nunca vai para migration, repositório, issue ou chat.

## Quando usar

- **Uma vez, antes do primeiro deploy do ETL.** A migration faz `GRANT` para os papéis; se eles não existirem, ela falha.
- **Ao trocar uma senha:** rotina, suspeita de vazamento ou saída de alguém com acesso.

## 1. Criar os papéis (uma vez)

Pré-requisito: o Postgres da Railway (`postgres-ssl:18`) já existe (T051).

1. Abra uma sessão `psql` com o usuário dono, usando a URL pública do painel da Railway (aba *Connect*). Use `psql` local ou `railway connect Postgres`.
2. Crie os papéis **sem senha no comando**. O `\password` pede a senha no terminal e envia só o hash, então ela não fica no histórico do shell nem no log do servidor:

   ```sql
   CREATE ROLE etl_escrita LOGIN;
   CREATE ROLE site_leitura LOGIN;
   \password etl_escrita
   \password site_leitura
   ```

   Gere cada senha com `openssl rand -base64 33 | tr -d '/+=' | cut -c1-32`. Cole direto no `\password` e no cofre (passo 3), sem salvar em arquivo.

3. Guarde cada URL **só** no cofre de quem a usa:

   | Variável | Onde | Formato |
   |---|---|---|
   | `DATABASE_URL_ESCRITA` | Railway → serviço do ETL → *Variables* | rede privada: `postgresql://etl_escrita:<senha>@<host>.railway.internal:5432/<banco>` |
   | `DATABASE_URL_LEITURA` | GitHub → *Settings* → *Environments* → `producao` → *Secrets* | proxy público: `postgresql://site_leitura:<senha>@<host-publico>:<porta>/<banco>?sslmode=require` |

   Senha com caractere especial precisa de *percent-encoding* na URL. A geração do passo 2 evita esses caracteres.

4. Faça o deploy do ETL. O pré-deploy aplica a migration, que concede as permissões.

## 2. Conferir as permissões

Rode como dono, depois de aplicar a migration. O resultado esperado é exatamente este (conferido no banco local em 2026-10-28):

```sql
SELECT r.papel,
       has_schema_privilege(r.papel, 'public', 'CREATE')            AS cria_no_schema,
       has_table_privilege(r.papel, 'parlamentar', 'SELECT')        AS le,
       has_table_privilege(r.papel, 'parlamentar', 'INSERT')        AS insere,
       has_table_privilege(r.papel, 'parlamentar', 'TRUNCATE')      AS trunca,
       has_table_privilege(r.papel, '_prisma_migrations', 'SELECT') AS le_migrations,
       (SELECT rolsuper OR rolcreaterole OR rolcreatedb
          FROM pg_roles WHERE rolname = r.papel)                    AS privilegio_admin
FROM (VALUES ('etl_escrita'), ('site_leitura')) AS r(papel);
```

```
    papel     | cria_no_schema | le | insere | trunca | le_migrations | privilegio_admin
--------------+----------------+----+--------+--------+---------------+------------------
 etl_escrita  | f              | t  | t      | f      | t             | f
 site_leitura | f              | t  | f      | f      | t             | f
```

Prova prática do papel de leitura (quickstart R4, T060). Conecte com `site_leitura` e rode:

```sql
BEGIN; INSERT INTO partido (sigla) VALUES ('X'); ROLLBACK;
-- esperado: ERROR:  permission denied for table partido
```

Qualquer diferença do esperado → **não publique**. Corrija as permissões com uma migration nova e repita a conferência.

## 3. Trocar uma senha

1. Como dono: `\password etl_escrita` (ou `site_leitura`), com uma senha nova gerada como no passo 1.2.
2. Atualize a URL no cofre correspondente (tabela do passo 1.3).
3. Confira se o próximo uso funciona:
   - **`etl_escrita`:** rode o ETL manualmente com `python -m etl verificar-config` no serviço da Railway, que deve sair com código 0.
   - **`site_leitura`:** acione o `publicar.yml` manualmente (*Run workflow*).

As conexões abertas continuam com a senha antiga até fechar. O ETL e o build abrem conexões novas a cada execução, então nenhum código muda.

**Suspeita de vazamento:** troque a senha **antes** de investigar. Se a suspeita for sobre o dono, troque também a senha dele no painel da Railway.

## 4. Revogar um papel

Só se o papel deixar de existir no projeto:

```sql
REASSIGN OWNED BY site_leitura TO postgres;
DROP OWNED BY site_leitura;
DROP ROLE site_leitura;
```

Antes, remova a URL do cofre. Senão, o próximo build falha com erro de autenticação e o alerta acusa a causa (FR-020a).
