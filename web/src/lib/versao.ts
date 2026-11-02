// FR-028: identifica a versão publicada (execução da coleta + commit do build).
// GITHUB_SHA existe no GitHub Actions; fora dele, o build é local.
export const COMMIT = process.env.GITHUB_SHA ?? "local";

export function versaoPublicada(execucaoId: number): string {
  return `execucao=${execucaoId};commit=${COMMIT}`;
}
