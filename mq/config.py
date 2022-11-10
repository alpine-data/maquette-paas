from pathlib import Path
from typing import List

from click import ClickException
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="MQ",
    settings_files=[
        "settings.toml",
        ".secrets.toml",
        "/Users/michael.wellner/.mq/config.toml",
    ],
)

# Initialize Target values
current_target = settings.get("cli.target", "default")
target = settings.get(f"cli.targets.{current_target}")

if target is None:
    raise ClickException(
        f"Currently selected target `{current_target}` is not configured."
    )


class Config:
    class CLI:
        class Target:
            endpoint: str = target.get("endpoint", "http://localhost:8000")
            org: str = target.get("org", "wellnr")
            space: str = target.get("space", "hippo")

        class Push:

            ignore_by_default: List[str] = settings.get(
                "cli.push.ignore_by_default", []
            )

    class Server:

        domain: str = str(settings.get("server.domain", "home.wellnr.de"))

        working_directory: Path = Path(settings.get("server.working_directory", "."))

        network_name: str = str(settings.get("server.network_name", "mq-apps"))

        deployment_timeout_in_seconds: int = settings.get(
            "server.deployment_timeout_in_seconds", 120
        )

        class NGINX:

            pid_file: str = str(
                settings.get(
                    "server.nginx.pid_file", "/usr/local/etc/nginx/logs/nginx.pid"
                )
            )

            config_file: str = str(
                settings.get(
                    "server.nginx.config_file", "/usr/local/etc/nginx/nginx.conf"
                )
            )
