FROM python:3.11-slim

# Blender 4.2.3 LTS (version figée, somme SHA-256 vérifiée au build) pour le moteur bim_3d en mode headless.
ARG BLENDER_VERSION=4.2.3
ARG BLENDER_SHA256=3a64efd1982465395abab4259b4091d5c8c56054c7267e9633e4f702a71ea3f4
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 \
        libxext6 libxkbcommon0 libsm6 libice6 libgl1 libegl1 libglib2.0-0 libgomp1 \
    && curl -fsSL -o /tmp/blender.tar.xz \
        "https://download.blender.org/release/Blender4.2/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && echo "${BLENDER_SHA256}  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/blender && tar -xJf /tmp/blender.tar.xz -C /opt/blender --strip-components=1 \
    && ln -s /opt/blender/blender /usr/local/bin/blender \
    && rm /tmp/blender.tar.xz && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
    && blender --version

WORKDIR /app
COPY . /app
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
ENV CA_DATA_ROOT=/var/data/api_projects
CMD ["python", "deploy/render_start.py"]
