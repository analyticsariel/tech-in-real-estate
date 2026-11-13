# tire-agent Lambda image (S20.G, decision #137). Build context: the repo root.
# The corpus (tire_agent/build/) is built in CI just before this, so the agent answers from the
# same commit the site serves. The Lambda Web Adapter runs uvicorn and streams the response (SSE).
FROM public.ecr.aws/docker/library/python:3.12-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter

ENV PORT=8080 \
    AWS_LWA_INVOKE_MODE=response_stream \
    AWS_LWA_READINESS_CHECK_PATH=/health \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY tire_agent/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# `agents` is a namespace package: no __init__.py at that level.
COPY agents/tire_agent /app/agents/tire_agent
RUN test -f /app/tire_agent/build/tire.db || (echo "corpus missing: run python -m tire_agent.build_db first" && exit 1)
# Lambda runs the container as a non-root user. build_db writes build/ owner-only (0700), so make the
# whole app world-readable (directories traversable) regardless of the permissions the build left.
RUN chmod -R a+rX /app

CMD ["uvicorn", "--factory", "tire_agent.server:create_app", "--host", "0.0.0.0", "--port", "8080"]
