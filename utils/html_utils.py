from bs4 import BeautifulSoup, NavigableString
import re
import bleach
import bs4
import urllib3


ELEMENT_ID_ATTRIBUTE = 'vilda-element-id'


def filter_html(soup: BeautifulSoup):
    """
    Filters tags and their contents from html
    :param soup: Parsed html
    :return: Filtered html
    """
    scripts = soup.find_all("script")
    for tag in scripts:
        tag.decompose()

    iframes = soup.find_all("iframe")
    for tag in iframes:
        tag.decompose()

    link_tags = soup.find_all("link")
    for tag in link_tags:
        tag.decompose()

    metas = soup.find_all("meta")
    for tag in metas:
        tag.decompose()

    styles = soup.find_all("style")
    for tag in styles:
        tag.decompose()

    return soup


def process_contents(tag, string_list):
    for item in tag.contents:
        if isinstance(item, NavigableString):
            string_list.append(str(item))
        else:
            process_contents(item, string_list)


def keep_paragraphs(soup: BeautifulSoup):
    result_list = []

    p_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for p_tag in p_tags:
        process_contents(p_tag, result_list)

    text = '\n'.join(result_list)
    return re.sub('\n+', '\n', text)


def trim_text_start_length(text, trim_length):
    tag_texts = text.split('\n')
    start = -1
    for i, tag in enumerate(tag_texts):
        if len(tag.split()) > trim_length:
            start = i
            break

    new_text = ''
    for i in range(start, len(tag_texts)):
        new_text += tag_texts[i]

    return new_text


def html_to_plaintext(html, keep_paragraphs_only=False, trim_start=None, lowercase=True, merge_whitespaces=True):
    soup = BeautifulSoup(html, 'lxml')

    if keep_paragraphs_only:
        soup_text = keep_paragraphs(soup)
        if trim_start:
            soup_text = trim_text_start_length(soup_text, trim_start)
    else:
        soup_text = soup.get_text()

    if lowercase:
        soup_text = soup_text.lower()

    if merge_whitespaces:
        soup_text = re.sub('\\s+', ' ', soup_text)

    return soup_text


def xpath_soup(element):
    # type: (typing.Union[bs4.element.Tag, bs4.element.NavigableString]) -> str
    """
    Generate xpath from BeautifulSoup4 element.
    :param element: BeautifulSoup4 element.
    :type element: bs4.element.Tag or bs4.element.NavigableString
    :return: xpath as string
    :rtype: str
    Usage
    -----
    >>> import bs4
    >>> html = (
    ...     '<html><head><title>title</title></head>'
    ...     '<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>'
    ...     )
    >>> soup = bs4.BeautifulSoup(html, 'html.parser')
    >>> xpath_soup(soup.html.body.p.i)
    '/html/body/p[1]/i'
    >>> import bs4
    >>> xml = '<doc><elm/><elm/></doc>'
    >>> soup = bs4.BeautifulSoup(xml, 'lxml-xml')
    >>> xpath_soup(soup.doc.elm.next_sibling)
    '/doc/elm[2]'
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
                )
            )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def _clean_text(text):
    return re.sub('\\s+', ' ', text)


allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']
def process_for_extraction(html):
    soup = bs4.BeautifulSoup(html)
    relevant_elements = soup.find_all(allowed_tags)

    id_to_element = {
        i: el for i, el in enumerate(relevant_elements)
    }

    for i, el in id_to_element.items():
        el[ELEMENT_ID_ATTRIBUTE] = i
    
    id_text_list = [
        {
            'id': i,
            'text': _clean_text(el.get_text()),
            'tag': el.tag
        }
        for i, el in id_to_element.items()
    ]

    return {
        'soup': soup,
        'texts': id_text_list,
        'id_element_map': id_to_element 
    }


def download_html_from_url(url):
    response = urllib3.request.urlopen(url)
    content = response.read().decode('UTF-8')
    return content
