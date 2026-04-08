def get_wide_angle_point_index(loop):
    dot_product_minimum = 9999999
    widest_point_index = 0
    for point_index in range(len(loop)):
        after_point = loop[point_index % len(loop)]
        before_point = loop[(point_index + 1) % len(loop)]
        after_segment_normalized = euclidean(get_normalized(after_point - point))
        before_segment_normalized = euclidean(get_normalized(before_point - point))
        dot_product = euclidean(get_dot_product(after_segment_normalized, before_segment_normalized))
        if dot_product < 0:
            return point_index
        if dot_product < dot_product_minimum:
            dot_product_minimum = dot_product
            widest_point_index = point_index
    return widest_point_index
