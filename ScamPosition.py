from functions import get_possible_movements
class ScamPosition(object):
    def __init__(self, game_state, isRed, mode, ReflexCaptureAgent):
        self.state = game_state
        self.red = isRed
        self.mode = mode
        self.width = game_state.data.layout.width
        self.height = game_state.data.layout.height
        self.Agent = ReflexCaptureAgent
        self.territory = self.get_territory()
        self.food = self.get_food()  # determine which territory we are interested in
        self.coord_info_map = {}

    def get_territory(self):
        if self.red:
            if self.mode == 'attack':
                return (range(self.width // 2, self.width-1), range(1, self.height-1))
            return (range(1, self.width // 2), range(1, self.height-1))
        else:
            if self.mode == 'attack':
                return (range(1, self.width // 2), range(1, self.height - 1))
            return (range(self.width // 2, self.width - 1), range(1, self.height - 1))
    
    def get_food(self):
        if self.mode == 'attack':
            return self.Agent.get_food(self, self.state)
        return self.Agent.get_food_you_are_defending(self, self.state)
    
    def get_dead_end_map(self):
        xrange, yrange = self.territory
        for x in xrange:
            for y in yrange:
                if not self.state.has_wall(x, y) and len(get_possible_movements(self.state, (x, y))) == 1:
                    self.coord_info_map[(x, y)] = {'end': True, 'path': False, 'begin': False, 'food': set()}
                    if self.food[x][y]:
                        self.coord_info_map[(x, y)]['food'].add((x, y))
        return self.coord_info_map
    
    def merge_info(self, pos, neighbours):
        for neighbour in neighbours:
            if neighbour not in self.coord_info_map:
                continue
            if self.coord_info_map[neighbour]['path'] or self.coord_info_map[neighbour]['end']:
                self.coord_info_map[neighbour]['begin'] = False
                self.coord_info_map[pos] = {'end': False, 'path': False, 'begin': False, 'food': set()}
                self.coord_info_map[pos]['food'] = self.coord_info_map[pos]['food'].union(self.coord_info_map[neighbour]['food'])
    
    def has_path_nearby(self, pos, neighbours):
        cnt = 0
        for neighbour in neighbours:
            if neighbour not in self.coord_info_map:
                continue
            if self.coord_info_map[neighbour]['path'] or self.coord_info_map[neighbour]['end']:
                cnt += 1
        if cnt == len(neighbours) - 1:
            self.merge_info(pos, neighbours)
            return True
        return False
    
    def is_path(self, pos, neighbours):        
        if len(neighbours) == 1:
            self.coord_info_map[pos] = {'end': False, 'path': False, 'begin': False, 'food': set()}
            return True        
        if len(neighbours) == 2 or len(neighbours) == 3:        
            if self.has_path_nearby(pos, neighbours):
                return True
        return False
    
    def get_next_pos(self, neighbours):
        for neighbour in neighbours:
            if neighbour not in self.coord_info_map:
                return neighbour
            
    def get_path_and_begin_map(self):
        coord_info_map = self.get_dead_end_map().copy()

        for pos in coord_info_map.keys():
            neighbours = list(get_possible_movements(self.state, pos).keys())  
            current_pos = pos      
            while not self.coord_info_map[current_pos]['begin']:
                next_pos = self.get_next_pos(neighbours)  
                if not next_pos:
                    break
                neighbours = list(get_possible_movements(self.state, next_pos).keys())
                neighbours.remove(current_pos)  

                if self.is_path(next_pos, neighbours):
                    self.coord_info_map[next_pos]['path'] = True
                    self.coord_info_map[next_pos]['food'] = self.coord_info_map[next_pos]['food'].union(self.coord_info_map[current_pos]['food'].copy())
                    if self.food[next_pos[0]][next_pos[1]]:
                        self.coord_info_map[next_pos]['food'].add(next_pos)
                    current_pos = next_pos
                else:
                    self.coord_info_map[current_pos]['begin'] = True
        return self.coord_info_map
    
    def get_info_set(self,type):
        coord_info_map = self.get_path_and_begin_map().copy()
        if type=='begin':
            type_set={}
        else:
            type_set = set()
        for coord, info in coord_info_map.items():
            if info[type]:
                if type=='begin':
                   type_set[coord]=info['food'] 
                else:
                    type_set.add(coord)
        return type_set    