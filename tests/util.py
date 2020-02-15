from inspect import signature
from typing import TypeVar
from unittest.mock import create_autospec, DEFAULT


__all__ = ['mock', 'when']


T = TypeVar('T')


def mock(spec: T, *, instance: bool = True, **kwargs) -> T:
    return create_autospec(spec, spec_set=True, instance=instance, **kwargs)


# noinspection PyPep8Naming
class when:
    def __init__(self, mock_object):
        self.mock_object = mock_object

    def called_with(self, *args, **kwargs):
        return CalledWith(self.mock_object, *args, **kwargs)


class CalledWith:
    def __init__(self, mock_object, *args, **kwargs):
        self.mock_object = mock_object
        self.signature = signature(self.mock_object)
        self.arguments = self._normalized_arguments(*args, **kwargs)

    def _normalized_arguments(self, *args, **kwargs):
        bound_arguments = self.signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        return dict(bound_arguments.arguments)

    def then_return(self, value):
        original_side_effect = self.mock_object.side_effect

        if callable(original_side_effect):
            fall_back = original_side_effect
        elif original_side_effect is None:
            def fall_back(*args, **kwargs):
                return DEFAULT
        else:
            raise ValueError

        def side_effect(*args, **kwargs):
            if self._normalized_arguments(*args, **kwargs) == self.arguments:
                return value
            return fall_back(*args, **kwargs)

        self.mock_object.side_effect = side_effect
