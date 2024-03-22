# baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

import random
import util
from functions import get_home_4_border, get_possible_movements
from ScamPosition import ScamPosition
from captureAgents import CaptureAgent
from game import Directions
from game import Actions
from util import nearestPoint


#################
# Team creation #
#################

def create_team(first_index, second_index, is_red,
                first='OffensiveReflexAgent', second='DefensiveReflexAgent', num_training=0):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(first)(first_index), eval(second)(second_index)]


##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that choose score-maximizing actions
    """

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None        

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)        
        self.state = game_state
        self.width = game_state.data.layout.width
        self.height = game_state.data.layout.height
        self.home_border = self.get_list_border(self.state,"home")        
        self.enemy_border = self.get_list_border(self.state,"enemy")
        self.home_territory = self.get_territory("home")
        self.enemy_territory = self.get_territory("enemy")
        self.member_ID = self.get_member_ID(game_state)
        self.num_wander = 0
        self.is_in_begin_dead_end = False
        self.dead_end_begin_potion = None
        self.safe_pos = None
        self.attack_point = None
        self.is_changed_attack_point = False
        self.queue = util.Queue()
        self.escape_state = False
        self.cost = 0
        self.go_home_path = []
        self.is_dodging = False
        self.opponents = self.get_opponents(game_state)
        self.defending_capsule = self.get_capsules_you_are_defending(game_state)
        self.home_4_border = get_home_4_border(game_state, self.red)
        self.home_border_without_corner = self.get_home_border_without_corner(game_state)
        self.defense_path = []
        self.time = 0
        self.Maze_goal_pos = random.choice(self.home_border_without_corner)  #new add
        self.can_reverse = True
        self.last_position = None
        
    def specify_global_info(self, game_state):
        self.reward_map = {'attack': self.get_reward_map(game_state, 'attack'),'defend': self.get_reward_map(game_state, 'defend')}
        sp_home = ScamPosition(game_state, self.red, 'defend', ReflexCaptureAgent)
        sp_enemy = ScamPosition(game_state, self.red, 'attack', ReflexCaptureAgent)
        self.begin_dead_end_food_map = {'home': sp_home.get_info_set('begin'), 'enemy': sp_enemy.get_info_set('begin')}
        self.dead_end_set = {'home': sp_home.get_info_set('end'), 'enemy': sp_enemy.get_info_set('end')}
        self.path_set = {'home': sp_home.get_info_set('path'), 'enemy': sp_enemy.get_info_set('path')}
        self.food_carrying = game_state.get_agent_state(self.index).num_carrying
        self.food_carrying_member = game_state.get_agent_state(self.member_ID).num_carrying
        self.food_left = len(self.get_food(game_state).as_list())
        self.food_left_you_are_defending = len(self.get_food_you_are_defending(game_state).as_list())
        self.position = game_state.get_agent_position(self.index)
        if self.position == self.start:
            self.eraseInfo()
    
    def get_home_border_without_corner(self, game_state):
        self.specify_global_info(game_state)
        # boarder line
        x = self.width // 2
        # red home boarder
        if self.red:
            x -= 1
        boarder_list = [(x, y) for y in range(1, self.height - 1) if not game_state.has_wall(x, y) and (x, y) not in self.dead_end_set['home']]
        return boarder_list

    def record_info(self, cur_pos, next_pos):
        self.safe_pos = cur_pos
        self.dead_end_begin_potion = next_pos
        self.is_in_begin_dead_end = True

    def eraseInfo(self):
        self.dead_end_begin_potion = None
        self.safe_pos = None
        self.is_in_begin_dead_end = False

    def get_territory(self,type):        
        y_range = range(1, self.height - 1)
        if self.red:
            if type=="home":
                x_range = range(1, self.width // 2)
                return (x_range, y_range)
            else:
                x_range = range(self.width // 2, self.width - 1)
                return (x_range, y_range)
        else:
            if type=="home":
                x_range = range(self.width // 2, self.width - 1)
                return (x_range, y_range)
            else:
                x_range = range(1, self.width // 2)
                return (x_range, y_range)
    

    def get_list_border(self,game_state,type):
        x = self.width // 2
        if type=="home":        
            if self.red:
                x -= 1
        else:
            if not self.red:
                x -= 1        
        border_list = [(x, y) for y in range(1, self.height - 1) if not game_state.has_wall(x, y)]
        return border_list   

    def get_member_ID(self, game_state):
        teamID = self.get_team(game_state)
        teamID.remove(self.index)
        return teamID[0] 
    
    def get_reward_map(self, game_state, mode='attack'):
        # determine which part we are interested in
        if mode == 'attack':
            attack_territory = self.enemy_territory
            defend_territory = self.home_territory
            food_map = self.get_food(game_state)
            capsuleMap = self.get_capsules(game_state)
        else:
            attack_territory = self.home_territory
            defend_territory = self.enemy_territory
            food_map = self.get_food_you_are_defending(game_state)
            capsuleMap = self.get_capsules_you_are_defending(game_state)

        reward_dict = {}  # a dictionary maps from coordinate to reward
        xrange, yrange = attack_territory

        for x in xrange:
            for y in yrange:
                if (x, y) in food_map.as_list():
                    reward_dict[(x, y)] = food_score  # assign food score to coordinates with food dot
                elif (x, y) in capsuleMap:
                    reward_dict[(x, y)] = capsule_score  # assign capsule score to coordinates with capsule
                else:
                    if not game_state.has_wall(x, y):
                        reward_dict[(x, y)] = blank_enemy_score  # assign blank enemy score in blank enemy territory

        xrange, yrange = defend_territory
        for x in xrange:
            for y in yrange:
                if not game_state.has_wall(x, y):
                    reward_dict[(x, y)] = blank_home_score  # assign blank home score in blank home territory

        return reward_dict

    def choose_action(self, game_state):
        """
        Picks among the actions with the highest Q(s,a).
        """
        pass

    def get_successor(self, game_state, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = game_state.generate_successor(self.index, action)
        pos = successor.get_agent_state(self.index).get_position()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generate_successor(self.index, action)
        else:
            return successor

    def evaluate(self, game_state, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)
        return features * weights   
    
    def choose_strategy(self, game_state):
        eat_food = True
        food_carrying = game_state.get_agent_state(self.index).num_carrying
        food_left = len(self.get_food(game_state).as_list())
    
        width = game_state.data.layout.width
        height = game_state.data.layout.height
        map_size = (width * height)
        threshold = 3
        food_density = food_left / map_size     
    
        distance2boarder = self.get_distance("home",game_state=game_state)
        timeLeft = int(game_state.data.timeleft / 4)

        if map_size > 150:
            threshold = int(2 * food_density * food_left)
            if threshold < 5:
                threshold = 5
        else: 
            threshold = int(food_density * food_left)
            if threshold < 4:
                threshold = 4

        ghosts = self.has_visible_enemy(game_state)

        if food_carrying:      
            if timeLeft - 10 <= distance2boarder or distance2boarder <= 2:
                eat_food = False
            else:
                if food_left <= 2:
                    eat_food = False
                else:
                    if ghosts and min(self.get_distance("ghost",game_state=game_state, ghosts=ghosts)) < 5 and not self.get_capsules(game_state):
                        if not self.is_scare(game_state) and ghosts and min(self.get_distance("ghost",game_state=game_state, ghosts=ghosts)) < 5:
                                eat_food = False

                    if food_carrying >= threshold:
                        if not self.is_scare(game_state): 
                            eat_food = False
                        elif food_carrying >= 2*threshold: 
                            eat_food = False
            
                    enemy = self.opponents
                    if game_state.get_agent_state(enemy[0]).is_pacman and game_state.get_agent_state(enemy[1]).is_pacman:
                        eat_food = True
    
        return eat_food
    
    def get_go_home_action(self, game_state):
        if self.position in self.get_go_home_points(game_state):
            if self.red:
                return 'West'
            else:
                return 'East'

        if self.is_in_begin_dead_end:
            action = self.turn_back_action(game_state)
        else:
            self.eraseInfo()
            if self.is_escape(game_state):
                action = self.escape_and_go_home_action(game_state)
                self.can_reverse = False
            else:
                action = self.go_home_point_action(game_state)
        if self.is_repeating_enemy():
            action = self.one_step_to_team_map(game_state)

        if len(self.queue.list) >= 6:
            self.queue.pop()
            self.queue.push(self.position)
        else:
            self.queue.push(self.position)

        self.last_position = self.position
        self.last_action = action

        return action
    
    def go_home_point_action(self, game_state):
        best_action = None
        min_distance = self.get_maze_distance(self.get_closest_home_point(game_state), self.position)
        best_pos = (); candidates = []
        for next_pos, action in get_possible_movements(game_state, self.position).items():
            if (not self.can_reverse) and (next_pos == self.last_position or next_pos in self.begin_dead_end_food_map['enemy']):
                continue
            candidates.append((next_pos, action))
        for pos, action in candidates:
            distance = self.get_maze_distance(pos, self.get_closest_home_point(game_state)) 
            if distance < min_distance:
                best_action = action
                best_pos = pos
                self.can_reverse = True
                break
        else:
            if candidates:
                best_pos, best_action = random.choice(candidates)
        return best_action
    
    def is_scare(self, game_state):    
        is_scared = False
        enemies = [game_state.get_agent_state(i) for i in self.get_opponents(game_state)]
        ghosts = [enemy for enemy in enemies if not enemy.is_pacman] 

        if ghosts:
            if len(ghosts) == 1 and ghosts[0].scared_timer > 5:  
                is_scared = True
            elif len(ghosts) == 2: 
                ghost_around = [enemy for enemy in ghosts if enemy.get_position() is not None]
                if ghost_around:
                    try: 
                        distances = self.get_ghost_distance(game_state, ghost_around)
                        minDist = float('inf')
                        closest_idx = None
                        for idx, distance in enumerate(distances):
                            if minDist >= distance:
                                minDist = distance
                                closest_idx = idx
                        if ghosts[closest_idx].scared_timer > 5:  
                            is_scared = True
                    except:
                        pass
                else: 
                    ghost1 = ghosts[0].scared_timer
                    ghost2 = ghosts[1].scared_timer
                    if min(ghost1, ghost2) > 5:
                        is_scared = True
        return is_scared

    def escape_and_go_home_action(self, game_state):
        idx_pos_dict = self.get_enemy_idx_position(game_state)
        dis = self.get_distance("enemy",pos=self.position, enemy_dict=idx_pos_dict)
        candidates = []; tie = []
        for next_pos, action in get_possible_movements(game_state, self.position).items():
            if next_pos not in self.begin_dead_end_food_map['enemy'].keys():
                if self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict) == dis:
                    tie.append((next_pos, action))
                if self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict) > dis:
                    dis = self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict)
                    tie = []; tie.append((next_pos, action))
            else:
                if self.get_closest("capsule",game_state=game_state):
                    if self.get_maze_distance(next_pos, self.get_closest("capsule",game_state=game_state)) < self.get_maze_distance(self.position, self.get_closest("capsule",game_state=game_state)):
                        candidates.append((next_pos, action))
        candidates.extend(tie)
        
        for next_pos, action in candidates:
            if self.get_maze_distance(next_pos, self.get_closest_home_point(game_state)) < self.get_maze_distance(self.position, self.get_closest_home_point(game_state)):
                return action
        
        if candidates:
            if self.get_closest("capsule",game_state=game_state):
                for next_pos, action in candidates:
                    if next_pos == self.get_closest("capsule",game_state=game_state):
                        return action
                    if self.get_maze_distance(next_pos, self.get_closest("capsule",game_state=game_state)) < self.get_maze_distance(self.position, self.get_closest("capsule",game_state=game_state)):
                        return action
            return random.choice(candidates)[1]
    
    def get_closest_home_point(self, game_state):
        go_home_points = self.get_go_home_points(game_state)
        closest_point = None
        closest_distance = float('inf')
        for home_point in go_home_points:
            distance = self.get_maze_distance(self.position, home_point)
            if distance < closest_distance:
                closest_distance = distance
                closest_point = home_point
        return closest_point

    def get_go_home_points(self, game_state):
        go_home_points = []
        for x, y in self.enemy_border:
            if self.red:
                if not game_state.has_wall(x-1, y):
                    go_home_points.append((x, y))
            else:
                if not game_state.has_wall(x+1, y):
                    go_home_points.append((x, y))
        return go_home_points
    
    def has_visible_enemy(self, game_state):
        enemies = [game_state.get_agent_state(i) for i in self.get_opponents(game_state)] 
        ghosts = [enemy for enemy in enemies if not enemy.is_pacman and enemy.get_position() is not None]
        return ghosts
    
    def get_distance(self,type, /,*,game_state=None,ghosts=None,enemy_dict=None,pos=None):
        if not pos and game_state:
            pos = game_state.get_agent_state(self.index).get_position()
        if type=="ghost" and game_state:
            ghost_distance_list = []        
            for ghost in ghosts:
                ghost_distance = self.get_maze_distance(pos, ghost.get_position())
                ghost_distance_list.append(ghost_distance)
            return ghost_distance_list
        elif type=="home" and game_state:
            minBord = min([self.get_maze_distance(pos, bord) for bord in self.home_border])
            return minBord
        elif type=="enemy" and enemy_dict:
            distance = 0
            for enemy_pos in enemy_dict.values():
                distance += self.get_maze_distance(pos, enemy_pos)
            return distance

    
    def get_closest(self, type,/,*,game_state=None,enemy_dict=None):
        closest_type = None
        closest_distance = float('inf')        
        if type=="capsule" and game_state:
            if self.get_capsules(game_state):
                items=self.get_capsules(game_state)
            else:
                return None
        elif type=="food"and game_state:
            items=self.get_food(game_state).as_list()
        elif type=="enemy" and enemy_dict:
            items=enemy_dict
        else:
            return None
        for item in items:
            if type=="enemy":
                distance = self.get_maze_distance(self.position, items[item])
            else:
                distance = self.get_maze_distance(self.position, item)
            if distance < closest_distance:
                closest_distance = distance
                closest_type = item
        return closest_type    
    
    
    def eat_food_strategy(self, game_state):
        if not game_state.get_agent_state(self.index).is_pacman:
            self.can_reverse = True
            if self.num_wander >= 2:
                action = self.change_attack_point_action(game_state)
            else:
                if not self.is_attack(game_state, 3):
                    action = self.wander_action(game_state)
                    self.num_wander += 1
                else:
                    if self.is_enemy_pacman(game_state):
                        action = self.escape_of_enemy_pacman_action(game_state)                        
                    else:
                        action = self.eat_food_action(game_state)                    
        else:
            self.num_wander = 0
            if self.is_in_begin_dead_end:
                if self.has_to_turn_back(game_state):
                    action = self.turn_back_action(game_state)                    
                else:
                    action = self.eat_food_action(game_state)                    
            else:
                if self.is_escape(game_state):
                    self.can_reverse = False
                    action = self.escape_action(game_state)                    
                else:
                    action = self.eat_food_action(game_state)                    
        if self.is_repeating_home():
            self.num_wander = 2
        if self.is_repeating_enemy():
            if game_state.get_agent_state(self.index).num_carrying == 0:
                self.num_wander = 2        
            action = self.one_step_to_team_map(game_state)

        if len(self.queue.list) >= 6:
            self.queue.pop()
            self.queue.push(self.position)
        else:
            self.queue.push(self.position)

        self.last_position = self.position
        self.last_action = action
        return action
    
    def has_to_turn_back(self, game_state):    
        if not self.begin_dead_end_food_map['enemy'][self.dead_end_begin_potion]:
            return True

        idx_pos_dict = {}
        for enemy in self.get_opponents(game_state):
            enemy_state = game_state.get_agent_state(enemy)
            if enemy_state.get_position() and not enemy_state.is_pacman:                
                position = enemy_state.get_position()
                idx_pos_dict[enemy] = position

        if len(idx_pos_dict)>0:            
            closest_idx = self.get_closest("enemy",enemy_dict=idx_pos_dict)
            idx, pos = closest_idx, idx_pos_dict[closest_idx]
            if self.get_maze_distance(pos, self.safe_pos) - self.get_maze_distance(self.position, self.safe_pos) <= 3:
                if game_state.get_agent_state(idx).scared_timer > 5:
                    return False
                return True
        return False
    
    def turn_back_action(self, game_state):
        action = self.one_step_closer_action(game_state, self.position, self.safe_pos)
        if not action:
            return None
        next_pos = game_state.generate_successor(self.index, action).get_agent_position(self.index)

        if next_pos == self.safe_pos:
            self.eraseInfo()

        return action

    def one_step_closer_action(self, game_state, source, target):
        cur_dis = self.get_maze_distance(source, target)
        for next_pos, action in get_possible_movements(game_state, source).items():
            if self.get_maze_distance(next_pos, target) < cur_dis:
                return action
    
    def eat_food_action(self, game_state):    
        best_action = None
        min_distance = self.get_maze_distance(self.get_closest("food",game_state=game_state), self.position)
        best_pos = (); candidates = []
        for next_pos, action in get_possible_movements(game_state, self.position).items():
            if (not self.can_reverse) and (next_pos == self.last_position or next_pos in self.begin_dead_end_food_map['enemy']):
                continue
            candidates.append((next_pos, action))
        for pos, action in candidates:
            distance = self.get_maze_distance(pos, self.get_closest("food",game_state=game_state)) 
            if distance < min_distance:
                best_action = action
                best_pos = pos
                self.can_reverse = True
                break
        else:
            if candidates:
                best_pos, best_action = random.choice(candidates)

        if best_pos in self.begin_dead_end_food_map['enemy'] and self.begin_dead_end_food_map['enemy'][best_pos]:
            self.record_info(self.position, best_pos)

        return best_action
    
    def is_escape(self, game_state):
        if self.get_enemy_idx_position(game_state):
            idx_pos_dict = self.get_enemy_idx_position(game_state)
            closest_idx = self.get_closest("enemy",enemy_dict=idx_pos_dict)
            idx, pos = closest_idx, idx_pos_dict[closest_idx]
            if self.get_maze_distance(self.position, pos) <= 5:
                if game_state.get_agent_state(idx).scared_timer > 5:
                    return False
                return True
        return False
    
    def escape_action(self, game_state):
        idx_pos_dict = self.get_enemy_idx_position(game_state)
        dis = self.get_distance("enemy",pos=self.position, enemy_dict=idx_pos_dict)
        candidates = []; tie = []
        for next_pos, action in get_possible_movements(game_state, self.position).items():
            if next_pos not in self.begin_dead_end_food_map['enemy'].keys():
                if self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict) == dis:
                    tie.append((next_pos, action))
                if self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict) > dis:
                    dis = self.get_distance("enemy",pos=next_pos, enemy_dict=idx_pos_dict)
                    tie = []; tie.append((next_pos, action))
            else:
                if self.get_closest("capsule",game_state=game_state):
                    if self.get_maze_distance(next_pos, self.get_closest("capsule",game_state=game_state)) < self.get_maze_distance(self.position, self.get_closest("capsule",game_state=game_state)):
                        candidates.append((next_pos, action))
        candidates.extend(tie)
        
        if candidates:
            if self.get_closest("capsule",game_state=game_state):
                for next_pos, action in candidates:
                    if next_pos == self.get_closest("capsule",game_state=game_state):
                        return action
                    if self.get_maze_distance(next_pos, self.get_closest("capsule",game_state=game_state)) < self.get_maze_distance(self.position, self.get_closest("capsule",game_state=game_state)):
                        return action
            for next_pos, action in candidates:
                if self.get_maze_distance(next_pos, self.get_closest("food",game_state=game_state)) < self.get_maze_distance(self.position, self.get_closest("food",game_state=game_state)):
                    return action
        return random.choice(candidates)[1]
    
    def is_repeating_home(self):
        if len(self.queue.list) < 5:
            return False
        pos_list = self.queue.list
        if (pos_list[0] in self.home_border and pos_list[2] in self.home_border and pos_list[1] in self.enemy_border and pos_list[3] in self.enemy_border):
            return True
        if pos_list[0] == pos_list[4] and pos_list[0][0] in self.home_territory[0] and pos_list[4][0] in self.home_territory[0]:
            return True
        return False

    def is_repeating_enemy(self):
        if len(self.queue.list) < 5:
            return False
        pos_list = self.queue.list
        if pos_list[0][0] in self.enemy_territory[0] and pos_list[1][0] in self.enemy_territory[0] and pos_list[2][0] in self.enemy_territory[0] and pos_list[3][0] in self.enemy_territory[0] and pos_list[4][0] in self.enemy_territory[0] and pos_list[5][0] in self.enemy_territory[0] and (pos_list[0] == pos_list[2] == pos_list[4] and pos_list[1] == pos_list[3] == pos_list[5]):
            return True
        return False
    
    def one_step_to_team_map(self, game_state):
        for next_pos, action in get_possible_movements(game_state, self.position).items():
            if self.red:
                if next_pos[0] < self.position[0]:
                    return action
            else:
                if next_pos[0] > self.position[0]:
                    return action
        legal_actions = game_state.get_legal_actions(self.index)
        if self.last_action in legal_actions:
            legal_actions.remove(self.last_action)
        return random.choice(legal_actions)
    
    def is_attack(self, game_state, threshold):
        for enemy in self.get_opponents(game_state):
            enemy_state = game_state.get_agent_state(enemy)
            if enemy_state.get_position() and not enemy_state.is_pacman and enemy_state.scared_timer == 0:
                if self.get_maze_distance(self.position, enemy_state.get_position()) <= threshold:
                    return False
        return True

    def wander_action(self, game_state):
        candidate_actions = game_state.get_legal_actions(self.index)
        for action in candidate_actions.copy():
            successor = game_state.generate_successor(self.index, action)
            if successor.get_agent_state(self.index).is_pacman:
                candidate_actions.remove(action)
        return random.choice(candidate_actions)

    def get_enemy_pacman_index(self, game_state):
        closest_idx = None; closest_dis = float('inf')
        for enemy in self.get_opponents(game_state):
            enemy_state = game_state.get_agent_state(enemy)
            if enemy_state.get_position() and enemy_state.is_pacman:
                if self.get_maze_distance(self.position, enemy_state.get_position()) < closest_dis:
                    closest_dis = self.get_maze_distance(self.position, enemy_state.get_position())
                    closest_idx = enemy
        return closest_idx

    def is_enemy_pacman(self, game_state):
        my_state = game_state.get_agent_state(self.index)
        enemy_idx = self.get_enemy_pacman_index(game_state)
        if enemy_idx:
            pos = game_state.get_agent_state(enemy_idx).get_position()
            if self.get_maze_distance(self.position, pos) <= 3:
                if my_state.scared_timer > 0:
                    return True
        return False

    def escape_of_enemy_pacman_action(self, game_state):
        enemy_idx = self.get_enemy_pacman_index(game_state)
        if enemy_idx:
            pos = game_state.get_agent_state(enemy_idx).get_position()
            for next_pos, action in get_possible_movements(game_state, self.position).items():
                if next_pos not in self.begin_dead_end_food_map['home']:
                    if self.get_maze_distance(next_pos, pos) > self.get_maze_distance(self.position, pos):
                        return action
    
    def get_enemy_idx_position(self, game_state):
        dicts = {}
        for enemy in self.get_opponents(game_state):
            enemy_state = game_state.get_agent_state(enemy)
            if enemy_state.get_position() and not enemy_state.is_pacman:                
                position = enemy_state.get_position()
                if self.get_maze_distance(self.position, position) <= 5:
                    dicts[enemy] = position
        return dicts if dicts else None
    
    def change_attack_point_action(self, game_state):
        if not self.is_changed_attack_point:
            original_attack_point = self.attack_point
            candidate_points = self.choose_attack_points(game_state)
            if original_attack_point == self.position:
                candidate_points.remove(original_attack_point)
            else:
                if original_attack_point and (self.position in candidate_points):
                    candidate_points.remove(original_attack_point)
                    candidate_points.remove(self.position)
            if not candidate_points:
                self.attack_point = random.choice(self.home_4_border)
            else:
                self.attack_point = random.choice(candidate_points)
            self.is_changed_attack_point = True
        path = self.bfs_home(game_state, self.position, self.attack_point)
        if not path:
            return random.choice(game_state.get_legal_actions(self.index))

        if game_state.generate_successor(self.index, path[0]).get_agent_position(self.index) == self.attack_point:
            self.num_wander = 0
            self.is_changed_attack_point = False
        return path[0]
    
    def bfs_home(self, game_state, source, target):
        path = []
        queue = util.Queue()
        closed = [source]
        xrange, _ = self.home_territory
        queue.push((source, path))
        while not queue.isEmpty():
            current_pos, path = queue.pop()
            if current_pos == target:
                return path
            for next_pos, action in get_possible_movements(game_state, current_pos).items():
                if next_pos[0] in xrange and next_pos not in closed:
                    closed.append(next_pos)
                    queue.push((next_pos, path + [action]))
    
    def choose_attack_points(self, game_state):
        attack_points = []
        for candidate in self.home_border:
            if self.red:
                if not game_state.has_wall(candidate[0] + 1, candidate[1]):
                    if not game_state.has_wall(candidate[0] + 2, candidate[1]):
                        if not game_state.has_wall(candidate[0] + 3, candidate[1]):
                            attack_points.append(candidate)
                        else:
                            if not game_state.has_wall(candidate[0] + 3, candidate[1] + 1) or not game_state.has_wall(candidate[0] + 3, candidate[1] - 1):
                                attack_points.append(candidate)
                    else:
                        if not game_state.has_wall(candidate[0] + 2, candidate[1] + 1) or not game_state.has_wall(candidate[0] + 2, candidate[1] - 1):
                            attack_points.append(candidate)
            else:
                if not game_state.has_wall(candidate[0] - 1, candidate[1]):
                    if not game_state.has_wall(candidate[0] - 2, candidate[1]):
                        if not game_state.has_wall(candidate[0] - 3, candidate[1]):
                            attack_points.append(candidate)
                        else:
                            if not game_state.has_wall(candidate[0] - 3, candidate[1] + 1) or not game_state.has_wall(candidate[0] - 3, candidate[1] - 1):
                                attack_points.append(candidate)
                    else:
                        if not game_state.has_wall(candidate[0] - 2, candidate[1] + 1) or not game_state.has_wall(candidate[0] - 2, candidate[1] - 1):
                            attack_points.append(candidate)
        return attack_points

    def get_features(self, game_state, action):
        pass

    def get_weights(self, game_state, action):
        """
        Normally, weights do not depend on the game state.  They can be either
        a counter or a dictionary.
        """
        pass
    


class OffensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that seeks food. This is an agent
    we give you to get an idea of what an offensive agent might look like,
    but it is by no means the best or only way to build an offensive agent.
    """
    def choose_action(self, game_state):
        """
        Picks among the actions with the highest Q(s,a).
        """
        self.specify_global_info(game_state)  # get global information
        action = None

        eat_food = self.choose_strategy(game_state)

        if eat_food:
            # strategy checking above, the below is eat food action impletementation
            action = self.eat_food_strategy(game_state)

        else:
            action = self.get_go_home_action(game_state)            
            if not action:
                action = random.choice(game_state.get_legal_actions(self.index))
        return action
    def get_features(self, game_state, action):
        pass

    def get_weights(self, game_state, action):
        """
        Normally, weights do not depend on the game state.  They can be either
        a counter or a dictionary.
        """
        pass
    

    

class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """
    def choose_action(self, game_state):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = game_state.get_legal_actions(self.index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(game_state, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

        max_value = max(values)
        best_actions = [a for a, v in zip(actions, values) if v == max_value]

        food_left = len(self.get_food(game_state).as_list())

        if food_left <= 2:
            best_dist = 9999
            best_action = None
            for action in actions:
                successor = self.get_successor(game_state, action)
                pos2 = successor.get_agent_position(self.index)
                dist = self.get_maze_distance(self.start, pos2)
                if dist < best_dist:
                    best_action = action
                    best_dist = dist
            return best_action

        return random.choice(best_actions)

    def get_features(self, game_state, action):
        features = util.Counter()
        successor = self.get_successor(game_state, action)

        my_state = successor.get_agent_state(self.index)
        my_pos = my_state.get_position()

        # Computes whether we're on defense (1) or offense (0)
        features['on_defense'] = 1
        if my_state.is_pacman: features['on_defense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        invaders = [a for a in enemies if a.is_pacman and a.get_position() is not None]
        features['num_invaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.get_maze_distance(my_pos, a.get_position()) for a in invaders]
            features['invader_distance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def get_weights(self, game_state, action):
        return {'num_invaders': -1000, 'on_defense': 100, 'invader_distance': -10, 'stop': -100, 'reverse': -2}
    
    def evaluate(self, game_state, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)
        return features * weights




blank_home_score = -1  # living reward at home territory
blank_enemy_score = 1  # living reward at enemy territory
food_score = 100  
capsule_score = 500  
 