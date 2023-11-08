import torch
from processing.html_utils import html_to_plaintext

device = 'cuda' if torch.cuda.is_available() else 'cpu'


def classify(html, model, tokenizer):
    cls_token_index = tokenizer.cls_token_id
    sep_token_index = tokenizer.sep_token_id

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
    return sum(predictions) >= 1


def split_into_blocks(encoding, cls_token_index, sep_token_index, block_size):
    length = len(encoding.input_ids)
    block_count = int(length / block_size)
    if length % block_size != 0:
        block_count += 1

    blocks = []
    for i in range(block_count):
        if i == block_count - 1:
            input_ids = [cls_token_index]
            input_ids.extend(encoding.input_ids[i * block_size:])
            input_ids.append(sep_token_index)
            blocks.append({
                'input_ids': torch.tensor([input_ids], dtype=torch.int),
                'attention_mask': torch.tensor([[1 for _ in range(len(input_ids))]], dtype=torch.int)
            })
        else:
            input_ids = [cls_token_index]
            input_ids.extend(encoding.input_ids[i * block_size: (i + 1) * block_size])
            input_ids.append(sep_token_index)
            blocks.append({
                'input_ids': torch.tensor([input_ids], dtype=torch.int),
                'attention_mask': torch.tensor([[1 for _ in range(len(input_ids))]], dtype=torch.int)
            })

    return blocks
