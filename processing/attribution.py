import config
from processing.attribution_utils import *
from processing.html_utils import html_to_plaintext
import nltk
import torch

from processing.model_utils import split_into_blocks, get_cls_sep, get_embeddings

device = 'cuda' if torch.cuda.is_available() else 'cpu'
logit_fn = torch.nn.Softmax(dim=1)


def rationales(html, model, tokenizer):
    text = html_to_plaintext(html, keep_paragraphs_only=True, trim_start=config.TRIM_LENGTH,
                             lowercase=False, merge_whitespaces=False)
    result = generate_rationales(text, model, tokenizer)
    # TODO postprocess and prettify result
    return result


def generate_rationales(text, model, tokenizer):
    cls_token_index, sep_token_index = get_cls_sep(tokenizer)
    embeddings = get_embeddings(model)

    sentences = nltk.sent_tokenize(text)
    encoded = tokenizer(sentences, is_split_into_words=True, add_special_tokens=False)
    blocks = split_into_blocks(encoded, cls_token_index, sep_token_index, 510)

    if len(blocks) == 0:
        return None

    attrs_complete = []
    for block in blocks:
        input_embeds = torch.unsqueeze(torch.index_select(embeddings, 0, torch.squeeze(block['input_ids']).to(device)), 0).requires_grad_(True).to(device)
        attention_mask = block['attention_mask'].to(device)

        attrs = ig_attributions(input_embeds, attention_mask, 1, 0 * input_embeds, model, logit_fn, steps=config.IG_SAMPLES)
        attrs_complete.extend(format_attrs(attrs))

    attributions = filter_attributions(attrs_complete, config.ATTRS_TOP_PERCENT)
    relevant_sentence_ids = extract_relevant_sentences(attributions, encoded.word_ids(), config.FRACTION_TOKENS_HIT, config.RECURSE_MAX_DEPTH)

    return [sentences[i] for i in relevant_sentence_ids]
