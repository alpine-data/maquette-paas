import traceback

import docker
import yaml
from docker.models.containers import Container
from loguru import logger

from mq.buildpacks.Buildpacks import Buildpacks
from mq.config import Config
from mq.deployment.DeploymentInfo import DeploymentInfo
from mq.deployment.DeploymentInfo import DeploymentStatus
from mq.deployment.Infrastructure import Infrastructure
from mq.deployment.Manifest import Application
from mq.deployment.Manifest import Manifest


class Deployment:
    def __init__(self, id: str) -> None:
        self.id = id
        self.working_dir = Config.Server.working_directory / "deployments" / id

        logger.add(
            self.working_dir / "deployment.log",
            filter=lambda record: record["extra"].get("name") == id,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        )

        self.log = logger.bind(name=id)

    def run(self) -> None:
        self._update_status(DeploymentStatus.running)
        self.log.info("Started deployment {}", self.id)

        try:
            #
            # Deploy specified applications.
            #
            manifest = self._read_manifest()
            for app in manifest.applications:
                self.deploy_application(app)

            #
            # Update NGINX.
            #
            Infrastructure.discard_old_instances()
            Infrastructure.update_load_balancer()

            self._update_status(DeploymentStatus.succeeded)
        except Exception as err:
            traceback.print_exception(err)
            self.log.error(str(err))
            self._update_status(DeploymentStatus.failed)

    def deploy_application(self, application: Application) -> None:
        """ """

        #
        # Build image with buildpack.
        #
        self.log.info(
            "Building `{}` with `{}`.", application.name, application.buildback
        )

        buildpack = Buildpacks.get(application.buildback)
        image_tag = f"{application.name}:{self.id}"
        buildpack.build(self.working_dir / "files", image_tag, self.log)

        #
        # Deploy image.
        #
        self.log.info("Starting `{}`", application.name, application.buildback)
        docker_client = docker.from_env()

        container: Container = docker_client.containers.run(
            image_tag,
            name=f"mq--{application.name}--{self.id}",
            detach=True,
            environment={"PORT": 3000},
            network=Config.Server.network_name,
            labels={
                "MQ__APPLICATION": yaml.safe_dump(application.to_dict()),
                "MQ__DEPLOYMENT_ID": self.id,
                "MQ__PORT": str(buildpack.webapp_port()),
            },
            publish_all_ports=True,
        )

        self.log.info(
            "Initialized `{}/{}` with status `{}`",
            container.id,
            container.name,
            container.status,
        )

        #
        # Wait until started.
        #
        Infrastructure.wait_until_started(container.id, self.log)
        container.reload()

        #
        # Check status.
        #
        if container.status == "running":
            self.log.info("Succesffully started app `{}`.", application.name)
        else:
            self.log.error(
                "Application `{}` did not start within specified timeout of {} seconds. Killing application.",
                application.name,
                Config.Server.deployment_timeout_in_seconds,
            )
            container.stop()
            raise Exception("An error occurred while starting app.")

    def _read_manifest(self) -> Manifest:
        """
        Check whether manifest exists. If it exists, validate the manifets.

        TODO: Replace variables.
        """

        manifest_file = self.working_dir / "manifest.yml"

        if manifest_file.exists():
            self.log.info("Reading Manifest from `{}`.", manifest_file.name)
            manifest = Manifest.from_dict(yaml.safe_load(manifest_file.read_text()))
        else:
            self.log.info("No Manifest found. Try to detect Manifest settings.")
            bp_matches = [bp for bp in Buildpacks.all if bp.autodect(self.working_dir)]

            if not bp_matches:
                self.log.error(
                    "No buildpack can be detected. Please specify buildpack in manifest file."
                )
                raise Exception("TODO: Nice exception ...")

            # TODO get app name from client's project directory name
            buildpack = bp_matches[0].name
            self.log.info("Detected buildback `{}`.", buildpack)

            manifest = Manifest([Application("app", buildpack)])

        self.log.info(
            "Using Manifest:\n---\n{}\n---",
            yaml.safe_dump(manifest.to_dict(), sort_keys=False).strip(),
        )
        return manifest

    def _update_status(self, status: DeploymentStatus) -> None:
        path = self.working_dir / "deployment.info.yml"
        info = DeploymentInfo.from_dict(yaml.safe_load(path.read_text()))

        info.status = status

        path.write_text(yaml.safe_dump(info.dict()))
