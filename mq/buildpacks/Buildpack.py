import abc
from pathlib import Path

import loguru


class Buildpack(abc.ABC):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name

    def autodect(self, path: Path) -> bool:
        """
        Check a direcory whether it can be handled by this buildback.

        This function is used to autodetect a buildpack if now buildpack is provided.
        """

        return False

    @abc.abstractmethod
    def build(self, path: Path, tag: str, logger: "loguru.Logger") -> None:
        """
        Run the buildpack and create a docker image in the local docker registry.

        Parameters
        ----------
        path : Path
            The path to the working directory which contains the project files.
        tag : str
            The image tag which should be created.
        """

    def webapp_port(self) -> int:
        return 3000
