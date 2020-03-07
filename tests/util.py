from inspect import signature
from typing import Type, TypeVar
from unittest.mock import DEFAULT, create_autospec


__all__ = ['mock', 'when']


T = TypeVar('T')


def mock(spec: Type[T], **kwargs) -> T:
    return create_autospec(spec, spec_set=True, instance=True, **kwargs)


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
        def side_effect():
            return value
        self._add_new_side_effect(side_effect)

    def then_raise(self, exception):
        def side_effect():
            raise exception
        self._add_new_side_effect(side_effect)

    def _add_new_side_effect(self, new_side_effect):
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
                return new_side_effect()
            return fall_back(*args, **kwargs)

        self.mock_object.side_effect = side_effect
