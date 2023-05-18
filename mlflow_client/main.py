import uvicorn
from fastapi import FastAPI
from routers import proph


app = FastAPI()
app.include_router(proph.router)


@app.get('/healthcheck')
def healthcheck():
    return {
        'status': 'success',
        'message': 'Server is running!'
    }


if __name__ == '__main__':
    uvicorn.run('main:app',
                host='0.0.0.0',
                port=80,
                reload=True,
                log_level='info')