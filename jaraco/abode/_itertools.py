import functools

import jaraco.itertools
import jaraco.functools
import more_itertools

single = jaraco.functools.compose(
    more_itertools.first, jaraco.itertools.always_iterable
)

opt_single = jaraco.functools.compose(
    functools.partial(more_itertools.first, default=None),
    jaraco.itertools.always_iterable,
)
