import inspect

from third_party.openmontage import events


def test_events_surface_is_read_only() -> None:
    assert hasattr(events, "read_events")
    assert not hasattr(events, "emit_event")
    assert not hasattr(events, "infer_project_dir")
    source = inspect.getsource(events)
    assert 'open(' not in source
    assert ".write" not in source
