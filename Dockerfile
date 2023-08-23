# syntax=docker/dockerfile:1
ARG BUILD_IMAGE=python:3.11-alpine3.18
ARG RUN_IMAGE=python:3.11-alpine3.18
ARG VIRTUAL_ENV=/opt/venv
ARG LIBRD_VER=2.2.0
ARG CUSTOM_CRT_URL=http://pki.jlab.org/JLabCA.crt

################## Stage 0
FROM ${BUILD_IMAGE} as builder
ARG VIRTUAL_ENV
ARG LIBRD_VER
ARG CUSTOM_CRT_URL
ARG BUILD_DEPS="gcc linux-headers libc-dev bash make g++ musl-dev zlib-dev openssl zstd-dev pkgconfig libc-dev"
USER root
WORKDIR /
## Allow JLab intercepting proxy to intercept with it's legacy renegotiation and custom cert else onsite builds fail
RUN sed -i 's/providers = provider_sect/providers = provider_sect\n\
ssl_conf = ssl_sect\n\
\n\
[ssl_sect]\n\
system_default = system_default_sect\n\
\n\
[system_default_sect]\n\
Options = UnsafeLegacyRenegotiation/' /etc/ssl/openssl.cnf
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && update-ca-certificates \
    ; fi
## Build librdkafka from source
RUN apk add $BUILD_DEPS \
    && wget https://github.com/confluentinc/librdkafka/archive/refs/tags/v${LIBRD_VER}.tar.gz \
    && tar -xvf v${LIBRD_VER}.tar.gz  \
    && cd librdkafka-${LIBRD_VER}  \
    && ./configure --prefix /usr  \
    && make  \
    && make install

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY . /app
RUN cd /app \
    && python -m venv $VIRTUAL_ENV \
    && rm -rf build \
    && pip install .
## Note: when running pip install . the local build dir is re-used if it exists so we remove it first to avoid contamination

################## Stage 1
FROM ${RUN_IMAGE} as runner
ARG VIRTUAL_ENV
ARG LIBRD_VER
ARG CUSTOM_CRT_URL
ARG RUN_DEPS="shadow curl git bash zstd-libs"
## Allow JLab intercepting proxy to intercept with it's legacy renegotiation and custom cert else onsite builds fail
RUN sed -i 's/providers = provider_sect/providers = provider_sect\n\
ssl_conf = ssl_sect\n\
\n\
[ssl_sect]\n\
system_default = system_default_sect\n\
\n\
[system_default_sect]\n\
Options = UnsafeLegacyRenegotiation/' /etc/ssl/openssl.cnf
RUN if [ -z "${CUSTOM_CRT_URL}" ] ; then echo "No custom cert needed"; else \
       wget -O /usr/local/share/ca-certificates/customcert.crt $CUSTOM_CRT_URL \
       && update-ca-certificates \
    ; fi \
    && apk add --no-cache $RUN_DEPS \
    && usermod -d /tmp guest
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder /usr/lib/librdkafka.so.1 /usr/lib
ENV TZ=UTC
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PS1="\W \$ "
COPY --from=builder /app/docker/app/docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
HEALTHCHECK --interval=10s --timeout=10s --start-period=20s --start-interval=10s --retries=5 CMD test $(list_schemas | wc -l) -gt 20
