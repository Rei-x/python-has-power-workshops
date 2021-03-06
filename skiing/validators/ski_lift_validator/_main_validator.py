from collections import OrderedDict

from ._validators import SkiLiftValidatorBase


class SkiLiftValidator:
    @staticmethod
    def validate(data: OrderedDict) -> OrderedDict:
        validators = SkiLiftValidatorBase.__subclasses__()

        for validator in validators:
            validator(data).validate()

        return data
