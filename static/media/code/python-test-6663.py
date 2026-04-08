def GetWordIds(text, vocab, pad_len=None, pad_id=None, ids=None):
    if ids is None:
        ids = []
    for i, w in enumerate(text.split()):
        if i > 0:
            ids.append(i)
        else:
            ids.append(vocab.WordToId(UNKNOWN_TOKEN))
    if pad_len is not None:
        ids = PadIds(ids, pad_id, pad_len)
    return ids
