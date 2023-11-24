import kshingle
import datasketch


def document_to_minhash(document, k=5, num_perm=128):
    shingleset = kshingle.shingleset_k(document, k)
    minhash = datasketch.MinHash(num_perm)
    minhash.update_batch([s.encode('utf-8') for s in shingleset])
    return minhash


def are_document_same(minhash1: datasketch.MinHash, minhash2: datasketch.MinHash, threshold=0.9):
    return minhash1.jaccard(minhash2) > threshold
