"""Texto dos alertas ao responsável (FR-029, FR-020a, research §10).

O alerta diz o tipo da falha e o execucao_id. Credencial recusada aparece como
"falha de autenticação: <credencial>", para o responsável saber o que renovar.
"""

from collections.abc import Sequence
from typing import Any

from etl import registro
from etl.portas import CredencialInvalida


def descrever_erro(erro: BaseException) -> dict[str, str]:
    descricao = {"tipo": type(erro).__name__, "mensagem": registro.mascarar(str(erro))}
    if isinstance(erro, CredencialInvalida):
        descricao["credencial"] = erro.credencial
    return descricao


def _linha(problema: dict[str, Any]) -> str:
    etapa = problema.get("etapa", "?")
    if "credencial" in problema:
        return f"- {etapa}: falha de autenticação: {problema['credencial']}"
    partes = [problema.get("tipo"), problema.get("mensagem")]
    if "falhas" in problema:
        partes.append(f"{problema['falhas']} falha(s)")
    return f"- {etapa}: " + " — ".join(str(p) for p in partes if p)


def montar_alerta(titulo: str, execucao_id: int | None, problemas: Sequence[dict[str, Any]]) -> str:
    linhas = [f"fiscaldogov: {titulo}"]
    if execucao_id is not None:
        linhas.append(f"execução {execucao_id}")
    linhas.extend(_linha(problema) for problema in problemas)
    return "\n".join(linhas)
