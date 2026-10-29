"""Seleção do deputado exibido na F2 (FR-006, research §4).

Regra objetiva, sem escolha pessoal (princípio II): entre os em exercício, o
primeiro pelo nome parlamentar em minúsculas e sem acento, independente de locale.
"""

from dataclasses import dataclass

import pytest

from etl.dominio.selecao import normalizar_nome, selecionar_deputado


@dataclass(frozen=True)
class _Deputado:
    nome_parlamentar: str


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("Átila Lira", "atila lira"),
        ("ÁLVARO", "alvaro"),
        ("João Gonçalves", "joao goncalves"),
        ("Zé Trovão", "ze trovao"),
        ("Pr. Marco Feliciano", "pr. marco feliciano"),
    ],
)
def test_nome_de_ordenacao_e_minusculo_e_sem_acento(nome: str, esperado: str) -> None:
    assert normalizar_nome(nome) == esperado


def test_alvaro_com_e_sem_acento_tem_o_mesmo_nome_de_ordenacao() -> None:
    assert normalizar_nome("álvaro") == normalizar_nome("Alvaro")


def test_acento_nao_empurra_o_nome_para_o_fim() -> None:
    # na comparação crua, "Á" (U+00C1) vem depois de "B"
    atila = _Deputado("Átila Lira")

    assert selecionar_deputado([_Deputado("Bruno Farias"), atila]) is atila


def test_maiuscula_nao_passa_na_frente() -> None:
    # na comparação crua, "C" vem antes de "b"
    bruno = _Deputado("bruno Farias")

    assert selecionar_deputado([_Deputado("Carlos Jordy"), bruno]) is bruno


def test_escolhe_o_primeiro_entre_varios() -> None:
    deputados = [_Deputado(nome) for nome in ("Zeca Dirceu", "Érika Kokay", "Acácio Favacho")]

    assert selecionar_deputado(deputados).nome_parlamentar == "Acácio Favacho"


def test_lista_vazia_e_recusada() -> None:
    with pytest.raises(ValueError, match="nenhum deputado"):
        selecionar_deputado([])
