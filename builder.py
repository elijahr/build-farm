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
from sh import sh  # pylint: disable=no-name-in-module
from sh import which  # pylint: disable=no-name-in-module


docker = functools.partial(_docker, _out=sys.stdout, _err=sys.stderr)
docker_compose = functools.partial(_docker_compose, _out=sys.stdout, _err=sys.stderr)

PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


class Dumper(yaml.RoundTripDumper):
    def ignore_aliases(self, data):
        # Strip aliases
        return True


def slugify(string, delim="-", allowed_chars=""):
    return re.sub(r"[^\w%s]" % re.escape(allowed_chars), delim, string).lower()


def get_current_arch():
    return sh(
        "-c",
        f". {PROJECT_DIR / 'shared-build-context/shared/scripts/functions.sh; normalize_to_docker_arch'}",
    ).strip()


docker_manifest_args = {
    "amd64": ["--arch", "amd64"],
    "386": ["--arch", "386"],
    "arm/v5": ["--arch", "arm", "--variant", "v5"],
    "arm/v6": ["--arch", "arm", "--variant", "v6"],
    "arm/v7": ["--arch", "arm", "--variant", "v7"],
    "arm64/v8": ["--arch", "arm64", "--variant", "v8"],
    "ppc": ["--arch", "ppc"],
    "ppc64le": ["--arch", "ppc64le"],
    "s390x": ["--arch", "s390x"],
    "mips64le": ["--arch", "mips64le"],
}


def configure_qemu():
    pass
    # if not which("qemu-aarch64") and not which("qemu-system-aarch64"):
    #     raise RuntimeError(
    #         "QEMU not installed, install missing pkg (apt: qemu,qemu-user-static | pacman: qemu-headless,qemu-headless-arch-extra | brew: qemu)."
    #     )

    # images = docker("images", "--format", "{{ .Repository }}", _out=None, _err=None)
    # if "multiarch/qemu-user-static" not in images:
    #     docker(
    #         "run",
    #         "--rm",
    #         "--privileged",
    #         "multiarch/qemu-user-static",
    #         "--reset",
    #         "-p",
    #         "yes",
    #     )


def arch_slug(arch):
    return arch.replace("arm/", "arm32").replace("arm64/", "arm64")


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
        host_pkg="elijahru/build-farm",
        client_pkg="elijahru/build-farm-client",
        tmp_pkg="elijahru/tmp",
    ):
        self.name = name
        self.tmp_pkg = tmp_pkg
        self.host_pkg = host_pkg
        self.client_pkg = client_pkg
        self.registry[name] = self
        self._context = None
        self.env = Environment(autoescape=False, undefined=StrictUndefined)
        self.env.filters["compiler_archs"] = self.compiler_archs_by_host_arch.get
        self.env.filters["compiler_port"] = self.ports_by_arch.get
        self.env.filters["toolchain"] = self.toolchains_by_arch.get
        self.env.filters["compiler_path_part"] = self.get_compiler_path_part
        self.env.filters["host_image_tag"] = self.host_image_tag
        self.env.filters["client_image_tag"] = self.client_image_tag
        self.env.filters["arch_slug"] = arch_slug

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

    def host_simple_manifest_tag(self):
        return f"{self.host_pkg}:{self.slug}"

    def host_versioned_manifest_tag(self, version):
        return f"{self.host_pkg}:{self.slug}--{version}"

    def host_manifest_tags(self, version):
        return (
            self.host_versioned_manifest_tag(version),
            self.host_simple_manifest_tag(),
        )

    def host_image_tag(self, version, arch):
        return f"{self.tmp_pkg}:{slugify(self.host_pkg.split('/')[1])}--{self.slug}--{arch_slug(arch)}--{version}"

    def client_simple_manifest_tag(self):
        return f"{self.client_pkg}:{self.slug}"

    def client_versioned_manifest_tag(self, version):
        return f"{self.client_pkg}:{self.slug}--{version}"

    def client_manifest_tags(self, version):
        return (
            self.client_versioned_manifest_tag(version),
            self.client_simple_manifest_tag(),
        )

    def client_image_tag(self, version, arch):
        return f"{self.tmp_pkg}:{slugify(self.client_pkg.split('/')[1])}--{self.slug}--{arch_slug(arch)}--{version}"

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

    def from_image(self, arch):
        return self.name

    @abc.abstractmethod
    def get_compiler_path_part(self, compiler_arch):
        ...

    @property
    def slug(self):
        return slugify(self.name, allowed_chars=".")

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
                    self.out_path / "host" / f"Dockerfile.{arch_slug(host_arch)}",
                )

    def render_dockerfile_client(self):
        for host_arch in self.host_archs:
            for compiler_arch in self.compiler_archs_by_host_arch[host_arch]:
                with self.set_context(host_arch=host_arch, compiler_arch=compiler_arch):
                    self.render_template(
                        self.template_path / "client/Dockerfile.jinja",
                        self.out_path
                        / "client"
                        / f"Dockerfile.{arch_slug(compiler_arch)}",
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
                    self.out_path
                    / f"host/build-context/scripts/run-{arch_slug(host_arch)}.sh",
                )

    def build_host(self, host_arch, version, push=False):
        configure_qemu()

        self.render(version=version)

        image = self.host_image_tag(version, host_arch)
        dockerfile = self.out_path / f"host/Dockerfile.{arch_slug(host_arch)}"
        try:
            docker("pull", image, "--platform", f"linux/{host_arch}")
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
            f"linux/{host_arch}",
            "--progress",
            "plain",
        )
        if push:
            docker("push", image)

    def build_client(self, client_arch, version, host_arch=None, push=False):
        configure_qemu()

        if host_arch is None:
            host_arch = get_current_arch()

        self.render(version=version)

        image = self.client_image_tag(version, client_arch)
        dockerfile = self.out_path / f"client/Dockerfile.{arch_slug(client_arch)}"
        try:
            docker("pull", image, "--platform", f"linux/{client_arch}")
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
            f"linux/{client_arch}",
            "--progress",
            "plain",
        )
        if push:
            docker("push", image)

    def test(self, client_arch, version, host_arch=None):
        configure_qemu()

        with self.run_host(host_arch=host_arch):
            image = self.client_image_tag(version, client_arch)
            docker(
                "run",
                "-t",
                "--platform",
                f"linux/{client_arch}",
                image,
                "sh",
                "/scripts/build-cjson.sh",
            )

    def push_host_manifest(self, version):
        os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

        images = {}
        for host_arch in self.host_archs:
            image = self.host_image_tag(version, host_arch)
            images[host_arch] = image
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

    @contextlib.contextmanager
    def run_host(self, host_arch=None):
        if host_arch is None:
            host_arch = get_current_arch()

        service_name = f"host-{arch_slug(host_arch)}"

        image_id = lambda: docker(
            "ps",
            "--filter",
            f"name={service_name}",
            "--format",
            "{{.ID}}",
            _out=None,
            _err=None,
        ).strip()
        id = image_id()
        if id:
            docker("kill", id, _out=None, _err=None)
        docker_compose("-f", self.docker_compose_yml_path, "up", "-d", service_name)
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
        "386",
        "arm/v5",
        "arm/v7",
        "arm64/v8",
        "ppc64le",
        "s390x",
        "mips64le",
    )
    compiler_archs = (
        "amd64",
        "386",
        "arm/v5",
        "arm/v7",
        "arm64/v8",
        "ppc64le",
        "s390x",
        "mips64le",
    )
    compiler_archs_by_host_arch = {
        "amd64": (
            "amd64",
            "386",
            "arm/v5",
            "arm/v7",
            "arm64/v8",
            "ppc64le",
            "s390x",
            "mips64le",
        ),
        "386": (
            "amd64",
            "386",
            "arm/v5",
            "arm/v7",
            "arm64/v8",
            "ppc64le",
            "s390x",
            "mips64le",
        ),
        "arm/v5": ("arm/v5",),
        "arm/v7": ("arm/v7",),
        "arm64/v8": ("amd64", "386", "arm/v5", "arm/v7", "arm64/v8"),
        "ppc64le": ("amd64", "386", "arm64/v8", "ppc64le"),
        "s390x": ("s390x",),
        "mips64le": ("mips64le",),
    }
    pkgs_by_arch = {
        "amd64": "gcc-x86-64-linux-gnu g++-x86-64-linux-gnu binutils-x86-64-linux-gnu",
        "386": "gcc-i686-linux-gnu g++-i686-linux-gnu binutils-i686-linux-gnu",
        "arm/v5": "gcc-arm-linux-gnueabi g++-arm-linux-gnueabi binutils-arm-linux-gnueabi",
        "arm/v7": "gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf binutils-arm-linux-gnueabihf",
        "arm64/v8": "gcc-aarch64-linux-gnu g++-aarch64-linux-gnu binutils-aarch64-linux-gnu",
        "ppc64le": "gcc-powerpc64le-linux-gnu g++-powerpc64le-linux-gnu binutils-powerpc64le-linux-gnu",
        "s390x": "gcc-s390x-linux-gnu g++-s390x-linux-gnu binutils-s390x-linux-gnu",
        "mips64le": "gcc-mipsel-linux-gnu g++-mipsel-linux-gnu binutils-mipsel-linux-gnu",
    }
    ports_by_arch = {
        "386": "3603",
        "amd64": "3604",
        "arm/v5": "3605",
        "arm/v7": "3607",
        "arm64/v8": "3608",
        "s390x": "3609",
        "ppc64le": "3610",
        "mips64le": "3611",
    }
    toolchains_by_arch = {
        "amd64": "x86_64-linux-gnu",
        "386": "i686-linux-gnu",
        "arm/v5": "arm-linux-gnueabi",
        "arm/v7": "arm-linux-gnueabihf",
        "arm64/v8": "aarch64-linux-gnu",
        "ppc64le": "powerpc64le-linux-gnu",
        "s390x": "s390x-linux-gnu",
        "mips64le": "mipsel-linux-gnu",
    }
    flags_by_arch = {
        "amd64": "START_DISTCC_X86_64_LINUX_GNU",
        "386": "START_DISTCC_I686_LINUX_GNU",
        "arm/v5": "START_DISTCC_ARM_LINUX_GNUEABI",
        "arm/v7": "START_DISTCC_ARM_LINUX_GNUEABIHF",
        "arm64/v8": "START_DISTCC_AARCH64_LINUX_GNU",
        "ppc64le": "START_DISTCC_PPC64LE_LINUX_GNU",
        "s390x": "START_DISTCC_S390X_LINUX_GNU",
        "mips64le": "START_DISTCC_MIPS64LE_LINUX_GNU",
    }

    def __init__(self, **kwargs):
        super(DebianLike, self).__init__(**kwargs)
        self.env.filters["flag"] = self.flags_by_arch.get
        self.env.filters["apt_pkgs"] = self.get_apt_pkgs

    def get_apt_pkgs(self, host_arch):
        pkgs = "build-essential g++ distcc lsb-base"
        for compiler_arch in self.compiler_archs_by_host_arch[host_arch]:
            pkgs += f" {self.pkgs_by_arch[compiler_arch]}"
        return pkgs

    def get_compiler_path_part(self, compiler_arch):
        if self.context["host_arch"] == compiler_arch:
            return ""
        return Path("/usr/local/") / self.toolchains_by_arch[compiler_arch] / "bin:"


class XtoolsDistro(Distro):
    @property
    @abc.abstractmethod
    def xtools_release(self):
        ...

    @property
    @abc.abstractmethod
    def toolchains_by_arch(self):
        ...

    def get_compiler_path_part(self, compiler_arch):
        if self.context["host_arch"] == compiler_arch:
            return ""
        return (
            Path("/usr/lib/gcc-cross") / self.toolchains_by_arch[compiler_arch] / "bin:"
        )

    def get_toolchain_url(self, host_arch, compiler_arch):
        os = self.name.replace(":", "")
        host_arch = arch_slug(host_arch)
        toolchain = self.toolchains_by_arch[compiler_arch]
        tarball = f"x-tools--host.{os}-{host_arch}--target.{toolchain}--{self.xtools_release}.tar.xz"
        return f"https://github.com/elijahr/x-tools/releases/download/{self.xtools_release}/{tarball}"


class ArchLinuxLike(XtoolsDistro):
    template_path = Path("archlinux-like")
    xtools_release = "devel-20201227"
    host_archs = (
        "amd64",
        "arm/v5",
        "arm/v6",
        "arm/v7",
        "arm64/v8",
    )
    compiler_archs = (
        "amd64",
        "arm/v5",
        "arm/v6",
        "arm/v7",
        "arm64/v8",
    )
    compiler_archs_by_host_arch = {
        "amd64": (
            "amd64",
            "arm/v5",
            "arm/v6",
            "arm/v7",
            "arm64/v8",
        ),
        "arm/v5": ("arm/v5",),
        "arm/v6": ("arm/v6",),
        "arm/v7": ("arm/v7",),
        "arm64/v8": ("arm64/v8",),
    }
    ports_by_arch = {
        "amd64": "3704",
        "arm/v5": "3705",
        "arm/v6": "3706",
        "arm/v7": "3707",
        "arm64/v8": "3708",
    }
    toolchains_by_arch = {
        "amd64": "x86_64-build_pc-linux-gnu",
        "arm/v5": "armv5tel-unknown-linux-gnueabi",
        "arm/v6": "armv6l-unknown-linux-gnueabihf",
        "arm/v7": "armv7l-unknown-linux-gnueabihf",
        "arm64/v8": "aarch64-unknown-linux-gnu",
    }

    def from_image(self, arch):
        if arch == "amd64":
            return "archlinux:base-devel"
        return "lopsided/archlinux:devel"


class AlpineLike(XtoolsDistro):
    template_path = Path("alpine-like")
    xtools_release = "devel-20201227"
    host_archs = (
        "386",
        "amd64",
        "arm/v6",
        "arm/v7",
        "arm64/v8",
        "ppc64le",
    )
    compiler_archs = (
        "386",
        "amd64",
        "arm/v6",
        "arm/v7",
        "arm64/v8",
        "ppc64le",
    )
    compiler_archs_by_host_arch = {
        "386": ("386",),
        "amd64": ("amd64", "386", "arm/v6", "arm/v7", "arm64/v8", "ppc64le"),
        "arm/v6": ("arm/v6",),
        "arm/v7": ("arm/v7",),
        "arm64/v8": ("arm64/v8",),
        "ppc64le": ("ppc64le",),
    }
    ports_by_arch = {
        "386": "3803",
        "amd64": "3804",
        "arm/v6": "3806",
        "arm/v7": "3807",
        "arm64/v8": "3808",
        "ppc64le": "3810",
    }
    toolchains_by_arch = {
        "386": "i686-alpine-linux-musl",
        "amd64": "x86_64-alpine-linux-musl",
        "arm/v6": "armv6-alpine-linux-musleabihf",
        "arm/v7": "armv7-alpine-linux-musleabihf",
        "arm64/v8": "aarch64-alpine-linux-musl",
        "ppc64le": "powerpc64le-alpine-linux-musl",
    }


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
    env.filters["arch_slug"] = arch_slug
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
    parser_build_host.add_argument("--arch", required=True)
    parser_build_host.add_argument("--version", required=True)
    parser_build_host.add_argument("--push", action="store_true")

    # build-client
    parser_build_client = subparsers.add_parser("build-client")
    parser_build_client.add_argument("--distro", type=Distro.get, required=True)
    parser_build_client.add_argument("--arch", required=True)
    parser_build_client.add_argument("--version", required=True)
    parser_build_client.add_argument("--push", action="store_true")

    # build-all
    parser_build_all = subparsers.add_parser("build-all")
    parser_build_all.add_argument("--version", required=True)
    parser_build_all.add_argument("--push", action="store_true")

    # clean
    subparsers.add_parser("clean")

    # test
    parser_test = subparsers.add_parser("test")
    parser_test.add_argument("--distro", type=Distro.get, required=True)
    parser_test.add_argument("--host-arch")
    parser_test.add_argument("--client-arch", required=True)
    parser_test.add_argument("--version", required=True)

    # push-host-manifest
    parser_push_host_manifest = subparsers.add_parser("push-host-manifest")
    parser_push_host_manifest.add_argument("--distro", type=Distro.get, required=True)
    parser_push_host_manifest.add_argument("--version", required=True)

    # push-client-manifest
    parser_push_client_manifest = subparsers.add_parser("push-client-manifest")
    parser_push_client_manifest.add_argument("--distro", type=Distro.get, required=True)
    parser_push_client_manifest.add_argument("--version", required=True)

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
        args.distro.build_host(args.arch, version=args.version, push=args.push)

    elif args.subcommand == "build-client":
        args.distro.build_client(args.arch, version=args.version, push=args.push)

    elif args.subcommand == "build-all":
        Distro.build_all(version=args.version, push=args.push)

    elif args.subcommand == "clean":
        Distro.clean_all()

    elif args.subcommand == "test":
        args.distro.test(
            host_arch=args.host_arch, client_arch=args.client_arch, version=args.version
        )

    elif args.subcommand == "push-host-manifest":
        args.distro.push_host_manifest(version=args.version)

    elif args.subcommand == "push-client-manifest":
        args.distro.push_client_manifest(version=args.version)

    elif args.subcommand == "render-readme":
        render_readme()

    else:
        raise ValueError(f"Unknown subcommand {args.subcommand}")


if __name__ == "__main__":
    main()
