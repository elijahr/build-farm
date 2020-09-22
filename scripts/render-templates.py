#!/usr/bin/env python3

"""
Generate various docker and config files across a matrix of archs/distros.
"""

import os
import re

# Debian
debian_host_distros = ( 'debian:buster', )
debian_host_archs = ( 'amd64', )
debian_client_distros = ( 'debian:buster', )
debian_client_archs = ( 'amd64', 'i386', 'arm32v7', 'arm64v8', 'ppc64le', 's390x' )
debian_ports_by_arch = {
  'i386': 3603,
  'amd64': 3604,
  'arm32v7': 3607,
  'arm64v8': 3608,
  's390x': 3609,
  'ppc64le': 3610,
}
debian_toolchains_by_arch = {
  'amd64': 'x86_64-linux-gnu',
  'i386': 'i686-linux-gnu',
  'ppc64le': 'powerpc64le-linux-gnu',
  's390x': 's390x-linux-gnu',
  'arm32v7': 'arm-linux-gnueabihf',
  'arm64v8': 'aarch64-linux-gnu',
}
debian_flags_by_arch = {
  'amd64': 'START_DISTCC_X86_64_LINUX_GNU',
  'i386': 'START_DISTCC_I686_LINUX_GNU',
  'ppc64le': 'START_DISTCC_PPC64LE_LINUX_GNU',
  's390x': 'START_DISTCC_S390X_LINUX_GNU',
  'arm32v7': 'START_DISTCC_ARM_LINUX_GNUEABIHF',
  'arm64v8': 'START_DISTCC_AARCH64_LINUX_GNU',
}


# Arch Linux
archlinux_host_archs = ( 'amd64', )
archlinux_client_archs = ( 'amd64', 'arm32v5', 'arm32v6', 'arm32v7', 'arm64v8', )
archlinux_ports_by_arch = {
  'amd64': 3704,
  'arm32v5': 3705,
  'arm32v6': 3706,
  'arm32v7': 3707,
  'arm64v8': 3708,
}
archlinux_images_by_arch = {
  'amd64': 'archlinux:20200908',
  'arm32v5': 'lopsided/archlinux@sha256:66b26a83a39e26e2a390b5b92105f80e6042d0db79ee22b1f57d169307b87a58',
  'arm32v6': 'lopsided/archlinux@sha256:109729d4d863e14fed6faa1437f0eaee8133b26c310079c8294a4c7db6dbebb5',
  'arm32v7': 'lopsided/archlinux@sha256:fbf2d806f207a2e9a5400bd20672b80ca318a2e59fc56c1c0f90b4e9adb60f4a',
  'arm64v8': 'lopsided/archlinux@sha256:f9d68dd73a85b587539e04ef26b18d91b243bee8e1a343ad97f67183f275e548'
}
archlinux_toolchains_by_arch = {
  'arm32v5': 'x-tools/arm-unknown-linux-gnueabi',
  'arm32v6': 'x-tool6h/arm-unknown-linux-gnueabihf',
  'arm32v7': 'x-tool7h/arm-unknown-linux-gnueabihf',
  'arm64v8': 'x-tool8/aarch64-unknown-linux-gnu',
}


def get_debian_compiler_path_part_by_arch(arch):
  if arch == 'amd64':
    return ''
  return '/usr/local/'+debian_toolchains_by_arch[arch]+'/bin:'


def get_archlinux_compiler_path_part_by_arch(arch):
  if arch == 'amd64':
    return ''
  return '/root/'+archlinux_toolchains_by_arch[arch]+'/bin:'


def slugify(string):
  return re.sub(r'[^\w]', '-', string).lower()


def render(template, out, context):
  in_name = os.path.join('templates', template)
  with open(in_name, 'r') as f:
    rendered = f.read().format(**context)
  out_name = os.path.join('rendered', out.format(**context))
  dir_name = os.path.dirname(out_name)
  if not os.path.exists(dir_name):
    os.makedirs(dir_name)
  with open(out_name, 'w') as f:
    f.write(rendered)
  print('Wrote %s' % out_name)
  return out_name


def generate_host_dockerfiles():
  for host_arch in debian_host_archs:
    for host_distro in debian_host_distros:
      host_distro_slug = slugify(host_distro)
      render(
        'Dockerfile.distcc-cross-compiler-host-debian.template',
        'Dockerfile.distcc-cross-compiler-host-{host_distro_slug}.{host_arch}',
        locals(),
      )

  for host_arch in archlinux_host_archs:
    host_image = archlinux_images_by_arch[host_arch]
    render(
      'Dockerfile.distcc-cross-compiler-host-archlinux.template',
      'Dockerfile.distcc-cross-compiler-host-archlinux.{host_arch}',
      locals(),
    )


def generate_client_dockerfiles():
  for client_arch in debian_client_archs:
    for client_distro in debian_client_distros:
      host_distro_slug = slugify(client_distro)
      host_port = debian_ports_by_arch[client_arch]
      render(
        'Dockerfile.distcc-cross-compiler-client-debian.template',
        'Dockerfile.distcc-cross-compiler-client-{host_distro_slug}.{client_arch}',
        locals(),
      )

  for client_arch in archlinux_client_archs:
    client_image = archlinux_images_by_arch[client_arch]
    host_port = archlinux_ports_by_arch[client_arch]
    render(
      'Dockerfile.distcc-cross-compiler-client-archlinux.template',
      'Dockerfile.distcc-cross-compiler-client-archlinux.{client_arch}',
      locals(),
    )


def generate_docker_compose():
  for host_arch in debian_host_archs:
    for host_distro in debian_host_distros:
      host_distro_slug = slugify(host_distro)
      for client_arch in debian_client_archs:
        host_port = debian_ports_by_arch[client_arch]
        for client_distro in debian_client_distros:##
          client_distro_slug = slugify(client_distro)
          render(
            'docker-compose.debian.template.yml',
            'docker-compose.host-{host_distro_slug}-{host_arch}.client-{client_distro_slug}-{client_arch}.yml',
            locals()
          )

  for host_arch in archlinux_host_archs:
    host_distro_slug = 'archlinux'
    client_distro_slug = 'archlinux'
    for client_arch in archlinux_client_archs:
      host_port = archlinux_ports_by_arch[client_arch]
      render(
        'docker-compose.archlinux.template.yml',
        'docker-compose.host-{host_distro_slug}-{host_arch}.client-{client_distro_slug}-{client_arch}.yml',
        locals()
      )


def generate_distccd_config():
  for client_arch in debian_client_archs:
    flag = debian_flags_by_arch[client_arch]
    toolchain = debian_toolchains_by_arch[client_arch]
    host_port = debian_ports_by_arch[client_arch]
    compiler_path_part = get_debian_compiler_path_part_by_arch(client_arch)

    render(
      'distcc-cross-compiler-host-debian/etc/default/distccd-template',
      'distcc-cross-compiler-host-debian/etc/default/distccd-{toolchain}',
      locals(),
    )
    render(
      'distcc-cross-compiler-host-debian/etc/init.d/distccd-template',
      'distcc-cross-compiler-host-debian/etc/init.d/distccd-{toolchain}',
      locals(),
    )
    render(
      'distcc-cross-compiler-host-debian/etc/logrotate.d/distccd-template',
      'distcc-cross-compiler-host-debian/etc/logrotate.d/distccd-{toolchain}',
      locals(),
    )

  for client_arch in archlinux_client_archs:
    host_port = archlinux_ports_by_arch[client_arch]
    compiler_path_part = get_archlinux_compiler_path_part_by_arch(client_arch)

    render(
      'distcc-cross-compiler-host-archlinux/etc/conf.d/distccd-template',
      'distcc-cross-compiler-host-archlinux/etc/conf.d/distccd-{client_arch}',
      locals(),
    )
    render(
      'distcc-cross-compiler-host-archlinux/usr/lib/systemd/system/distccd.service-template',
      'distcc-cross-compiler-host-archlinux/usr/lib/systemd/system/distccd-{client_arch}.service',
      locals(),
    )


if __name__ == '__main__':
  os.chdir(os.path.join(os.path.dirname(__file__), '..'))
  generate_host_dockerfiles()
  generate_client_dockerfiles()
  generate_docker_compose()
  generate_distccd_config()
