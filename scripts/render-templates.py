#!/usr/bin/env python3

"""
Generate various docker and config files across a matrix of archs/distros.
"""

import os
import re

host_debian_distros = ( 'debian:buster', 'debian:stretch' )
host_archs = ( 'amd64', )

client_debian_distros = ( 'debian:buster', 'debian:stretch' )
client_archs = ( 'amd64', 'i386', 'arm32v7', 'arm64v8', 'ppc64le', 's390x' )

ports_by_arch = {
  'amd64': 3632,
  'i386': 3633,
  'arm32v7': 3634,
  'arm64v8': 3635,
  'ppc64le': 3636,
  's390x': 3637,
}

toolchains_by_arch = {
  'amd64': 'x86_64-linux-gnu',
  'i386': 'i686-linux-gnu',
  'arm32v7': 'arm-linux-gnueabihf',
  'arm64v8': 'aarch64-linux-gnu',
  'ppc64le': 'powerpc64le-linux-gnu',
  's390x': 's390x-linux-gnu',
}

flags_by_arch = {
  'amd64': 'START_DISTCC_X86_64_LINUX_GNU',
  'i386': 'START_DISTCC_I686_LINUX_GNU',
  'arm32v7': 'START_DISTCC_ARM_LINUX_GNUEABIHF',
  'arm64v8': 'START_DISTCC_AARCH64_LINUX_GNU',
  'ppc64le': 'START_DISTCC_PPC64LE_LINUX_GNU',
  's390x': 'START_DISTCC_S390X_LINUX_GNU',
}

def get_compiler_path_part_by_arch(arch):
  if arch == 'amd64':
    return ''
  return '/usr/local/'+toolchains_by_arch[arch]+'/bin:'


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
  for arch in host_archs:
    for distro in host_debian_distros:
      distro_slug = slugify(distro)
      render(
        'Dockerfile.distcc-host.debian.template',
        'Dockerfile.distcc-host.{distro_slug}.{arch}',
        locals(),
      )


def generate_client_dockerfiles():
  for arch in client_archs:
    for distro in client_debian_distros:
      distro_slug = slugify(distro)
      render(
        'Dockerfile.distcc-client.debian.template',
        'Dockerfile.distcc-client.{distro_slug}.{arch}',
        locals(),
      )


def generate_docker_compose():
  for host_arch in host_archs:
    for host_distro in host_debian_distros:
      host_distro_slug = slugify(host_distro)
      for client_arch in client_archs:
        host_port = ports_by_arch[client_arch]
        for client_distro in client_debian_distros:
          client_distro_slug = slugify(client_distro)
          render(
            'docker-compose.template.yml',
            'docker-compose.host-{host_distro_slug}-{host_arch}.client-{client_distro_slug}-{client_arch}.yml',
            locals()
          )


def generate_distccd_config():
  for arch in client_archs:
    flag = flags_by_arch[arch]
    toolchain = toolchains_by_arch[arch]
    host_port = ports_by_arch[arch]
    compiler_path_part = get_compiler_path_part_by_arch(arch)

    render(
      'etc/default/distccd-template',
      'etc/default/distccd-{toolchain}',
      locals(),
    )
    render(
      'etc/init.d/distccd-template',
      'etc/init.d/distccd-{toolchain}',
      locals(),
    )
    render(
      'etc/logrotate.d/distccd-template',
      'etc/logrotate.d/distccd-{toolchain}',
      locals(),
    )


if __name__ == '__main__':
  os.chdir(os.path.join(os.path.dirname(__file__), '..'))
  generate_host_dockerfiles()
  generate_client_dockerfiles()
  generate_docker_compose()
  generate_distccd_config()
