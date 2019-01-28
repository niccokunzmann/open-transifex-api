# see https://hub.docker.com/_/python/
FROM python:3-alpine

# Prepare execution
EXPOSE 80
RUN mkdir /app
WORKDIR /app/
ENV PYTHONUNBUFFERED 0
ENTRYPOINT ["python3", "app.py"]

# Prepare the environment
RUN pip install --no-cache --upgrade pip
COPY LICENSE .
COPY requirements.txt .

# install the environment
RUN cd /app && \
    pip install --no-cache -r requirements.txt

COPY templates templates
COPY app.py .

