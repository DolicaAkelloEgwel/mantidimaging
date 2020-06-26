from dataclasses import dataclass


class ScalarCoR:
    __slots__ = 'value'
    value: float

    def __init__(self, value):
        assert isinstance(value, float), f"Value is not float. Actual type:{type(float)}"
        self.value = value

    def to_vec(self, detector_width):
        return VectorCoR(detector_width / 2 - self.value)


class VectorCoR:
    __slots__ = 'value'
    value: float

    def __init__(self, value):
        assert isinstance(value, float)
        self.value = value

    def to_scalar(self, detector_width):
        return ScalarCoR(detector_width / 2 + self.value)