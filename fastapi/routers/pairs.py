from fastapi import APIRouter, HTTPException
from models import Pair, Pairs


router = APIRouter(
    prefix='/pair',
    tags=['Pairs']
)
