"""Novas tentativas de uma requisição (FR-013, research §5).

Até 3 tentativas (a original + 2 novas), com esperas de 5 s e 20 s. Quem chama
diz o que é falha passageira: este módulo não conhece o cliente HTTP. Cada
tentativa que falha é registrada, para ir a execucao_etl.tentativas.
"""

import time
from collections.abc import Callable
from typing import Any

from etl import registro

ESPERAS_S = (5, 20)
MAXIMO_DE_TENTATIVAS = len(ESPERAS_S) + 1


def com_tentativas[T](
    operacao: Callable[[], T],
    *,
    passageira: Callable[[Exception], bool],
    descricao: str,
    esperar: Callable[[float], None] = time.sleep,
    registrar: Callable[[dict[str, Any]], None] = lambda _: None,
) -> T:
    for tentativa in range(1, MAXIMO_DE_TENTATIVAS + 1):
        try:
            return operacao()
        except Exception as erro:
            if not passageira(erro):
                raise
            espera = ESPERAS_S[tentativa - 1] if tentativa < MAXIMO_DE_TENTATIVAS else None
            registrar(
                {
                    "requisicao": descricao,
                    "tentativa": tentativa,
                    "erro": type(erro).__name__,
                    "detalhe": registro.mascarar(_detalhe(erro)),
                    "espera_s": espera,
                }
            )
            if espera is None:
                raise
            esperar(espera)
    raise AssertionError("inalcançável: a última tentativa devolve ou levanta")


def _detalhe(erro: Exception) -> str:
    # HTTP com status: só o código, sem a URL inteira
    resposta = getattr(erro, "response", None)
    codigo = getattr(resposta, "status_code", None)
    return f"HTTP {codigo}" if codigo is not None else str(erro)
