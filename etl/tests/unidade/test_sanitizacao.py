"""Sanitização das respostas brutas antes de guardá-las (contracts/fonte-camara-api-v2.md).

Defesa em profundidade: nenhum endpoint consumido traz essas chaves hoje, mas se
algum passar a trazer, elas não chegam ao R2 (RNF06, FR-009).
"""

import copy

from etl.adaptadores.camara.sanitizacao import CHAVES_BLOQUEADAS, sanitizar


def test_lista_de_bloqueio_do_contrato() -> None:
    assert set(CHAVES_BLOQUEADAS) == {
        "cpf",
        "dataNascimento",
        "municipioNascimento",
        "ufNascimento",
        "escolaridade",
    }


def test_remove_as_chaves_em_qualquer_nivel() -> None:
    resposta = {
        "dados": {
            "id": 204496,
            "cpf": "00000000000",
            "dataNascimento": "1980-01-01",
            "ultimoStatus": {
                "nome": "Fulano",
                "municipioNascimento": "Belém",
                "ufNascimento": "PA",
            },
            "eventos": [{"escolaridade": "Superior", "situacao": "Exercício"}],
        },
        "links": [],
    }

    assert sanitizar(resposta) == {
        "dados": {
            "id": 204496,
            "ultimoStatus": {"nome": "Fulano"},
            "eventos": [{"situacao": "Exercício"}],
        },
        "links": [],
    }


def test_resposta_sem_chaves_bloqueadas_fica_igual() -> None:
    resposta = {"dados": [{"id": 1, "nome": "Fulano", "siglaUf": "PA"}], "links": []}

    assert sanitizar(resposta) == resposta


def test_nao_altera_a_resposta_original() -> None:
    resposta = {"dados": [{"id": 1, "cpf": "00000000000"}]}
    original = copy.deepcopy(resposta)

    sanitizar(resposta)

    assert resposta == original


def test_valor_que_contem_o_nome_da_chave_nao_e_removido() -> None:
    # só a chave é bloqueada; texto que menciona "cpf" é dado legítimo
    resposta = {"descricaoStatus": "cpf não informado", "cpfs": 1}

    assert sanitizar(resposta) == resposta
