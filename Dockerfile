FROM python:3.9

COPY . /code

WORKDIR /code

RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r /code/requirements.txt

