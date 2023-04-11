from fastapi import APIRouter, HTTPException
from models import Other, Pair

router = APIRouter(
    prefix='/other',
    tags=['Other']
)

@router.get('/update')
async def update_other():
    '''Update supported vs_currencies and coins list.
        
    Returns an inserted id after success request,
    otherwise returns None.'''

    result = await Other.update()

    if result:
        return {
            'response': 200,
            'detail': 'Successfull update',
            'data': str(result)
        }
    else:
        return {
            'response': 401,
            'detail': 'Failed coin and vs_currencies data update'
        }


@router.post('/check')
async def check_pair_existence(pair: Pair):
    '''Check if pair exist.
    
    Accepts a Pair instance. Return json data with message.

    :return: 432 - Wrong vs_currency.
    :return: 433 - Wrong coin.
    :return: 200 - Everything is correct'''

    result = await Other.pair_existence([pair.coin_id, pair.vs_currency])

    if result == 200:
        return {
            'status': 'success',
            'detail': 'valid pair'
        }
    
    elif result == 432:
        raise HTTPException(
            status_code=432,
            detail=f'vs_currency not valid: {pair.vs_currency}'
        )
    
    elif result == 433:
        raise HTTPException(
            status_code=433,
            detail=f'coin not valid: {pair.coin_id}'
        )
