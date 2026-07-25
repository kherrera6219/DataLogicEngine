# DataLogicEngine-owned SeaweedFS runtime image.
#
# SeaweedFS 4.40 shipped google.golang.org/grpc v1.81.1. GHSA-hrxh-6v49-42gf
# requires v1.82.1 or newer, so the application rebuilds the exact upstream
# release source with that dependency update while retaining the official
# 4.40 image as the final runtime base.

FROM docker.io/library/golang@sha256:56961d79ea8129efddcc0b8643fd8a5416b4e6228cfd477e3fd61deb2672c587 AS builder

RUN apk add --no-cache git

ARG SEAWEEDFS_SOURCE_REVISION=875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa
ARG GRPC_GO_VERSION=v1.82.1

RUN git clone https://github.com/seaweedfs/seaweedfs.git /src \
    && cd /src \
    && git checkout "${SEAWEEDFS_SOURCE_REVISION}" \
    && test "$(git rev-parse HEAD)" = "${SEAWEEDFS_SOURCE_REVISION}"

WORKDIR /src
RUN go get "google.golang.org/grpc@${GRPC_GO_VERSION}" \
    && test "$(go list -m -f '{{.Version}}' google.golang.org/grpc)" = "${GRPC_GO_VERSION}"

WORKDIR /src/weed
RUN CGO_ENABLED=0 go build \
    -ldflags "-extldflags -static -X github.com/seaweedfs/seaweedfs/weed/util/version.COMMIT=875cd1f67" \
    -o /out/weed .

FROM docker.io/chrislusf/seaweedfs@sha256:52194fba4fecd0083c842158b3a902ba6e04a63619b2b0efcd08007bdb6a4602

COPY --from=builder /out/weed /usr/bin/weed

LABEL org.opencontainers.image.version="4.40-dle.1" \
      org.opencontainers.image.revision="875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa" \
      org.opencontainers.image.licenses="Apache-2.0" \
      com.datalogicengine.upstream.version="4.40" \
      com.datalogicengine.grpc-go.version="v1.82.1" \
      com.datalogicengine.security.patch="GHSA-hrxh-6v49-42gf"
