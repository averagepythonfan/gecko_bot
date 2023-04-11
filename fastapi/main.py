import uvicorn
from fastapi import FastAPI
from routers import other, users, pairs


app = FastAPI()


app.include_router(other.router)
app.include_router(users.router)
app.include_router(pairs.router)


@app.get('/healthcheck')
def healthcheck():
    return {
        'response': 200,
        'message': 'Server is running!'
    }
    

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80, reload=True, log_level='info')