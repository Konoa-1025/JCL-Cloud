FROM debian:stable-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tcc gcc timeout ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY app/ /app/

# 非root実行
RUN useradd -m jcl
USER jcl

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
