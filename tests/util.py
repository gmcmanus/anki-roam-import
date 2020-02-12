from unittest.mock import create_autospec, call, Mock


__all__ = ['mock', 'call']


def mock(spec=None, *, instance=None, **kwargs):
    if spec is None:
        if instance is not None:
            raise ValueError
        return Mock(**kwargs)

    if instance is None:
        instance = True

    return create_autospec(spec, spec_set=True, instance=instance, **kwargs)
