import type { NextConfig } from "next";

// Exportação estática: o site é gerado inteiro após cada coleta e servido pela CDN (ADR-0002).
const nextConfig: NextConfig = {
  output: "export",
  reactStrictMode: true,
  images: { unoptimized: true },
};

export default nextConfig;
