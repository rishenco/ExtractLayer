from collections.abc import Mapping


class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: int) -> None:
        super().__init__(f"{entity} {entity_id} does not exist")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(DomainError):
    def __init__(self, details: Mapping[str, str]) -> None:
        super().__init__(
            "; ".join(f"{field}: {message}" for field, message in sorted(details.items()))
        )
        self.details = dict(details)
