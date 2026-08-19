FROM python:3.11-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY extractlayer ./extractlayer

RUN pip install --no-cache-dir .

ENV HOST=0.0.0.0
ENV API_PORT=8420

EXPOSE 8420

CMD ["python", "-m", "extractlayer.main"]
