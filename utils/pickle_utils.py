import pickle

def to_binary_string(obj):
    return pickle.dumps(obj)

def from_binary_string(string):
    return pickle.loads(string)