import kshingle
import datasketch
from utils.html_utils import html_to_plaintext
import xxhash


def hash_f(d):
    return xxhash.xxh32(d).intdigest()


def document_to_minhash(document, k=5, num_perm=512):
    text = html_to_plaintext(document, trim_start=0)
    shingleset = kshingle.shingleset_k(text, k)
    minhash = datasketch.MinHash(num_perm, hashfunc=hash_f)
    minhash.update_batch([s.encode('utf-8') for s in shingleset])
    return minhash




def are_documents_same(minhash1: datasketch.MinHash, minhash2: datasketch.MinHash, threshold=0.95):
    print(f'> {threshold} => are same')
    print(minhash1.jaccard(minhash2))
    return minhash1.jaccard(minhash2) > threshold

