import os
import sys
import time
from multiprocessing import Process
from typing import List

import yaml
from loguru import logger

from mq.config import Config
from mq.deployment.Deployment import Deployment
from mq.deployment.DeploymentInfo import DeploymentInfo
from mq.deployment.DeploymentInfo import DeploymentStatus


class DeploymentMonitor(Process):
    def __init__(self) -> None:
        super().__init__()
        self.daemon = True

        self.deployments_dir = Config.Server.working_directory / "deployments"

    def run(self) -> None:
        # We can do an endless loop here because we flagged the process as
        # being a "daemon". This ensures it will exit when the parent exists.

        logger.remove()
        logger.add(sys.stdout, level="INFO")

        while True:
            logger.debug("Checking for new deployments.")

            deployments: List[str] = []
            if self.deployments_dir.is_dir() and self.deployments_dir.exists():
                deployments = os.listdir(self.deployments_dir)

            for deployment in deployments:
                deployment_info_file = (
                    self.deployments_dir / deployment / "deployment.info.yml"
                )

                if deployment_info_file.exists():
                    deployment_info = DeploymentInfo.from_dict(
                        yaml.safe_load(deployment_info_file.read_text())
                    )
                else:
                    continue

                if deployment_info.status == DeploymentStatus.scheduled:
                    Deployment(deployment).run()

            # Wait at least 5 seconds for the next execution
            time.sleep(5)
