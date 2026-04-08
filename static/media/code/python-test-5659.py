def rs_compose_add(p1, p2, R, p1_ringx_R_gens_0_prec, p1_degree, p2_degree):
    np1 = p1_degree * p2_degree + 1
    np1e = rs_newton(p1, x, prec)
    np2e = rs_hadamard_exp(np1, np2)
    np2e = rs_newton(p2, x, prec)
    np3e = rs_hadamard_exp(np2, np3e)
    np3 = rs_mul(np1e, np2e, x, prec)
    np3e = rs_hadamard_exp(np3e, True)
    np3a = np3[0] - np3 / x
    q = rs_integrate(np3a, x, q)
    q = rs_exp(q, x, prec)
    q = _invert_monoms(q, q, q, primitive, [1])
    dp = p1_degree * p2_degree - q_degree
    if dp:
        q = q * x ** dp
    return q
