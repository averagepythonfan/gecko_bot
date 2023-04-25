#!/bin/bash

mlflow ui --backend-store-uri=postgresql+psycopg2://$PG_USER:$PG_PASSWORD@$PG_HOST:5432/$PG_DATABASE --host=0.0.0.0 --port=5000
