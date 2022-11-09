from typing import List
from api.buildpacks.Buildpack import Buildpack
from api.buildpacks.StaticWebapp import StaticWebapp


class Buildpacks:

    all: List[Buildpack] = list([
        StaticWebapp()
    ])