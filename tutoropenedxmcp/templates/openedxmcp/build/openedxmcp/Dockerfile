FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY openedxmcp /app/openedxmcp
RUN pip install --no-cache-dir .

EXPOSE 8080
CMD ["openedxmcp-server"]
