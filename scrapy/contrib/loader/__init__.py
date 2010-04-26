"""
Item Loader

See documentation in docs/topics/loaders.rst
"""

from collections import defaultdict
import re

from scrapy.item import Item
from scrapy.selector import HtmlXPathSelector
from scrapy.utils.misc import arg_to_iter, extract_regex
from scrapy.utils.python import flatten
from .common import wrap_loader_context
from .processor import Identity

class ItemLoader(object):

    default_item_class = Item
    default_input_processor = Identity()
    default_output_processor = Identity()

    def __init__(self, item=None, **context):
        if item is None:
            item = self.default_item_class()
        self.item = context['item'] = item
        self.context = context
        self._values = defaultdict(list)

    def add_value(self, field_name, value, *processors, **kw):
        """ Process and then add value
            field_name - the field to add the processed value
                        * if None, values for multiple fields may be added. The processed
                          value should be a dict with field_name mapped to values.
                        * else the processed value will be only added to the given field
            processors - passed to get_value
            kw - passed to get_value
        """
        value = self.get_value(value, *processors, **kw)
        if not value:
            return
        if not field_name:
            for k,v in value.iteritems():
                self._add_value(k, v)
        else:
            self._add_value(field_name, value)

    def replace_value(self, field_name, value, *processors, **kw):
        """ Process and then replace value
            field_name - the field to replace the processed value
                        * if None, values for multiple fields may be replaced. The processed
                          value should be a dict with field_name mapped to values.
                        * else the processed value will be only added to the given field
            processors - passed to get_value
            kw - passed to get_value
        """
        value = self.get_value(value, *processors, **kw)
        if not value:
            return
        if not field_name:
            for k,v in value.iteritems():
                self._replace_value(k, v)
        else:
            self._replace_value(field_name, value)

    def _add_value(self, field_name, value):
        value = arg_to_iter(value)
        processed_value = self._process_input_value(field_name, value)
        if processed_value:
            self._values[field_name] += arg_to_iter(processed_value)

    def _replace_value(self, field_name, value):
        self._values.pop(field_name, None)
        self._add_value(field_name, value)

    def get_value(self, value, *processors, **kw):
        """ Process value by processors and given keyword arguments
            Available keyword arguments:
            * re(str or compiled regex) - a regular expression to use for extracting data from the given value,
                                          applied before processors
        """

        regex = kw.get('re', None)
        if regex:
            value = arg_to_iter(value)
            value = flatten([extract_regex(regex, x) for x in value])

        for proc in processors:
            if value is None:
                break
            proc = wrap_loader_context(proc, self.context)
            value = proc(value)
        return value

    def load_item(self, skip_empty=True):
        """ Populate and return the item

        skip_empty - don't populate empty field
        """
        item = self.item
        for field_name in self._values:
            value = self.get_output_value(field_name)
            if not skip_empty or value:
                item[field_name] = value
        return item

    def get_output_value(self, field_name):
        proc = self.get_output_processor(field_name)
        proc = wrap_loader_context(proc, self.context)
        return proc(self._values[field_name])

    def get_collected_values(self, field_name):
        return self._values[field_name]

    def get_input_processor(self, field_name):
        proc = getattr(self, '%s_in' % field_name, None)
        if not proc:
            proc = self._get_item_field_attr(field_name, 'input_processor', \
                self.default_input_processor)
        return proc

    def get_output_processor(self, field_name):
        proc = getattr(self, '%s_out' % field_name, None)
        if not proc:
            proc = self._get_item_field_attr(field_name, 'output_processor', \
                self.default_output_processor)
        return proc

    def _process_input_value(self, field_name, value):
        proc = self.get_input_processor(field_name)
        proc = wrap_loader_context(proc, self.context)
        return proc(value)

    def _get_item_field_attr(self, field_name, key, default=None):
        if isinstance(self.item, Item):
            value = self.item.fields[field_name].get(key, default)
        else:
            value = default
        return value

class XPathItemLoader(ItemLoader):

    default_selector_class = HtmlXPathSelector

    def __init__(self, item=None, selector=None, response=None, **context):
        if selector is None and response is None:
            raise RuntimeError("%s must be instantiated with a selector " \
                "or response" % self.__class__.__name__)
        if selector is None:
            selector = self.default_selector_class(response)
        self.selector = selector
        context.update(selector=selector, response=response)
        super(XPathItemLoader, self).__init__(item, **context)

    def add_xpath(self, field_name, xpath, *processors, **kw):
        values = self._get_values(xpath, **kw)
        self.add_value(field_name, values, *processors, **kw)

    def replace_xpath(self, field_name, xpath, *processors, **kw):
        values = self._get_values(xpath, **kw)
        self.replace_value(field_name, values, *processors, **kw)

    def get_xpath(self, xpath, *processors, **kw):
        values = self._get_values(xpath, **kw)
        return self.get_value(values, *processors, **kw)

    def _get_values(self, xpaths, **kw):
        xpaths = arg_to_iter(xpaths)
        return flatten([self.selector.select(xpath).extract() for xpath in xpaths])

