import numpy as np

def build_dataset(n_samples=50, n_features=200, n_informative_features=10, n_targets=1, random_state=np.random.RandomState(0)):
    if n_targets > 1:
        w = random_state.randn(n_features, n_targets)
    else:
        w = random_state.randn(n_features)
        w[:n_informative_features] = 0
    X = random_state.randn(n_samples, n_features)
    y = np.dot(X, w)
    X_test = random_state.randn(n_samples, n_features)
    y_test = np.dot(X_test, w)
    return X, y, X_test, y_test
