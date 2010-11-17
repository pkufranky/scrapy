"""
This module provides some commonly used processors for Item Loaders.

See documentation in docs/topics/loaders.rst
"""

import re
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.datatypes import MergeDict
from scrapy.utils.python import flatten
from .common import wrap_loader_context

class MapCompose(object):

    def __init__(self, *functions, **default_loader_context):
        self.functions = functions
        self.default_loader_context = default_loader_context
        
    def __call__(self, value, loader_context=None):
        values = arg_to_iter(value)
        if loader_context:
            context = MergeDict(loader_context, self.default_loader_context)
        else:
            context = self.default_loader_context
        wrapped_funcs = [wrap_loader_context(f, context) for f in self.functions]
        for func in wrapped_funcs:
            next_values = []
            for v in values:
                next_values += arg_to_iter(func(v))
            values = next_values
        return values


class Compose(object):

    def __init__(self, *functions, **default_loader_context):
        self.functions = functions
        self.stop_on_none = default_loader_context.get('stop_on_none', True)
        self.default_loader_context = default_loader_context
    
    def __call__(self, value, loader_context=None):
        if loader_context:
            context = MergeDict(loader_context, self.default_loader_context)
        else:
            context = self.default_loader_context
        wrapped_funcs = [wrap_loader_context(f, context) for f in self.functions]
        for func in wrapped_funcs:
            if value is None and self.stop_on_none:
                break
            value = func(value)
        return value


class TakeFirst(object):

    def __call__(self, values):
        for value in values:
            if value:
                return value


class Identity(object):

    def __call__(self, values):
        return values


class Join(object):

    def __init__(self, separator=u' '):
        self.separator = separator

    def __call__(self, values):
        return self.separator.join(values)

class Take(object):
    def __init__(self, start, end=None):
        self.start = start
        self.end = end
    def __call__(self, values):
        if self.end is None:
            return values[self.start:]
        else:
            return values[self.start:self.end]

class TakeOne(object):
    def __init__(self, index):
        self.index = index
    def __call__(self, values):
        return values[self.index]

class RegexExtract(object):

    def __init__(self, regexes):
        self.regexes = arg_to_iter(regexes)

    def __call__(self, value):
        matches = ()
        values = arg_to_iter(value)
        for value in values:
            for regex in self.regexes:
                m = re.search(regex, value)
                if m:
                    matches = matches + m.groups()
                    break

        return matches

class XPathExtract(object):

    def __init__(self, xpaths, re=None):
        self.xpaths = arg_to_iter(xpaths)
        self.re = re

    def __call__(self, value):
        from scrapy.selector import HtmlXPathSelector
        def extract(hxs, xpath):
            if self.re:
                return hxs.select(xpath).re(self.re)
            else:
                return hxs.select(xpath).extract()
        def extract_xpaths(hxs):
            return [extract(hxs, x) for x in self.xpaths]

        value = arg_to_iter(value)
        return flatten([extract_xpaths(HtmlXPathSelector(text=x)) for x in value])

class SingleMultipleProcessor(object):
    def __call__(self, value):
        if hasattr(value, '__iter__'):
            return [self.process(x) for x in value if x is not None]
        elif value is not None:
            return self.process(value)
    def process(self, value):
        """ The real process function, should be overriden by sub class
            value - assured not None and not iterable
        """
        raise NotImplementedError()

class ReplaceTag(SingleMultipleProcessor):

    def __init__(self, replacement=u''):
        self.replacement = replacement

    def process(self, value):
        from scrapy.utils.markup import replace_tags
        return replace_tags(value, self.replacement)

class RemoveTag(SingleMultipleProcessor):

    def __init__(self, which_ones=(), keep=(), keep_content=True):
        assert (not keep or keep_content), 'Can not handle this case for now'
        self.which_ones = arg_to_iter(which_ones)
        self.keep = arg_to_iter(keep)
        self.keep_content = keep_content

    def process(self, value):
        from scrapy.utils.markup import remove_tags, remove_tags_with_content
        if not value:
            return value
        if self.keep_content:
            return remove_tags(value, self.which_ones, self.keep)
        else:
            return remove_tags_with_content(value, self.which_ones)

class Strip(SingleMultipleProcessor):
    def __init__(self, chars=None):
        self.chars = chars

    def process(self, value):
        if hasattr(value, 'strip'):
            value = value.strip(self.chars)
        return value

class Replace(SingleMultipleProcessor):

    def __init__(self, pattern, replacement=u''):
        self.pattern = pattern
        self.replacement = replacement

    def process(self, value):
        return re.sub(self.pattern, self.replacement, value)

class Split(SingleMultipleProcessor):

    def __init__(self, pattern):
        self.pattern = pattern

    def process(self, value):
        return re.split(self.pattern, value)

class JoinCanonicalizeUrl(SingleMultipleProcessor):
    def __init__(self, base=None, canonicalize=True):
        self.base = base
        self.canonicalize = canonicalize

    def process(self, url):
        from scrapy.utils.url import urljoin_rfc, canonicalize_url
        if self.base:
            url = urljoin_rfc(self.base, url)
        if self.canonicalize:
            url = canonicalize_url(url)
        return url
