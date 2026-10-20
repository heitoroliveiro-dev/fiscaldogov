import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

/**
 * O tailwind-merge precisa conhecer os tokens que não existem no Tailwind padrão.
 * Sem isso, `text-2xs` seria lido como cor e removido ao lado de `text-muted-foreground`.
 */
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: ["2xs", "md"],
      shadow: ["raised", "overlay", "modal"],
      ease: ["standard", "enter", "exit"],
    },
  },
});

/** Combina classes condicionais e resolve conflitos do Tailwind (padrão shadcn/ui). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
