"""Comando coletar: etapas de contracts/etl-cli.md (T040, T070).

A execução só começa se não houver outra em andamento há menos de 60 min; as
travadas há mais tempo são fechadas como "interrompida" e alertadas (FR-013a).
O vigia cobre da coleta ao disparo da publicação: estourou, tudo é desfeito e a
execução termina `falha` por tempo esgotado.

As respostas brutas chegam durante a coleta e ficam em memória até haver
execucao_id; são guardadas antes da gravação dos dados (etapa 4) e também
quando a coleta falha, para diagnóstico. Falha da fonte ou da gravação vira
`falha` sem gravar nada; falha ao guardar bruto ou ao disparar a publicação vira
`com_pendencias`, com os dados gravados. `falha` e `com_pendencias` geram alerta
(etapa 9); falha no envio do alerta não muda o resultado (FR-029).

O backup (etapa 6) entra na US5.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from etl.dominio.entidades import DadosDoParlamentar, IdentificadorExterno, Mandato, Parlamentar
from etl.dominio.historico import derivar_filiacoes, derivar_periodos, derivar_uf
from etl.dominio.selecao import selecionar_deputado
from etl.pipeline.alertas import descrever_erro, montar_alerta
from etl.pipeline.vigia import TempoEsgotado, limite_de_tempo
from etl.portas import (
    Alertador,
    ArmazemDeBrutos,
    ColetaEmAndamento,
    FonteDaCasa,
    Gatilho,
    Publicador,
    RegistroDeExecucoes,
    RepositorioDeDados,
    StatusExecucao,
)

__all__ = ["Coleta", "ColetaEmAndamento", "Resultado"]

LEGISLATURA = 57  # o M1 cobre só a 57ª (contexto §4.1)
CASA = "CD"
TEMPO_LIMITE_PADRAO_S = 3600
TITULOS_DO_ALERTA = {
    StatusExecucao.FALHA: "coleta com falha",
    StatusExecucao.COM_PENDENCIAS: "coleta com pendências",
}

log = logging.getLogger("etl.coletar")

AoReceber = Callable[[str, Any], None]
AoTentar = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class Resultado:
    execucao_id: int
    status: StatusExecucao


@dataclass(frozen=True)
class Coleta:
    criar_fonte: Callable[[AoReceber, AoTentar], FonteDaCasa]
    repositorio: RepositorioDeDados
    brutos: ArmazemDeBrutos
    execucoes: RegistroDeExecucoes
    publicador: Publicador
    alertador: Alertador
    versao_codigo: str
    tempo_limite_s: int = TEMPO_LIMITE_PADRAO_S

    def executar(self, gatilho: Gatilho) -> Resultado:
        abertura = self.execucoes.abrir(gatilho, self.versao_codigo)
        for travada in abertura.interrompidas:
            log.error("coleta anterior interrompida", extra={"execucao_id": travada})
            self._alertar(
                montar_alerta(
                    "coleta interrompida (passou de 60 min sem terminar)",
                    travada,
                    [{"etapa": "vigia", "tipo": "interrompida"}],
                )
            )

        execucao_id = abertura.execucao_id
        log.info("coleta iniciada", extra={"execucao_id": execucao_id, "gatilho": gatilho.value})
        tentativas: list[dict[str, Any]] = []
        try:
            with limite_de_tempo(self.tempo_limite_s):
                status, detalhes = self._etapas(execucao_id, tentativas)
        except TempoEsgotado as erro:
            log.error("coleta interrompida pelo vigia", extra={"execucao_id": execucao_id})
            status, detalhes = (
                StatusExecucao.FALHA,
                {"erros": [{"etapa": "vigia", **descrever_erro(erro)}]},
            )

        if tentativas:
            detalhes["tentativas"] = tentativas
        self.execucoes.finalizar(execucao_id, status, **detalhes)
        log.info(
            "coleta terminada",
            extra={"execucao_id": execucao_id, "status": status.value, **detalhes},
        )

        if status in TITULOS_DO_ALERTA:
            problemas = detalhes.get("erros") or detalhes.get("pendencias") or []
            self._alertar(montar_alerta(TITULOS_DO_ALERTA[status], execucao_id, problemas))
        return Resultado(execucao_id, status)

    def _etapas(
        self, execucao_id: int, tentativas: list[dict[str, Any]]
    ) -> tuple[StatusExecucao, dict[str, Any]]:
        respostas: list[tuple[str, Any]] = []
        fonte = self.criar_fonte(
            lambda url, conteudo: respostas.append((url, conteudo)), tentativas.append
        )

        try:
            todos = self._coletar(fonte)
        except Exception as erro:
            self._guardar_brutos(execucao_id, respostas)
            return self._falha("coleta", erro, execucao_id)

        pendencias: list[dict[str, Any]] = []
        falhas_de_bruto = self._guardar_brutos(execucao_id, respostas)
        if falhas_de_bruto:
            pendencias.append({"etapa": "brutos", "falhas": falhas_de_bruto})

        try:
            contagens = self.repositorio.gravar(todos)
        except Exception as erro:
            return self._falha("gravacao", erro, execucao_id)

        try:
            self.publicador.disparar(execucao_id)
        except Exception as erro:
            log.error("disparo da publicação falhou", extra={"execucao_id": execucao_id})
            pendencias.append({"etapa": "publicacao", **descrever_erro(erro)})

        status = StatusExecucao.COM_PENDENCIAS if pendencias else StatusExecucao.SUCESSO
        return status, {"contagens": contagens, "pendencias": pendencias}

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

    @staticmethod
    def _falha(
        etapa: str, erro: Exception, execucao_id: int
    ) -> tuple[StatusExecucao, dict[str, Any]]:
        descricao = {"etapa": etapa, **descrever_erro(erro)}
        log.error("coleta falhou", extra={"execucao_id": execucao_id, **descricao})
        return StatusExecucao.FALHA, {"erros": [descricao]}

    def _alertar(self, texto: str) -> None:
        try:
            self.alertador.alertar(texto)
        except Exception:
            # o alertador real não levanta; isto protege o resultado de um alertador defeituoso
            log.exception("alerta não enviado")
