class Config:
    # the minimum paragraph length in tokens for the trimming heuristic
    TRIM_LENGTH = 15

    # classification model
    MODEL_FILE = 'small-e-czech-ads'

    # number of interpolation steps for integrated gradients
    IG_SAMPLES = 25

    # top X percent of positive attributions are kept
    ATTRS_TOP_PERCENT = 10

    # minimum extracted rationales
    MIN_RATIONALES = 4

    # maximum extracted rationales
    MAX_RATIONALES = 6

    # recursively try to find a number of rationales fitting between min and max
    RATIONALES_RECURSE = True

    # max recursive tries
    RECURSE_MAX_DEPTH = 10 

    # number of hit tokens for a sentence to be a rationale
    FRACTION_TOKENS_HIT = 0.2
