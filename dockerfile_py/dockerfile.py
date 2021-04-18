import json
from io import StringIO
from typing import Optional, List, Literal, Union

# A general note on the implementation here: Whenever we enquote strings for the
# Dockerfile, we generally use json.dumps() instead of repr(). The reason is that *some*
# Docker commands indeed expect JSON strings (in particular: strings must be enquoted by
# double quotation marks!) which suggests that all other commands expect strings to be
# JSON strings, too.


class Dockerfile:
    """
    A rather barebones way to create a Dockerfile. No consistency checks of any kind are
    performed.
    """
    def __init__(self, syntax: Optional[str] = None, escape: Optional[str] = None):
        """
        For `syntax` and `escape` see
        https://docs.docker.com/engine/reference/builder/#parser-directives
        """
        self._lines: List[str] = []

        if syntax is not None:
            self._lines.append(f"# syntax: {syntax}")
        if escape is not None:
            self._lines.append(f"# escape: {escape}")

    def __str__(self) -> str:
        return "".join(self._lines)

    def as_fileobj(self) -> StringIO:
        """
        Return the Dockerfile as a file-like object. Useful for passing the Dockerfile
        to the Docker Python library (https://docker-py.readthedocs.io/en/stable/index.html).
        """
        return StringIO(str(self))

    def include(self, dockerfile: "Dockerfile") -> None:
        """
        Include another Dockerfile inside the present Dockerfile as if the commands in
        the former had been added directly to the latter.
        """
        self._lines += dockerfile._lines

    # ----------------------------------------------------------------------------------
    # Dockerfile commands
    # ----------------------------------------------------------------------------------

    def ADD(self, src: str, dest: str, chown: Optional[str] = None):
        """
        See https://docs.docker.com/engine/reference/builder/#add
        """
        if chown is not None:
            chown_param = f"--chown={chown} "
        else:
            chown_param = ""

        self._lines.append(f"ADD {chown_param}{src} {dest}")

    def ARG(self, varname: str, default_value: Optional[str] = None) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#arg

        The `default_value` will be enquoted automatically.
        """
        if default_value is not None:
            default_param = f"={json.dumps(default_value)}"
        else:
            default_param = ""

        self._lines.append(f"ARG {varname}{default_param}")

    def COPY(self, src: Union[str, List[str]], dest: str, from_: Optional[str] = None, chown: Optional[str] = None):
        """
        See https://docs.docker.com/engine/reference/builder/#copy
        """
        if from_ is not None:
            from_param = f"--from={from_} "
        else:
            from_param = ""

        if chown is not None:
            chown_param = f"--chown={chown} "
        else:
            chown_param = ""

        if isinstance(src, str):
            src_and_dest = f"{src} {dest}"
        elif isinstance(src, list):
            src_and_dest = json.dumps(src + [dest])
        else:
            raise ValueError("src must be of type str or list")

        self._lines.append(f"COPY {from_param}{chown_param}{src_and_dest}")

    def CMD(self, command: str, *args: str) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#cmd

        Will use "shell" form of CMD command if only `command` is given and "exec" form
        if additional arguments are present.
        """
        if len(args) == 0:
            self._lines.append(f"CMD {command}")
        else:
            # "exec" form of CMD command expects JSON array
            params = json.dumps([command] + args)
            self._lines.append(f"CMD {params}")

    def ENTRYPOINT(self, command: str, *args: str) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#entrypoint

        Will use "shell" form of ENTRYPOINT command if only `command` is given and
        "exec" form if additional arguments are present.
        """
        if len(args) == 0:
            self._lines.append(f"ENTRYPOINT {command}")
        else:
            # "exec" form of ENTRYPOINT command expects JSON array
            params = json.dumps([command] + args)
            self._lines.append(f"ENTRYPOINT {params}")

    def ENV(self, varname: str, value: str) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#env

        The value will always be enquoted in the Dockerfile. Multiple variables inside
        one ENV statement are currently not supported.
        """
        self._lines.append(f"ENV {varname}={json.dumps(value)}")

    def EXPOSE(self, port: int, protocol: Union[Literal["tcp", "udp"]] = "tcp"):
        """
        See https://docs.docker.com/engine/reference/builder/#expose
        """
        self._lines.append(f"EXPOSE {port}/{protocol}")

    def FROM(self, base_image: str, as_image: Optional[str] = None, platform: Optional[str] = None) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#from
        """
        if platform is not None:
            platform_param = f"--platform={platform}"
        else:
            platform_param = ""

        if as_image is not None:
            as_image_param = f" as {as_image}"
        else:
            as_image_param = ""

        self._lines.append(f"FROM {platform_param}{base_image}{as_image_param}")

    def LABEL(self, key: str, value: str) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#label

        Multiple variables inside one LABEL statement are currently not supported.
        """
        self._lines.append(f"LABEL {json.dumps(key)}={json.dumps(value)}")

    def RUN(self, command: str, *args: str) -> None:
        """
        See https://docs.docker.com/engine/reference/builder/#run

        Will use "shell" form of RUN command if only `command` is given and "exec" form
        if additional arguments are present.
        """
        if len(args) == 0:
            self._lines.append(f"RUN {command}")
        else:
            # "exec" form of RUN command expects JSON array
            params = json.dumps([command] + args)
            self._lines.append(f"RUN {params}")

    def SHELL(self, executable: str, *params: str):
        """
        See https://docs.docker.com/engine/reference/builder/#shell
        """
        # Parameters must be given as JSON array
        self._lines.append(f"SHELL {json.dumps([executable] + params)}")

    def USER(self, user: str, group: Optional[str] = None):
        """
        See https://docs.docker.com/engine/reference/builder/#user
        """
        if group is not None:
            group_param = f":{group}"
        else:
            group_param = ""
        self._lines.append(f"USER {user}{group_param}")

    def VOLUME(self, path: str, *additional_paths: str):
        """
        See https://docs.docker.com/engine/reference/builder/#volume

        Will always use the "list" form of the VOLUME statement.
        """

        # list of paths must be given as JSON array
        paths = json.dumps([path] + additional_paths)
        self._lines.append(f"VOLUME {paths}")

    def WORKDIR(self, path: str):
        """
        See https://docs.docker.com/engine/reference/builder/#workdir
        """
        self._lines.append(f"WORKDIR {path}")
