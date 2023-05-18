import requests
import time
import logging
from datetime import datetime
from pymongo import MongoClient
from config import MONGO, MLFLOW_CLIENT, MLFLOW_SERVER, TOKEN, ADMIN


__all__ = [
    'PairTask',
    'ModelTask',
    'GeckoCoinAPIException'
]


# set logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GeckoCoinAPIException(BaseException):
    pass


class PairTask:

    def __init__(self,
                 address: str = MONGO,
                 port: int = 27017,
                 database: str = 'main_database',
                 users: str = 'users',
                 pairs: str = 'pairs') -> None:
        """Earn data from mongodb like unique pairs."""

        self.client = MongoClient(address, port)
        self.db = self.client.get_database(database)
        self.users = self.db.get_collection(users)
        self.pairs = self.db.get_collection(pairs)
        self._pairs_update = {el['pair_name'] for el in self.pairs.find({}, {'pair_name': 1})}
        self._pairs_insert = set()
        for el in self.users.find({'pairs': {'$ne': []}}):
            self._pairs_insert = self._pairs_insert.union(set(el['pairs']) - self._pairs_update)

    @staticmethod
    def _request(pair: str) -> dict:
        '''Make request to GeckoCoinAPI to get data'''

        coin_id, vs_currency = pair.split('-')

        headers = {'accept': 'application/json'}

        NOW = int(time.time())
        THEN = NOW - 60 * 60 * 24 * 89

        params = {
            'vs_currency': vs_currency,
            'from': THEN,
            'to': NOW,
        }

        resp = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range',
                            params=params,
                            headers=headers)

        pair_data: dict = resp.json()
        if pair_data.get('prices'):
            return pair_data
        else:
            raise GeckoCoinAPIException('Pair data update fail')

    def update_data(self) -> None:
        print('Start updating')
        for el in self._pairs_update:
            res = self.pairs.update_one(
                {'pair_name': el},
                {'$set': {'data': self._request(el)}}
            )
            logger.info(f'Pair {el} updated, ID: {res.upserted_id}')
            logger.debug('Wait for 10 seconds')
            time.sleep(10)
        for el in self._pairs_insert:
            res = self.pairs.insert_one({
                'pair_name': el,
                'data': self._request(el)
            })
            logger.info(f'Pair {el} inserted, ID: {res.inserted_id}')
            logger.debug('Wait for 10 seconds')
            time.sleep(10)

    @staticmethod
    def on_failure():
        params = {
            'chat_id': ADMIN,
            'text': f'Updating pairs fail at {datetime.now()}'
        }

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url=url, params=params)


class ModelTask:

    def __init__(self, mlflow_server: str = MLFLOW_SERVER, mlflow_client: str = MLFLOW_CLIENT) -> None:
        '''Get all experiment names and do new runs'''

        self.mlflow_server = mlflow_server
        self.mlflow_client = mlflow_client
        resp = requests.post(
            f'http://{self.mlflow_server}:5000/api/2.0/mlflow/experiments/search',
            json={'max_results': 100},
            headers={'accept': 'application/json'}
        )
        if resp.status_code == 200:
            resp = resp.json()
            self.exp = {el['name'] for el in resp['experiments']}

    def do_runs(self) -> None:
        for el in self.exp:
            COIN_ID, VS_CURRENCY = el.split('-')
            resp = requests.post(
                f'http://{self.mlflow_client}:80/prophet/do_run',
                params={'coin_id': COIN_ID, 'vs_currency': VS_CURRENCY})
            if resp.status_code == 200:
                resp = resp.json()['detail']['model_uri']
                logger.info(f'Success run for {el}, model URI: {resp}')
