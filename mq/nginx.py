import os
import signal

from nginx.config.api import Comment
from nginx.config.api import Config
from nginx.config.api import Location
from nginx.config.api import Section
from nginx.config.api.blocks import EmptyBlock


def adopt_nginx() -> None:
    events = Section("events", worker_connections=1024)

    http = Section(
        "http",
        include="mime.types",
        default_type="application/octet-stream",
        sendfile="on",
        keepalive_timeout=65,
    )

    http.sections.add(
        Comment(comment="Hello World"),
        Section(
            "server",
            Location("/", root="html", index="index.html index.htm"),
            # Location("/", root="/Users/michael.wellner/Workspaces/mq-apps/test", index="index.html index.htm"),
            listen=8080,
            server_name="localhost",
        ),
    )

    config = Config(
        EmptyBlock(),
        events,
        http,
        worker_processes=1,
        pid="/usr/local/etc/nginx/logs/nginx.pid",
    )

    nginx = EmptyBlock(config)

    with open("/usr/local/etc/nginx/nginx.conf", "w") as f:
        f.write(str(nginx))

    with open("/usr/local/etc/nginx/logs/nginx.pid", "r") as file:
        pid = int(file.read())
        os.kill(pid, signal.SIGHUP)

    print(nginx)


if __name__ == "__main__":
    print("huh")
