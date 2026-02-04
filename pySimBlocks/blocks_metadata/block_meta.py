from abc import ABC
from typing import Any


class BlockMetaAbstract(ABC):

    @property
    def name(self) -> str:
        if not hasattr(self, "_name"):
            raise NotImplementedError(
                "La classe enfant doit définir l'attribut '_name'"
            )
        return self._name

    @property
    def category(self) -> str:
        if not hasattr(self, "_category"):
            raise NotImplementedError(
                "La classe enfant doit définir l'attribut '_category'"
            )
        return self._category

    @property
    def type(self) -> str:
        if not hasattr(self, "_type"):
            raise NotImplementedError(
                "La classe enfant doit définir l'attribut '_type'"
            )
        return self._type

    @property
    def summary(self) -> str:
        if not hasattr(self, "_summary"):
            raise NotImplementedError(
                "La classe enfant doit définir l'attribut '_summary'"
            )
        return self._summary

    @property
    def description(self) -> str:
        if not hasattr(self, "_description"):
            raise NotImplementedError(
                "La classe enfant doit définir l'attribut '_description'"
            )
        return self._description

    def parameters(self) -> dict[str, Parameter]:
        return {}

    def ports(self) -> dict[str, list[dict[str, Any]]]:
        return {}
