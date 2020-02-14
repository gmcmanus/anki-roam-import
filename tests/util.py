from inspect import signature
from typing import Optional, Any
from unittest.mock import create_autospec, call, Mock, DEFAULT, sentinel


__all__ = ['mock', 'call', 'when', 'sentinel']


def mock(spec: Any = None, *, instance: Optional[bool] = None, **kwargs) -> Any:
    if spec is None:
        if instance is not None:
            raise ValueError
        return Mock(**kwargs)

    if instance is None:
        instance = True

    return create_autospec(spec, spec_set=True, instance=instance, **kwargs)


class when:
    def __init__(self, mock):
        self.mock = mock

    def called_with(self, *args, **kwargs):
        return CalledWith(self.mock, args, kwargs)


class CalledWith:
    def __init__(self, mock, args, kwargs):
        self.mock = mock
        self.signature = signature(self.mock)
        self.arguments = self._normalized_arguments(args, kwargs)

    def _normalized_arguments(self, args, kwargs):
        bound_arguments = self.signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        return dict(bound_arguments.arguments)

    def then_return(self, value):
        if self.mock.side_effect is None:
            def fall_back(args, kwargs):
                return DEFAULT
        elif callable(self.mock.side_effect):
            def fall_back(args, kwargs):
                return self.mock.side_effect(*args, **kwargs)
        else:
            raise ValueError

        def side_effect(*args, **kwargs):
            if self._normalized_arguments(args, kwargs) == self.arguments:
                return value
            return fall_back(*args, **kwargs)

        self.mock.side_effect = side_effect
