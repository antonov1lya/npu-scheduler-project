FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir gradio matplotlib

WORKDIR /app

COPY . .

RUN mkdir build

WORKDIR /app/build
RUN cmake .. && make
WORKDIR /app

EXPOSE 7860

CMD ["python", "./gradio_demo/demo.py"]
