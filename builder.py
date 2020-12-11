#!/usr/bin/env python3

"""
Generate various docker and config files across a matrix of archs/distros.
"""

import abc
import argparse
import contextlib
import functools
import itertools
import json
import os
import pathlib
import re
import shutil
import sys
import time

from jinja2 import (
    contextfilter,
    Environment,
    StrictUndefined,
)
from path import Path
from ruamel import yaml
from sh import docker as _docker  # pylint: disable=no-name-in-module
from sh import docker_compose as _docker_compose  # pylint: disable=no-name-in-module
from sh import ErrorReturnCode_1  # pylint: disable=no-name-in-module
from sh import which  # pylint: disable=no-name-in-module


docker = functools.partial(_docker, _out=sys.stdout, _err=sys.stderr)
docker_compose = functools.partial(_docker_compose, _out=sys.stdout, _err=sys.stderr)

PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


class Dumper(yaml.RoundTripDumper):
    def ignore_aliases(self, data):
        # Strip aliases
        return True


def slugify(string, delim="-"):
    return re.sub(r"[^\w]", delim, string).lower()


docker_manifest_args = {
    "amd64": ["--arch", "amd64"],
    "i386": ["--arch", "386"],
    "arm32v5": ["--arch", "arm", "--variant", "v5"],
    "arm32v6": ["--arch", "arm", "--variant", "v6"],
    "arm32v7": ["--arch", "arm", "--variant", "v7"],
    "arm64v8": ["--arch", "arm64", "--variant", "v8"],
    "ppc": ["--arch", "ppc"],
    "ppc64le": ["--arch", "ppc64le"],
    "s390x": ["--arch", "s390x"],
    "mips64le": ["--arch", "mips64le"],
}


def configure_qemu():
    if not which("qemu-aarch64") and not which("qemu-system-aarch64"):
        raise RuntimeError(
            "QEMU not installed, install missing package (apt: qemu,qemu-user-static | pacman: qemu-headless,qemu-headless-arch-extra | brew: qemu)."
        )

    images = docker("images", "--format", "{{ .Repository }}", _out=None, _err=None)
    if "multiarch/qemu-user-static" not in images:
        docker(
            "run",
            "--rm",
            "--privileged",
            "multiarch/qemu-user-static",
            "--reset",
            "-p",
            "yes",
        )


def get_platform(arch):
    return f"linux/{arch.replace('arm32', 'arm/').replace('arm64', 'arm64/')}"


class Distro(metaclass=abc.ABCMeta):
    template_path = None
    registry = {}
    host_archs = ()
    compiler_archs = ()
    ports_by_arch = {}
    toolchains_by_arch = {}
    compiler_archs_by_host_arch = {}

    def __init__(
        self,
        *,
        name,
        host_image="elijahru/build-farm",
        client_image="elijahru/build-farm-client",
    ):
        self.name = name
        self.host_image = host_image
        self.client_image = client_image
        self.registry[name] = self
        self._context = None
        self.env = Environment(autoescape=False, undefined=StrictUndefined)
        self.env.filters["compiler_archs"] = self.compiler_archs_by_host_arch.get
        self.env.filters["compiler_port"] = self.ports_by_arch.get
        self.env.filters["toolchain"] = self.toolchains_by_arch.get
        self.env.filters["compiler_path_part"] = self.get_compiler_path_part
        self.env.filters["host_image_tag"] = self.host_image_tag
        self.env.filters["client_image_tag"] = self.client_image_tag

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"

    @classmethod
    def get(cls, name):
        if name not in cls.registry:
            raise ValueError(
                f'Unsupported distro {name}, choose from {", ".join(cls.registry.keys())}'
            )
        return cls.registry[name]

    @classmethod
    def clean_all(cls):
        for distro in cls.registry.values():
            distro.clean()

    @classmethod
    def render_all(cls, **context):
        for distro in cls.registry.values():
            distro.render(**context)

    @classmethod
    def build_all(cls, version, push=False):
        for distro in cls.registry.values():
            for host_arch in distro.host_archs:
                distro.build_host(host_arch, version=version, push=push)
                for compiler_arch in distro.compiler_archs_by_host_arch[host_arch]:
                    distro.build_client(
                        host_arch, compiler_arch, version=version, push=push
                    )

    @property
    def context(self):
        if self._context is None:
            raise RuntimeError("Distro context not entered")
        return self._context

    def host_manifest_tags(self, version):
        return (
            f"{self.host_image}:{self.slug}--{version}",
            f"{self.host_image}:{self.slug}",
        )

    def host_image_tag(self, version, arch):
        return f"{self.host_image}:{self.slug}--{arch}--{version}"

    def host_image_latest_tag(self, arch):
        return f"{self.host_image}:{self.slug}--{arch}"

    def client_manifest_tags(self, version):
        return (
            f"{self.client_image}:{self.slug}--{version}",
            f"{self.client_image}:{self.slug}",
        )

    def client_image_tag(self, version, arch):
        return f"{self.client_image}:{self.slug}--{arch}--{version}"

    def client_image_latest_tag(self, arch):
        return f"{self.client_image}:{self.slug}--{arch}"

    @contextlib.contextmanager
    def set_context(self, **context):
        prev_context = self._context.copy() if self._context else None
        new_context = self._context.copy() if self._context else {}
        new_context.update(context)
        self._context = self.get_template_context(**new_context)
        try:
            yield
        finally:
            self._context = prev_context

    def render_template(self, template_path, out_path):
        with PROJECT_DIR:
            template_path = template_path.format(**self.context)
            with open(template_path, "r") as f:
                rendered = self.env.from_string(f.read()).render(**self.context)
            out_path = out_path.format(**self.context)
            dir_name = os.path.dirname(out_path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            lines = rendered.split("\n")
            if lines and lines[0].startswith("#!"):
                lines.insert(1, f"# Rendered from {template_path}\n")
            else:
                lines.insert(0, f"# Rendered from {template_path}\n")
            rendered = "\n".join(lines)

            with open(out_path, "w") as f:
                f.write(rendered)
            print(f"Rendered {template_path} -> {out_path}")
            return out_path

    def interpolate_yaml(self, yaml_path):
        with PROJECT_DIR:
            yaml_path = yaml_path.format(**self.context)
            with open(yaml_path, "r") as f:
                rendered = yaml.load(f, Loader=yaml.RoundTripLoader)

            # Remove _anchors section
            if "_anchors" in rendered:
                del rendered["_anchors"]

            # Use custom Dumper that replaces aliases with referenced content
            rendered = yaml.dump(rendered, Dumper=Dumper)

            with open(yaml_path, "w") as f:
                f.write(rendered)

            print(f"Interpolated {yaml_path}")
            return yaml_path

    @property
    def docker_compose_yml_path(self):
        return self.out_path / f"docker-compose.yml"

    @property
    def github_actions_yml_path(self):
        return Path(f".github/workflows/{self.slug}.yml")

    def clean(self):
        if os.path.exists(self.out_path):
            shutil.rmtree(self.out_path)
            print(f"Removed {self.out_path}")
        if os.path.exists(self.github_actions_yml_path):
            os.unlink(self.github_actions_yml_path)
            print(f"Removed {self.github_actions_yml_path}")

    @property
    def out_path(self):
        return Path(self.slug)

    @abc.abstractmethod
    def get_compiler_path_part(self, compiler_arch):
        ...

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def identifier(self):
        return slugify(self.name, "_")

    def get_template_context(self, **context):
        context.update(
            dict(
                distro=self,
            )
        )
        return context

    def render(self, **context):
        with self.set_context(**context):
            self.render_dockerfile_host()
            self.render_dockerfile_client()
            self.render_run_sh()
            self.render_docker_compose()
            self.render_github_actions()

            with PROJECT_DIR:
                for root, _, files in os.walk(self.template_path):
                    root = Path(root)
                    new_root = Path(root.replace(self.template_path, self.out_path))
                    for f in files:
                        if ".jinja" in f:
                            continue
                        if not os.path.exists(os.path.dirname(new_root / f)):
                            os.makedirs(os.path.dirname(new_root / f))
                        shutil.copyfile(root / f, new_root / f)
                        print(f"Copied {root / f} -> {new_root / f}")

                for root, _, files in os.walk(Path("shared-build-context") / "host"):
                    root = Path(root)
                    new_root = Path(
                        root.replace(
                            "shared-build-context/host",
                            self.out_path / "host/build-context",
                        )
                    )
                    for f in files:
                        if ".jinja" in f:
                            continue
                        if not os.path.exists(os.path.dirname(new_root / f)):
                            os.makedirs(os.path.dirname(new_root / f))
                        shutil.copyfile(root / f, new_root / f)
                        print(f"Copied {root / f} -> {new_root / f}")

                for root, _, files in os.walk(Path("shared-build-context") / "client"):
                    root = Path(root)
                    new_root = Path(
                        root.replace(
                            "shared-build-context/client",
                            self.out_path / "client/build-context",
                        )
                    )
                    for f in files:
                        if ".jinja" in f:
                            continue
                        if not os.path.exists(os.path.dirname(new_root / f)):
                            os.makedirs(os.path.dirname(new_root / f))
                        shutil.copyfile(root / f, new_root / f)
                        print(f"Copied {root / f} -> {new_root / f}")

                for root, _, files in os.walk(Path("shared-build-context") / "shared"):
                    root = Path(root)
                    for container_type in ("host", "client"):
                        new_root = Path(
                            root.replace(
                                "shared-build-context/shared",
                                self.out_path / container_type / "build-context",
                            )
                        )
                        for f in files:
                            if ".jinja" in f:
                                continue
                            if not os.path.exists(os.path.dirname(new_root / f)):
                                os.makedirs(os.path.dirname(new_root / f))
                            shutil.copyfile(root / f, new_root / f)
                            print(f"Copied {root / f} -> {new_root / f}")

    def render_dockerfile_host(self):
        for host_arch in self.host_archs:
            with self.set_context(host_arch=host_arch):
                self.render_template(
                    self.template_path / "host/Dockerfile.jinja",
                    self.out_path / "host" / "Dockerfile.{host_arch}",
                )

    def render_dockerfile_client(self):
        for host_arch in self.host_archs:
            for compiler_arch in self.compiler_archs_by_host_arch[host_arch]:
                with self.set_context(host_arch=host_arch, compiler_arch=compiler_arch):
                    self.render_template(
                        self.template_path / "client/Dockerfile.jinja",
                        self.out_path / "client" / "Dockerfile.{compiler_arch}",
                    )

    def render_docker_compose(self):
        self.render_template(
            self.template_path / "docker-compose.yml.jinja",
            self.docker_compose_yml_path,
        )

    def render_github_actions(self):
        with self.set_context():
            self.render_template(
                Path(".github/workflows/build.yml.jinja"),
                self.github_actions_yml_path,
            )
            # Replace YAML aliases in rendered jinja output
            self.interpolate_yaml(self.github_actions_yml_path)

    def render_run_sh(self):
        for host_arch in self.host_archs:
            with self.set_context(host_arch=host_arch):
                self.render_template(
                    "shared-build-context/host/scripts/run.sh.jinja",
                    self.out_path / f"host/build-context/scripts/run-{host_arch}.sh",
                )

    def build_host(self, host_arch, version, push=False):
        configure_qemu()

        self.render(version=version)

        image = self.host_image_tag(version, host_arch)
        dockerfile = self.out_path / f"host/Dockerfile.{host_arch}"
        try:
            docker("pull", image, "--platform", get_platform(host_arch))
        except ErrorReturnCode_1:
            pass
        docker(
            "build",
            self.out_path / "host/build-context",
            "--file",
            dockerfile,
            "--tag",
            image,
            "--cache-from",
            image,
            "--platform",
            get_platform(host_arch),
        )
        if push:
            docker("push", image)

    def build_client(self, client_arch, version, push=False):
        configure_qemu()

        self.render(version=version)

        # TODO - determine host_arch
        with self.run_host(host_arch="amd64"):
            image = self.client_image_tag(version, client_arch)
            dockerfile = self.out_path / f"client/Dockerfile.{client_arch}"
            try:
                docker("pull", image, "--platform", get_platform(client_arch))
            except ErrorReturnCode_1:
                pass

            docker(
                "build",
                self.out_path / "client/build-context",
                "--file",
                dockerfile,
                "--tag",
                image,
                "--cache-from",
                image,
                "--platform",
                get_platform(client_arch),
            )
            if push:
                docker("push", image)

    def push_host_manifest(self, version):
        os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

        images = {
            host_arch: self.host_image_tag(version, host_arch)
            for host_arch in self.host_archs
        }

        for image in images.values():
            docker("pull", image)

        for manifest in self.host_manifest_tags(version):
            try:
                docker("manifest", "create", "--amend", manifest, *images.values())
            except ErrorReturnCode_1:
                docker("manifest", "create", manifest, *images.values())

            for host_arch in self.host_archs:
                docker(
                    "manifest",
                    "annotate",
                    manifest,
                    images[host_arch],
                    "--os",
                    "linux",
                    *docker_manifest_args[host_arch],
                )

            docker("manifest", "push", manifest)

    def push_client_manifest(self, version):
        os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

        images = {
            compiler_arch: self.client_image_tag(version, compiler_arch)
            for compiler_arch in self.compiler_archs
        }

        for image in images.values():
            docker("pull", image)

        for manifest in self.client_manifest_tags(version):
            try:
                docker("manifest", "create", "--amend", manifest, *images.values())
            except ErrorReturnCode_1:
                docker("manifest", "create", manifest, *images.values())

            for compiler_arch in self.compiler_archs:
                docker(
                    "manifest",
                    "annotate",
                    manifest,
                    images[compiler_arch],
                    "--os",
                    "linux",
                    *docker_manifest_args[compiler_arch],
                )

            docker("manifest", "push", manifest)

    def tag_host_latest(self, version):
        os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

        images = {
            host_arch: (
                self.host_image_tag(version, host_arch),
                self.host_image_latest_tag(host_arch),
            )
            for host_arch in self.host_archs
        }

        for image, latest in images.values():
            docker("pull", image)
            docker("tag", image, latest)
            docker("push", latest)

    def tag_client_latest(self, version):
        os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

        images = {
            compiler_arch: (
                self.client_image_tag(version, compiler_arch),
                self.client_image_latest_tag(compiler_arch),
            )
            for compiler_arch in self.compiler_archs
        }

        for image, latest in images.values():
            docker("pull", image)
            docker("tag", image, latest)
            docker("push", latest)

    @contextlib.contextmanager
    def run_host(self, host_arch):
        image_id = lambda: docker(
            "ps",
            "--filter",
            f"name=host-{host_arch}",
            "--format",
            "{{.ID}}",
            _out=None,
            _err=None,
        ).strip()
        id = image_id()
        if id:
            docker("kill", id, _out=None, _err=None)
        docker_compose(
            "-f", self.docker_compose_yml_path, "up", "-d", f"host-{host_arch}"
        )
        time.sleep(5)
        try:
            yield
        finally:
            id = image_id()
            if id:
                docker("kill", id, _out=None, _err=None)


class DebianLike(Distro):
    template_path = Path("debian-like")

    host_archs = (
        "amd64",
        "i386",
        "arm32v5",
        "arm32v7",
        "arm64v8",
        "ppc64le",
        "s390x",
        "mips64le",
    )
    compiler_archs = (
        "amd64",
        "i386",
        "arm32v5",
        "arm32v7",
        "arm64v8",
        "ppc64le",
        "s390x",
        "mips64le",
    )
    compiler_archs_by_host_arch = {
        "amd64": (
            "amd64",
            "i386",
            "arm32v5",
            "arm32v7",
            "arm64v8",
            "ppc64le",
            "s390x",
            "mips64le",
        ),
        "i386": (
            "amd64",
            "i386",
            "arm32v5",
            "arm32v7",
            "arm64v8",
            "ppc64le",
            "s390x",
            "mips64le",
        ),
        "arm32v5": ("arm32v5",),
        "arm32v7": ("arm32v7",),
        "arm64v8": ("amd64", "i386", "arm32v5", "arm32v7", "arm64v8"),
        "ppc64le": ("amd64", "i386", "arm64v8", "ppc64le"),
        "s390x": ("s390x",),
        "mips64le": ("mips64le",),
    }
    packages_by_arch = {
        "amd64": "gcc-x86-64-linux-gnu g++-x86-64-linux-gnu binutils-x86-64-linux-gnu",
        "i386": "gcc-i686-linux-gnu g++-i686-linux-gnu binutils-i686-linux-gnu",
        "arm32v5": "gcc-arm-linux-gnueabi g++-arm-linux-gnueabi binutils-arm-linux-gnueabi",
        "arm32v7": "gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf binutils-arm-linux-gnueabihf",
        "arm64v8": "gcc-aarch64-linux-gnu g++-aarch64-linux-gnu binutils-aarch64-linux-gnu",
        "ppc64le": "gcc-powerpc64le-linux-gnu g++-powerpc64le-linux-gnu binutils-powerpc64le-linux-gnu",
        "s390x": "gcc-s390x-linux-gnu g++-s390x-linux-gnu binutils-s390x-linux-gnu",
        "mips64le": "gcc-mipsel-linux-gnu g++-mipsel-linux-gnu binutils-mipsel-linux-gnu",
    }
    ports_by_arch = {
        "i386": "3603",
        "amd64": "3604",
        "arm32v5": "3605",
        "arm32v7": "3607",
        "arm64v8": "3608",
        "s390x": "3609",
        "ppc64le": "3610",
        "mips64le": "3611",
    }
    toolchains_by_arch = {
        "amd64": "x86_64-linux-gnu",
        "i386": "i686-linux-gnu",
        "arm32v5": "arm-linux-gnueabi",
        "arm32v7": "arm-linux-gnueabihf",
        "arm64v8": "aarch64-linux-gnu",
        "ppc64le": "powerpc64le-linux-gnu",
        "s390x": "s390x-linux-gnu",
        "mips64le": "mipsel-linux-gnu",
    }
    flags_by_arch = {
        "amd64": "START_DISTCC_X86_64_LINUX_GNU",
        "i386": "START_DISTCC_I686_LINUX_GNU",
        "arm32v5": "START_DISTCC_ARM_LINUX_GNUEABI",
        "arm32v7": "START_DISTCC_ARM_LINUX_GNUEABIHF",
        "arm64v8": "START_DISTCC_AARCH64_LINUX_GNU",
        "ppc64le": "START_DISTCC_PPC64LE_LINUX_GNU",
        "s390x": "START_DISTCC_S390X_LINUX_GNU",
        "mips64le": "START_DISTCC_MIPS64LE_LINUX_GNU",
    }

    def __init__(self, **kwargs):
        super(DebianLike, self).__init__(**kwargs)
        self.env.filters["flag"] = self.flags_by_arch.get
        self.env.filters["apt_packages"] = self.get_apt_packages

    def get_apt_packages(self, host_arch):
        packages = "build-essential g++ distcc lsb-base"
        for compiler_arch in self.compiler_archs_by_host_arch[host_arch]:
            packages += f" {self.packages_by_arch[compiler_arch]}"
        return packages

    def get_compiler_path_part(self, compiler_arch):
        if self.context["host_arch"] == compiler_arch:
            return ""
        return Path("/usr/local/") / self.toolchains_by_arch[compiler_arch] / "bin:"


class ArchLinuxLike(Distro):
    template_path = Path("archlinux-like")

    host_archs = (
        "amd64",
        "arm32v5",
        "arm32v6",
        "arm32v7",
        "arm64v8",
    )
    compiler_archs = (
        "amd64",
        "arm32v5",
        "arm32v6",
        "arm32v7",
        "arm64v8",
    )
    compiler_archs_by_host_arch = {
        "amd64": (
            "amd64",
            "arm32v5",
            "arm32v6",
            "arm32v7",
            "arm64v8",
        ),
        "arm32v5": ("arm32v5",),
        "arm32v6": ("arm32v6",),
        "arm32v7": ("arm32v7",),
        "arm64v8": ("arm64v8",),
    }
    ports_by_arch = {
        "amd64": "3704",
        "arm32v5": "3705",
        "arm32v6": "3706",
        "arm32v7": "3707",
        "arm64v8": "3708",
    }
    toolchains_by_arch = {
        "arm32v5": "/toolchains/x-tools/arm-unknown-linux-gnueabi",
        "arm32v6": "/toolchains/x-tools6h/arm-unknown-linux-gnueabihf",
        "arm32v7": "/toolchains/x-tools7h/arm-unknown-linux-gnueabihf",
        "arm64v8": "/toolchains/x-tools8/aarch64-unknown-linux-gnu",
    }

    def get_compiler_path_part(self, compiler_arch):
        if self.context["host_arch"] == compiler_arch:
            return ""
        return Path(self.toolchains_by_arch[compiler_arch]) / "bin:"


class AlpineLike(Distro):
    template_path = Path("alpine-like")

    host_archs = (
        "amd64",
        "i386",
        "arm32v6",
        "arm32v7",
        "arm64v8",
        "ppc64le",
        "s390x",
    )
    compiler_archs = (
        "amd64",
        "i386",
        "arm32v6",
        "arm32v7",
        "arm64v8",
        "ppc64le",
        "s390x",
    )
    compiler_archs_by_host_arch = {
        "amd64": ("amd64", "i386", "arm32v6", "arm32v7", "arm64v8", "ppc64le", "s390x"),
        "i386": ("amd64", "i386", "arm32v6", "arm32v7", "arm64v8", "ppc64le", "s390x"),
        "arm32v6": ("arm32v6",),
        "arm32v7": ("arm32v7",),
        "arm64v8": ("arm64v8",),
        "ppc64le": ("ppc64le",),
        "s390x": ("s390x",),
    }
    ports_by_arch = {
        "i386": "3803",
        "amd64": "3804",
        "arm32v6": "3806",
        "arm32v7": "3807",
        "arm64v8": "3808",
        "s390x": "3809",
        "ppc64le": "3810",
    }
    toolchain_urls_by_host_arch = {
        "amd64": {
            "i386": "https://more.musl.cc/9/x86_64-linux-musl/i686-linux-musl-cross.tgz",
            "arm32v6": "https://more.musl.cc/9/x86_64-linux-musl/armel-linux-musleabi-cross.tgz",
            "arm32v7": "https://more.musl.cc/9/x86_64-linux-musl/armel-linux-musleabihf-cross.tgz",
            "arm64v8": "https://more.musl.cc/9/x86_64-linux-musl/aarch64-linux-musl-cross.tgz",
            "s390x": "https://more.musl.cc/9/x86_64-linux-musl/s390x-linux-musl-cross.tgz",
            "ppc64le": "https://more.musl.cc/9/x86_64-linux-musl/powerpc64le-linux-musl-cross.tgz",
        },
        "i386": {
            "amd64": "https://more.musl.cc/9/i686-linux-musl/x86_64-linux-musl-cross.tgz",
            "arm32v6": "https://more.musl.cc/9/i686-linux-musl/armel-linux-musleabi-cross.tgz",
            "arm32v7": "https://more.musl.cc/9/i686-linux-musl/armel-linux-musleabihf-cross.tgz",
            "arm64v8": "https://more.musl.cc/9/i686-linux-musl/aarch64-linux-musl-cross.tgz",
            "s390x": "https://more.musl.cc/9/i686-linux-musl/s390x-linux-musl-cross.tgz",
            "ppc64le": "https://more.musl.cc/9/i686-linux-musl/powerpc64le-linux-musl-cross.tgz",
        },
    }
    toolchains_by_arch = {
        "i386": "/toolchains/i686-linux-musl-cross",
        "amd64": "/toolchains/x86_64-linux-musl-cross",
        "arm32v6": "/toolchains/armel-linux-musleabi-cross",
        "arm32v7": "/toolchains/armel-linux-musleabihf-cross",
        "arm64v8": "/toolchains/aarch64-linux-musl-cross",
        "s390x": "/toolchains/s390x-linux-musl-cross",
        "ppc64le": "/toolchains/powerpc64le-linux-musl-cross",
    }

    def get_compiler_path_part(self, compiler_arch):
        if self.context["host_arch"] == compiler_arch:
            return ""
        return Path(self.toolchains_by_arch[compiler_arch]) / "bin:"


# Register supported distributions
debian_buster = DebianLike(
    name="debian:buster",
)
debian_buster_slim = DebianLike(
    name="debian:buster-slim",
)
archlinux = ArchLinuxLike(
    name="archlinux",
)
alpine_3_12 = AlpineLike(
    name="alpine:3.12",
)


def render_readme():
    env = Environment(autoescape=False, undefined=StrictUndefined)
    env.filters["slugify"] = slugify
    with PROJECT_DIR:
        context = dict(
            project_name="build-farm",
            repo="elijahr/build-farm",
            Distro=Distro,
        )
        for distro in Distro.registry.values():
            context[distro.identifier] = distro
        with open("README.md.jinja", "r") as f:
            rendered = env.from_string(f.read()).render(**context)
        with open("README.md", "w") as f:
            f.write(rendered)
        print("Rendered README.md.jinja -> README.md")


def make_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subcommand")

    # list-distros
    subparsers.add_parser("list-distros")

    # list-host-archs
    parser_list_host_archs = subparsers.add_parser("list-host-archs")
    parser_list_host_archs.add_argument("--distro", type=Distro.get, required=True)

    # list-compiler-archs
    parser_list_compiler_archs = subparsers.add_parser("list-compiler-archs")
    parser_list_compiler_archs.add_argument("--distro", type=Distro.get, required=True)

    # render
    parser_render = subparsers.add_parser("render")
    parser_render.add_argument("--version", required=True)

    # render
    subparsers.add_parser("render-github-actions")

    # build-host
    parser_build_host = subparsers.add_parser("build-host")
    parser_build_host.add_argument("--distro", type=Distro.get, required=True)
    parser_build_host.add_argument("--host-arch", required=True)
    parser_build_host.add_argument("--version", required=True)
    parser_build_host.add_argument("--push", action="store_true")

    # build-client
    parser_build_client = subparsers.add_parser("build-client")
    parser_build_client.add_argument("--distro", type=Distro.get, required=True)
    parser_build_client.add_argument("--client-arch", required=True)
    parser_build_client.add_argument("--version", required=True)
    parser_build_client.add_argument("--push", action="store_true")

    # build-all
    parser_build_all = subparsers.add_parser("build-all")
    parser_build_all.add_argument("--version", required=True)
    parser_build_all.add_argument("--push", action="store_true")

    # clean
    subparsers.add_parser("clean")

    # push-host-manifest
    parser_push_host_manifest = subparsers.add_parser("push-host-manifest")
    parser_push_host_manifest.add_argument("--distro", type=Distro.get, required=True)
    parser_push_host_manifest.add_argument("--version", required=True)

    # push-client-manifest
    parser_push_client_manifest = subparsers.add_parser("push-client-manifest")
    parser_push_client_manifest.add_argument("--distro", type=Distro.get, required=True)
    parser_push_client_manifest.add_argument("--version", required=True)

    # tag-host-latest
    parser_tag_host_latest = subparsers.add_parser("tag-host-latest")
    parser_tag_host_latest.add_argument("--distro", type=Distro.get, required=True)
    parser_tag_host_latest.add_argument("--version", required=True)

    # tag-client-latest
    parser_tag_client_latest = subparsers.add_parser("tag-client-latest")
    parser_tag_client_latest.add_argument("--distro", type=Distro.get, required=True)
    parser_tag_client_latest.add_argument("--version", required=True)

    # render-readme
    subparsers.add_parser("render-readme")

    return parser


def main():
    args = make_parser().parse_args()
    if args.subcommand == "list-distros":
        print("\n".join(Distro.registry.keys()))

    elif args.subcommand == "list-host-archs":
        print("\n".join(args.distro.host_archs))

    elif args.subcommand == "list-compiler-archs":
        print("\n".join(args.distro.compiler_archs))

    elif args.subcommand == "render":
        Distro.render_all(version=args.version)

    elif args.subcommand == "render-github-actions":
        for distro in Distro.registry.values():
            distro.render_github_actions()

    elif args.subcommand == "build-host":
        args.distro.build_host(args.host_arch, version=args.version, push=args.push)

    elif args.subcommand == "build-client":
        args.distro.build_client(args.client_arch, version=args.version, push=args.push)

    elif args.subcommand == "build-all":
        Distro.build_all(version=args.version, push=args.push)

    elif args.subcommand == "clean":
        Distro.clean_all()

    elif args.subcommand == "test":
        args.distro.test(args.host_arch, args.client_arch, version=args.version)

    elif args.subcommand == "push-host-manifest":
        args.distro.push_host_manifest(version=args.version)

    elif args.subcommand == "push-client-manifest":
        args.distro.push_client_manifest(version=args.version)

    elif args.subcommand == "tag-host-latest":
        args.distro.tag_host_latest(version=args.version)

    elif args.subcommand == "tag-client-latest":
        args.distro.tag_client_latest(version=args.version)

    elif args.subcommand == "render-readme":
        render_readme()

    else:
        raise ValueError(f"Unknown subcommand {args.subcommand}")


if __name__ == "__main__":
    main()
