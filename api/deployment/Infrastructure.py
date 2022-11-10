import os
import signal
from email.mime import application
from pathlib import Path
from time import sleep
import traceback
from typing import Dict
from typing import List
from typing import Set

import docker
from dynaconf.utils.functional import Empty
import loguru
from nginx.config.api.blocks import EmptyBlock
import yaml
from docker.models.containers import Container
from loguru import logger
from nginx.config.api import Comment
from nginx.config.api import Config as NGINXConfig
from nginx.config.api import Location
from nginx.config.api import Section
from nginx.config.helpers import duplicate_options

from api.deployment.Manifest import Application
from mq.config import Config


class ApplicationInstance:
    def __init__(
        self,
        application: Application,
        deployment_id: str,
        container_id: str,
        container_name: str,
        webapp_port: int,
        status: str
    ) -> None:

        self.application = application
        self.deployment_id = deployment_id
        self.container_id = container_id
        self.container_name = container_name
        self.webapp_port = webapp_port
        self.status = status

    @staticmethod
    def from_dict(data: dict) -> "ApplicationInstance":
        return ApplicationInstance(
            application=Application.from_dict(data["application"]),
            deployment_id=data["deployment_id"],
            container_id=data["container_id"],
            container_name=data["container_name"],
            webapp_port=data["webapp_port"],
            status=data["status"],
        )

    def to_dict(self) -> dict:
        return {
            "application": self.application.to_dict(),
            "deployment_id": self.deployment_id,
            "container_id": self.container_id,
            "container_name": self.container_name,
            "webapp_port": self.webapp_port,
            "status": self.status,
        }


class Infrastructure:
    @staticmethod
    def restore_instances() -> None:
        """
        Restarts stopped containers.
        """

        containers: List[Container] = list(
            [c for c in Infrastructure._containers() if c.status in ["exited"]]
        )

        for container in containers:
            logger.info("Starting stopped container `{}`.", container.name)
            container.start()
            Infrastructure.wait_until_started(container.id, logger)

    @staticmethod
    def discard_old_instances() -> None:
        """
        Check for old instances of apps and remove them.
        """

        docker_client = docker.from_env()

        all_instances = Infrastructure.list_instances()
        all_instances.sort(key=lambda app: app.deployment_id, reverse=True)
        apps: Dict[str, ApplicationInstance] = {}

        for app in all_instances:
            print(app.application.name, app.deployment_id, app.status)

        for instance in all_instances:
            if instance.application.name in apps:
                container = docker_client.containers.get(instance.container_id)

                logger.info(
                    "Removing old container instance `{}` for app `{}`.",
                    container.id,
                    instance.application.name,
                )

                if isinstance(container, Container):
                    container.remove(force=True, v=True)
            else:
                apps[instance.application.name] = instance

    @staticmethod
    def list_apps() -> List[ApplicationInstance]:
        """
        List all apps.
        """

        all_instances = Infrastructure.list_instances()
        all_instances.sort(key=lambda app: app.deployment_id, reverse=True)
        apps: Set[ApplicationInstance] = set([])

        for app in all_instances:
            if app not in apps:
                apps.add(app)

        apps_distinct = list(apps)
        apps_distinct.sort(key=lambda app: app.application.name)

        return apps_distinct

    @staticmethod
    def list_instances() -> List[ApplicationInstance]:
        """
        List all applications running on local Docker engine.
        """

        containers: List[Container] = [
            container
            for container in Infrastructure._containers()
            if container.status in ["running"]
        ]
        instances: List[ApplicationInstance] = []

        for container in containers:
            try:
                application_yml = container.labels["MQ__APPLICATION"].strip()
                deployment_id = container.labels["MQ__DEPLOYMENT_ID"].strip()
                webapp_port = container.labels["MQ__PORT"].strip()

                assert len(application_yml) > 0, f"`MQ__APPLICATION` must be set."
                assert len(deployment_id) > 0, f"`MQ__DEPLOYMENT_ID` must be set."
                assert len(webapp_port) > 0, f"`MQ__PORT` must be set."

                instances.append(
                    ApplicationInstance(
                        application=Application.from_dict(
                            yaml.safe_load(application_yml)
                        ),
                        deployment_id=deployment_id,
                        container_id=container.id,
                        container_name=container.name,
                        webapp_port=int(webapp_port),
                        status=container.status,
                    )
                )
            except Exception as e:
                traceback.print_exc(e)
                logger.warning(
                    "Unable to fetch environment information from container `{}`: {}.",
                    container.name,
                    e
                )

        return instances

    @staticmethod
    def update_load_balancer(reload_nginx: bool = True) -> None:
        """
        Update NGINX load balancer with currently configured apps.
        """

        apps = Infrastructure.list_apps()

        events = Section("events", worker_connections=1024)

        http = Section(
            "http",
            include="mime.types",
            default_type="application/octet-stream",
            sendfile="on",
            keepalive_timeout=65,
        )

        servers: List[EmptyBlock] = []
        for app in apps:
            servers.append(EmptyBlock(
                Comment(comment=f"{app.application.name} ({app.deployment_id})"),
                Section(
                    "server",
                    Location(
                        "/",
                        proxy_pass=f"http://{app.container_name}:{app.webapp_port}",
                    ),
                    server_name=f"{app.application.name}.{Config.Server.domain}",
                ),
            ))

        

        servers.append(EmptyBlock(
            Comment(comment=f"MQ Server Proxy"),
            Section(
                "server",
                duplicate_options("listen", ["80 default_server", "[::]:80 default_server"]),
                Location("/", proxy_pass="http://localhost:8000")
            )
        ))

        http.sections.add(duplicate_options("server", servers))

        config = NGINXConfig(
            events, http, worker_processes=1, pid=Config.Server.NGINX.pid_file
        )

        logger.info("Updating NGINX configuration:\n{}", config)
        Path(Config.Server.NGINX.config_file).write_text(str(config))

        try:
            if reload_nginx:
                pid = int(Path(Config.Server.NGINX.pid_file).read_text())
                os.kill(pid, signal.SIGHUP)
        except Exception:
            logger.warning("Error occurred updating NGINX configuration.")

    @staticmethod
    def wait_until_started(id: str, log: "loguru.Logger") -> None:
        """
        Wait until a container is started.

        Parameters
        ----------
        id : str
            The Docker container id to watch.
        """

        docker_client = docker.from_env()
        waited_seconds = 0
        container = docker_client.containers.get(id)

        while (
            container.status != "running"
            and waited_seconds < Config.Server.deployment_timeout_in_seconds
        ):
            log.info(
                "Waiting for app `{}`, current status is `{}` ...",
                application.name,
                container.status,
            )
            sleep(5)
            waited_seconds += 5
            container.reload()

    @staticmethod
    def _containers() -> List[Container]:
        """
        Returns a list of application containers.
        """

        docker_client = docker.from_env()

        return list(
            [
                container
                for container in docker_client.containers.list(all=True)
                if isinstance(container, Container)
                and str(container.name).startswith("mq--")
            ]
        )
