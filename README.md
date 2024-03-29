
![debian:buster](https://github.com/elijahr/build-farm/workflows/debian%3Abuster/badge.svg)

![debian:buster-slim](https://github.com/elijahr/build-farm/workflows/debian%3Abuster-slim/badge.svg)

![archlinux](https://github.com/elijahr/build-farm/workflows/archlinux/badge.svg)

![alpine:3.15](https://github.com/elijahr/build-farm/workflows/alpine%3A3.15/badge.svg)


# build-farm

Fast & easy cross-compiling with `docker` and `distcc`.

### Use cases

* Cross-compiling for embedded systems
* Parallel build farm
* Continuous integration across a matrix of architectures

### Compiler containers

Each host container runs at least one distccd daemon. Each daemon listens on a different port, targeting a different compiler toolchain.

#### Alpine Linux

Image: `elijahru/build-farm:alpine-3.15`

| Host platform | Compiler toolchain for platform | Compiler port |
|---------------|---------------------------------|---------------|
| `linux/386` | `linux/386` | 3803 |
| `linux/amd64` | `linux/amd64` | 3804 |
| `linux/amd64` | `linux/386` | 3803 |
| `linux/amd64` | `linux/arm/v6` | 3806 |
| `linux/amd64` | `linux/arm/v7` | 3807 |
| `linux/amd64` | `linux/arm64/v8` | 3808 |
| `linux/amd64` | `linux/ppc64le` | 3810 |
| `linux/arm/v6` | `linux/arm/v6` | 3806 |
| `linux/arm/v7` | `linux/arm/v7` | 3807 |
| `linux/arm64/v8` | `linux/arm64/v8` | 3808 |
| `linux/ppc64le` | `linux/ppc64le` | 3810 |

#### Arch Linux

Image: `elijahru/build-farm:archlinux`

| Host platform | Compiler toolchain for platform | Compiler port |
|---------------|---------------------------------|---------------|
| `linux/amd64` | `linux/amd64` | 3704 |
| `linux/amd64` | `linux/arm/v5` | 3705 |
| `linux/amd64` | `linux/arm/v6` | 3706 |
| `linux/amd64` | `linux/arm/v7` | 3707 |
| `linux/amd64` | `linux/arm64/v8` | 3708 |
| `linux/arm/v5` | `linux/arm/v5` | 3705 |
| `linux/arm/v6` | `linux/arm/v6` | 3706 |
| `linux/arm/v7` | `linux/arm/v7` | 3707 |
| `linux/arm64/v8` | `linux/arm64/v8` | 3708 |

#### Debian Buster

Image: `elijahru/build-farm:debian-buster`
Slim image: `elijahru/build-farm:debian-buster-slim`

| Host platform | Compiler toolchain for platform | Compiler port |
|---------------|---------------------------------|---------------|
| `linux/amd64` | `linux/amd64` | 3604 |
| `linux/amd64` | `linux/386` | 3603 |
| `linux/amd64` | `linux/arm/v5` | 3605 |
| `linux/amd64` | `linux/arm/v7` | 3607 |
| `linux/amd64` | `linux/arm64/v8` | 3608 |
| `linux/amd64` | `linux/ppc64le` | 3610 |
| `linux/amd64` | `linux/s390x` | 3609 |
| `linux/amd64` | `linux/mips64le` | 3611 |
| `linux/386` | `linux/amd64` | 3604 |
| `linux/386` | `linux/386` | 3603 |
| `linux/386` | `linux/arm/v5` | 3605 |
| `linux/386` | `linux/arm/v7` | 3607 |
| `linux/386` | `linux/arm64/v8` | 3608 |
| `linux/386` | `linux/ppc64le` | 3610 |
| `linux/386` | `linux/s390x` | 3609 |
| `linux/386` | `linux/mips64le` | 3611 |
| `linux/arm/v5` | `linux/arm/v5` | 3605 |
| `linux/arm/v7` | `linux/arm/v7` | 3607 |
| `linux/arm64/v8` | `linux/amd64` | 3604 |
| `linux/arm64/v8` | `linux/386` | 3603 |
| `linux/arm64/v8` | `linux/arm/v5` | 3605 |
| `linux/arm64/v8` | `linux/arm/v7` | 3607 |
| `linux/arm64/v8` | `linux/arm64/v8` | 3608 |
| `linux/ppc64le` | `linux/amd64` | 3604 |
| `linux/ppc64le` | `linux/386` | 3603 |
| `linux/ppc64le` | `linux/arm64/v8` | 3608 |
| `linux/ppc64le` | `linux/ppc64le` | 3610 |
| `linux/s390x` | `linux/s390x` | 3609 |
| `linux/mips64le` | `linux/mips64le` | 3611 |

### Client containers

By default, the client containers will assume that a compiler image is running in the same docker network. The compiler address is configured via the environment variable `DISTCC_HOSTS`, whose default value is `172.17.0.1:<compiler-port>`, where `172.17.0.1` is the default Docker network IP and `<compiler-port>` corresponds to the table above. These defaults should work for most Docker installations. You can also use `DISTCC_HOSTS=host.docker.internal:<port>` on macOS or Windows hosts. The client containers require the `multiarch/qemu-user-static` package for emulation, which can be installed via:

macOS:
```shell
brew install qemu
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Debian/Ubuntu:
```shell
sudo apt-get update -q -y
sudo apt-get -qq install -y qemu qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Arch Linux/Manjaro:
```shell
sudo pacman -Syu qemu qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Windows hasn't been tested. You can install QEMU via https://www.qemu.org/download/#windows. If additional steps are required please submit a PR with instructions added to this README.

#### Alpine Linux

Image: `elijahru/build-farm-client:alpine-3.15`

| Platform | `DISTCC_HOSTS` |
|----------|----------------|
| `linux/386` | `172.17.0.1:3803` |
| `linux/amd64` | `172.17.0.1:3804` |
| `linux/arm/v6` | `172.17.0.1:3806` |
| `linux/arm/v7` | `172.17.0.1:3807` |
| `linux/arm64/v8` | `172.17.0.1:3808` |
| `linux/ppc64le` | `172.17.0.1:3810` |

#### Arch Linux

Image: `elijahru/build-farm-client:archlinux`

| Platform | `DISTCC_HOSTS` |
|----------|----------------|
| `linux/amd64` | `172.17.0.1:3704` |
| `linux/arm/v5` | `172.17.0.1:3705` |
| `linux/arm/v6` | `172.17.0.1:3706` |
| `linux/arm/v7` | `172.17.0.1:3707` |
| `linux/arm64/v8` | `172.17.0.1:3708` |

#### Debian Buster

Image: `elijahru/build-farm-client:debian-buster`
Slim image: `elijahru/build-farm-client:debian-buster-slim`

| Platform | `DISTCC_HOSTS` |
|----------|----------------|
| `linux/amd64` | `172.17.0.1:3604` |
| `linux/386` | `172.17.0.1:3603` |
| `linux/arm/v5` | `172.17.0.1:3605` |
| `linux/arm/v7` | `172.17.0.1:3607` |
| `linux/arm64/v8` | `172.17.0.1:3608` |
| `linux/ppc64le` | `172.17.0.1:3610` |
| `linux/s390x` | `172.17.0.1:3609` |
| `linux/mips64le` | `172.17.0.1:3611` |

### Simple example: cross-compiler

In this example, `host` is a native Debian `amd64` container which exposes an `arm64/v8` cross-compiler on port `3608`.

`client` is an emulated `arm64/v8` container that offloads all `gcc/g++/cc/etc` work to the cross-compiler exposed on `host:3608`.

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:debian-buster
    platform: linux/amd64
    ports:
      - 3608:3608

  build-client:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/arm64/v8
    depends_on: [ build-host ]
    volumes:
      # Your code
      - .:/code
    command: ./configure && make
```

### Advanced example: cross-compiler matrix for all available Alpine Linux targets

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:alpine-3.15
    platform: linux/amd64
    ports:
      # amd64
      - 3804:3804
      # 386
      - 3803:3803
      # arm/v6
      - 3806:3806
      # arm/v7
      - 3807:3807
      # arm64/v8
      - 3808:3808
      # ppc64le
      - 3810:3810
  
  build-client-amd64:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/amd64
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-386:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/386
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v6:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/arm/v6
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v7:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/arm/v7
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm64v8:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/arm64/v8
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-ppc64le:
    image: elijahru/build-farm-client:alpine-3.15
    platform: linux/ppc64le
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
```

### Advanced example: cross-compiler matrix for all available Arch Linux targets

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:archlinux
    platform: linux/amd64
    ports:
      # amd64
      - 3704:3704
      # arm/v5
      - 3705:3705
      # arm/v6
      - 3706:3706
      # arm/v7
      - 3707:3707
      # arm64/v8
      - 3708:3708
  
  build-client-amd64:
    image: elijahru/build-farm-client:archlinux
    platform: linux/amd64
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v5:
    image: elijahru/build-farm-client:archlinux
    platform: linux/arm/v5
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v6:
    image: elijahru/build-farm-client:archlinux
    platform: linux/arm/v6
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v7:
    image: elijahru/build-farm-client:archlinux
    platform: linux/arm/v7
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm64v8:
    image: elijahru/build-farm-client:archlinux
    platform: linux/arm64/v8
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
```

### Advanced example: cross-compiler matrix for all available Debian targets

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:debian-buster
    platform: linux/amd64
    ports:
      # amd64
      - 3604:3604
      # 386
      - 3603:3603
      # arm/v5
      - 3605:3605
      # arm/v7
      - 3607:3607
      # arm64/v8
      - 3608:3608
      # ppc64le
      - 3610:3610
      # s390x
      - 3609:3609
      # mips64le
      - 3611:3611
  
  build-client-amd64:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/amd64
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-386:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/386
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v5:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/arm/v5
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm32v7:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/arm/v7
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-arm64v8:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/arm64/v8
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-ppc64le:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/ppc64le
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-s390x:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/s390x
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
  build-client-mips64le:
    image: elijahru/build-farm-client:debian-buster
    platform: linux/mips64le
    depends_on: [ build-host ]
    volumes:
      - .:/code
    command: ./configure && make
  
```

### Build farm

Assuming several nodes, configured as follows:

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:archlinux
    ports:
      - 3704:3704
```

Where each node can be resolved via DNS as `build-host1`, `build-host2`, `build-host3`, etc, a client can distribute compilation across the nodes by using the `DISTCC_HOSTS` environment variable:

```yml
version: '3'
services:
  client:
    environment:
      - DISTCC_HOSTS="build-host1:3704 build-host2:3704 build-host3:3704"
    image: elijahru/build-farm-client:archlinux
    volumes:
      - .:/code
    command: ./configure && make
```

See the [distcc man page](https://linux.die.net/man/1/distcc) for documentation on `DISTCC_HOSTS`.

### Github Actions

Below is an example GitHub Actions workflow config, named say `.github/workflows/build.yml`:

```yml
name: Build project

on:
  push:
    branches: [ '*' ]
    tags: [ '*' ]

jobs:
  build:
    name: Build for archlinux ${{ matrix.arch }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        arch: [ amd64, arm64v8 ]

    steps:
      - name: Checkout repo
        uses: actions/checkout@v2
        with:
          fetch-depth: 1
          submodules: recursive

      - name: Install dependencies
        run: |
          sudo apt-get update -q -y
          sudo apt-get -qq install -y qemu qemu-user-static
          docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

      - name: Build
        run: docker-compose run build-${{ matrix.arch }}
```

The above workflow config assumes the repository contains a `docker-compose.yml` as follows:

```yml
version: '3'
services:
  build-host:
    image: elijahru/build-farm:archlinux
    platform: linux/amd64
    ports:
      # amd64
      - 3704:3704
      # arm64/v8
      - 3708:3708

  build-amd64:
    image: elijahru/build-farm-client:archlinux
    platform: linux/amd64
    depends_on: [ build-host ]
    command: |
      bash -c "\
        curl -LsSf https://github.com/DaveGamble/cJSON/archive/master.tar.gz -o cJSON.tar.gz; \
        tar xzf cJSON.tar.gz; \
        cd cJSON-master; \
        echo 'Waiting for builder...'; \
        sleep 10; \
        make; \
        make test; "

  build-arm64v8:
    image: elijahru/build-farm-client:archlinux
    platform: linux/arm64/v8
    depends_on: [ build-host ]
    command: |
      bash -c "\
        curl -LsSf https://github.com/DaveGamble/cJSON/archive/master.tar.gz -o cJSON.tar.gz; \
        tar xzf cJSON.tar.gz; \
        cd cJSON-master; \
        echo 'Waiting for builder...'; \
        sleep 10; \
        make; \
        make test; "
```

### Contributing

Adding new target operating systems should be fairly straightforward by following the existing distro patterns. Please do submit pull requests.

Most of the work happens via `builder.py build-host` and `builder.py build-client`. Pass `--help` for usage.

The easiest way to install all requirements for building is to use pipenv. `pipenv install -r requirements.txt --pre` should install the requirements, and then the build script can be run with `pipenv run ./builder.py [subcommand] [args]`.

There are some useful git hooks that can be enabled by running `git config --local core.hooksPath .githooks/`.

If you are looking for an idea, contributions for the following are especially welcome:

* A GitHub Action for GitHub Marketplace to make using these containers in CI easier
* Windows amd64 and arm64/v8 support?
* Pump support
* Zeroconf support

### Changelog

* 2020-12-27
  * Use latest x-tools, with gdb and strace support.

* 2020-12-25
  * Alpine and Arch Linux now use toolchains from [x-tools](https://github.com/elijahr/x-tools).

* 2020-12-20
  * Add cross compilers for Alpine.

* 2020-12-11
  * Add Alpine 3.15 images.
  * Add Arch Linux ARM hosts.

* 2020-12-05
  * Consolidated hosts to new container [`elijahru/build-farm`](https://hub.docker.com/repository/docker/elijahru/build-farm).
  * Consolidated clients to new container [`elijahru/build-farm-client`](https://hub.docker.com/repository/docker/elijahru/build-farm-client).
  * Add `debian:buster-slim` based containers.
  * Add `mips64le` and `arm/v5` architectures for `debian`.