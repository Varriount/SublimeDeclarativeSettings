# SublimeDeclarativeSettings
Declarative settings mixin for Sublime Text 2 &amp; 3

This repository contains a simple mixin/utility class for Sublime Text 2 
&amp; 3 plugins allowing objects to declare and bind setting entries to 
individual attributes.

## Installation ##
Add the 'SublimeDeclarativeSettings' to your plugin's package control
[dependancies](https://packagecontrol.io/docs/dependencies), then
import what you need from the package.

## Basic Usage ##
To use the declarative settings loader, have your command,
eventlistener, or object inherit from the 
`DeclarativeSettingsMixin`, *in addition to* the classes
it also inherits from:
```python
from sublime import ApplicationCommand
class WordFinder(ApplicationCommand, DeclarativeSettingsMixin):
    pass
```

Next, declare/assign your settings tree the the `settings_entries` 
class or object attribute.  
The settings tree looks like this:
```
(
    ('attribute_name_one', 'setting_key_one', default_value_one),
    ('attribute_name_two', 'setting_key_two', default_value_two)
    ...
)
```

That is, the settings tree is a tuple composed of three-part tuples, each
containing the attribute to bind to, the setting key to retrieve a value
from, and the default value to use.

```
from sublime import ApplicationCommand

class WordFinder(ApplicationCommand, DeclarativeSettingsMixin):
    settings_entries = (
        ('enabled', 'enable_wordfinder', True),
        ('remember', 'remember_last_word', False)
    )
```

Finally, the setting tree can be processed and the settings loaded by calling
the 'load_settings' method with a settings file name, and optionally, the
entry tree. If the entry tree isn't passed, the loader defaults to
using the 'settings_entries' attribute.

```
from sublime import ApplicationCommand

class WordFinder(ApplicationCommand, DeclarativeSettingsMixin):
    settings_entries = (
        ('enabled', 'enable_wordfinder', True),
        ('remember', 'remember_last_word', False)
    )

    def __init__(self):
        self.load_settings('wordfinder.sublime-settings')
```


## Embedding Sub-Trees ##
Aside from the standard 3-part tuples, the settings tree can also contain
other trees, whose entries are then included during processing:
```python
(
    ('attribute_name_one', 'setting_key_one', default_value_one),
    (
    	  ('attribute_name_two', 'setting_key_two', default_value_two)
    )
)
```

While this feature isn't commonly used with tuple-literals, it is quite handy
when used with variables or parent class attributes, as it allows previous
declarations to be reused and built-upon:

```python
from sublime import ApplicationCommand

class FinderCommand(ApplicationCommand):
    settings_entries = (
        ('remember', 'remember_last_word', False)
    )

class WordFinder(FinderCommand, DeclarativeSettingsMixin):
    settings_entries = (
        ('enabled', 'enable_wordfinder', True),
        FinderCommand.settings_entries
    )

    def __init__(self):
        self.load_settings('wordfinder.sublime-settings')
```


## Extension ##

SublimeDeclarativeSettings supports limited extension via a single overridable
method, `process_setting_entry`. This method is called to process and act upon
each each entry encountered:
```python
from sublime import ApplicationCommand

class FinderCommand(ApplicationCommand, DeclarativeSettingsMixin):
    settings_entries = (
        ('remember', 'remember_last_word', False)
    )
    
    def process_setting_entry(self, entry):
        processed_key = self.name + '.' + entry[1]
        super(DeclarativeSettingsMixin, self).process_setting_entry(
        	(entr[0], processed_key, entry[2])
        )
        return processed_key

class WordFinder(FinderCommand, DeclarativeSettingsMixin):
    settings_entries = (
        ('enabled', 'enable_wordfinder', True),
        FinderCommand.settings_entries
    )

    def __init__(self):
        self.load_settings('wordfinder.sublime-settings')
```

The `process_setting_entry` method is responsible for processing, loading,
and binding the setting specified in the entry to the correct object
attribute. Additionally, the method must also return the final key used to
load the setting, so that the loader may register the correct update handlers.
