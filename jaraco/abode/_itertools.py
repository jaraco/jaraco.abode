import functools

import jaraco.itertools
import jaraco.functools
import more_itertools

single = jaraco.functools.compose(more_itertools.only, jaraco.itertools.always_iterable)

opt_single = jaraco.functools.compose(
    functools.partial(more_itertools.only, default=None),
    jaraco.itertools.always_iterable,
)
