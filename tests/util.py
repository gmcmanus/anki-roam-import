from typing import Mapping, Optional, Any
from unittest.mock import create_autospec, call, Mock


__all__ = ['mock', 'call']


def mock(spec: Any = None, *, instance: Optional[bool] = None, **kwargs) -> Any:
    if spec is None:
        if instance is not None:
            raise ValueError
        return Mock(**kwargs)

    if instance is None:
        instance = True

    return create_autospec(spec, spec_set=True, instance=instance, **kwargs)


def map_side_effect(mock_object, map: Mapping[Any, Any], default: Any = None) -> None:
    mock_object.side_effect = lambda key: map.get(key, default)
