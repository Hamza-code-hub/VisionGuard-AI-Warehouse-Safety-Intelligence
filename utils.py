from vision.zones import bottom_center


def calculate_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def get_box_center(box):
    x1, y1, x2, y2 = box
    return (
        int((x1 + x2) / 2),
        int((y1 + y2) / 2),
    )


__all__ = ["calculate_distance", "get_box_center", "bottom_center"]
