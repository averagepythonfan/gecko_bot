import uvicorn
from fastapi import FastAPI
from models import Other, Pair
from routers import other


app = FastAPI()


app.include_router(other.router)


@app.get('/healthcheck')
def healthcheck():
    return {'response': 200, 'message': 'Server is running!'}


# @app.get('/user/{user_id}')
# async def check_if_user_exist(user_id: int):
#     '''Checking user existence. If user does not exist, create new.'''
#     pass



    

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80, reload=True, log_level='info')