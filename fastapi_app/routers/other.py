from fastapi import APIRouter, HTTPException
from models import Other, Pair


router = APIRouter(
    prefix='/other',
    tags=['Other']
)


@router.get('/update')
async def update_other():
    '''Update supported vs_currencies and coins list.
        
    :return: 200, successfull update,
    :return: 438, data update error'''

    result = await Other.update()

    if result:
        return {
            'response': 200,
            'detail': 'successfull update',
            'data': str(result)
        }
    else:
        raise HTTPException(
            status_code=438,
            detail='failed coin and vs_currencies data update'
        )


@router.post('/check')
async def check_pair_existence(pair: Pair):
    '''Check if pair exist.
    
    Accepts a Pair instance. Return json data with message.

    :return: 200, everything is correct,
    :return: 432, vs_currency not valid: {vs_currency},
    :return: 433, coin not valid: {pair.coin_id}'''

    result = await Other.pair_existence(pair=pair)

    if result['code'] == 200:
        return {
            'status': 'success',
            'detail': 'valid pair'
        }
    
    else:
        raise HTTPException(
            status_code=result['code'],
            detail=result['detail']
        )
