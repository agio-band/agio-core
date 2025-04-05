from pathlib import Path


class VenvManager:

    def __init__(self, venv_path: str):
        self.path = Path(venv_path).expanduser().as_posix()
