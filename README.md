# Dockerfile.py

A simple Python package to write Dockerfiles through Python code. Can be used along with 
[docker-py](https://docker-py.readthedocs.io/en/stable/) to create & start Docker images
from within Python.

Currently, this is pre-alpha software, so use it at your own risk. That being said, the 
code is dead simple (just one single Python class), so you can easily adapt this to your 
needs.


# Examples

Basic example:

```python
from dockerfile_py import Dockerfile

d = Dockerfile()

builder_image = "builder"
some_arg = "foo"

d.FROM("ubuntu/latest", as_image=builder_image)
d.RUN("useradd user")
d.USER("user", "user")
d.WORKDIR("/home/user")
d.COPY(src="./lots_of_scripts/*", dest="./", chown="user:user")
d.RUN(f"./my-command.sh arg1 {some_arg}")  # shell form
d.RUN("./another-command.sh", "arg1", some_arg)  # exec form

d.FROM(builder_image)
d.COPY("./start.sh", from_image=builder_image)
d.CMD("./start.sh", "arg1", "arg2")  # exec form


if __name__ == "__main__":
    print(str(d))  # Print the Docker file
    
    # Build the image using docker-py
    import docker
    client = docker.from_env()
    client.images.build(path="path/to/docker_build_context", fileobj=d.as_fileobj(), ...)
```


Modularizing your Dockerfile:

```python
from dockerfile_py import Dockerfile

d1 = Dockerfile()
d1.RUN("useradd user")
d1.USER("user", "user")
d1.WORKDIR("/home/user")


d2 = Dockerfile()
d2.FROM("ubuntu/latest")
# This will insert the commands from d1 right after `FROM`
d2.include(d1)
d2.RUN("echo", "I will be executed right after the commands from d1")
# ...
```


# Raison d'être

> Everything should be made as simple as possible, but not simpler
>
-- Commonly attributed to Albert Einstein

The Dockerfile DSL was purposefully chosen not to be Turing-complete. While this makes
sense for a lot of reasons, this actively hinders usage in more complicated scenarios. 
For instance, currently [there is no – and probably never will be an – `INCLUDE` 
statement](https://github.com/moby/moby/issues/735) to modularize Dockerfiles and re-use
parts of one Dockerfile in another. Moreover, if your Dockerfile needs to be adapted
slightly depending on the context, you're out of luck, too. You will either have to copy
and paste Dockerfile code all the time; resort to adding `ARG`s and complicated shell
scripts to your Docker image to capture all your use cases; or you will have to run a
preprocessing shell script (involving `sed` and the like) on your Dockerfile before
building your image. Clearly, the first option is very prone to mistakes, and the third
option is a very bad idea, too – it's hard to reason about, hard to debug and there is
generally no clear dependency injection, making things equally hard to refactor.

As for the second option, not only will additional shell logic result in unnecessary 
build steps but `ARG`s are a complicated beast and their interaction with `ENV`, 
multi-stage builds and other Dockerfile commands is anything but obvious. The same thing 
goes for `ENV` variables. Besides, have you ever wondered whether it's Docker that 
replaces `$VARIABLE` or whether it's the shell? (Hint: It *depends*.) Finally, 
environment variables are a very bad way of passing values to other executables to begin 
with. What environment variables an executable respects is hardly explorable, usually 
badly documented and, once set, environment variables are global state, resulting in 
what Einstein would have called "spooky action at a distance".

So let's forget about this altogether. Let's keep our Dockerfile strictly declarative 
and non-dynamic and minimize our usage of `ARG`, `ENV` and shell scripts as far as 
possible. Instead, let's use the power of Python to generate our Dockerfile.
(Imperatively declare our Docker image, so to speak.) After all, Python provides much
better support for modularization, dependency injection and code inspection than a wild 
blend of Dockerfiles, environment variables and shell scripts ever could.


# Unsupported commands
Dockerfile commands that are currently not supported:

- HEALTHCHECK
- ONBUILD
- STOPSIGNAL


# Copyright & license
(c) Copyright 2021 codethief

This project is licensed under the terms of the GPLv3 license, see [LICENSE](LICENSE) 
for the full text.
