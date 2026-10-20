# ADR-0002 — Hospedagem, publicação diária, agendamento e backup

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** Heitor Oliveiro

## Contexto

Com a stack definida (ADR-0001), falta decidir onde cada parte roda e como os dados viram páginas publicadas todo dia. As forças em jogo:

- **RNF01:** o ETL roda de madrugada; dados de um dia no ar até as 08:00 do dia seguinte.
- **RNF02:** disponibilidade de 99% ao mês; falha do ETL não derruba o site.
- **RNF03:** LCP ≤ 2,5 s no 4G.
- **RNF04:** custo ≤ US$ 10/mês, sem escalar com o acesso (≥ 95% das requisições servidas por cache/CDN); risco de tráfego viral (R07).
- **RNF07:** alertas no Telegram para falha do ETL e queda do site.
- **Constituição, princípio V:** o site só lê; a credencial de escrita fica só com o ETL.
- **Infraestrutura existente:** plano Hobby do Railway (US$ 5/mês, com US$ 5 de uso incluído); repositório público no GitHub (DA08).
- **Escopo do M1:** nenhuma tela precisa de consulta dinâmica — presença, perfil, ranking, home e metodologia mudam só quando o ETL roda.

## Decisão

**O site é gerado inteiro como arquivos estáticos depois de cada execução do ETL e servido pela Cloudflare.**

```
03:00 BRT  Railway — cron do ETL (Python)
           ├─ coleta as fontes (DA07), grava e calcula as estatísticas no Postgres
           ├─ pg_dump → Cloudflare R2
           ├─ heartbeat → monitor de execução
           └─ dispara o build no GitHub (repository_dispatch)
                         ▼
           GitHub Actions
           ├─ next build com output: 'export', lendo o banco com o papel só-SELECT
           └─ publica os arquivos na Cloudflare (Workers static assets)
                         ▼
           Cloudflare — domínio do projeto, arquivos estáticos
```

| Parte | Decisão |
|---|---|
| **Site** | Next.js em **exportação estática** (`output: 'export'`): uma página HTML por rota, gerada no build. Rotas dinâmicas (perfil do deputado) usam `generateStaticParams`. Filtros do ranking (partido, estado, ano) rodam no navegador sobre um JSON gerado no mesmo build. |
| **Servir o site** | **Cloudflare Workers static assets** no plano gratuito: requisições a arquivos estáticos são gratuitas e ilimitadas; até 20.000 arquivos por versão (o M1 tem da ordem de 1.500). DNS do domínio na Cloudflare. |
| **Build e publicação** | **GitHub Actions** (gratuito em repositório público), disparado pelo ETL ao terminar com sucesso, e também a cada merge em `main`. Se o build falhar, a versão anterior continua no ar. |
| **Banco** | Postgres no Railway (ADR-0001). O ETL acessa pela rede privada do Railway com o papel de escrita. O build acessa pelo proxy público do Railway (TLS) **apenas com o papel só-SELECT**. |
| **Agendamento do ETL** | **Cron do Railway**, `0 6 * * *` (06:00 UTC = 03:00 em Brasília). O serviço termina ao fim da execução e só é cobrado enquanto roda. Se uma execução ainda estiver rodando na hora da próxima, o Railway pula a nova. |
| **Backup** | O ETL faz **`pg_dump` diário para o Cloudflare R2** (gratuito até 10 GB), com retenção de 7 diários e 4 semanais. Runbook de restauração escrito e testado na F4. Se o Railway oferecer backup de volume no Hobby, ele é ativado como segunda camada. |
| **Monitoramento** | Heartbeat do ETL num monitor externo gratuito (alerta se não houver sinal em 26 h) e checagem de disponibilidade do site a cada 5 min, ambos com alerta no Telegram (RNF02, RNF07). Ferramentas escolhidas na F4. |
| **Segredos** | No Railway: URL do banco com o papel de escrita, token do GitHub (fine-grained, só para disparar o workflow deste repositório), credenciais do R2 e do monitor. No GitHub: URL do banco com o papel só-SELECT e token da Cloudflare restrito ao deploy. Nenhum no repositório (princípio VI). |

**Custo estimado:** Railway dentro dos US$ 5 já pagos (Postgres + alguns minutos diários de ETL); Cloudflare, GitHub Actions, R2 e monitores no plano gratuito. Total ≈ US$ 5/mês + domínio.

## Alternativas consideradas

- **Servidor Next.js no Railway com a Cloudflare como cache na frente.** Permitiria atualização incremental e partes dinâmicas desde já, mas acrescenta ~US$ 3–5/mês de servidor sempre ligado, e no tráfego viral toda requisição que escapa do cache chega a um servidor pequeno. Sem tela dinâmica no M1, o custo não se paga.
- **Vercel (plano Hobby).** Integração nativa com o Next.js, mas o Hobby é para uso pessoal e não comercial e tem teto de tráfego mensal; ao estourar, exige o Pro (US$ 20/mês), fora da RNF04.
- **ETL agendado no GitHub Actions.** Gratuito e tudo num lugar só, mas em repositório público o agendamento é desligado automaticamente após 60 dias sem atividade, o que pararia o site em silêncio, e a credencial de escrita do banco sairia do Railway.
- **O ETL exportar um arquivo de dados para o build, sem o build acessar o banco.** Evitaria expor o banco pelo proxy público, mas cria um segundo formato de dados para manter em sincronia com o schema, e o Prisma (ADR-0001) ficaria sem uso. O risco do proxy é contido pelo papel só-SELECT.
- **Só o backup de volume do Railway.** A documentação não deixa claro se o Hobby inclui backup de volume; o dump no R2 independe do plano e do provedor.
- **Sem backup, recriando tudo das fontes.** Quase tudo pode ser recoletado, mas a leitura única da lacuna de 2020 (S1) e o histórico de execuções se perderiam, e a restauração levaria horas.

## Consequências

- **Positivas:**
  - O custo não cresce com o acesso; o tráfego viral é absorvido pela Cloudflare sem custo (RNF04, R07).
  - Não há servidor de site para cair: se o ETL ou o build falharem, a última versão continua no ar com a data visível (RNF02).
  - Páginas prontas favorecem o LCP no celular (RNF03) e a prévia de compartilhamento (RF10).
- **Negativas / trade-offs:**
  - Nada dinâmico no site enquanto durar esta decisão: sem busca no servidor, sem atualização incremental, sem redirects e headers do Next (vão para a configuração da Cloudflare).
  - Três provedores para operar (Railway, GitHub, Cloudflare), cada um com seus segredos.
  - O banco fica acessível pelo proxy público do Railway, ainda que só com o papel de leitura.
  - Toda mudança de dado só aparece depois do build seguinte.
- **Riscos e mitigação:**
  - *Prévias de compartilhamento (RF10) na exportação estática* → validar na F2 que as imagens são geradas no build; alternativa: o ETL gerar as imagens.
  - *HU03 (busca em dezenas de milhares de proposições) não cabe em páginas pré-geradas nem no limite de 20.000 arquivos* → ADR próprio antes da HU03 (candidatos: Worker com cache na Cloudflare, ou o adaptador OpenNext).
  - *Build falhando em silêncio* → o workflow alerta no Telegram em caso de falha, e o monitor de disponibilidade confere a data da última atualização exibida.
  - *Credencial vazada do papel de leitura* → só permite ler dados públicos; troca de senha documentada em runbook.

## Referências

- Next.js, exportação estática (recursos suportados e não suportados): <https://nextjs.org/docs/app/guides/static-exports>
- Cloudflare Workers, static assets (gratuitos e ilimitados): <https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/>
- Cloudflare Workers, limites (20.000 arquivos no Free; 100.000 requisições/dia para o Worker): <https://developers.cloudflare.com/workers/platform/limits/>
- Railway, cron jobs (UTC, intervalo mínimo de 5 min, execução sobreposta é pulada): <https://docs.railway.com/reference/cron-jobs>
- Railway, backups de volume: <https://docs.railway.com/reference/backups>
- GitHub Actions, agendamento desligado após 60 dias sem atividade: <https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow>
- Análise de custo: ver a entrevista de requisitos não funcionais (RNF04) e o risco R07 no contexto.
