import time
import zipfile
from pathlib import Path
from typing import Optional

import requests
from pathspec import PathSpec
from requests import Response

from api.deployment.DeploymentInfo import DeploymentStatus
from mq.config import Config


class Push:
    @staticmethod
    def run(working_directory: Optional[Path] = None) -> None:
        """
        This task pushes a local project to the Maquette Apps server and triggers build/ deployment of the project.

        Parameters
        ----------
        working_directory : Optional[str]
            The project's root directory. It's content will be published and pushed.
        """

        if working_directory is None:
            working_directory = Path(".").resolve()

        # Create ZIP file
        zip_file = working_directory / ".mq" / "upload" / "test.zip"
        Push._zip_directory(working_directory, zip_file)

        # Upload to backend
        with open(zip_file, "rb") as f:
            result = requests.post(
                f"{Config.CLI.Target.endpoint}/api/{Config.CLI.Target.space}/push",
                files={"files": f},
            )
            deployment_id = result.json()["id"]

        # Print deployment logs
        Push._log_and_wait(deployment_id)

    @staticmethod
    def _log_and_wait(deployment_id: str) -> None:
        """
        Fetches logging information from the backend and wait until deployment succeeded or failed.

        Parameters
        ----------
        deployment_id : str
            The deployment id to fetch the log from the baxckend.
        """

        running = True
        logs_offset = 0

        while running:
            time.sleep(3)

            logs_response: Response = requests.get(
                f"{Config.CLI.Target.endpoint}/api/{Config.CLI.Target.space}/push/{deployment_id}"
            )
            logs = logs_response.text

            if len(logs) > logs_offset:
                print(logs[logs_offset:], end="")
                logs_offset = len(logs)

            if logs_response.headers["MQ-Deployment-Status"] in [
                DeploymentStatus.succeeded.value,
                DeploymentStatus.failed.value,
            ]:
                running = False

    @staticmethod
    def _zip_directory(directory: Path, target: Path) -> None:
        """
        Zips the directory respecting `.gitignore` file.

        Only the `.gitignore` file on the root directory gets respected, nested ignore files are not supported. The ZIP file will contain the directory contents
        without the root directory.

        Parameters
        ----------
        directory : Path
            The directory to package.
        target : Path
            The target (zip-)file which is created by this method.
        """

        all_files = list(directory.glob("**/*"))
        gitignore = directory / ".gitignore"

        if gitignore.exists():
            lines = gitignore.read_text().splitlines()
            lines = lines + Config.CLI.Push.ignore_by_default

            spec = PathSpec.from_lines("gitwildmatch", lines)

            all_files = list(
                [
                    file
                    for file in all_files
                    if not spec.match_file(str(file.relative_to(directory)))
                    and file.is_file()
                ]
            )

        if not target.parent.exists():
            target.parent.mkdir(parents=True)

        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in all_files:
                zipf.write(file, file.relative_to(directory))
