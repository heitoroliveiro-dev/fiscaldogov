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
7. Efeitos de luz só em destaque/landing, um por tela.
8. Acessibilidade: `aria-label` em botão só-ícone, `<Label htmlFor>` em todo campo, `aria-invalid` + `aria-describedby` em erro, foco sempre visível, **estado nunca só por cor**.
9. Tokens se editam em `tokens/` e se geram com `npm run tokens` — nunca editar os arquivos gerados.

## Regras deste produto

Derivadas do contexto (§3 público, DA04 neutralidade, OE04 verificabilidade):

- **Mobile-first de verdade.** Toda tela é desenhada primeiro para ~360px de largura. Os breakpoints do sistema já são mobile-first (`sm` 640 · `md` 768 · `lg` 1024).
- **Fonte e data em todo dado.** Componente de "fonte oficial" (casa + link para o registro + data da última atualização) presente em toda tela que mostra dado (RF07, RF08).
- **Termo técnico explicado na tela.** Votação nominal, tramitação, suplente etc. vêm com explicação curta acessível sem sair da página (Tooltip não funciona em toque — usar Popover ou texto expansível).
- **Neutralidade visual.** Nenhum partido é identificado pela sua cor partidária; cores de status (`danger`, `success`) não qualificam pessoas (ex.: taxa de presença baixa não fica vermelha). Ranking mostra o número e a metodologia; o julgamento é do eleitor.
- **Busca visível.** O sistema é keyboard-first (⌘K); aqui o público está no celular, então a busca é um campo visível, e o ⌘K é complemento no desktop.

## Adaptações do sistema — decisões pendentes (suas)

O design system foi feito para uma ferramenta de trabalho densa, no desktop, dark-first. O público deste produto é o eleitor leigo no celular. Pontos em que os dois se chocam:

| # | Ponto | Padrão do sistema | Tensão com o produto | Sugestão (a decidir) |
|---|---|---|---|---|
| D1 | Densidade de texto | Corpo `text-sm` = 13px | Pequeno para leitura casual no celular; no iOS, campo com fonte < 16px dá zoom automático ao focar | Corpo 16px no mobile (`text-base`), 13–14px só em metadados; campos sempre ≥ 16px |
| D2 | Alvo de toque | Controles `h-8` (32px); mínimo 24px (WCAG 2.5.8 AA) | Dedo precisa de mais área que cursor | Alvos de toque ≥ 44px no mobile (WCAG 2.5.5 AAA / Apple HIG); manter densidade no `lg+` |
| D3 | Tema padrão | Dark-first, light completo | Público geral, uso ao ar livre | Seguir a preferência do sistema operacional (`prefers-color-scheme`), com troca manual |
| D4 | Cor de marca | `brand.hue` 277 (violeta) | Cores carregam leitura partidária no Brasil | Manter um matiz sem associação forte a partido ou campanha; violeta é candidato razoável |
| D5 | Efeitos de luz | Glow/BorderBeam em destaque | Sobriedade institucional; custo em celular simples | Restringir à landing, ou não usar |

Cada decisão tomada aqui sai desta tabela e vira regra na seção acima (ou ADR, se mexer nos tokens do sistema).
