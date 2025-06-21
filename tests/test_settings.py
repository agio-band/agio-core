import pytest
from agio.core.settings import APackageSettings, IntField
from agio.core.exceptions import RequiredValueNotSetError, ValueTypeError


def test_int_field():
    class TestSettings(APackageSettings):
        value: IntField

    with pytest.raises(RequiredValueNotSetError):
        _ = TestSettings()
    inst = TestSettings(value=10)
    assert inst.value.get() == 10
    inst.value.set(20)
    assert inst.value.get() == 20

    with pytest.raises(ValueTypeError):
        inst.value.set('notvalid')

    with pytest.raises(ValueTypeError):
        _ = TestSettings(value='notvalid')
    with pytest.raises(ValueTypeError):
        _ = TestSettings(value=[1,2,3])

