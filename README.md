# distcc-cross-compiler

Fast & easy cross-compiling with `distcc`.

Supported Linux targets:

* `arm64v8` aka `aarch64`
* `arm32v7` aka `armhf`
* `ppc64le` aka `powerpc64le` aka `powerpc64el`
* `s390x`
* `amd64` aka `x86_64`
* `i686` aka `i386`

## Why?

Building projects from source can take a long time in an emulator. Instead of building in an emulated container, we can offload compilation to a native container configured for cross-compilation. This can speed up builds dramatically.

## Simple example

In this example, `builder` is an `amd64` container that exposes an `aarch64-linux-gnu` cross-compiler on port `3634`.

`client-arm64v8` is an emulated container that offloads all `gcc/g++/cc/etc` work to the `aarch64-linux-gnu` cross-compiler exposed on `builder:3634`.

The compiled object code will be cached via `ccache` and stored in a persistent volume, so that subsequent builds do not request re-compilation of unchanged code.

```yml
version: '3'
services:
  builder:
    image: elijahru/distcc-host:latest
    ports:
      # distccd for cross-compiling aarch64-linux-gnu listens on 3635
      - 3635:3635

  client-arm64v8:
    image: elijahru/distcc-client:latest-debian-buster-arm64v8
    environment:
      - DISTCC_HOSTS=builder:3635
    volumes:
      # Your code
      - .:/code
      # Cache resulting object code between builds
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make
```

## Example with all available build targets

```yml
version: '3'
services:
  builder:
    image: elijahru/distcc-host:latest
    ports:
      # distccd for native compiling x86_64-linux-gnu listens on 3632
      - 3632:3632
      # distccd for cross-compiling i686-linux-gnu listens on 3633
      - 3633:3633
      # distccd for cross-compiling arm-linux-gnueabihf listens on 3634
      - 3634:3634
      # distccd for cross-compiling aarch64-linux-gnu listens on 3635
      - 3635:3635
      # distccd for cross-compiling powerpc64le-linux-gnu listens on 3636
      - 3636:3636
      # distccd for cross-compiling s390x-linux-gnu listens on 3637
      - 3637:3637

  client-amd64:
    image: elijahru/distcc-client:latest-debian-buster-amd64
    environment:
      - DISTCC_HOSTS=builder:3632
    volumes:
      - .:/code
      - ./caches/amd64/ccache:/root/.ccache
    command: ./configure && make

  client-i386:
    image: elijahru/distcc-client:latest-debian-buster-i386
    environment:
      - DISTCC_HOSTS=builder:3633
    volumes:
      - .:/code
      - ./caches/i386/ccache:/root/.ccache
    command: ./configure && make

  client-arm32v7:
    image: elijahru/distcc-client:latest-debian-buster-arm32v7
    environment:
      - DISTCC_HOSTS=builder:3634
    volumes:
      - .:/code
      - ./caches/arm32v7/ccache:/root/.ccache
    command: ./configure && make

  client-arm64v8:
    image: elijahru/distcc-client:latest-debian-buster-arm64v8
    environment:
      - DISTCC_HOSTS=builder:3635
    volumes:
      - .:/code
      - ./caches/arm64v8/ccache:/root/.ccache
    command: ./configure && make

  client-ppc64le:
    image: elijahru/distcc-client:latest-debian-buster-ppc64le
    environment:
      - DISTCC_HOSTS=builder:3636
    volumes:
      - .:/code
      - ./caches/ppc64le/ccache:/root/.ccache
    command: ./configure && make

  client-s390x:
    image: elijahru/distcc-client:latest-debian-buster-s390x
    environment:
      - DISTCC_HOSTS=builder:3637
    volumes:
      - .:/code
      - ./caches/s390x/ccache:/root/.ccache
    command: ./configure && make
```

## Additional usage

The `elijahru/distcc-host` image runs six `distcc`:

* Native compiler targeting `x86_64-linux-gnu` (`amd64`) on port `3632`.
* Cross-compiler targeting `i686-linux-gnu` (`i386`) on port `3633`.
* Cross-compiler targeting `arm-linux-gnueabihf` (`arm32v7`) on port `3634`.
* Cross-compiler targeting `aarch64-linux-gnu` (`arm64v8`) on port `3635`.
* Cross-compiler targeting `powerpc64le-linux-gnu` (`ppc64le`) on port `3636`.
* Cross-compiler targeting `s390x-linux-gnu` on port `3637`.

The following tags are available:

### debian stretch

* Manifest: `elijahru/distcc-host:<version>-debian-stretch`
  * `elijahru/distcc-host:<version>-debian-stretch-amd64`

* Manifest: `elijahru/distcc-client:<version>-debian-stretch`
  * `elijahru/distcc-client:<version>-debian-stretch-amd64`
  * `elijahru/distcc-client:<version>-debian-stretch-i386`
  * `elijahru/distcc-client:<version>-debian-stretch-arm32v7`
  * `elijahru/distcc-client:<version>-debian-stretch-arm64v8`
  * `elijahru/distcc-client:<version>-debian-stretch-ppc64le`
  * `elijahru/distcc-client:<version>-debian-stretch-s390x`

### debian buster

* Manifest: `elijahru/distcc-host:<version>-debian-buster`
  * `elijahru/distcc-host:<version>-debian-buster-amd64`

* Manifest: `elijahru/distcc-client:<version>-debian-buster`
  * `elijahru/distcc-client:<version>-debian-buster-amd64`
  * `elijahru/distcc-client:<version>-debian-buster-i386`
  * `elijahru/distcc-client:<version>-debian-buster-arm32v7`
  * `elijahru/distcc-client:<version>-debian-buster-arm64v8`
  * `elijahru/distcc-client:<version>-debian-buster-ppc64le`
  * `elijahru/distcc-client:<version>-debian-buster-s390x`

Where `<version>` is either `latest` or a git tag in this repository, such as `v0.1.0`.
