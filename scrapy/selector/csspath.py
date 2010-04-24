import re

def css2xpath(css_xpath): # {{{
    '''
    Convert the css and xpath mixture to xpath

    >>> css2xpath('span')
    '//span'
    >>> css2xpath('div span')
    '//div//span'
    >>> css2xpath('div > span')
    '//div/span'
    >>> css2xpath('div>span')
    '//div/span'
    >>> css2xpath('span.red')
    '//span[contains(concat(" ", @class, " "), " red ")]'
    >>> css2xpath('.red')
    '//*[contains(concat(" ", @class, " "), " red ")]'
    >>> css2xpath('div#red')
    '//div[@id="red"]'
    >>> css2xpath('#red')
    '//*[@id="red"]'
    >>> css2xpath('//h1 span/b')
    '//h1//span/b'
    >>> css2xpath('//span[contains(concat(" ", @class, " "), " red ")]')
    '//span[contains(concat(" ", @class, " "), " red ")]'
    >>> css2xpath('./span')
    './span'
    >>> css2xpath('@href')
    '@href'
    '''

    parts = re.split('(/+)', css_xpath)
    parts = filter(lambda x: x, parts)
    new_parts = []
    if is_css_path(parts[0]):
        new_parts.append('//')

    for part in parts:
        if not part or re.match('/+', part):
            new_part = part
        elif part:
            new_part = term(part)
        if new_part:
            new_parts.append(new_part)


    return ''.join(new_parts)
# end def }}}

def is_css_path(path):
    yes = re.search(r'[.#]?[\w]+', path) and re.match(r'[ >\w#.-]+$', path)
    return yes

def term(css_or_xpath): # {{{
    if not is_css_path(css_or_xpath): # skip non css path
        return css_or_xpath

    parts = re.split('([ >]+)', css_or_xpath)
    parts = filter(lambda x: x, parts)
    new_parts = []
    for part in parts:
        if re.match('^ +$', part):
            new_part = '//'
        elif re.match('[ >]+', part):
            new_part = '/'
        else:
            new_part = operand(part)
        new_parts.append(new_part)

    return ''.join(new_parts)
# end def }}}

def operand(css_xpath): # {{{
    css_xpath = css_xpath.strip()
    name2regex = {
            'p.red': r'([-\w]+)\.([-\w]+)',
            'p#red': r'([-\w]+)#([-\w]+)',
            '.red': r'\.([-\w]+)',
            '#red': r'#([-\w]+)',
            }
    for name, regex in name2regex.iteritems():
        m = re.match(regex, css_xpath)
        if not m:
            continue
        class_template = '%s[contains(concat(" ", @class, " "), " %s ")]'
        id_template = '%s[@id="%s"]'
        if name == 'p.red':
            p, red = m.group(1, 2)
            res = class_template % m.group(1, 2)
        elif name == '.red':
            res = class_template % ('*', m.group(1))
        elif name == 'p#red':
            res = id_template % m.group(1, 2)
        else: # '#red'
            res = id_template % ('*', m.group(1))

        return res
    # end for

    return css_xpath
# end def }}}

if __name__ == "__main__":
    import doctest
    doctest.testmod()
