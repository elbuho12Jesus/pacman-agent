def get_possible_movements(game_state, pos):
    x, y = pos
    up = (x, y+1); down = (x, y-1); left = (x-1, y); right = (x+1, y)
    get_possible_movements = {}

    if not game_state.has_wall(up[0], up[1]):
        get_possible_movements[up] = 'North'

    if not game_state.has_wall(down[0], down[1]):
        get_possible_movements[down] = 'South'

    if not game_state.has_wall(left[0], left[1]):
        get_possible_movements[left] = 'West'

    if not game_state.has_wall(right[0], right[1]):
        get_possible_movements[right] = 'East'

    return get_possible_movements

def get_home_4_border(game_state, red):
    width = game_state.data.layout.width
    height = game_state.data.layout.height
    halfway = width // 2
    y1 = 0
    y2 = height - 1
    redx1 = 0
    redx2 = halfway - 1
    bluex1 = halfway
    bluex2 = width - 1
    if red:
        return (redx1, redx2, y1, y2)
    else:
        return (bluex1, bluex2, y1, y2)