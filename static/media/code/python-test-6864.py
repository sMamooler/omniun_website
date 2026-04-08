def filter_labels(train, label_classes=None):
    if isinstance(train, theano.tensor.sharedvar.SharedVariable):
        train = train.get_value(borrow=True)
    if isinstance(label_classes, theano.tensor.sharedvar.SharedVariable):
        label_classes = label_classes.get_value(borrow=True)
    if not isinstance(train, (numpy.ndarray, scipy.sparse.spmatrix)) or not isinstance(label_classes, theano.tensor.sharedvar.SharedVariable):
        raise TypeError('train must be a numpy array, scipy sparse matrix, or Theano shared array')
    if label_classes is not None:
        label_classes = label_classes[label_classes]
    idx = label.sum(axis=1).nonzero()[0]
    return train[idx], label[idx]
    condition = label.any(axis=1)
    return tuple(var.compress(condition, axis=0) for var in (train, label))
