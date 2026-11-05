FROM python:3.12-slim
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin runner && mkdir -p /work && chown 10001:10001 /work
WORKDIR /work
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# No ENTRYPOINT: Docker command arguments select the allowlisted executable.
