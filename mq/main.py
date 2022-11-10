import os

import click
from django.core.management import execute_from_command_line
from loguru import logger
from api.deployment.Infrastructure import Infrastructure

from mq.cli.push import Push


@click.group()
def mq() -> None:
    """
    Maquette Apps CLI.
    """


@mq.group()
def server() -> None:
    """
    
    """

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

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mq.settings")

    logger.info("Starting Maquette Apps.")

    execute_from_command_line(argv=["manage.py", "migrate"])
    execute_from_command_line(argv=["manage.py", "runserver", "--noreload"])


@mq.command()
def push() -> None:
    Push.run()


if __name__ == "__main__":
    mq()
