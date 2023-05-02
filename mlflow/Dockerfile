FROM ubuntu/mlflow:2.1.1_1.0-22.04

WORKDIR /app

RUN pip install psycopg2-binary prophet

COPY entrypoint.sh entrypoint.sh

RUN chmod +x entrypoint.sh

EXPOSE 5000/tcp

ENTRYPOINT [ "./entrypoint.sh" ]
