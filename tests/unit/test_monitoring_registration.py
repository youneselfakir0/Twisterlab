from twisterlab.monitoring_utils import register_standard_metrics


def test_register_standard_metrics_idempotent():
    m1 = register_standard_metrics()
    m2 = register_standard_metrics()
    assert isinstance(m1, dict)
    assert isinstance(m2, dict)
    # Both calls should return a dict and not raise; if registered twice, value may be None
    assert set(m1.keys()) == set(m2.keys())
