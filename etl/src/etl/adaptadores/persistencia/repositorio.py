"""Gravação dos dados de domínio da coleta (T038, FR-007a, FR-008, FR-012).

Tudo numa única transação: erro em qualquer parlamentar desfaz a coleta inteira.
Parlamentar, partido e mandato são atualizados no lugar, achados pelo
identificador da fonte; períodos e filiações do parlamentar são substituídos
pelos derivados agora. Rodar duas vezes com os mesmos dados dá o mesmo estado.
"""

from collections.abc import Sequence

from sqlalchemy import Connection, select

from etl.adaptadores.persistencia.banco import Banco
from etl.dominio.entidades import (
    DadosDoParlamentar,
    IdentificadorExterno,
    Mandato,
    Parlamentar,
    Partido,
    SistemaExterno,
)


class Repositorio:
    def __init__(self, banco: Banco) -> None:
        self._banco = banco
        self._t = banco.tabelas

    def parlamentares_armazenados(self) -> list[IdentificadorExterno]:
        ie = self._t["identificador_externo"]
        consulta = (
            select(ie.c.valor)
            .where(ie.c.sistema == SistemaExterno.CAMARA_V2.value, ie.c.parlamentar_id.is_not(None))
            .order_by(ie.c.valor)
        )
        with self._banco.engine.connect() as conexao:
            return [
                IdentificadorExterno(SistemaExterno.CAMARA_V2, valor)
                for valor in conexao.execute(consulta).scalars()
            ]

    def gravar(self, todos: Sequence[DadosDoParlamentar]) -> dict[str, int]:
        with self._banco.transacao() as conexao:
            for dados in todos:
                self._gravar_um(conexao, dados)
        return {
            "parlamentar": len(todos),
            "periodo_exercicio": sum(len(dados.periodos) for dados in todos),
            "filiacao": sum(len(dados.filiacoes) for dados in todos),
        }

    def _gravar_um(self, conexao: Connection, dados: DadosDoParlamentar) -> None:
        parlamentar_id = self._parlamentar(conexao, dados.identificador, dados.parlamentar)
        mandato_id = self._mandato(conexao, parlamentar_id, dados.mandato)
        fonte = {"fonte_url": dados.origem.url, "coletado_em": dados.origem.coletado_em}

        periodo = self._t["periodo_exercicio"]
        conexao.execute(periodo.delete().where(periodo.c.mandato_id == mandato_id))
        for p in dados.periodos:
            conexao.execute(
                periodo.insert().values(
                    mandato_id=mandato_id,
                    inicio=p.inicio,
                    fim=p.fim,
                    condicao=p.condicao.value,
                    motivo_inicio=p.motivo_inicio,
                    motivo_fim=p.motivo_fim,
                    **fonte,
                )
            )

        filiacao = self._t["filiacao"]
        conexao.execute(filiacao.delete().where(filiacao.c.parlamentar_id == parlamentar_id))
        for f in dados.filiacoes:
            conexao.execute(
                filiacao.insert().values(
                    parlamentar_id=parlamentar_id,
                    partido_id=self._partido(conexao, f.partido),
                    inicio=f.inicio,
                    fim=f.fim,
                    **fonte,
                )
            )

    def _id_por_identificador(
        self, conexao: Connection, identificador: IdentificadorExterno, coluna: str
    ) -> int | None:
        ie = self._t["identificador_externo"]
        return conexao.execute(
            select(ie.c[coluna]).where(
                ie.c.sistema == identificador.sistema.value,
                ie.c.valor == identificador.valor,
                ie.c.legislatura_numero.is_(None)
                if identificador.legislatura is None
                else ie.c.legislatura_numero == identificador.legislatura,
            )
        ).scalar_one_or_none()

    def _registrar_identificador(
        self, conexao: Connection, identificador: IdentificadorExterno, **dono: int
    ) -> None:
        conexao.execute(
            self._t["identificador_externo"]
            .insert()
            .values(
                sistema=identificador.sistema.value,
                valor=identificador.valor,
                legislatura_numero=identificador.legislatura,
                **dono,
            )
        )

    def _parlamentar(
        self,
        conexao: Connection,
        identificador: IdentificadorExterno,
        parlamentar: Parlamentar | None,
    ) -> int:
        tabela = self._t["parlamentar"]
        parlamentar_id = self._id_por_identificador(conexao, identificador, "parlamentar_id")
        if parlamentar is None:
            if parlamentar_id is None:
                raise ValueError(f"parlamentar {identificador.valor} sem cadastro e fora da lista")
            return parlamentar_id

        cadastro = {
            "nome_parlamentar": parlamentar.nome_parlamentar,
            "nome_ordenacao": parlamentar.nome_ordenacao,
            "url_foto": parlamentar.url_foto,
            "fonte_url": parlamentar.origem.url,
            "coletado_em": parlamentar.origem.coletado_em,
        }
        if parlamentar_id is not None:
            conexao.execute(tabela.update().where(tabela.c.id == parlamentar_id).values(**cadastro))
            return parlamentar_id

        parlamentar_id = conexao.execute(
            tabela.insert().values(**cadastro).returning(tabela.c.id)
        ).scalar_one()
        self._registrar_identificador(conexao, identificador, parlamentar_id=parlamentar_id)
        return parlamentar_id

    def _partido(self, conexao: Connection, partido: Partido) -> int:
        tabela = self._t["partido"]
        partido_id = self._id_por_identificador(conexao, partido.identificador, "partido_id")
        if partido_id is not None:
            conexao.execute(
                tabela.update().where(tabela.c.id == partido_id).values(sigla=partido.sigla)
            )
            return partido_id

        partido_id = conexao.execute(
            tabela.insert().values(sigla=partido.sigla).returning(tabela.c.id)
        ).scalar_one()
        self._registrar_identificador(conexao, partido.identificador, partido_id=partido_id)
        return partido_id

    def _mandato(self, conexao: Connection, parlamentar_id: int, mandato: Mandato) -> int:
        tabela = self._t["mandato"]
        casa = self._t["casa_legislativa"]
        casa_id = conexao.execute(
            select(casa.c.id).where(casa.c.sigla == mandato.casa)
        ).scalar_one()
        chave = (
            tabela.c.parlamentar_id == parlamentar_id,
            tabela.c.casa_id == casa_id,
            tabela.c.legislatura_numero == mandato.legislatura,
        )
        mandato_id = conexao.execute(select(tabela.c.id).where(*chave)).scalar_one_or_none()
        if mandato_id is not None:
            conexao.execute(tabela.update().where(tabela.c.id == mandato_id).values(uf=mandato.uf))
            return mandato_id

        return conexao.execute(
            tabela.insert()
            .values(
                parlamentar_id=parlamentar_id,
                casa_id=casa_id,
                legislatura_numero=mandato.legislatura,
                uf=mandato.uf,
            )
            .returning(tabela.c.id)
        ).scalar_one()
