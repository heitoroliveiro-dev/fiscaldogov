import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Transparência do Congresso — versão de testes",
  description: "Atuação de deputados federais com dados oficiais da Câmara, fonte e data.",
  // FR-005: a página de testes fica fora dos buscadores (também no _headers)
  robots: { index: false, follow: false },
};

export default function Layout({ children }: { children: ReactNode }) {
  return (
    // next-themes muda a classe do <html> antes da hidratação
    <html lang="pt-BR" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
