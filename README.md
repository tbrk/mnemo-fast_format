Fast Format Plugin for Mnemosyne 1.1+
-------------------------------------
Timothy Bourke <tim@tbrk.org>

Plugin providing fixed ascii shortcuts for common html tags.

Allow faster markup of some common formatting for cards entered from
dictionary entries:
    [text] is put into italics
    {text} is changed into (text) in italics

Shortcuts for italics and bold that are easier to type than html:
    _text_ to italics
    *text* to bold
These irc-style notations were chosen instead of wiki-style ones, like
''italics'' and '''bold'''.

Shortcuts for colours that are much easier to type:
    `text` to red
    ``text`` to gray
    #text# to blue
    ##text## to green

Parsing of the question and answer text is not sophisticated (just regular
expressions executed in order) but should suffice for most users.

In Mnemosyne 1.x, local settings can be given in config.py:

    fast_format = { 'formats' : [ ... ],
                    'include_default' : True }

New shortcuts are defined in the 'formats' entry as pairs: a regular
expression and replacement. They are processed before the default
shortcuts. The default shortcuts can be overridden completely by setting
'include_default' to False.

In Mnemosyne 2.x, the regular expressions can be edited through the Settings
configuration dialog.

Some ideas for more shortcuts:
  * change the font for special characters
  * include commonly used images
  * etc.

