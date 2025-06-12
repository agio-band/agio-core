from uuid import UUID


def get_project(project_id: UUID) -> dict:
    pass


def get_project_by_name(name: str) -> dict:
    pass


def create_project(payload: dict) -> dict:
    pass


def update_project(project_id: UUID, payload: dict) -> dict:
    pass


def delete_project(project_id: UUID) -> None:
    pass


def get_entity(entity_id: UUID) -> dict:
    pass


def get_entity_by_name(project_id: UUID, entity_type: str, name: str) -> dict:
    pass

