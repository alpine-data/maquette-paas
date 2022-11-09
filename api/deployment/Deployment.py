from time import sleep
import yaml
from api.buildpacks.Buildpacks import Buildpacks
from api.deployment.DeploymentInfo import DeploymentInfo, DeploymentStatus
from api.deployment.Manifest import Application, Manifest
from mq.config import Config

from loguru import logger

class Deployment:

    def __init__(self, id: str) -> None:
        self.id = id
        self.working_dir = Config.Server.working_directory / "deployments" / id

        logger.add(
            self.working_dir / "deployment.log",
            filter=lambda record: record["extra"].get("name") == id,
        )

        self.log = logger.bind(name=id)

    def run(self) -> None:
        self._update_status(DeploymentStatus.running)
        self.log.info("Started deployment {}", self.id)

        sleep(4)
        self._read_manifest()

        sleep(3)
        self._update_status(DeploymentStatus.succeeded)

    def _read_manifest(self) -> Manifest:
        """
        Check whether manifest exists. If it exists, validate the manifets.

        TODO: Replace variables.
        """

        manifest_file = self.working_dir / "manifest.yml"

        if manifest_file.exists():
            self.log.info("Reading Manifest from `{}`.", manifest_file.name)
            manifest = Manifest.from_dict(yaml.load(manifest_file.read_text()))
        else:
            self.log.info("No Manifest found. Try to detect Manifest settings.")
            bp_matches = [ bp for bp in Buildpacks.all if bp.autodect(self.working_dir) ]

            if not bp_matches:
                self.log.error("No buildpack can be detected. Please specify buildpack in manifest file.")
                raise Exception("TODO: Nice exception ...")

            # TODO get app name from client's project directory name
            buildpack = bp_matches[0].name
            self.log.info("Detected buildback `{}`.", buildpack)

            manifest = Manifest([Application("app", buildpack)])

        self.log.info("Using Manifest:\n---\n{}\n---", yaml.safe_dump(manifest.to_dict(), sort_keys=False).strip())
        return manifest

    def _update_status(self, status: DeploymentStatus) -> None:
        path = self.working_dir / "deployment.info.yml"
        info = DeploymentInfo.from_dict(yaml.safe_load(path.read_text()))

        info.status = status

        path.write_text(yaml.safe_dump(info.dict()))