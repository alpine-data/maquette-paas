import os
import uuid
import zipfile
from datetime import datetime

import yaml
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.deployment.DeploymentInfo import DeploymentInfo
from api.deployment.DeploymentInfo import DeploymentStatus
from mq.config import Config


@csrf_exempt
def push(request: HttpRequest, space_name: str) -> JsonResponse:
    # Initialize working directory
    deployment_timestamp = datetime.now().strftime("%Y%d%m%H%M%S")
    deployment_hash = str(uuid.uuid4())[:4]
    deployment_id = f"{deployment_timestamp}-{deployment_hash}"
    working_dir = Config.Server.working_directory / "deployments" / deployment_id

    working_dir.mkdir(parents=True)

    # Save uploaded files and extract
    with open(working_dir / "files.zip", "wb+") as destination:
        for chunk in request.FILES["files"].chunks():  # type: ignore
            destination.write(chunk)

    with zipfile.ZipFile(working_dir / "files.zip", "r") as zip_ref:
        zip_ref.extractall(working_dir / "files")

    os.remove(working_dir / "files.zip")

    info = DeploymentInfo(status=DeploymentStatus.scheduled)
    (working_dir / "deployment.info.yml").write_text(yaml.dump(info.dict()))

    return JsonResponse({"id": deployment_id})


def push_logs(
    request: HttpRequest, space_name: str, deployment_id: str
) -> HttpResponse:
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

        response = HttpResponse(log)
        response.headers["MQ-Deployment-Status"] = info.status.value
        return response
    else:
        raise Http404("Deployment does not exist.")
