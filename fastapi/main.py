import uvicorn
from fastapi import FastAPI
from models import Other, Pair


app = FastAPI()

@app.get('/healthcheck')
def healthcheck():
    return {'response': 200, 'message': 'Everything is good!'}


@app.get('/user/{user_id}')
async def check_if_user_exist(user_id: int):
    '''Checking user existence. If user does not exist, create new.'''
    pass

@app.get('/other/update')
async def update_other():
    '''Update coin and vs_currency data'''

    result = await Other.update()
    if result:
        return {'response': 200, 'message': 'Successfull update','data': str(result)}
    else:
        return {'response': 401, 'message': 'Something went wrong...'}

@app.post('/other/exist')
async def check_pair_existence(pair: Pair):
    result = await Other.pair_existence([pair.coin_id, pair.vs_currency])
    if result == 200:
        return {'response': 200, 'message': 'Valid pair'}
    elif result == 401:
        return {'response': 401, 'message': f'Wrong vs_currency: {pair.vs_currency}'}
    elif result == 402:
        return {'response': 402, 'message': f'Wrong coin: {pair.coin_id}'}
    

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80, reload=True, log_level='info')