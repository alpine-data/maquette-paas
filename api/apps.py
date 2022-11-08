from django.apps import AppConfig

from api.deployment.DeploymentProcess import DeploymentMonitor


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        super().ready()

        DeploymentMonitor().start()
