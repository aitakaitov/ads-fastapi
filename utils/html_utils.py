from bs4 import BeautifulSoup, NavigableString
import re
import bleach


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


allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
def html_to_text_keep_p_h_tags(html, add_outside_to_par=False):
    cleaned = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=[],
        strip=True
    )

    text = cleaned
    text = re.sub('\\n+', '\n', text)
    text = re.sub('\\t+', '\t', text)
    text = re.sub('<p>', '\nPPPPPS\n', text)
    text = re.sub('</p>', '\nPPPPPE\n', text)

    for tag in allowed_tags[1:]:
        text = re.sub(f'<{tag}>', '\nHHHHHS\n', text)
        text = re.sub(f'</{tag}>', '\nHHHHHE\n', text)
    
    if add_outside_to_par:
        lines = text.split('\n')

        new_lines = []
        segment_lines = []
        found_begin = False
        for line in lines:
            if "PPPPPS" in line:
                if len(segment_lines) == 0 or not found_begin:
                    segment_lines.append(line)
                    found_begin = True

                else:
                    new_lines.extend(segment_lines)
                    new_lines.append("PPPPPE")
                    segment_lines = ["PPPPPS"]
                    found_begin = False

            elif "PPPPPE" in line:
                continue
            else:
                segment_lines.append(line)

        if len(segment_lines) != 0:
            if segment_lines[-1] != "PPPPPE":
                segment_lines.append("PPPPPE")
            new_lines.extend(segment_lines)
            

        text = '\n'.join(new_lines)

    return text


if __name__ == '__main__':
    import os

    for file in os.listdir('cookies'):
        with open(f'cookies/{file}', 'r', encoding='utf-8') as f:
            html = f.read()

        cleaned = html_to_text_keep_p_h_tags(html)
        
        with open(f'cookies/{file}.processed', 'w+', encoding='utf-8') as f:
            f.write(cleaned)    