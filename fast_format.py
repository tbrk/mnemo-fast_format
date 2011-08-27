##############################################################################
#
# fast_format.py <tim@tbrk.org>
#
# Plugin providing fixed ascii shortcuts for common html tags.
#
# Allow faster markup of some common formatting for cards entered from
# dictionary entries:
#   [text] is put into italics
#   {text} is changed into (text) in italics
#
# Shortcuts for italics and bold that are easier to type than html:
#   _text_ to italics
#   *text* to bold
# These irc-style notations were chosen instead of wiki-style ones, like
# ''italics'' and '''bold'''.
#
# Shortcuts for colours that are much easier to type:
#   `text` to red
#   ``text`` to gray
#   #text# to blue
#   ##text## to green
#
# Parsing of the question and answer text is not sophisticated (just regular
# expressions executed in order) but should suffice for most users.
# One possible improvement would be to respect the html tree structure when
# pairing regular expressions, possible working from the leaves outward.
#
# ---------------------------------------------------------------------------
# Instructions for Mnemosyne 1.x
# ------------------------------
#
# Local settings can be given in config.py:
#
#   fast_format = { 'formats' : [ ... ],
#                   'include_default' : True }
#
# New shortcuts are defined in the 'formats' entry as pairs: a regular
# expression and replacement. They are processed before the default
# shortcuts. The default shortcuts can be overridden completely by setting
# 'include_default' to False.
#
# ---------------------------------------------------------------------------
#
# Some ideas for more shortcuts:
#   * change the font for special characters
#   * include commonly used images
#   * etc.
#
# Changes in 1.1.0
#   * Allow backslash-escaped characters.
#   * Don't match inside or across HTML tags.
#
# Changes in 1.2.0
#   * Interface with Mnemogogo
#
# Changes in 1.3.0
#   * Support for Mnemosyne 2.x
#     (Based on Peter Bienstman's filter and configuration example plugins.)
#
##############################################################################

try:
  from mnemosyne.core import *
  mnemosyne_version = 1

except ImportError:
  mnemosyne_version = 2
  from PyQt4 import QtCore, QtGui
  from mnemosyne.libmnemosyne.hook import Hook
  from mnemosyne.libmnemosyne.filter import Filter
  from mnemosyne.libmnemosyne.plugin import Plugin
  from mnemosyne.libmnemosyne.ui_components.configuration_widget import \
       ConfigurationWidget

import re

name = "FastFormat"
version = "1.3.0"
description = "ASCII shortcuts for common HTML tags. (v" + version + ")"
help_text = "Use python \
  <a href=\"http://docs.python.org/howto/regex.html\">regular expressions</a>:\
  patterns captured in <i>match</i> can be recalled in <i>replacement</i>."

default_formats = [
    # order is important!
    # ( regex ,        replacement )
    (r'([^\\]|^)(\[.*?[^\\]\])', r'\1<font color="gray"><i>\2</i></font>'),
                                                # [ ... ] to [gray italics]

    (r'\\\[', r'['),
    (r'\\\]', r']'),

    (r'([^\\]|^)\{(.*?[^\\])\}', r'\1<i>(\2)</i>'),   # { ... } to (italics)
    (r'\\\{', r'{'),
    (r'\\\}', r'}'),

    (r"([^\\]|^)_(.*?[^\\])_", r'\1<i>\2</i>'),       # _ ... _ to italics
    (r'\\_', r'_'),

    (r'([^\\]|^)\*(.*?[^\\])\*', r'\1<b>\2</b>'),     # * ... * to bold
    (r'\\\*', r'*'),

    (r'([^\\]|^)``(.*?[^\\])``', r'\1<font color="gray">\2</font>'),# `` ... `` to gray
    (r'([^\\]|^)`(.*?[^\\])`', r'\1<font color="red">\2</font>'), # ` ... ` to red
    (r'\\`', r'`'),

    (r'([^\\]|^)##(.*?[^\\])##', r'\1<font color="green">\2</font>'),# ## ... ## to green
    (r'([^\\]|^)#(.*?[^\\])#', r'\1<font color="blue">\2</font>'),# # ... # to blue
    (r'\\#', r'#'),
    ]

class FastFormatBase():
    name = name
    version = version

    formats = default_formats

    tag_re = re.compile('(<[^>]*>)', re.DOTALL)
    compiled_formats = []
    exclude_cats = []

    def description(self):
        return description

    def format(self, text):
        results = []
        texts = self.tag_re.split(text)

        for t in texts:
            if not t.startswith('<'):
                for (regex, subtext) in self.compiled_formats:
                    t = regex.sub(subtext, t)
            results.append(t)

        return "".join(results)

##############################################################################
# Mnemosyne 1.x
if mnemosyne_version == 1:

    class FastFormat(FastFormatBase, Plugin):

        def load(self):

            try: config = get_config("fast_format")
            except KeyError:
                set_config("fast_format", {})
                config = {}
            if not config.has_key('include_default'):
                config['include_default'] = True;
            
            if config.has_key('formats'):
                formats = config['formats'];
                if config['include_default']: formats.extend(self.formats)
            else:
                formats = self.formats

            for (ret, sub) in formats:
                self.compiled_formats.append((re.compile(ret, re.DOTALL), sub))

            register_function_hook("filter_q", self.run)
            register_function_hook("filter_a", self.run)
            register_function_hook("gogo_q", self.run)
            register_function_hook("gogo_a", self.run)

        def unload(self):
            unregister_function_hook("filter_q", self.run)
            unregister_function_hook("filter_a", self.run)
            unregister_function_hook("gogo_q", self.run)
            unregister_function_hook("gogo_a", self.run)

        def run(self, text, card):
            if card.cat.name in self.exclude_cats:
                return text
            return self.format(text)

    p = FastFormat()
    p.load()

##############################################################################
# Mnemosyne 2.x
elif mnemosyne_version == 2:

    class FastFormatConfig(Hook):
        used_for = "configuration_defaults"

        def run(self):
            self.config().setdefault("formats", default_formats)

    class FastFormatConfigWdgt(QtGui.QWidget, ConfigurationWidget):

        name = name

        def __init__(self, component_manager, parent):
            ConfigurationWidget.__init__(self, component_manager)
            QtGui.QDialog.__init__(self, self.main_widget())
            self.vlayout = QtGui.QVBoxLayout(self)
            self.hlayout = QtGui.QHBoxLayout()

            formats = self.config()["formats"]

            # explanatory label
            self.hlayout = QtGui.QHBoxLayout()

            self.help_label = QtGui.QLabel(self)
            self.help_label.setObjectName("help_label")
            self.help_label.setText(QtGui.QApplication.translate("FastFormat",
                help_text, None, QtGui.QApplication.UnicodeUTF8))

            self.hlayout.addWidget(self.help_label)
            self.vlayout.addLayout(self.hlayout)

            # add match/subst table
            self.hlayout = QtGui.QHBoxLayout()

            self.formats_table = QtGui.QTableWidget(self)
            self.formats_table.setAlternatingRowColors(True)
            self.formats_table.setColumnCount(2)
            self.formats_table.horizontalHeader().setVisible(True)
            self.formats_table.horizontalHeader().setStretchLastSection(True)
            self.formats_table.verticalHeader().setVisible(True)
            self.formats_table.setObjectName("formatsWidget")

            item = QtGui.QTableWidgetItem()
            self.formats_table.setHorizontalHeaderItem(0, item)
            self.formats_table.horizontalHeaderItem(0).setText(\
                QtGui.QApplication.translate("FastFormat",
                    "match", None, QtGui.QApplication.UnicodeUTF8))

            item = QtGui.QTableWidgetItem()
            self.formats_table.setHorizontalHeaderItem(1, item)
            self.formats_table.horizontalHeaderItem(1).setText(\
                QtGui.QApplication.translate("FastFormat",
                    "replacement", None, QtGui.QApplication.UnicodeUTF8))

            self.hlayout.addWidget(self.formats_table)
            self.vlayout.addLayout(self.hlayout)

            # add "add" and "remove" buttons
            self.hlayout = QtGui.QHBoxLayout()

            self.add_button = QtGui.QPushButton(self)
            self.add_button.setText(QtGui.QApplication.translate("FastFormat",
                    "Add", None, QtGui.QApplication.UnicodeUTF8))
            self.connect(self.add_button, QtCore.SIGNAL("clicked()"),
                    self.add_clicked)
            self.del_button = QtGui.QPushButton(self)
            self.del_button.setText(QtGui.QApplication.translate("FastFormat",
                    "Remove", None, QtGui.QApplication.UnicodeUTF8))
            self.connect(self.del_button, QtCore.SIGNAL("clicked()"),
                    self.del_clicked)

            self.hlayout.addStretch()
            self.hlayout.addWidget(self.del_button)
            self.hlayout.addWidget(self.add_button)

            self.vlayout.addLayout(self.hlayout)

            self.display() # XXX

        def add_clicked(self):
            row = self.formats_table.currentRow()

            if row == -1:
                self.formats_table.insertRow(self.formats_table.rowCount())
            else:
                self.formats_table.insertRow(row)

        def del_clicked(self):
            rows = set()
            for item in self.formats_table.selectedItems():
                rows.add(item.row())

            for row in sorted(rows, reverse=True):
                self.formats_table.removeRow(row)

        def _update_formats_table(self, formats):
            self.formats_table.setRowCount(len(formats))

            i = 0
            for (match, subst) in formats:
                item = QtGui.QTableWidgetItem()
                item.setText(match)
                self.formats_table.setItem(i, 0, item)

                item = QtGui.QTableWidgetItem()
                item.setText(subst)
                self.formats_table.setItem(i, 1, item)

                i = i + 1
            
        def display(self):
            self._update_formats_table(self.config()["formats"])
                
        def reset_to_defaults(self):
            self._update_formats_table(default_formats)
            
        def apply(self):
            n_rows = self.formats_table.rowCount()

            formats = []
            for i in range(n_rows):
                match = str(self.formats_table.item(i, 0).text())
                subst = str(self.formats_table.item(i, 1).text())
                formats.append((match, subst))

            self.config()["formats"] = formats

    class FastFormat(FastFormatBase, Filter):

        def activate(self):
            formats = self.config()["formats"]

            for (ret, sub) in formats:
                self.compiled_formats.append((re.compile(ret, re.DOTALL), sub))

            self.render_chain("default").\
                register_filter(FastFormat, in_front=False)
            self.render_chain("card_browser").\
                register_filter(FastFormat, in_front=False)
            
        def deactivate(self):
            self.render_chain("default").\
                unregister_filter(FastFormat)
            
        def run(self, text, **render_args):
            return self.format(text)

    class FastFormatPlugin(Plugin):
        
        name = name
        description = description
        components = [FastFormatConfig, FastFormatConfigWdgt, FastFormat]

    # Register plugin.

    from mnemosyne.libmnemosyne.plugin import register_user_plugin
    register_user_plugin(FastFormatPlugin)

