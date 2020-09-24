# distcc-cross-compiler

Fast & easy cross-compiling with `docker` and `distcc`.

### Use cases

* Cross-compiling for embedded systems
* Parallel build farm
* Continuous integration across a matrix of architectures

### Compiler containers

The following table outlines which compilers are available. A single `amd64` container per supported operating system is configured with several distccd daemons listening on different ports, each daemon targeting a different compiler toolchain.

| OS            | Target architecture   | Compiler image on Docker Hub                                     | Compiler port       |
|---------------|-----------------------|------------------------------------------------------------------|---------------------|
| Arch Linux    | `amd64` (`x86_64`)    | `elijahru/distcc-cross-compiler-host-archlinux:latest-amd64`     | 3704                |
| Arch Linux    | `arm32v5`             | `elijahru/distcc-cross-compiler-host-archlinux:latest-amd64`     | 3705                |
| Arch Linux    | `arm32v6`             | `elijahru/distcc-cross-compiler-host-archlinux:latest-amd64`     | 3706                |
| Arch Linux    | `arm32v7`             | `elijahru/distcc-cross-compiler-host-archlinux:latest-amd64`     | 3707                |
| Arch Linux    | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-host-archlinux:latest-amd64`     | 3708                |
| Debian Buster | `i386` (`i686`)       | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3603                |
| Debian Buster | `amd64` (`x86_64`)    | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3604                |
| Debian Buster | `arm32v7`             | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3607                |
| Debian Buster | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3608                |
| Debian Buster | `s390x`               | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3609                |
| Debian Buster | `ppc64le`             | `elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64` | 3610                |

### Client containers

The below table outlines which distcc client images are available. By default, these containers will assume that a compiler image is running in the same docker network. The compiler address is configured via the environment variable `DISTCC_HOSTS`, whose default value is `172.17.0.1:<compiler-port>`, where `172.17.0.1` is the default Docker network IP and `<compiler-port>` corresponds to the table above. These defaults should work for most Docker installations. You can also use `DISTCC_HOSTS=host.docker.internal:<port>` on macOS or Windows hosts. The client containers require the `multiarch/qemu-user-static` package for emulation, which can be installed via:

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

| OS            | Emulated architecture | Client image on Docker Hub                                           | `DISTCC_HOSTS`    |
|---------------|-----------------------|----------------------------------------------------------------------|-------------------|
| Arch Linux    | `amd64` (`x86_64`)    | `elijahru/distcc-cross-compiler-client-archlinux:latest-amd64`       | `172.17.0.1:3704` |
| Arch Linux    | `arm32v5`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v5`     | `172.17.0.1:3705` |
| Arch Linux    | `arm32v6`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v6`     | `172.17.0.1:3706` |
| Arch Linux    | `arm32v7`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v7`     | `172.17.0.1:3707` |
| Arch Linux    | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm64v8`     | `172.17.0.1:3708` |
| Debian Buster | `i386` (`i686`)       | `elijahru/distcc-cross-compiler-client-debian-buster:latest-i386`    | `172.17.0.1:3603` |
| Debian Buster | `amd64` (`x86_64`)    | `elijahru/distcc-cross-compiler-client-debian-buster:latest-amd64`   | `172.17.0.1:3604` |
| Debian Buster | `arm32v7`             | `elijahru/distcc-cross-compiler-client-debian-buster:latest-arm32v7` | `172.17.0.1:3607` |
| Debian Buster | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-client-debian-buster:latest-arm64v8` | `172.17.0.1:3608` |
| Debian Buster | `s390x`               | `elijahru/distcc-cross-compiler-client-debian-buster:latest-s390x`   | `172.17.0.1:3609` |
| Debian Buster | `ppc64le`             | `elijahru/distcc-cross-compiler-client-debian-buster:latest-ppc64le` | `172.17.0.1:3610` |

The client containers also use ccache to avoid repeat compilation. ccached object files are volatile unless you mount /root/.ccache as a volume (see examples).

### Simple example: cross-compiler

In this example, `host` is a native Debian `amd64` container which exposes an `arm64v8` cross-compiler on port `3608`.

`client` is an emulated `arm64v8` container that offloads all `gcc/g++/cc/etc` work to the cross-compiler exposed on `host:3608`.

The compiled object code is cached via `ccache` in a persistent volume, so that subsequent builds do not re-compile unchanged code.

```yml
version: '3'
services:
  host:
    image: elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64
    ports:
      - 3608:3608

  client:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-arm64v8
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
  builder:
    image: elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64
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
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-i386
    volumes:
      - .:/code
      - ./caches/i386/ccache:/root/.ccache
    command: ./configure && make

  client-amd64:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-amd64
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v7:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-arm32v7
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-arm64v8
    volumes:
      - .:/code
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make

  client-s390x:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-s390x
    volumes:
      - .:/code
      - ./caches/s390x/ccache:/root/.ccache
    command: ./configure && make

  client-ppc64le:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-ppc64le
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
    image: elijahru/distcc-cross-compiler-host-archlinux:latest-amd64
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

  client-amd64:
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-amd64
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v5:
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v5
    volumes:
      - .:/code
      - ./caches/arm32v5/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v6:
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v6
    volumes:
      - .:/code
      - ./caches/arm32v6/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v7:
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v7
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-arm64v8
    volumes:
      - .:/code
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make
```

### Build farm

Assuming several nodes, configured as follows:

```yml
version: '3'
services:
  builder:
    image: elijahru/distcc-cross-compiler-host-archlinux:latest-amd64
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
    image: elijahru/distcc-cross-compiler-client-archlinux:latest-amd64
    volumes:
      - .:/code
    command: ./configure && make
```

See the [distcc man page](https://linux.die.net/man/1/distcc) for documentation on `DISTCC_HOSTS`.

## Github Actions

```yml

```

### Contributing

Adding new target operating systems should be fairly straightforward by following the existing patterns for Debian and Arch Linux. Please do submit pull requests.

The images can be built and tested locally using `scripts/build-debian-buster.sh` and `scripts/build-archlinux.sh`.

The build scripts essentially do the following:

* Render templates to produce a matrix of `docker-compose.yml` and `Dockerfiles`
* Build the host and client images using the rendered templates
* Run the tests for each client image, one at a time

The tests verify that an arbitrary C project (cJSON) is compiled using distcc, and that the resulting executable is valid. The tests then verify that subsequent builds use ccache to avoid repeat compilation.

If you are looking for an idea, contributions for the following are especially welcome:

* Project name suggestions (distcc-cross-compiler is a mouthful)
* Make ccache optional in the client containers via an environment variable
* A GitHub Action for GitHub Marketplace to make using these containers in CI easier
* Windows arm64v8 or NetBSD/* toolchains?
