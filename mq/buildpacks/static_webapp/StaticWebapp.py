from importlib import resources
from pathlib import Path

import docker
import loguru

from mq.buildpacks import static_webapp
from mq.buildpacks.Buildpack import Buildpack


class StaticWebapp(Buildpack):
    def __init__(self) -> None:
        super().__init__("static-webapp")

    def autodect(self, path: Path) -> bool:
        return True

    def build(self, path: Path, tag: str, logger: "loguru.Logger") -> None:
        self._create_dockerfile(path)

        logger.info("Building image `{}`.", tag)

        client = docker.from_env()
        (_, log) = client.images.build(path=str(path), tag=tag, rm=True)

        log_complete = "".join([line["stream"] for line in log if "stream" in line])
        logger.info("Image build logs:\n{}", log_complete)

    def _create_dockerfile(self, target_dir: Path) -> None:
        dockerfile = resources.read_text(static_webapp, "Dockerfile")
        (target_dir / "Dockerfile").write_text(dockerfile)
