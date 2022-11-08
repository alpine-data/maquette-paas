import os
import sys
import time
from multiprocessing import Process
from pathlib import Path
from typing import List

import yaml
from loguru import logger

from api.deployment.DeploymentInfo import DeploymentInfo
from api.deployment.DeploymentInfo import DeploymentStatus
from mq.config import Config


class DeploymentMonitor(Process):
    def __init__(self) -> None:
        super().__init__()
        self.daemon = True

    def run(self) -> None:
        # We can do an endless loop here because we flagged the process as
        # being a "daemon". This ensures it will exit when the parent exists.

        logger.remove()
        logger.add(sys.stdout, level="INFO")

        while True:
            logger.debug("Checking for new deployments.")
            deployments_dir = Config.Server.working_directory / "deployments"

            deployments: List[str] = []
            if deployments_dir.is_dir() and deployments_dir.exists():
                deployments = os.listdir(deployments_dir)

            for deployment in deployments:
                deployment_info_file = (
                    deployments_dir / deployment / "deployment.info.yml"
                )

                if deployment_info_file.exists():
                    deployment_info = DeploymentInfo.from_dict(
                        yaml.safe_load(deployment_info_file.read_text())
                    )
                else:
                    continue

                if deployment_info.status == DeploymentStatus.scheduled:
                    self._run_deployment(
                        deployment, deployment_info, deployments_dir / deployment
                    )

            # Wait at least 5 seconds for the next execution
            time.sleep(5)

    def _run_deployment(
        self, deployment_id: str, deployment_info: DeploymentInfo, working_dir: Path
    ) -> None:
        logger.add(
            (working_dir / "deployment.log").absolute(),
            filter=lambda record: record["extra"].get("name") == deployment_id,
        )

        deployment_info.status = DeploymentStatus.running
        self._update_deployment_info(deployment_id, deployment_info)

        deployment_log = logger.bind(name=deployment_id)
        deployment_log.info("Started deployment {}", deployment_id)

        time.sleep(8)

        deployment_log.info("Doing something ...")

        time.sleep(5)

        deployment_log.info("Deployment succeeded.")
        deployment_info.status = DeploymentStatus.succeeded
        self._update_deployment_info(deployment_id, deployment_info)

    def _update_deployment_info(
        self, deployment_id: str, deployment_info: DeploymentInfo
    ) -> None:
        """ """
        (
            Config.Server.working_directory
            / "deployments"
            / deployment_id
            / "deployment.info.yml"
        ).write_text(yaml.safe_dump(deployment_info.dict()))
