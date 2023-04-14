from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models import User, Users, Pair


router = APIRouter(
    prefix='/user',
    tags=['User']
)


@router.post('/create')
async def create_user(user: User):
    '''Creates a user.
    
    :return: 200, inserted id
    :return: 434, user already exists.'''

    res = await Users.create_user(user=user)
    if res:
        return {
            'status': 'success',
            'detail': f'Inserted: {res}'
        }
    else:
        raise HTTPException(
            status_code=434,
            detail='User already exists'
        )


@router.get('/all')
async def get_all_users():
    '''Return all users data.
    
    :return: 200, list with user's data'''

    res = await Users.get_all_users()
    if res:
        return {
            'status': 'success',
            'deatil': 'users data',
            'data': res
        }


@router.get('/{user_id}')
async def get_user_data(user_id: int):
    '''Get user data by id.

    :return: 200, user data
    :return: 435, user not found'''

    res = await Users.get_user(user_id=user_id)
    if res:
        return {
            'status': 'success',
            'user_data': res
        }
    else:
        raise HTTPException(
            status_code=435,
            detail='User not found'
        )


@router.put('/{user_id}/set_n_pairs/{n_pairs}')
async def set_n_pairs_for_user(user_id: int, n_pairs: int):
    '''Set number of pairs for user by id.
    
    Requires only id and n_pairs.
    :return: 200, updated user data
    :return: 436, setting n_pairs error'''

    res = await Users.set_n_pairs(user_id=user_id, n_pairs=n_pairs)
    if res:
        return {
            'status': 'success',
            'user_data': res
        }
    else:
        raise HTTPException(
            status_code=436,
            detail='setting n_pairs error'
        )


@router.put('/{user_id}/add_pair')
async def add_new_pair(user_id: int, pair: Pair):
    '''Add pair to user data.
    
    :return: 200, pair successfully added,
    :return: 432, vs_currency not valid: {vs_currency},
    :return: 433, coin not valid: {pair.coin_id},
    :return: 435, user not found {user_id}
    :return: 439, n_pair limit is over'''

    res = await Users.add_pair(user_id=user_id, pair=pair)
    if res:
        if res['code'] == 200:
            return {
                'status': 'success',
                'detail': res['detail']
            }
        else:
            raise HTTPException(
                status_code=res['code'],
                detail=res['detail']
            )


@router.delete('/{user_id}/delete_pair')
async def delete_user_pair(user_id: int, pair: Pair):
    '''Delete user's pair by user_id and pair
    
    :return: 200, pair successfully deleted,
    :return: 437, pair not found'''

    res = await Users.delete_users_pair(
        user_id=user_id,
        pair=f'{pair.coin_id}-{pair.vs_currency}'
    )
    if res['code'] == 200:
        return {
            'status': 'success',
            'detail': res['detail']
        }
    else:
        raise HTTPException(
            status_code=437,
            detail=res['detail'] + f'{pair.coin_id}-{pair.vs_currency}'
        )


@router.delete('/{user_id}/delete_user')
async def delete_user(user_id: int):
    '''Delete user by id.
    
    :return: 200, deletion data {'n': 1, 'ok': 1.0}
    :return: 435, deletion error: user not found'''

    res = await Users.delete_user(user_id=user_id)
    if res:
        return {
            'status': 'success',
            'detail': f'{res}'
        }
    else:
        raise HTTPException(
            status_code=435,
            detail='deletion error: user not found'
        )
