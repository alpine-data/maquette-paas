from typing import List

from mq.buildpacks.Buildpack import Buildpack
from mq.buildpacks.static_webapp.StaticWebapp import StaticWebapp


class Buildpacks:

    all: List[Buildpack] = list([StaticWebapp()])

    @staticmethod
    def get(name: str) -> Buildpack:
        """ """

        matches = [bp for bp in Buildpacks.all if bp.name == name]

        if matches:
            return matches[0]
        else:
            raise Exception(f"No buildpack `{name}` registered.")
