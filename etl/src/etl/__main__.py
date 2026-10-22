"""Ponto de entrada: python -m etl <comando> (contracts/etl-cli.md).

A configuração é validada antes de qualquer comando: inválida, sai com código 2
sem executar nada. Os comandos entram na T040 (coletar, verificar-config) e na
T071 (reserva, agendado).
"""

import logging
import os
import sys

from etl import registro
from etl.config import ConfiguracaoInvalida, carregar

SAIDA_FALHA = 1
SAIDA_CONFIGURACAO_INVALIDA = 2

log = logging.getLogger("etl")


def main(argumentos: list[str]) -> int:
    registro.configurar()
    try:
        carregar(os.environ)
    except ConfiguracaoInvalida as erro:
        log.error(str(erro))
        return SAIDA_CONFIGURACAO_INVALIDA

    comando = argumentos[0] if argumentos else ""
    log.error("comando ainda não disponível: %r", comando)
    return SAIDA_FALHA


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
