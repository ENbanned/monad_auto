from decimal import Decimal
import random

def randfloat(from_: int | float | str, to_: int | float | str,
              step: int | float | str | None = None) -> float:
    """
    Return a random float from the range.

    :param Union[int, float, str] from_: the minimum value
    :param Union[int, float, str] to_: the maximum value
    :param Optional[Union[int, float, str]] step: the step size (calculated based on the number of decimal places)
    :return float: the random float
    """
    from_ = Decimal(str(from_))
    to_ = Decimal(str(to_))
    if not step:
        step = 1 / 10 ** (min(from_.as_tuple().exponent, to_.as_tuple().exponent) * -1)

    step = Decimal(str(step))
    rand_int = Decimal(str(random.randint(0, int((to_ - from_) / step))))
    return float(rand_int * step + from_)