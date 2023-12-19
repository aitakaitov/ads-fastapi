import torch


def get_cls_sep(tokenizer):
    return tokenizer.cls_token_id, tokenizer.sep_token_id


def get_embeddings(model):
    return model.electra.base_model.embeddings.word_embeddings.weight.data


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