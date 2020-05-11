FROM python:3.7

WORKDIR /app

ADD . /app

RUN apt-get update && apt-get install -y \
        libmemcached-dev \
        libmemcached-dev zlib1g-dev

RUN pip install -r requirements.txt

EXPOSE 8080
EXPOSE 11211
EXPOSE 239

CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:8080", "startup:app"]
