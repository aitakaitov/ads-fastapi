import torch
from utils.html_utils import html_to_plaintext
from utils.document_similarity import document_to_minhash
from advertisement_processing.model_utils import get_cls_sep, split_into_blocks

device = 'cuda' if torch.cuda.is_available() else 'cpu'


def classify(html, model, tokenizer):
    cls_token_index, sep_token_index = get_cls_sep(tokenizer)

    text = html_to_plaintext(html, lowercase=False)

    encoded = tokenizer(text, add_special_tokens=False)

    blocks = split_into_blocks(encoded, cls_token_index, sep_token_index, 510)
    if len(blocks) == 0:
        return None

    predictions = []
    for block in blocks:
        logits = model(input_ids=block['input_ids'].to(device), attention_mask=block['attention_mask'].to(device)).logits
        pred = int(torch.argmax(logits, dim=1))
        predictions.append(pred)

    print(predictions)
    return sum(predictions) >= 1, document_to_minhash(text)
