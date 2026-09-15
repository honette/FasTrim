from fastrim.geom import box_size, parse_aspect, selection_from_drag, snap_box


def test_parse_aspect() -> None:
    assert parse_aspect("16:9") == (16, 9)
    assert parse_aspect("1:1") == (1, 1)
    assert parse_aspect("nope") is None


def test_drag_plain() -> None:
    box = selection_from_drag(10, 20, 110, 80, 200, 200)
    assert box == (10, 20, 110, 80)
    assert box_size(box) == (100, 60)


def test_drag_clamps_to_image() -> None:
    box = selection_from_drag(-10, -10, 500, 500, 100, 80)
    assert box == (0, 0, 100, 80)


def test_aspect_16_9() -> None:
    box = selection_from_drag(0, 0, 160, 10, 1000, 1000, aspect=(16, 9))
    left, top, right, bottom = box
    assert left == 0 and top == 0
    assert right - left == 160
    assert bottom - top == 90


def test_grid_snap() -> None:
    box = selection_from_drag(3, 3, 41, 41, 200, 200, grid=10)
    assert box == (0, 0, 40, 40)


def test_snap_box_empty_grows() -> None:
    assert snap_box(10, 10, 10, 10, 8, 100, 100)[2] > 10
