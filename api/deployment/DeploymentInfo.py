from enum import Enum


class DeploymentStatus(Enum):
    scheduled = "scheduled"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class DeploymentInfo:
    def __init__(self, status: DeploymentStatus) -> None:
        self.status = status

    @staticmethod
    def from_dict(data: dict) -> "DeploymentInfo":
        return DeploymentInfo(status=DeploymentStatus[data["status"]])

    def dict(self) -> dict:
        return {"status": str(self.status.value)}
