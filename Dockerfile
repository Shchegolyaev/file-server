FROM python:3.9

COPY . /code

WORKDIR /code

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 8080/tcp

CMD export PYTHONPATH=$(pwd) && \
    cd ./src/db && \
    alembic upgrade head && \
    cd ../.. && \
    uvicorn src.main:app --host 0.0.0.0 --port 8080

