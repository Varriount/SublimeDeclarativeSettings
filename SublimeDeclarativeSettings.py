import time
import sys
from pprint import pformat, pprint

import sublime

API_READY = False

def plugin_loaded():
    global API_READY
    API_READY = True


class DeclarativeSettingsMixin(object):
    """
    Mixin class for commands and event listeners that implements loading
    settings via a declarative, class attribute based mechanism.
    To load the settings tree, call self.load_settings with the given
    settings file name.
    """

    # Setting entries associated with the command or event listener.
    # Each entry should either be a tuple of the form
    #     (attribute_identifier, entry_name, default_value)
    # or a tuple containing sub-entries of the same form.
    setting_entries = ()

    def load_settings(self, settings_file, entry_tree=None, auto_update=True,
                      sparse_update=False):
        """
        Load settings from the given settings file into the object, using
        either the entry tree stored in the object's 'setting_entries'
        attribute, or the given setting entry tree. Note that this method
        should only be called once with the 'auto_update' parameter set to
        true, otherwise multiple update handlers may be installed for the same
        set of keys.

        If `auto_update` is True, install a handler that automatically updates
        the attributes holding the setting values. If 'sparse_update' is also
        true, closures are used to individually update each entry (the default
        mechanism updates all entries when one is changed. This takes more
        memory (for closure generation) but means that
        settings.clear_on_change will work as expected. When false, all
        settings will be reloaded whenever a change occurs. This takes less
        memory, but means that calling settings.clear_on_change won't
        necessarily stop a setting attribute from being updated.

        Although all declared settings will have a value after this method is
        called, they will be set to their default value if the Sublime Text
        API has not yet fully loaded (only in Sublime Text 3). Additionally,
        until the API has fully loaded, the '_settings_obj' will be set to
        None.

        :type settings_file: str
        :type entry_tree: tuple
        :type auto_update: bool
        :type sparse_update: bool
        """
        etree = entry_tree
        if etree is None:
            etree = self.setting_entries

        global API_READY
        if API_READY:
            self._settings_obj = sublime.load_settings(settings_file)
            self.__reload_settings(etree, auto_update, sparse_update)
        else:
            self._settings_obj = None
            self.__reload_settings(etree)

            def _loader():
                self.load_settings(
                    settings_file, etree, auto_update, sparse_update
                )

            sublime.set_timeout(_loader, 500)

    def process_setting_entry(self, entry):
        """
        Process an entry loaded from the settings tree. Override this to
        implement more complex entry processing.

        :type entry: tuple[str, str, Any]
        """
        settings_obj = self._settings_obj
        attribute, key, default = entry
        if key == '' or key == Ellipsis:
            key = attribute
        if settings_obj is None:
            setattr(self, attribute, default)
        else:
            setattr(self, attribute, settings_obj.get(key, default))
        return key

    def __reload_settings(self, entry_tree, install_update_handler=False,
                          sparse=False):
        process_setting_entry = self.process_setting_entry
        settings_obj = self._settings_obj

        def update_handler():
            self.__delay_reload_settings(
                entry_tree, install_update_handler, sparse
            )

        def _is_setting_entry(entry):
            return (
                len(entry) == 3 and
                isinstance(entry[0], str)
            )

        # Use a recursive parser. Note that this doesn't protect
        # against recursive setting trees!
        def _load_entry(entry):
            # Process entry
            if _is_setting_entry(entry):
                processed_key = process_setting_entry(entry)
                if install_update_handler:
                    if sparse:
                        update_handler = lambda: process_setting_entry(entry)
                    else:
                        update_handler = _load_entry.update_handler
                    settings_obj.add_on_change(entry, update_handler)

            # Process entry tree
            elif isinstance(entry, tuple):
                for sub_entry in entry:
                    _load_entry(sub_entry)

            # Process bad entry
            else:
                raise TypeError(
                    "Bad setting entry type: {0}\n"
                    "Entry representation:\n{1}".format(
                        type(entry), pformat(entry)
                    )
                )
        _load_entry.update_handler = update_handler

        _load_entry(entry_tree)

    # Technically more complicated than simply attaching a change listener to a
    # non-existant key, however this is future proof (and doesn't rely on
    # unspecified behavior)
    def __delay_reload_settings(self):
        current_time = time.clock()
        # Python 2.6 doesn't have strict monotonic support, and in any case, we
        # just want to know the time difference between two calls.
        if abs(current_time - self._settings_update_time) > 2:
            self._settings_update_time = current_time
            sublime.set_timeout(self.__reload_settings, 2)