import click
import uvicorn
from loguru import logger

from mq.cli.push import Push
from mq.deployment.DeploymentProcess import DeploymentMonitor
from mq.deployment.Infrastructure import Infrastructure


@click.group()
def mq() -> None:
    """
    Maquette Apps CLI.
    """


@mq.group()
def server() -> None:
    """ """


@server.command()
def configure_nginx() -> None:
    """
    Configure the local NGINX. Usually used for inital config.
    """

    Infrastructure.update_load_balancer(False)


@server.command()
def run() -> None:
    """
    Starts the Maquette Apps Server.
    """

    logger.info("Starting Maquette Apps.")

    Infrastructure.restore_instances()
    DeploymentMonitor().start()

    config = uvicorn.Config("mq.server:app", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()


@mq.command()
def push() -> None:
    Push.run()


if __name__ == "__main__":
    mq()
