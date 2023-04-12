from .models import UserResponse


def validate_user_data(input_data):
    raw = str(input_data)
    raw = raw.replace('ObjectId(', '').replace(')', '').replace("'", '"')
    valid = UserResponse.parse_raw(raw)
    return valid.dict()
