"""Comando coletar: etapas 1–5, 7 e 8 de contracts/etl-cli.md (T040).

As respostas brutas chegam durante a coleta e ficam em memória até haver
execucao_id; são guardadas antes da gravação dos dados (etapa 4) e também
quando a coleta falha, para diagnóstico. Falha da fonte ou da gravação vira
`falha` sem gravar nada; falha ao guardar bruto ou ao disparar a publicação vira
`com_pendencias`, com os dados gravados.

Vigia de 60 min, recusa com código 3, alertas e backup entram na US2 e na US5.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from etl import registro
from etl.dominio.entidades import DadosDoParlamentar, IdentificadorExterno, Mandato, Parlamentar
from etl.dominio.historico import derivar_filiacoes, derivar_periodos, derivar_uf
from etl.dominio.selecao import selecionar_deputado
from etl.portas import (
    ArmazemDeBrutos,
    FonteDaCasa,
    Gatilho,
    Publicador,
    RegistroDeExecucoes,
    RepositorioDeDados,
    StatusExecucao,
)

LEGISLATURA = 57  # o M1 cobre só a 57ª (contexto §4.1)
CASA = "CD"

log = logging.getLogger("etl.coletar")


@dataclass(frozen=True)
class Resultado:
    execucao_id: int
    status: StatusExecucao


def _descrever(erro: BaseException) -> dict[str, str]:
    return {"tipo": type(erro).__name__, "mensagem": registro.mascarar(str(erro))}


@dataclass(frozen=True)
class Coleta:
    criar_fonte: Callable[[Callable[[str, Any], None]], FonteDaCasa]
    repositorio: RepositorioDeDados
    brutos: ArmazemDeBrutos
    execucoes: RegistroDeExecucoes
    publicador: Publicador
    versao_codigo: str

    def executar(self, gatilho: Gatilho) -> Resultado:
        execucao_id = self.execucoes.iniciar(gatilho, self.versao_codigo)
        log.info("coleta iniciada", extra={"execucao_id": execucao_id, "gatilho": gatilho.value})
        respostas: list[tuple[str, Any]] = []
        fonte = self.criar_fonte(lambda url, conteudo: respostas.append((url, conteudo)))

        try:
            todos = self._coletar(fonte)
        except Exception as erro:
            self._guardar_brutos(execucao_id, respostas)
            return self._falhar(execucao_id, "coleta", erro)

        pendencias = []
        falhas_de_bruto = self._guardar_brutos(execucao_id, respostas)
        if falhas_de_bruto:
            pendencias.append({"etapa": "brutos", "falhas": falhas_de_bruto})

        try:
            contagens = self.repositorio.gravar(todos)
        except Exception as erro:
            return self._falhar(execucao_id, "gravacao", erro)

        try:
            self.publicador.disparar(execucao_id)
        except Exception as erro:
            log.error("disparo da publicação falhou", extra={"execucao_id": execucao_id})
            pendencias.append({"etapa": "publicacao", **_descrever(erro)})

        status = StatusExecucao.COM_PENDENCIAS if pendencias else StatusExecucao.SUCESSO
        self.execucoes.finalizar(execucao_id, status, contagens=contagens, pendencias=pendencias)
        log.info(
            "coleta terminada",
            extra={"execucao_id": execucao_id, "status": status.value, "contagens": contagens},
        )
        return Resultado(execucao_id, status)

    def _coletar(self, fonte: FonteDaCasa) -> list[DadosDoParlamentar]:
        deputados = fonte.listar_em_exercicio()
        selecionado = selecionar_deputado(deputados)
        em_exercicio = {deputado.identificador: deputado for deputado in deputados}
        # o selecionado e todos os já armazenados: quem saiu de exercício tem o período fechado
        alvos = [selecionado.identificador] + [
            identificador
            for identificador in self.repositorio.parlamentares_armazenados()
            if identificador != selecionado.identificador
        ]
        return [self._dados(fonte, alvo, em_exercicio.get(alvo)) for alvo in alvos]

    @staticmethod
    def _dados(
        fonte: FonteDaCasa, identificador: IdentificadorExterno, parlamentar: Parlamentar | None
    ) -> DadosDoParlamentar:
        historico = fonte.historico(identificador)
        return DadosDoParlamentar(
            identificador=identificador,
            parlamentar=parlamentar,
            mandato=Mandato(CASA, LEGISLATURA, derivar_uf(historico.eventos, LEGISLATURA)),
            periodos=tuple(derivar_periodos(historico.eventos, LEGISLATURA)),
            filiacoes=tuple(derivar_filiacoes(historico.eventos, LEGISLATURA)),
            origem=historico.origem,
        )

    def _guardar_brutos(self, execucao_id: int, respostas: list[tuple[str, Any]]) -> int:
        """Guarda cada resposta; devolve quantas falharam (falha não interrompe a coleta)."""
        falhas = 0
        for url, conteudo in respostas:
            try:
                self.brutos.guardar(execucao_id, url, conteudo)
            except Exception:
                falhas += 1
                log.exception("resposta bruta não guardada", extra={"url": url})
        return falhas

    def _falhar(self, execucao_id: int, etapa: str, erro: Exception) -> Resultado:
        log.error(
            "coleta falhou",
            extra={"execucao_id": execucao_id, "etapa": etapa, **_descrever(erro)},
        )
        self.execucoes.finalizar(
            execucao_id, StatusExecucao.FALHA, erros=[{"etapa": etapa, **_descrever(erro)}]
        )
        return Resultado(execucao_id, StatusExecucao.FALHA)
