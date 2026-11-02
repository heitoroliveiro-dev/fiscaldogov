"""Sanitização das respostas brutas antes de guardá-las (contracts/fonte-camara-api-v2.md).

Defesa em profundidade: nenhum endpoint consumido traz estas chaves hoje, mas
se algum passar a trazer, elas não chegam ao R2 (RNF06, FR-009). Só a chave é
bloqueada; o valor de outros campos nunca é alterado.
"""

from typing import Any

CHAVES_BLOQUEADAS = frozenset(
    {"cpf", "dataNascimento", "municipioNascimento", "ufNascimento", "escolaridade"}
)


def sanitizar(conteudo: Any) -> Any:
    """Cópia do conteúdo sem as chaves bloqueadas, em qualquer nível."""
    if isinstance(conteudo, dict):
        return {
            chave: sanitizar(valor)
            for chave, valor in conteudo.items()
            if chave not in CHAVES_BLOQUEADAS
        }
    if isinstance(conteudo, list):
        return [sanitizar(item) for item in conteudo]
    return conteudo
