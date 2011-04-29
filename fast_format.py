##############################################################################
#
# fast_format.py <timbob@bigpond.com>
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
# Local settings can be given in config.py:
#
#   fast_format = { 'formats' : [ ... ],
#		    'include_default' : True }
#
# New shortcuts are defined in the 'formats' entry as pairs: a regular
# expression and replacement. They are processed before the default
# shortcuts. The default shortcuts can be overridden completely by setting
# 'include_default' to False.
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
#   * Interface with MnemoGoGo
#
##############################################################################

from mnemosyne.core import *
import re

class FastFormat(Plugin):
    version = "1.2.1"
    formats = [
	# order is important!
	# ( regex ,	   replacement )
	(r'([^\\]|^)(\[.*?[^\\]\])', r'\1<font color="gray"><i>\2</i></font>'),
						    # [ ... ] to [gray italics]

	(r'\\\[', r'['),
	(r'\\\]', r']'),

	(r'([^\\]|^)\{(.*?[^\\])\}', r'\1<i>(\2)</i>'),   # { ... } to (italics)
	(r'\\\{', r'{'),
	(r'\\\}', r'}'),

	(r"([^\\]|^)_(.*?[^\\])_", r'\1<i>\2</i>'),	  # _ ... _ to italics
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
    tag_re = re.compile('(<[^>]*>)', re.DOTALL)
    compiled_formats = []
    exclude_cats = []

    def description(self):
	return ("Fixed ASCII shortcuts for common HTML tags. (v" +
		version + ")")

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

	for (retext, subtext) in formats:
	    self.compiled_formats.append((re.compile(retext, re.DOTALL),
					 subtext))

	register_function_hook("filter_q", self.format)
	register_function_hook("filter_a", self.format)
	register_function_hook("gogo_q", self.format)
	register_function_hook("gogo_a", self.format)

    def unload(self):
	unregister_function_hook("filter_q", self.format)
	unregister_function_hook("filter_a", self.format)
	unregister_function_hook("gogo_q", self.format)
	unregister_function_hook("gogo_a", self.format)

    def format(self, text, card):
	if card.cat.name in self.exclude_cats:
	    return text

	results = []
	texts = self.tag_re.split(text)

	for t in texts:
	    if not t.startswith('<'):
		for (regex, subtext) in self.compiled_formats:
		    t = regex.sub(subtext, t)
	    results.append(t)

	return "".join(results)

p = FastFormat()
p.load()

