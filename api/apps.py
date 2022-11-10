from django.apps import AppConfig

from api.deployment.DeploymentProcess import DeploymentMonitor
from api.deployment.Infrastructure import Infrastructure


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        super().ready()

        Infrastructure.restore_instances()
        DeploymentMonitor().start()
