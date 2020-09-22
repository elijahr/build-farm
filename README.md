# distcc-cross-compiler

Fast & easy cross-compiling with `docker` and `distcc`.

Supported Debian Buster targets:

* `arm64v8` aka `aarch64`
* `arm32v7` aka `armhf`
* `ppc64le` aka `powerpc64le` aka `powerpc64el`
* `s390x`
* `amd64` aka `x86_64`
* `i686` aka `i386`

Supported Arch Linux targets:

* `arm64v8` aka `aarch64`
* `arm32v7` aka `armhf`
* `arm32v6`
* `arm32v5`
* `amd64` aka `x86_64`

## Why?

Building projects from source can take a long time in an emulator. Instead of building in an emulated container, we can offload compilation to a native container configured for cross-compilation. This can speed up builds dramatically.

## Simple example

In this example, `host` is a native Debian `amd64` container which exposes an `aarch64-linux-gnu` cross-compiler on port `3635`.

`client` is an emulated `arm64v8` container that offloads all `gcc/g++/cc/etc` work to the cross-compiler exposed on `host:3635`.

The compiled object code is cached via `ccache` in a persistent volume, so that subsequent builds do not re-compile unchanged code.

```yml
version: '3'
services:
  host:
    image: elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64
    ports:
      # distccd for cross-compiling aarch64-linux-gnu listens on 3635
      - 3635:3635

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
      # i686-linux-gnu
      - 3603:3603
      # x86_64-linux-gnu
      - 3604:3604
      # arm-linux-gnueabihf
      - 3607:3607
      # aarch64-linux-gnu
      - 3608:3608
      # s390x-linux-gnux
      - 3609:3609
      # powerpc64le-linux-gnu
      - 3610:3610

  client-amd64:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-amd64
    environment:
      - DISTCC_HOSTS=builder:3632
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-i386:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-i386
    volumes:
      - .:/code
      - ./caches/i386/ccache:/root/.ccache
    command: ./configure && make

  client-ppc64le:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-ppc64le
    volumes:
      - .:/code
      - ./caches/ppc64le/ccache:/root/.ccache
    command: ./configure && make

  client-s390x:
    image: elijahru/distcc-cross-compiler-client-debian-buster:latest-s390x
    volumes:
      - .:/code
      - ./caches/s390x/ccache:/root/.ccache
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

## Additional usage

The following tags are available:

### Debian Buster

* Manifest: `elijahru/distcc-cross-compiler-host-debian-buster:<version>`
  * `elijahru/distcc-cross-compiler-host-debian-buster:<version>-amd64`

* Manifest: `elijahru/distcc-cross-compiler-client-debian-buster:<version>`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-amd64`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-i386`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-arm32v7`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-arm64v8`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-ppc64le`
  * `elijahru/distcc-cross-compiler-client-debian-buster:<version>-s390x`

### Arch Linux

* Manifest: `elijahru/distcc-cross-compiler-host-archlinux:<version>`
  * `elijahru/distcc-cross-compiler-host-archlinux:<version>-amd64`

* Manifest: `elijahru/distcc-cross-compiler-client-archlinux:<version>`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-amd64`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-i386`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-arm32v7`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-arm64v8`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-ppc64le`
  * `elijahru/distcc-cross-compiler-client-archlinux:<version>-s390x`

Where `<version>` is either `latest` or a git tag in this repository, such as `v0.1.0`.

### Contributing

Adding new target operating systems should be more or less straightforward by following the existing patterns for Debian and Arch. Please do submit pull requests!

The images can be built and tested locally using the `scripts/build-debian-buster.sh` and `scripts/build-archlinux.sh` scripts, respectively.

The build essentially does the following:

* Render templates to produce a matrix of `docker-compose.yml` and `Dockerfiles`
* Build the host and clients images using the rendered templates
* Run the tests for each client image, one at a time

The tests verify that an arbitrary project (cJSON) is compiled using distcc, and that the resulting executable is valid. The tests then verify that subsequent builds use ccache to avoid repeat compilation.
