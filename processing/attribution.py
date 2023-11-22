from processing.attribution_utils import *
from processing.html_utils import html_to_plaintext
import nltk
import torch
import re
from api.config import Config

from processing.model_utils import split_into_blocks, get_cls_sep, get_embeddings

device = 'cuda' if torch.cuda.is_available() else 'cpu'
logit_fn = torch.nn.Softmax(dim=1)
regexp = re.compile('\\s\\s\\s+')

def rationales(html, model, tokenizer):
    text = html_to_plaintext(html, keep_paragraphs_only=True, trim_start=Config.TRIM_LENGTH,
                             lowercase=False, merge_whitespaces=False)
    result = generate_rationales(text, model, tokenizer)
    result = postprocess_rationales(result)
    return result


def generate_rationales(text, model,  tokenizer):
    cls_token_index, sep_token_index = get_cls_sep(tokenizer)
    embeddings = get_embeddings(model)

    sentences = nltk.sent_tokenize(text)
    # remove short and part-empty sentences from the text
    new_sentences = []
    for s in sentences:
        if not regexp.search(s):
            new_sentences.append(s)
    sentences = new_sentences

    sentences = [re.sub('\\s+', ' ', text) for text in sentences]
    encoded = tokenizer(sentences, is_split_into_words=True, add_special_tokens=False)
    blocks = split_into_blocks(encoded, cls_token_index, sep_token_index, 510)

    if len(blocks) == 0:
        return None

    attrs_complete = []
    for block in blocks:
        input_embeds = torch.unsqueeze(torch.index_select(embeddings, 0, torch.squeeze(block['input_ids']).to(device)), 0).requires_grad_(True).to(device)
        attention_mask = block['attention_mask'].to(device)

        attrs = ig_attributions(input_embeds, attention_mask, 1, 0 * input_embeds, model, logit_fn, steps=Config.IG_SAMPLES)
        attrs_complete.extend(format_attrs(attrs))

    attributions = filter_attributions(attrs_complete, Config.ATTRS_TOP_PERCENT)
    relevant_sentence_ids = extract_relevant_sentences(attributions, encoded.word_ids(), Config.FRACTION_TOKENS_HIT, Config.RECURSE_MAX_DEPTH)

    return [sentences[i] for i in relevant_sentence_ids]


def postprocess_rationales(rationales):
    return rationales


def postprocess_sentences(sentences): 
    new_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        split = re.split('\\s\\s+', sentence)
        if len(split) == 1:
            new_sentences.append(sentence)
        else:
            for split_sentence in split:
                if len(split_sentence.split()) > 1:
                    new_sentences.append(split_sentence)

    return new_sentences