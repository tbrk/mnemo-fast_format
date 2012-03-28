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
# Changes in 2.0.0
#   * Support for Mnemosyne 2.x
#     (Based on Peter Bienstman's filter and configuration example plugins.)
#
# Changes in 2.0.1
#   * Fix a problem in Mnemosyne 2.x reported by Murray James Morrison where
#     Asian characters are not properly formatted (due to html tags inserted by
#     the 'increase size of non-latin characters' feature). We no longer skip
#     over html tags. In practice, this means that the double quote (") and
#     equals (=) characters should not be used in format patterns, and also that
#     ascii letters and characters should probably also be avoided (for fear of
#     messing up html formatting).
#
# Changes in 2.0.2
#   * Fix the problem where characters are replaced in the paths of images and
#     sounds.
#
# Changes in 2.0.3
#   * Fix some bugs in the config screen.
#   * Add up and down buttons for regular expressions
#   * Highlight errors in match string.
#
# Changes in 2.0.4
#   * Fix a bug in the handling of embedded audio.
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

name = "Fast Format"
version = "2.0.4"
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

render_chains = ["default", "card_browser", "mnemogogo"]

def compile_formats(formats):
    results = []
    for (ret, sub) in formats:
        try:
            cret = re.compile(ret, re.DOTALL)
            results.append((cret, sub))
        except re.error as e:
            pass

    return results

tag_re = re.compile('(<[^>]*>)', re.DOTALL)

def format(text, formats, skip_tags=False):
    try:
        if skip_tags:
            results = []
            texts = tag_re.split(text)

            for t in texts:
                if not t.startswith('<'):
                    for (regex, subtext) in formats:
                        try:
                            t = regex.sub(subtext, t)
                        except re.error as e:
                            pass
                results.append(t)

            return "".join(results)
        else:
            for (regex, subtext) in formats:
                text = regex.sub(subtext, text)
            return text

    except re.error as e:
        print "formatting error: %s" % e
        return text

##############################################################################
# Mnemosyne 1.x
if mnemosyne_version == 1:

    class FastFormat(Plugin):
        name = name
        version = version
        compiled_formats = []

        formats = default_formats

        exclude_cats = []

        def description(self):
            return description

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

            self.compiled_formats = compile_formats(formats)

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
            return format(text, self.compiled_formats, skip_tags=True)

    p = FastFormat()
    p.load()

##############################################################################
# Mnemosyne 2.x
elif mnemosyne_version == 2:

    strip_re = re.compile(r'(< *(?:img|audio)[^>]*>)')
    thread_re = re.compile(u'\ufffc([0-9]*)\ufffc')

    def strip_tags(text):
        texts = strip_re.split(text)
        tags = []
        for i in range(1, len(texts), 2):
            tags.append(texts[i])
            texts[i] = u'\ufffc%d\ufffc' % ((i - 1) / 2)

        return(''.join(texts), tags)

    def thread_tags(text, tags):
        texts = thread_re.split(text)

        for i in range(1, len(texts), 2):
            texts[i] = tags[int(texts[i])]

        return ''.join(texts)

    class FastFormatConfig(Hook):
        used_for = "configuration_defaults"

        def run(self):
            self.config().setdefault("formats", default_formats)

    class FastFormatConfigWdgt(QtGui.QWidget, ConfigurationWidget):
        name = name

        color_badre = QtGui.QColor(255,0,0)
        color_goodre = QtGui.QColor(0,255,0)
        color_unknownre = QtGui.QColor(0,0,0)

        def __init__(self, component_manager, parent):
            ConfigurationWidget.__init__(self, component_manager)
            QtGui.QDialog.__init__(self, self.main_widget())
            self.vlayout = QtGui.QVBoxLayout(self)
            self.hlayout = QtGui.QHBoxLayout()

            try:
                formats = self.config()["formats"]
            except KeyError:
                formats = []

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
            self.formats_table.setColumnWidth(0, 200)
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

            # test panels
            self.hlayout = QtGui.QHBoxLayout()

            self.input_text = QtGui.QTextEdit(self)
            self.input_text.setMaximumHeight(60)
            self.output_text = QtGui.QTextEdit(self)
            self.output_text.setMaximumHeight(60)
            self.output_text.setReadOnly(True)
            self.input_text.setPlainText("*test* ``data`` _area_")

            self.hlayout.addWidget(self.input_text)
            self.hlayout.addWidget(self.output_text)

            self.vlayout.addLayout(self.hlayout)

            # add "add" and "remove" buttons
            self.hlayout = QtGui.QHBoxLayout()

            self.up_button = QtGui.QToolButton(self)
            self.up_button.setArrowType(QtCore.Qt.UpArrow)

            self.down_button = QtGui.QToolButton(self)
            self.down_button.setArrowType(QtCore.Qt.DownArrow)

            self.add_button = QtGui.QPushButton(self)
            self.add_button.setText(QtGui.QApplication.translate("FastFormat",
                    "Add", None, QtGui.QApplication.UnicodeUTF8))
            self.del_button = QtGui.QPushButton(self)
            self.del_button.setText(QtGui.QApplication.translate("FastFormat",
                    "Remove", None, QtGui.QApplication.UnicodeUTF8))

            self.hlayout.addStretch()
            self.hlayout.addWidget(self.up_button)
            self.hlayout.addWidget(self.down_button)

            self.hlayout.addSpacing(40)
            self.hlayout.addWidget(self.del_button)
            self.hlayout.addWidget(self.add_button)

            self.vlayout.addLayout(self.hlayout)

            # connect events
            self.update_sample_text = False
            self.connect(self.up_button, QtCore.SIGNAL("clicked()"),
                    self.up_clicked)
            self.connect(self.down_button, QtCore.SIGNAL("clicked()"),
                    self.down_clicked)
            self.connect(self.del_button, QtCore.SIGNAL("clicked()"),
                    self.del_clicked)
            self.connect(self.add_button, QtCore.SIGNAL("clicked()"),
                    self.add_clicked)
            self.connect(self.formats_table,
                QtCore.SIGNAL("cellChanged(int, int)"), self.cell_changed)
            self.connect(self.input_text,
                QtCore.SIGNAL("textChanged()"), self.input_text_changed)

            self._update_formats_table(formats)
            self.update_sample_text = True
            self.input_text_changed()

        def input_text_changed(self):
            text = self.input_text.toPlainText()

            formats = self._table_to_formats()
            compiled_formats = compile_formats(formats)

            self.output_text.setHtml(format(unicode(text), compiled_formats))

        def cell_changed(self, row, col):
            text = unicode(self.input_text.toPlainText())

            if col == 0 or col == 1:
                item = self.formats_table.item(row, 0)
                subtext = self.formats_table.item(row, 1)
                match = unicode(item.text())
                try:
                    r = re.compile(match, re.DOTALL)
                    item.setTextColor(self.color_goodre)
                    item.setToolTip('')

                    try:
                        if r and subtext:
                            r.sub(unicode(subtext.text()), text)
                            subtext.setToolTip('')
                            subtext.setTextColor(self.color_unknownre)

                    except re.error as e:
                        subtext.setToolTip(unicode(e))
                        subtext.setTextColor(self.color_badre)

                except re.error as e:
                    item.setToolTip(unicode(e))
                    item.setTextColor(self.color_badre)

            if self.update_sample_text:
                self.input_text_changed()

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

            self.input_text_changed()

        def get_row(self, row):
            tag_item = self.formats_table.item(row, 0)
            font_item = self.formats_table.item(row, 1)

            tag, font, size = None, None, None
            if tag_item: tag = tag_item.text()
            if font_item: font = font_item.text()

            return (tag, font)

        def set_row(self, row, (tag, font)):
            if tag:
                tag_item = QtGui.QTableWidgetItem()
                tag_item.setText(tag)
                self.formats_table.setItem(row, 0, tag_item)

            if font:
                font_item = QtGui.QTableWidgetItem()
                font_item.setText(font)
                self.formats_table.setItem(row, 1, font_item)

        def move_row(self, old_row, new_row):
            items = self.get_row(old_row)
            self.formats_table.removeRow(old_row)
            self.formats_table.insertRow(new_row)
            self.set_row(new_row, items)

        def up_clicked(self):
            row = self.formats_table.currentRow()
            if row > 0:
                self.move_row(row, row - 1)
                self.formats_table.selectRow(row - 1)

        def down_clicked(self):
            row = self.formats_table.currentRow()
            if row + 1 < self.formats_table.rowCount():
                self.move_row(row, row + 1)
                self.formats_table.selectRow(row + 1)


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

        def reset_to_defaults(self):
            self._update_formats_table(default_formats)

        def _table_to_formats(self):
            n_rows = self.formats_table.rowCount()

            formats = []
            for i in range(n_rows):
                match_item = self.formats_table.item(i, 0)
                subst_item = self.formats_table.item(i, 1)

                if match_item is not None and subst_item is not None:
                    match = unicode(match_item.text())
                    subst = unicode(subst_item.text())
                    formats.append((match, subst))

            return formats

        def apply(self):
            self.config()["formats"] = self._table_to_formats()

            for chain in render_chains:
                try:
                    filter = self.render_chain(chain).filter(FastFormat)
                    filter.reconfigure()
                except KeyError: pass

            self.review_controller().update_dialog(redraw_all=True)

    class FastFormat(Filter):
        name = name
        version = version
        compiled_formats = None

        def __init__(self, component_manager):
            Filter.__init__(self, component_manager)
            self.reconfigure()

        def reconfigure(self):
            try:
                formats = self.config()["formats"]
            except KeyError:
                formats = []
            self.compiled_formats = compile_formats(formats)

        def run(self, text, card, fact_key, **render_args):
            (text, tags) = strip_tags(text)
            return thread_tags(format(text, self.compiled_formats), tags)

    class FastFormatPlugin(Plugin):
        name = name
        description = description
        components = [FastFormatConfig, FastFormatConfigWdgt, FastFormat]

        def __init__(self, component_manager):
            Plugin.__init__(self, component_manager)

        def activate(self):
            Plugin.activate(self)
            for chain in render_chains:
                try:
                    self.new_render_chain(chain)
                except KeyError: pass

        def deactivate(self):
            Plugin.deactivate(self)
            for chain in render_chains:
                try:
                    self.render_chain(chain).unregister_filter(FastFormat)
                except KeyError: pass

        def new_render_chain(self, name):
            if name in render_chains:
                self.render_chain(name).register_at_front(FastFormat,
                        ["EscapeToHtml", "EscapeToHtmlForCardBrowser"])

    # Register plugin.

    from mnemosyne.libmnemosyne.plugin import register_user_plugin
    register_user_plugin(FastFormatPlugin)

