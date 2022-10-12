import sys

import jaraco.abode


for name in tuple(sys.modules):
    if not name.startswith('jaraco.abode.'):
        continue
    orig_name = name.replace('jaraco.abode.', 'abodepy.')
    sys.modules[orig_name] = sys.modules[name]

del sys
globals().update(vars(jaraco.abode))
del jaraco
