from fastapi import APIRouter, HTTPException
from models import Pair, Pairs


router = APIRouter(
    prefix='/pair',
    tags=['Pairs']
)

@router.post('/add_pair')
async def add_pair(pair: Pair):
    '''Add pair to database.
    
    :return: 200, pair successfully added,
    :return: 432, vs_currency not valid: {vs_currency},
    :return: 433, coin not valid: {pair.coin_id}'''

    res = await Pairs.add_pair(pair=pair)
    if res == 432:
        raise HTTPException(
            status_code=432,
            detail='vs currency is incorrect'
        )
    elif res == 433:
        raise HTTPException(
            status_code=433,
            detail='coin is incorrect'
        )
    else:
        return {
            'status': 'success',
            'detail': str(res)
        }


@router.get('/get_pair/')
async def get_pair(coin_id: str, vs_currency: str, day: int = 7):
    '''Get pair data.'''

    res = await Pairs.get_pair(coin_id=coin_id, vs_currency=vs_currency, day=day)
    if res != 433:
        return {
            'status': 'success',
            'prices': res
        }
    else:
        raise HTTPException(
            status_code=433,
            detail='pair not found in database'
        )


@router.get('/send_pic')
async def send_pic(user_id: int, coin_id: str, vs_currency: str, day: int = 7):
    res = await Pairs.get_pic(
        user_id=user_id,
        coin_id=coin_id,
        vs_currency=vs_currency,
        day=day
    )
    if res['code'] == 200:
        return {
            'status': 'success',
            'detail': f'pic send to {user_id}',
            'data': res['detail']
        }
    else:
        raise HTTPException(
            status_code=res['code'],
            detail=res['detail']
        )
