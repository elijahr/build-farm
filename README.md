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
    image: elijahru/distcc-host-debian-buster:latest-amd64
    ports:
      # distccd for cross-compiling aarch64-linux-gnu listens on 3635
      - 3635:3635

  client:
    image: elijahru/distcc-client-debian-buster:latest-arm64v8
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
    image: elijahru/distcc-host-debian-buster:latest-amd64
    ports:
      # distccd for native compiling x86_64
      - 3633:3633
      # distccd for cross-compiling i686
      - 3634:3634
      # distccd for cross-compiling powerpc64le
      - 3635:3635
      # distccd for cross-compiling s390x
      - 3636:3636
      # distccd for cross-compiling arm32v7
      - 3637:3637
      # distccd for cross-compiling arm64v8
      - 3638:3638

  client-amd64:
    image: elijahru/distcc-client-debian-buster:latest-amd64
    environment:
      - DISTCC_HOSTS=builder:3632
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-i386:
    image: elijahru/distcc-client-debian-buster:latest-i386
    volumes:
      - .:/code
      - ./caches/i386/ccache:/root/.ccache
    command: ./configure && make

  client-ppc64le:
    image: elijahru/distcc-client-debian-buster:latest-ppc64le
    volumes:
      - .:/code
      - ./caches/ppc64le/ccache:/root/.ccache
    command: ./configure && make

  client-s390x:
    image: elijahru/distcc-client-debian-buster:latest-s390x
    volumes:
      - .:/code
      - ./caches/s390x/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v7:
    image: elijahru/distcc-client-debian-buster:latest-arm32v7
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/distcc-client-debian-buster:latest-arm64v8
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
    image: elijahru/distcc-host-archlinux:latest-amd64
    ports:
      # distccd for native compiling x86_64
      - 3704:3704
      # distccd for cross-compiling arm32v5
      - 3705:3705
      # distccd for cross-compiling arm32v6
      - 3706:3706
      # distccd for cross-compiling arm32v7
      - 3707:3707
      # distccd for cross-compiling arm64v8
      - 3708:3708

  client-amd64:
    image: elijahru/distcc-client-archlinux:latest-amd64
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v5:
    image: elijahru/distcc-client-archlinux:latest-arm32v5
    volumes:
      - .:/code
      - ./caches/arm32v5/ccache:/root/.ccache
    command: ./configure && make


  client-arm32v6:
    image: elijahru/distcc-client-archlinux:latest-arm32v6
    volumes:
      - .:/code
      - ./caches/arm32v6/ccache:/root/.ccache
    command: ./configure && make


  client-arm32v7:
    image: elijahru/distcc-client-archlinux:latest-arm32v7
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/distcc-client-archlinux:latest-arm64v8
    volumes:
      - .:/code
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make
```

## Additional usage

The following tags are available:

### Debian Buster

* Manifest: `elijahru/distcc-host-debian-buster:<version>`
  * `elijahru/distcc-host-debian-buster:<version>-amd64`

* Manifest: `elijahru/distcc-client-debian-buster:<version>`
  * `elijahru/distcc-client-debian-buster:<version>-amd64`
  * `elijahru/distcc-client-debian-buster:<version>-i386`
  * `elijahru/distcc-client-debian-buster:<version>-arm32v7`
  * `elijahru/distcc-client-debian-buster:<version>-arm64v8`
  * `elijahru/distcc-client-debian-buster:<version>-ppc64le`
  * `elijahru/distcc-client-debian-buster:<version>-s390x`

### Arch Linux

* Manifest: `elijahru/distcc-host-archlinux:<version>`
  * `elijahru/distcc-host-archlinux:<version>-amd64`

* Manifest: `elijahru/distcc-client-archlinux:<version>`
  * `elijahru/distcc-client-archlinux:<version>-amd64`
  * `elijahru/distcc-client-archlinux:<version>-i386`
  * `elijahru/distcc-client-archlinux:<version>-arm32v7`
  * `elijahru/distcc-client-archlinux:<version>-arm64v8`
  * `elijahru/distcc-client-archlinux:<version>-ppc64le`
  * `elijahru/distcc-client-archlinux:<version>-s390x`

Where `<version>` is either `latest` or a git tag in this repository, such as `v0.1.0`.
