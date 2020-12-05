
![debian:buster](https://github.com/elijahr/build-farm/workflows/debian%3Abuster/badge.svg)

![debian:buster-slim](https://github.com/elijahr/build-farm/workflows/debian%3Abuster-slim/badge.svg)

![archlinux](https://github.com/elijahr/build-farm/workflows/archlinux/badge.svg)


# build-farm

Fast & easy cross-compiling with `docker` and `distcc`.

### Use cases

* Cross-compiling for embedded systems
* Parallel build farm
* Continuous integration across a matrix of architectures

### Compiler containers

Each host container runs at least one distccd daemon. Each daemon listens on a different port, targeting a different compiler toolchain.

#### Arch Linux

The `elijahru/build-farm:v0.5.1` image exposes the following compilers:

| Host arch | Target arch | Compiler port |
|-----------|-------------|---------------|
| `amd64`   | `amd64`     | 3704          |
| `amd64`   | `arm32v5`   | 3705          |
| `amd64`   | `arm32v6`   | 3706          |
| `amd64`   | `arm32v7`   | 3707          |
| `amd64`   | `arm64v8`   | 3708          |

#### Debian Buster

The multi-architecture `elijahru/build-farm:v0.5.1` image exposes the following compilers:

| Host arch  | Target arch | Compiler port |
|------------|-------------|---------------|
| `amd64`    | `amd64`     | 3604          |
| `amd64`    | `i386`      | 3603          |
| `amd64`    | `arm32v5`   | 3605          |
| `amd64`    | `arm32v7`   | 3607          |
| `amd64`    | `arm64v8`   | 3608          |
| `amd64`    | `ppc64le`   | 3610          |
| `amd64`    | `s390x`     | 3609          |
| `amd64`    | `mips64le`  | 3611          |
| `i386`     | `amd64`     | 3604          |
| `i386`     | `i386`      | 3603          |
| `i386`     | `arm32v5`   | 3605          |
| `i386`     | `arm32v7`   | 3607          |
| `i386`     | `arm64v8`   | 3608          |
| `i386`     | `ppc64le`   | 3610          |
| `i386`     | `s390x`     | 3609          |
| `i386`     | `mips64le`  | 3611          |
| `arm32v5`  | `arm32v5`   | 3605          |
| `arm32v7`  | `arm32v7`   | 3607          |
| `arm64v8`  | `amd64`     | 3604          |
| `arm64v8`  | `i386`      | 3603          |
| `arm64v8`  | `arm32v5`   | 3605          |
| `arm64v8`  | `arm32v7`   | 3607          |
| `arm64v8`  | `arm64v8`   | 3608          |
| `ppc64le`  | `amd64`     | 3604          |
| `ppc64le`  | `i386`      | 3603          |
| `ppc64le`  | `arm64v8`   | 3608          |
| `ppc64le`  | `ppc64le`   | 3610          |
| `s390x`    | `s390x`     | 3609          |
| `mips64le` | `mips64le`  | 3611          |

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

The client containers also use ccache to avoid repeat compilation. ccached object files are volatile unless you mount /root/.ccache as a volume (see examples).

#### Arch Linux

| Emulated architecture | Client image on Docker Hub                                           | `DISTCC_HOSTS`    |
|-----------------------|----------------------------------------------------------------------|-------------------|
| `amd64` (`x86_64`)    | `elijahru/build-farm-client:v0.5.1-amd64`       | `172.17.0.1:3704` |
| `arm32v5`             | `elijahru/build-farm-client:v0.5.1-arm32v5`     | `172.17.0.1:3705` |
| `arm32v6`             | `elijahru/build-farm-client:v0.5.1-arm32v6`     | `172.17.0.1:3706` |
| `arm32v7`             | `elijahru/build-farm-client:v0.5.1-arm32v7`     | `172.17.0.1:3707` |
| `arm64v8` (`aarch64`) | `elijahru/build-farm-client:v0.5.1-arm64v8`     | `172.17.0.1:3708` |

#### Debian Buster

| Emulated architecture | Client image on Docker Hub                                           | `DISTCC_HOSTS`    |
|-----------------------|----------------------------------------------------------------------|-------------------|
| `amd64`               | `{{ debian_buster.client_image }}:{{ version }}-amd64`               | `172.17.0.1:3604` |
| `i386`                | `{{ debian_buster.client_image }}:{{ version }}-i386`                | `172.17.0.1:3603` |
| `arm32v5`             | `{{ debian_buster.client_image }}:{{ version }}-arm32v5`             | `172.17.0.1:3605` |
| `arm32v7`             | `{{ debian_buster.client_image }}:{{ version }}-arm32v7`             | `172.17.0.1:3607` |
| `arm64v8`             | `{{ debian_buster.client_image }}:{{ version }}-arm64v8`             | `172.17.0.1:3608` |
| `ppc64le`             | `{{ debian_buster.client_image }}:{{ version }}-ppc64le`             | `172.17.0.1:3610` |
| `s390x`               | `{{ debian_buster.client_image }}:{{ version }}-s390x`               | `172.17.0.1:3609` |
| `mips64le`            | `{{ debian_buster.client_image }}:{{ version }}-mips64le`            | `172.17.0.1:3611` |

### Simple example: cross-compiler

In this example, `host` is a native Debian `amd64` container which exposes an `arm64v8` cross-compiler on port `3608`.

`client` is an emulated `arm64v8` container that offloads all `gcc/g++/cc/etc` work to the cross-compiler exposed on `host:3608`.

The compiled object code is cached via `ccache` in a persistent volume, so that subsequent builds do not re-compile unchanged code.

```yml
version: '3'
services:
  host:
    image: elijahru/build-farm:v0.5.1-amd64
    ports:
      - 3608:3608

  client:
    image: elijahru/build-farm-client:v0.5.1-arm64v8
    volumes:
      # Your code
      - .:/code
      # Cache resulting object code between builds
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make
```

### Advanced example: cross-compiler matrix for all available Debian targets

```yml
version: '3'
services:
  build-farm:
    image: elijahru/build-farm:v0.5.1-amd64
    ports:
      # i386
      - 3603:3603
      # amd64
      - 3604:3604
      # arm32v7
      - 3607:3607
      # arm64v8
      - 3608:3608
      # s390x
      - 3609:3609
      # ppc64le
      - 3610:3610

  client-i386:
    image: elijahru/build-farm-client:v0.5.1-i386
    volumes:
      - .:/code
      - ./caches/i386/ccache:/root/.ccache
    command: ./configure && make

  client-amd64:
    image: elijahru/build-farm-client:v0.5.1-amd64
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v7:
    image: elijahru/build-farm-client:v0.5.1-arm32v7
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/build-farm-client:v0.5.1-arm64v8
    volumes:
      - .:/code
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make

  client-s390x:
    image: elijahru/build-farm-client:v0.5.1-s390x
    volumes:
      - .:/code
      - ./caches/s390x/ccache:/root/.ccache
    command: ./configure && make

  client-ppc64le:
    image: elijahru/build-farm-client:v0.5.1-ppc64le
    volumes:
      - .:/code
      - ./caches/ppc64le/ccache:/root/.ccache
    command: ./configure && make
```

### Advanced example: cross-compiler matrix for all available Arch Linux targets

```yml
version: '3'
services:
  builder:
    image: elijahru/build-farm:v0.5.1-amd64
    ports:
      
      # amd64
      - 3704:3704
      
      # arm32v5
      - 3705:3705
      
      # arm32v6
      - 3706:3706
      
      # arm32v7
      - 3707:3707
      
      # arm64v8
      - 3708:3708
      

  
  build-farm-client-amd64:
    image: elijahru/build-farm-client:v0.5.1-amd64
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make
  
  build-farm-client-arm32v5:
    image: elijahru/build-farm-client:v0.5.1-arm32v5
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make
  
  build-farm-client-arm32v6:
    image: elijahru/build-farm-client:v0.5.1-arm32v6
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make
  
  build-farm-client-arm32v7:
    image: elijahru/build-farm-client:v0.5.1-arm32v7
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make
  
  build-farm-client-arm64v8:
    image: elijahru/build-farm-client:v0.5.1-arm64v8
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make
  
```

### Build farm

Assuming several nodes, configured as follows:

```yml
version: '3'
services:
  builder:
    image: elijahru/build-farm:v0.5.1
    ports:
      - 3704:3704
```

Where each node can be resolved via DNS as `builder1`, `builder2`, `builder3`, etc, a client can distribute compilation across the nodes by using the `DISTCC_HOSTS` environment variable:

```yml
version: '3'
services:
  client:
    environment:
      - DISTCC_HOSTS=builder1:3704 builder2:3704 builder3:3704
    image: elijahru/build-farm-client:v0.5.1
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
    runs-on: ubuntu-v0.5.1

    strategy:
      matrix:
        arch: [ amd64, arm64v8 ]

    steps:
      - name: Setup cache
        uses: actions/cache@v2
        with:
          # Used by ccache
          path: caches
          key: ${{ matrix.arch }}

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
  builder:
    image: elijahru/build-farm:v0.5.1
    ports:
      # amd64
      - 3704:3704
      # arm64v8
      - 3708:3708

  build-amd64:
    image: elijahru/build-farm-client:v0.5.1-amd64
    depends_on: [ builder ]
    volumes:
      # Map GitHub Actions cache to ccache via volume
      - ./caches/amd64/ccache:/root/.ccache
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
    image: elijahru/build-farm-client:v0.5.1-arm64v8
    depends_on: [ builder ]
    volumes:
      # Map GitHub Actions cache to ccache via volume
      - ./caches/arm64v8/ccache:/root/.ccache
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

Adding new target operating systems should be fairly straightforward by following the existing patterns for Debian and Arch Linux. Please do submit pull requests.

Most of the work happens via `builder.py build-host` and `builder.py build-client`. Pass `--help` for usage.

The easiest way to install all requirements for building is to use pipenv. `pipenv install --python $(which python3.8)` should install the requirements, and then the build script can be run with `pipenv run ./builder.py [subcommand] [args]`.

There are some useful git hooks that can be enabled by running `git config --local core.hooksPath .githooks/`.

If you are looking for an idea, contributions for the following are especially welcome:

* Make ccache optional in the client containers via an environment variable
* A GitHub Action for GitHub Marketplace to make using these containers in CI easier
* Windows arm64v8 toolchain?

### Changelog

* v0.6.0 - 2020-12-04
  * Consolidated hosts to new container [`elijahru/build-farm`]().
  * Consolidated clients to new container `elijahru/build-farm-client`.
  * Added `debian:buster-slim` based containers.
  * Added `mips64le` and `arm32v5` architectures for `debian`.