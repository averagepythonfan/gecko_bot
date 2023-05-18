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

    await Other.update()

    return {
        'detail': 'successfull update'
    }
