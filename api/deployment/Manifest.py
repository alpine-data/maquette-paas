from typing import Dict
from typing import List
from typing import Optional


class Application:
    def __init__(
        self,
        name: str,
        buildback: str,
        env: Dict[str, str] = {},
        command: Optional[str] = None,
        services: List[str] = [],
    ) -> None:
        self.name = name
        self.buildback = buildback
        self.env = env
        self.command = command
        self.services = services

    @staticmethod
    def from_dict(data: dict) -> "Application":
        return Application(
            name=data["name"],
            buildback=data["buildback"],
            env=data.get("env", {}),
            command=data.get("command", None),
            services=data.get("services", []),
        )

    def to_dict(self) -> dict:
        result: dict = {"name": self.name, "buildback": self.buildback}

        if self.env:
            result["env"] = self.env

        if self.command:
            result["command"] = self.command

        if self.services:
            result["services"] = self.services

        return result


class Manifest:
    def __init__(self, applications: List[Application] = []) -> None:
        self.applications = applications

        self.validate()

    @staticmethod
    def from_dict(data: dict) -> "Manifest":
        applications = list(
            [Application.from_dict(app) for app in data.get("applications", [])]
        )
        return Manifest(applications)

    def to_dict(self) -> dict:
        result: dict = {}

        if self.applications:
            result["applications"] = list([app.to_dict() for app in self.applications])

        return result

    def validate(self) -> None:
        """
        Validates the Manifest instance.
        """

        # TODO implement.
