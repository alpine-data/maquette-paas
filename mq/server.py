import uuid
import zipfile
from datetime import datetime

import yaml
from fastapi import FastAPI
from fastapi import File
from fastapi import HTTPException
from fastapi import Response
from fastapi import UploadFile
from fastapi.responses import PlainTextResponse

from mq.config import Config
from mq.deployment.DeploymentInfo import DeploymentInfo
from mq.deployment.DeploymentInfo import DeploymentStatus
from mq.logger import Logger

Logger.initialize()
app = FastAPI()


@app.post("/api/push")
def push(files: UploadFile = File()) -> dict:
    # Initialize working directory
    deployment_timestamp = datetime.now().strftime("%Y%d%m%H%M%S")
    deployment_hash = str(uuid.uuid4())[:4]
    deployment_id = f"{deployment_timestamp}-{deployment_hash}"
    working_dir = Config.Server.working_directory / "deployments" / deployment_id

    working_dir.mkdir(parents=True)

    # Save uploaded files and extract
    with open(working_dir / "files.zip", "wb+") as destination:
        destination.write(files.file.read())

    with zipfile.ZipFile(working_dir / "files.zip", "r") as zip_ref:
        zip_ref.extractall(working_dir / "files")

    info = DeploymentInfo(status=DeploymentStatus.scheduled)
    (working_dir / "deployment.info.yml").write_text(yaml.dump(info.dict()))

    return {"id": deployment_id}


@app.get("/api/push/{deployment_id}", response_class=PlainTextResponse)
def read_push_logs(response: Response, deployment_id: str) -> str:
    deployment_info_file = (
        Config.Server.working_directory
        / "deployments"
        / deployment_id
        / "deployment.info.yml"
    )

    if deployment_info_file.exists():
        info = DeploymentInfo.from_dict(
            yaml.safe_load(deployment_info_file.read_text())
        )
        deployment_log_file = (
            Config.Server.working_directory
            / "deployments"
            / deployment_id
            / "deployment.log"
        )

        if deployment_log_file.exists():
            log = deployment_log_file.read_text()
        else:
            log = ""

        response.headers["MQ-Deployment-Status"] = info.status.value
        return log
    else:
        raise HTTPException(status_code=404, detail="Deployment does not exist.")
