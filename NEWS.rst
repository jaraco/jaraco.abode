v5.1.0
======

Features
--------

- Require Python 3.8 or later.


v5.0.1
======

Minor bugfixes and test updates.

v5.0.0
======

Device methods that change state (``.set_status``, ``.set_level``,
``.switch_on``, ``.switch_off``, ``.set_color``, ``.set_color_temp``,
``.lock``, ``.unlock``) no longer return ``True`` on success or
``False`` if no ``control_url`` is set. Instead, these methods now
return ``None`` and an exception is raised if no ``control_url`` is set
(where required).

v4.2.0
======

More internal refactoring.

v4.1.0
======

Deprecated unnecessary ``Automation.automation_id`` and ``.is_enabled``
properties. Use ``.id`` or ``.enabled`` instead.

v4.0.0
======

Substantial refactoring of "constants". All constants have been
removed from ``jaraco.abode.helpers.constants`` and either
inlined, replaced by constants in the relevant modules, or
replaced by other factors already present. These changes should
be backward-compatible except for libraries reliant on the
constants.

v3.3.0
======

Removed unnecessary ``_device_id`` and ``_device_uuid`` accessors
and deprecated ``device_id`` and ``device_uuid`` accessors in
favor of simply ``Device.id`` and ``Device.uuid`` accessors.

Remove aliases for ``Device.{_type,_generic_type,_name,_type_tag}``.

v3.2.2
======

#21: Derive UUID from MAC address late and only for Alarm objects.

v3.2.1
======

#16: Ensure that parent directories are created for
``config.paths.user_data``.

v3.2.0
======

Substantial refactoring in socketio logic.

v3.1.2
======

#14: Fixed three minor issues with sockets/events.

v3.1.1
======

#12: Restore support for ``Client.get_devices(generic_type)`` as an
iterable.

v3.1.0
======

Substantial refactoring and cleanup.

Switched to ``platformdirs`` dependency from ``app_paths``.

v3.0.0
======

Project no longer exposes a "cache" (or related options for cache-path).
Instead, state from cookies from the API is stored in an "app data"
path (platform-specific).

It's no longer possible to disable the "cache". Cookies are persisted
unconditionally.

As a result, a UUID is persisted only if an API login succeeded.

v2.0.0
======

Substantial refactoring for better namespacing.

Class names no longer are prefixed by "Abode" (including Exceptions).

"Abode" object is now called "Client".

v1.2.1
======

Updated tests to use native objects.

v1.2.0
======

#9: Internal refactoring to store the device state directly and
reflect it as properties.

v1.1.0
======

#8: Added support for camera snapshots.

v1.0.1
======

Refactoring and cleanup.

v1.0.0
======

Removed abodepy compatibility.

v0.8.0
======

#3: Removed test dependency on npm.

#4: Project is now continuously tested on Windows.

Cleaned up usage of unittest in tests.


v0.7.0
======

#1: Passwords are no longer stored in or retrieved from the cache
file. Instead, credentials must be supplied on the command line
or loaded from `keyring <https://pypi.org/project/keyring>`_.
This approach allows the passwords to be stored in a secure,
encrypted, system store. To avoid requiring a username on
each invocation, the default username is loaded from the
ABODE_USERNAME environment variable. If the password is not
present, the user will be prompted for it on the first invocation.

v0.6.0
======

#5: Added support for Abode Cam 2 devices.

#6: Added support for new event codes in ALARM_END_GROUP and
ARM_FAULT_GROUP groups.

v0.5.2
======

Fixed bug in CLI.

v0.5.1
======

Cleaned up README and other references to ``abodepy``.

v0.5.0
======

Added ``abode`` command, superseding ``abodepy``.

v0.4.0
======

Moved modules to ``jaraco.abode``.

v0.3.0
======

Package now uses relative imports throughout.

Prefer pytest for assertions.

General cleanup.

v0.2.0
======

Refreshed packaging. Enabled automated releases.

Require Python 3.7 or later.

v0.1.0
======

Initial release based on `abodepy 1.2.1 <https://pypi.org/project/abodepy>`_.
