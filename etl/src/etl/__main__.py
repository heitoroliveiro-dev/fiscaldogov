"""Ponto de entrada: python -m etl <comando> (contracts/etl-cli.md).

A configuração é validada antes de qualquer comando: inválida, sai com código 2
sem executar nada. Aqui se montam os adaptadores reais; o pipeline só conhece as
portas. Os comandos reserva e agendado entram na T071.
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from etl import registro
from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorR2, criar_cliente_r2
from etl.adaptadores.camara.api_v2 import CamaraApiV2, criar_cliente
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes
from etl.adaptadores.persistencia.repositorio import Repositorio
from etl.adaptadores.publicacao.github import PublicadorGitHub, criar_cliente_github
from etl.config import Configuracao, ConfiguracaoInvalida, carregar
from etl.pipeline.coletar import Coleta
from etl.portas import Gatilho, StatusExecucao

SAIDA_SUCESSO = 0
SAIDA_FALHA = 1
SAIDA_CONFIGURACAO_INVALIDA = 2

log = logging.getLogger("etl")


def codigo_de_saida(status: StatusExecucao) -> int:
    return SAIDA_FALHA if status is StatusExecucao.FALHA else SAIDA_SUCESSO


def versao_do_codigo(ambiente: Mapping[str, str]) -> str:
    # variável da Railway em deploys vindos do GitHub; conferir no serviço real (T051)
    return ambiente.get("RAILWAY_GIT_COMMIT_SHA") or "desconhecida"


def interpretar(argumentos: list[str]) -> argparse.Namespace:
    """Argumento inválido sai com código 2, o mesmo da configuração inválida."""
    analisador = argparse.ArgumentParser(prog=f"python -m {Path(__file__).parent.name}")
    comandos = analisador.add_subparsers(dest="comando", required=True)
    coletar = comandos.add_parser("coletar", help="coleta da Câmara, gravação e publicação")
    coletar.add_argument(
        "--gatilho",
        type=Gatilho,
        choices=[Gatilho.AGENDADA, Gatilho.MANUAL],
        default=Gatilho.MANUAL,
    )
    comandos.add_parser("verificar-config", help="variáveis e conectividade, sem gravar nada")
    return analisador.parse_args(argumentos)


def verificar(conferencias: Mapping[str, Callable[[], Any]]) -> int:
    """Roda todas as conferências, mesmo depois de uma falha, e relata cada uma."""
    falhas = 0
    for nome, conferir in conferencias.items():
        try:
            conferir()
        except Exception as erro:
            falhas += 1
            log.error(
                "conferência falhou",
                extra={"conferencia": nome, "erro": registro.mascarar(str(erro))},
            )
        else:
            log.info("conferência ok", extra={"conferencia": nome})
    return SAIDA_FALHA if falhas else SAIDA_SUCESSO


def _coletar(config: Configuracao, gatilho: Gatilho) -> int:
    banco = Banco.conectar(config.database_url_escrita, config.tempo_limite_s)
    s3 = criar_cliente_r2(
        config.r2_account_id, config.r2_access_key_id, config.r2_secret_access_key
    )
    try:
        with criar_cliente(config.camara_api_url) as camara, criar_cliente_github() as github:
            coleta = Coleta(
                criar_fonte=lambda ao_receber: CamaraApiV2(camara, ao_receber),
                repositorio=Repositorio(banco),
                brutos=ArmazemDeBrutos(banco, GravadorR2(s3, config.r2_bucket_brutos)),
                execucoes=Execucoes(banco),
                publicador=PublicadorGitHub(
                    github, config.github_repositorio, config.github_token_publicacao
                ),
                versao_codigo=versao_do_codigo(os.environ),
            )
            return codigo_de_saida(coleta.executar(gatilho).status)
    finally:
        banco.fechar()


def _verificar_config(config: Configuracao) -> int:
    def banco() -> None:
        Banco.conectar(config.database_url_escrita, config.tempo_limite_s).fechar()

    def r2() -> None:
        s3 = criar_cliente_r2(
            config.r2_account_id, config.r2_access_key_id, config.r2_secret_access_key
        )
        for bucket in (config.r2_bucket_brutos, config.r2_bucket_backup):
            s3.head_bucket(Bucket=bucket)

    def api_da_camara() -> None:
        # a lista, nunca /deputados/{id}: aquele devolve CPF
        with criar_cliente(config.camara_api_url) as cliente:
            cliente.get("/deputados", params={"itens": 1}).raise_for_status()

    return verificar({"banco": banco, "r2": r2, "api_da_camara": api_da_camara})


def main(argumentos: list[str]) -> int:
    registro.configurar()
    try:
        config = carregar(os.environ)
    except ConfiguracaoInvalida as erro:
        log.error(str(erro))
        return SAIDA_CONFIGURACAO_INVALIDA

    comando = interpretar(argumentos)
    if comando.comando == "coletar":
        return _coletar(config, comando.gatilho)
    return _verificar_config(config)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
