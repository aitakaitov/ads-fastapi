import numpy
import torch

import config

device = 'cuda' if torch.cuda.is_available() else 'cpu'
import numpy as np


def gradient_attributions(inputs_embeds, attention_mask, target_idx, model, logit_fn, x_inputs=False):
    """
    Vanilla Gradients
    :param inputs_embeds: input embeddings
    :param attention_mask: attention mask
    :param target_idx: target index in the model output
    :param model: model
    :param x_inputs: multiply by inputs
    :return:
    """
    inputs_embeds = inputs_embeds.requires_grad_(True).to(device)
    attention_mask = attention_mask.to(device)

    model.zero_grad()
    output = logit_fn(model(inputs_embeds=inputs_embeds, attention_mask=attention_mask).logits)[:, target_idx]
    grads = torch.autograd.grad(output, inputs_embeds)[0]

    if x_inputs:
        grads = grads * inputs_embeds

    return grads


def ig_attributions(inputs_embeds, attention_mask, target_idx, baseline, model, logit_fn, steps=50, method='trapezoid'):
    """
    Generates Integrated Gradients attributions for a sample
    :param inputs_embeds: input embeddings
    :param attention_mask: attention mask
    :param target_idx: taget index in the model output
    :param baseline: what baseline to use as a starting point for the interpolation
    :param model: model
    :param steps: number of interpolation steps
    :return:
    """

    if method == 'trapezoid':
        interpolated_samples = _ig_interpolate_samples(baseline, inputs_embeds, steps)
        gradients = torch.tensor([])
        for sample in interpolated_samples:
            sample = sample.to(device)
            grads = gradient_attributions(sample, attention_mask, target_idx, model, logit_fn).to('cpu')
            gradients = torch.cat((gradients, grads), dim=0)

        gradients = (gradients[:-1] + gradients[1:]) / 2.0
        average_gradients = torch.mean(gradients, dim=0)
        integrated_gradients = (inputs_embeds - baseline) * average_gradients.to(device)

        return integrated_gradients
    else:
        # scale the [-1, 1] interval to [0, 1]
        weights = list(0.5 * numpy.polynomial.legendre.leggauss(steps)[1])
        alphas = list(0.5 * (1 + numpy.polynomial.legendre.leggauss(steps)[0]))

        interpolated_samples = [(baseline + alpha * (inputs_embeds - baseline)).to('cpu') for alpha in alphas]
        total_grads = 0
        for i, sample in enumerate(interpolated_samples):
            sample = sample.to(device)
            grads = gradient_attributions(sample, attention_mask, target_idx, model, logit_fn).to('cpu')
            total_grads += grads * weights[i]

        integrated_gradients = (inputs_embeds - baseline) * total_grads.to(device)
        return integrated_gradients


def _ig_interpolate_samples(baseline, target, steps):
    return [(baseline + (float(i) / steps) * (target - baseline)).to('cpu') for i in range(0, steps + 1)]


def format_attrs(attrs):
    if len(attrs.shape) == 3:
        attrs = torch.mean(attrs, dim=2)

    if len(attrs.shape) == 2 and attrs.shape[0] == 1:
        attrs = torch.squeeze(attrs)

    attrs_list = attrs.tolist()

    return attrs_list[1:len(attrs) - 1]  # leave out cls and sep


def embed_input_ids(input_ids, embeddings):
    input_embeds = torch.unsqueeze(torch.index_select(embeddings, 0, torch.squeeze(input_ids).to(device)), 0).requires_grad_(True).to(device)
    return input_embeds


def filter_attributions(attributions, top_percent):
    attributions = [0 if a < 0 else a for a in attributions]
    lower_percentile = np.percentile(attributions, 100 - top_percent)
    attributions = [0 if a < lower_percentile else a for a in attributions]

    return attributions


def extract_relevant_sentences(attributions, word_ids, fraction_hit, depth):
    print(depth)
    sentence_count = len(list(set(word_ids)))

    sentence_lengths = [0 for _ in range(sentence_count)]
    sentence_hits = [0 for _ in range(sentence_count)]
    for sentence_id in range(sentence_count):
        for i in range(len(word_ids)):
            if word_ids[i] == sentence_id:
                sentence_lengths[sentence_id] += 1
                if attributions[i] != 0:
                    sentence_hits[sentence_id] += 1

    rationale_sentences = []
    for i, (length, hits) in enumerate(zip(sentence_lengths, sentence_hits)):
        if hits / length >= fraction_hit:
            rationale_sentences.append(i)

    if config.RATIONALES_RECURSE:
        if depth == -1:
            return None
        if len(rationale_sentences) > config.MAX_RATIONALES:
            new = extract_relevant_sentences(attributions, word_ids, fraction_hit + 0.025, depth - 1)
        elif len(rationale_sentences) < config.MIN_RATIONALES:
            new = extract_relevant_sentences(attributions, word_ids, fraction_hit - 0.025, depth - 1)
        else:
            return rationale_sentences

        if not new:
            return rationale_sentences
        else:
            return new

    return rationale_sentences
