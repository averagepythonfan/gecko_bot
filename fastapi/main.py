import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get('/healthcheck')
def healthcheck():
    return {'response': 200, 'message': 'Everything is good!'}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80, reload=True, log_level='info')