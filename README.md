# distcc-cross-compiler

Fast & easy cross-compiling with `docker` and `distcc`.

## Use cases

* Parallel build cluster
* Cross-compiling for embedded systems
* Continuous Integration across a matrix of targets

## Supported targets

| OS            | Architecture          | Image on Docker Hub                                                  | Host port |
|---------------|-----------------------|----------------------------------------------------------------------|-----------|
| Arch Linux    | `amd64`               | `elijahru/distcc-cross-compiler-client-archlinux:latest-amd64`       | 3704      |
| Arch Linux    | `arm32v5`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v5`     | 3705      |
| Arch Linux    | `arm32v6`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v6`     | 3706      |
| Arch Linux    | `arm32v7`             | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm32v7`     | 3707      |
| Arch Linux    | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-client-archlinux:latest-arm64v8`     | 3708      |
| Debian Buster | `i386` (`i686`)       | `elijahru/distcc-cross-compiler-client-debian-buster:latest-i386`    | 3603      |
| Debian Buster | `amd64` (`x86_64`)    | `elijahru/distcc-cross-compiler-client-debian-buster:latest-amd64`   | 3604      |
| Debian Buster | `arm32v7`             | `elijahru/distcc-cross-compiler-client-debian-buster:latest-arm32v7` | 3607      |
| Debian Buster | `arm64v8` (`aarch64`) | `elijahru/distcc-cross-compiler-client-debian-buster:latest-arm64v8` | 3608      |
| Debian Buster | `s390x`               | `elijahru/distcc-cross-compiler-client-debian-buster:latest-s390x`   | 3609      |
| Debian Buster | `ppc64le`             | `elijahru/distcc-cross-compiler-client-debian-buster:latest-ppc64le` | 3610      |

## Simple example

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

## Example with all available Debian build targets

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
    environment:
      - DISTCC_HOSTS=builder:3632
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

## Example with all available Arch Linux build targets

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

### Contributing

Adding new target operating systems should be fairly straightforward by following the existing patterns for Debian and Arch Linux. Please do submit pull requests!

The images can be built and tested locally using the `scripts/build-debian-buster.sh` and `scripts/build-archlinux.sh` scripts, respectively.

The build essentially does the following:

* Render templates to produce a matrix of `docker-compose.yml` and `Dockerfiles`
* Build the host and clients images using the rendered templates
* Run the tests for each client image, one at a time

The tests verify that an arbitrary project (cJSON) is compiled using distcc, and that the resulting executable is valid. The tests then verify that subsequent builds use ccache to avoid repeat compilation.
