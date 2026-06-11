# Motion Studio — container image for the editor server.
#
# Build:
#   docker build -t motion-studio .
#
# Run (mount your SMPL models and a persistent workspace as volumes):
#   docker run --rm -p 8815:8815 \
#       -v /path/to/smpl/models:/smpl:ro \
#       -v /path/to/workspace:/workspace \
#       -e SMPL_DIR=/smpl \
#       motion-studio --workspace /workspace --port 8815
#
# SMPL body model files are licensed separately and are NOT shipped in this
# image: mount them with -v and point the server at them via the SMPL_DIR
# environment variable (read by the default config) or --smpl-dir.
#
# The ENTRYPOINT already passes --host 0.0.0.0 --allow-remote so the server is
# reachable from outside the container. Motion Studio has no authentication and
# can run code from uploaded files, so publish the port only on a trusted
# network (or behind your own auth proxy).
FROM python:3.11-slim

# ffmpeg is needed for the server's video/audio handling; the rest are slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Install the package with every optional extra (torch, smplx, video stack).
RUN pip install --no-cache-dir ".[all]"

# Default mount points for the SMPL models and the persistent workspace.
ENV SMPL_DIR=/smpl
ENV MOTION_STUDIO_HOME=/workspace
VOLUME ["/smpl", "/workspace"]

EXPOSE 8815

# Bind all interfaces inside the container and acknowledge remote exposure;
# extra flags (e.g. --workspace, --port, --data) are appended at `docker run`.
ENTRYPOINT ["motion-studio", "--host", "0.0.0.0", "--allow-remote"]
