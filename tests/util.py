from unittest.mock import create_autospec, call


__all__ = ['mock', 'call']


def mock(spec, *, instance=True):
    return create_autospec(spec, spec_set=True, instance=instance)