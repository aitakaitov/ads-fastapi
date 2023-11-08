import numpy
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'


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