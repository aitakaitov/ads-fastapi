import copy
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


# def xpath_soup(element):
#     # type: (typing.Union[bs4.element.Tag, bs4.element.NavigableString]) -> str
#     """
#     Generate xpath from BeautifulSoup4 element.
#     :param element: BeautifulSoup4 element.
#     :type element: bs4.element.Tag or bs4.element.NavigableString
#     :return: xpath as string
#     :rtype: str
#     Usage
#     -----
#     >>> import bs4
#     >>> html = (
#     ...     '<html><head><title>title</title></head>'
#     ...     '<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>'
#     ...     )
#     >>> soup = bs4.BeautifulSoup(html, 'html.parser')
#     >>> xpath_soup(soup.html.body.p.i)
#     '/html/body/p[1]/i'
#     >>> import bs4
#     >>> xml = '<doc><elm/><elm/></doc>'
#     >>> soup = bs4.BeautifulSoup(xml, 'lxml-xml')
#     >>> xpath_soup(soup.doc.elm.next_sibling)
#     '/doc/elm[2]'
#     """
#     components = []
#     child = element if element.name else element.parent
#     for parent in child.parents:  # type: bs4.element.Tag
#         siblings = parent.find_all(child.name, recursive=False)
#         components.append(
#             child.name if 1 == len(siblings) else '%s[%d]' % (
#                 child.name,
#                 next(i for i, s in enumerate(siblings, 1) if s is child)
#                 )
#             )
#         child = parent
#     components.reverse()
#     return '/%s' % '/'.join(components)


def _clean_text(text):
    return re.sub('\\s+', ' ', text)

# list of tags we extract text from
ALLOWED_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']

def clone_and_clean_element(element: bs4.Tag) -> bs4.Tag:
    """
    Makes a deepcopy of an element, then removes any element with name in ALLOWED_TAGS from it. 
    Returns the modified element. Does not modify the passed element.
    """
    element_copy = copy.deepcopy(element)
    tags_to_remove = element_copy.find_all(ALLOWED_TAGS)
    for tag in tags_to_remove:
        try:
            tag.decompose()
        except Exception:
            pass
    return element_copy

# def get_text_recursive(element, texts = []):
#     for child in element.children:
#         if isinstance(child, bs4.NavigableString):
#             string = str(child)
#             texts.append(string)
#         elif child.name is not None:
#             get_token_sequence_from_element(child, texts)    
    
#     return texts

def process_for_extraction(html: str) -> dict[str, object]:
    """
    Parses the HTML.

    Finds all elements with name in ALLOWED_TAGS, removes multiplicity (e.g. an <ul> element containing another <ul> element will return the entire text only once,
    but possibly split across multiple parts).

    Creates element-ID mapping and ID-text mapping. The text is extracted from cleaned elements. 
    """
    
    # 'html.parser' is required as it keeps most of the HTML structure without modifying elements
    soup = bs4.BeautifulSoup(html, 'html.parser')
    relevant_elements = soup.find_all(ALLOWED_TAGS)

    # remove occurences of ALLOWED_TAGS elements in each element - to prevent multiplicity 
    modified_elements = [clone_and_clean_element(el) for el in relevant_elements]
    
    # create ID - element mappings
    id_to_modified_element: dict[int, bs4.Tag] = {
        i: el for i, el in enumerate(modified_elements)
    } 

    id_to_element: dict[int, bs4.Tag] = {
        i: el for i, el in enumerate(relevant_elements)
    }
    
    # construct objects to pass to Extractor
    id_text_list: list[dict[str, object]] = [
        {
            'id': i,
            'text': _clean_text(el.get_text()),
            'tag': el.name
        }
        for i, el in id_to_modified_element.items()
    ]

    return {
        'soup': soup,
        'texts': id_text_list,
        'id_element_map': id_to_element,
        'id_modified_element_map': id_to_modified_element
    }


def get_token_sequence_from_element(element, element_tokens = [], token_elements = []):
    for child in element.children:
        if isinstance(child, bs4.NavigableString):
            string = str(child)
            split = string.split()
            for t in split:
                if t.isspace() or t == '' or t == '\n':
                    continue
                if not t[-1].isalnum():
                    element_tokens.append(t[:-1])
                    element_tokens.append(t[-1])
                    token_elements.append(child)
                    token_elements.append(child)
                else:
                    element_tokens.append(t)
                    token_elements.append(child)
        elif child.name is not None:
            get_token_sequence_from_element(child, element_tokens, token_elements)    
    
    return element_tokens, token_elements


def get_range_in_elements(soup, elements, tokens, k=4) -> dict[str, bs4.Tag | int]:
    """
    Finds the start and end of a sequence of tokens in a list of elements.

    Finding the starting and ending offsets is based on k first/last tokens.

    Wraps the starting and ending bs4.NavigableString elements in spans and returns the wrappers.

    The offsets are in characters.
    """
    
    # tokenized element texts
    element_tokens = []
    # a corresponding element for each token (element_tokens[i] is from element token_elements[i])
    token_elements = []

    # for each element, extract tokenized text and concatenate them
    for element in elements:
        t, e = get_token_sequence_from_element(element)
        element_tokens.extend(t)
        token_elements.extend(e)

    # find the best match by sliding the target tokens over the extracted element tokens
    tokens_set = set(tokens)
    max_overlap_index = 0
    max_jaccard = 0
    for i in range(0, len(element_tokens) - len(tokens)):
        temp_set = set(element_tokens[i:i + len(tokens)])
        jacc = len(temp_set.intersection(tokens_set)) / len(temp_set.union(tokens_set))
        if jacc > max_jaccard:
            max_overlap_index = i
            max_jaccard = jacc
            if jacc == 1.0:
                # exit on exact match
                break
    
    # wrap the starting bs4.NavigableString element in a span
    start_wrapper = soup.new_tag('span')
    token_elements[max_overlap_index].insert_before(start_wrapper)
    start_wrapper.append(token_elements[max_overlap_index])

    # if the start and end are in the same elements, do nothing
    if token_elements[max_overlap_index] == token_elements[max_overlap_index + len(tokens)]:
        end_wrapper = start_wrapper
    else:
        # otherwise wrap the ending element
        end_wrapper = soup.new_tag('span')
        token_elements[max_overlap_index + len(tokens)].insert_before(end_wrapper)
        end_wrapper.append(token_elements[max_overlap_index + len(tokens)])

    # find the starting offset in the starting element
    current_k = k
    starting_offset = None
    while True:
        for i in range(current_k):
            if i == 0:
                start_text = tokens[i]
            elif tokens[i].isalnum():
                start_text += ' ' + tokens[i]
            else:
                start_text += tokens[i]

        try:
            starting_offset = start_wrapper.get_text().index(start_text)
            break
        except Exception:
            # if K is too high, lower it
            if current_k > 1:
                current_k -= 1
                continue
            else:
                starting_offset = -1
                break
        
    # do the same for the ending element
    current_k = k
    ending_offset = None
    while True:
        end_text = ''
        for i in range(current_k):
            if i == 0:
                end_text = tokens[-current_k]
            elif tokens[-current_k + i].isalnum():
                end_text += ' ' + tokens[-current_k + i]
            else:
                end_text += tokens[-current_k + i]
        
        try:
            ending_offset = end_wrapper.get_text().index(end_text) + len(end_text)
            break
        except Exception:
            if current_k > 1:
                current_k -= 1
                continue
            else:
                ending_offset = -1
                break
    
    # if we did not find the starting or ending offsets, set them to the start/end of the respective element
    if starting_offset == -1:
        starting_offset = 0
    if ending_offset == -1:
        ending_offset = len(end_wrapper.get_text()) - 1
    
    return {
        'start_element': start_wrapper,
        'start_offset': starting_offset,
        'end_element': end_wrapper,
        'end_offset': ending_offset
    }


def mark_elements(id2element, entities, soup) -> list[dict[str, object]]:
    """
    Given ID-element mapping and a list of extracted entities, finds the start and end of each appearance of each entity.

    Appearance is identified by a starting element and offset + ending element and offset

    Soup is passed by reference and modified
    """

    entity_data = []
    for entity in entities:
        # create entity dict
        e_data = {
            'type': entity['type'],
            'short_text': entity['short_text']
        }
        # find all appearances
        appearances = []
        for idx, appearance in enumerate(entity['appearances']):
            # find the start and end elements + offsets based on context tokens of the appearance
            data = get_range_in_elements(soup, [id2element[id] for id in appearance['ids']], appearance['context_tokens'])

            # modify the HTML by adding an attribute to the starting and ending elements
            # note that 'data' contains reference to the starting and ending element
            same_entity = data['start_element'] == data['end_element'] 
            if same_entity:
                # if it starts and ends with the same entity, we need only one element
                data['start_element'][ELEMENT_ID_ATTRIBUTE] = entity['type'] + f'-start-{idx}'
            else:
                # otherwise, we need to mark start and end 
                data['start_element'][ELEMENT_ID_ATTRIBUTE] = entity['type'] + f'-start-{idx}'
                data['end_element'][ELEMENT_ID_ATTRIBUTE] = entity['type'] + f'-end-{idx}'

            appearances.append({
                'attribute': ELEMENT_ID_ATTRIBUTE,
                'attr_start_value': entity['type'] + f'-start-{idx}',
                'attr_end_value': entity['type'] + f'-end-{idx}' if not same_entity else entity['type'] + f'-start-{idx}',
                'start_offset': data['start_offset'],
                'end_offset': data['end_offset']
            })
        e_data['appearances'] = appearances
        entity_data.append(e_data)

    return entity_data    

def analyze_cookies(html):
    # get elements and texts to pass to the extractor
    processed = process_for_extraction(html)

    # TODO pass the element texts to Extractor
    
    dummy_extracted_entities = [
        {
            'short_text': 'sit',
            'type': 'entity one',
            'appearances': [
                {
                    'ids': [0, 1],
                    'context_tokens': ['Lorem', 'ipsum', 'dolor', 'sit', 'amet'],
                },
                {
                    'ids': [1, 2],
                    'context_tokens': ['Nullam', 'eget', 'nisl', '.', 'Nullam', 'eget', 'nisl', '.'],
                }
            ],
        }
    ]

    # modify the HTML to allow for text highlighting
    entity_data = mark_elements(processed['id_element_map'], dummy_extracted_entities, processed['soup'])
    modified_html = processed['soup'].prettify()

    return modified_html, entity_data


if __name__ == '__main__':
    test_html = """
    <html>
        <body>
            <p>
                <h1>Lorem ipsum dolor</h1> sit amet, consectetuer adipiscing elit. Etiam quis quam. Duis viverra diam non justo. Mauris dictum facilisis augue.
            </p>
            <p>
                Fusce dui leo, imperdiet in, aliquam sit amet, feugiat eu, orci. Nullam eget nisl.
            </p>
            <p>
                Nullam eget nisl. <i>Nemo enim ipsam</i> voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.
            </p>
            <ul>
                <li>
                    <ul>
                        <li> something something 1</li>
                        <li> something something 2</li>
                    </ul>
                    <li> something something asasdasdasd</li>
                </li>
            </ul>
        </body>
    </html>
    """
    #with open('cookies/https_autocentrum_votice_skoda_auto_cz_company_company.html', 'r', encoding='utf-8') as f:
    #    test_html = f.read()
    #from bs4.diagnose import diagnose
    #diagnose(test_html)
    #exit() 

    result = analyze_cookies(test_html)
    print(result[0])
    print(result[1])