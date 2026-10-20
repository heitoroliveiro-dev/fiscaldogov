# Diretrizes de UI — Transparência do Congresso

## Base

O design system do projeto é `../design-system/linear` (v1.0.0, commit `9de9123`): tokens W3C DTCG, Tailwind CSS v4, Radix, convenções shadcn/ui, Inter + Geist Mono, lucide-react.

- Regras obrigatórias para geração de UI: `../design-system/linear/AGENTS.md`.
- Guias: `../design-system/linear/docs/` (cores, tipografia, layout, componentes, acessibilidade).
- Forma de adoção (template completo, só o sistema ou só tokens): `../design-system/linear/docs/08-uso-em-novos-projetos.md`. **A escolha depende do ADR-0001 (stack)** e é feita na F2.

Atualizações do design system entram no projeto de forma manual e deliberada (modelo shadcn: o código é copiado), consultando o `CHANGELOG.md` do sistema.

## Regras herdadas (resumo do `AGENTS.md`)

1. Cores só por tokens semânticos (`bg-card`, `text-muted-foreground`…). Nunca hex/rgb literais nem paleta padrão do Tailwind.
2. Reutilizar `src/components/ui` antes de criar markup.
3. Uma ação primária por região.
4. Raio: `rounded-md` controles, `rounded-lg` cards, `rounded-xl` dialogs.
5. Elevação só com `shadow-raised` / `shadow-overlay` / `shadow-modal`.
6. Movimento: `duration-(--duration-fast) ease-standard`; overlays ≤ 200 ms.
7. Acessibilidade: `aria-label` em botão só-ícone, `<Label htmlFor>` em todo campo, `aria-invalid` + `aria-describedby` em erro, foco sempre visível, **estado nunca só por cor**.
8. Tokens se editam em `tokens/` e se geram com `npm run tokens` — nunca editar os arquivos gerados.

## Regras deste produto

Derivadas do contexto (§3 público, DA04 neutralidade, DA06 web responsivo, OE04 verificabilidade).

### Plataforma

- **Web responsivo, computador e celular (DA06).** Site web com domínio próprio, sem app nativo no MVP. Toda tela é desenhada primeiro para 360px e funciona sem rolagem horizontal; no computador (`lg+`) a tela tem layout próprio — mais colunas, gráficos e tabela lado a lado —, não a versão de celular esticada. Breakpoints do sistema: `sm` 640 · `md` 768 · `lg` 1024.
- **Layout de telas grandes.** A partir de `lg` (1024 px), o conteúdo tem largura máxima de 1200 px, centralizado, e blocos de apoio (fonte e data, filtros) ficam ao lado do conteúdo principal, não abaixo dele (spec 001, FR-003).
- **Busca visível.** O campo de busca fica sempre visível; o ⌘K do sistema é só um complemento no desktop.

### Adaptações ao design system (decididas em 2026-10-20)

| # | Ponto | Padrão do sistema | Regra neste produto |
|---|---|---|---|
| D1 | Densidade de texto | Corpo `text-sm` (13px) | Corpo `text-base` (16px) abaixo de `lg`; 13–14px só em metadados. Campos de formulário sempre ≥ 16px (evita zoom automático no iOS). |
| D2 | Alvo de toque | Controles `h-8` (32px) | Alvos de toque ≥ 44px abaixo de `lg` (WCAG 2.5.5 / Apple HIG); densidade do sistema a partir de `lg`. |
| D3 | Tema | Dark-first | Segue `prefers-color-scheme` do sistema operacional, com troca manual; dark e light são obrigatórios em toda tela. |
| D4 | Cor de marca | `brand.hue` 277 (violeta) | Mantido 277: violeta não tem associação forte a partido ou campanha no Brasil. Mudar exige reavaliar esse critério. |
| D5 | Efeitos de luz | Glow/BorderBeam em destaque | Só na landing, no máximo um por tela; nunca em telas de dado. |

### Dado e linguagem

- **Fonte e data em todo dado.** Componente de "fonte oficial" (casa + link para o registro + data da última atualização) em toda tela que mostra dado (RF07, RF08).
- **Termo técnico explicado na tela.** Votação nominal, tramitação, suplente etc. vêm com explicação curta acessível sem sair da página. Tooltip não funciona em toque — usar Popover ou texto expansível.
- **Neutralidade visual.** Nenhum partido é identificado pela sua cor partidária; cores de status (`danger`, `success`) não qualificam pessoas (ex.: taxa de presença baixa não fica vermelha). O ranking mostra o número e a metodologia; o julgamento é do eleitor.
