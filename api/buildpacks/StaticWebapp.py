from pathlib import Path
from api.buildpacks.Buildpack import Buildpack

class StaticWebapp(Buildpack):

    def __init__(self) -> None:
        super().__init__("static-webapp")

    def autodect(self, path: Path) -> bool:
        return True