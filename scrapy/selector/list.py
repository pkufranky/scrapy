from scrapy.utils.python import flatten
from scrapy.utils.decorator import deprecated

class XPathSelectorList(list):

    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))

    def select(self, xpath):
        return self.__class__(flatten([x.select(xpath) for x in self]))

    def re(self, regex):
        return flatten([x.re(regex) for x in self])

    def re1(self, regex, index=0):
        """Perform the re() method on each XPathSelector of the list, and
        return the result as a flattened list of unicode strings"""
        matches = self.re(regex)
        if len(matches) > index:
            return matches[index]
        else:
            return None

    def extract(self):
        return [x.extract() for x in self]

    def extract1(self, index=0):
        """Return a unicode string of the content referenced by the first
        XPathSelector of the list, or None if the list is empty"""
        results = self.extract()
        try:
            return results[index]
        except IndexError:
            return None

    def extract_unquoted(self):
        return [x.extract_unquoted() for x in self]

    @deprecated(use_instead='XPathSelectorList.select')
    def x(self, xpath):
        return self.select(xpath)
