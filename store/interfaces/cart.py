from abc import ABC, abstractmethod
from typing import Dict, Any

class CartServiceInterface(ABC):
    """Contrato para operaciones de carrito."""

    @abstractmethod
    def add(self, request, *, variant_id: int | None, product_id: int, quantity: int) -> None:
        """Añade o actualiza un ítem en el carrito."""
        ...

    @abstractmethod
    def remove(self, request, *, variant_id: int | None, product_id: int, quantity: int) -> None:
        """Elimina o decrementa un ítem del carrito."""
        ...

    @abstractmethod
    def get(self, request) -> dict[str, dict[str, Any]]:
        """Obtiene el contenido bruto del carrito."""
        ...

    @abstractmethod
    def save(self, request, cart: dict[str, Any]) -> None:
        """Guarda el carrito en su almacén."""
        ...
