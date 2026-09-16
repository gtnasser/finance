class DomainError(Exception):
    """Erro de domínio base."""

class NotFoundError(DomainError):
    def __init__(self, entidade: str, identificador: object) -> None:
        self.entidade = entidade
        self.identificador = identificador
        super().__init__(f"{entidade} {identificador} não encontrado(a).")

class ConflictError(DomainError):
    """Violação de unicidade ou conflito de estado."""

class BusinessRuleError(DomainError):
    """Regra de negócio violada."""
