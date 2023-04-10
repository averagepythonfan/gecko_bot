
class NoneResponseMongoException(BaseException):
    def __repr__(self) -> str:
        return 'None response from mongo'