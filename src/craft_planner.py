import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from math import inf
from heapq import heappop, heappush

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    # print(rule)

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].

        if 'Consumes' in rule:
            for item, value in rule['Consumes'].items():
                if state[item] < value:  # don't have enough of that item
                    return False

        if 'Requires' in rule:
            for item, value in rule['Requires'].items():
                if state[item] == 0:
                    return False
        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].

        next_state = State.copy(state)

        for item, value in rule['Produces'].items():
            next_state[item] += value  # add item quantity to inventory

        if 'Consumes' in rule:
            for item, value in rule['Consumes'].items():
                next_state[item] -= value  # subtract item quantity from inventory

        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for item, value in goal.items():
            if state[item] < value:
                return False

        return True

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state):
    # Implement your heuristic here!

    # From hint: If we already have a tool, we don't need to make another one.
    # Or if we have plenty of a material, we don't need any more.
    # This works as long as the goal isn't to build more than 1 tool of a tool or to acquire more material than specified by the heuristic

    tools = ['furnace', 'bench', 'wooden_pickaxe', 'wooden_axe', 'stone_pickaxe', 'stone_axe', 'iron_pickaxe', 'iron_axe']
    materials_with_heuristic_value = {  # value based on recipe that uses the most of that specific material (eg. furnace requires 8 cobble so we'll likely never need more than 8 at one time)
        'coal':   1,
        'cobble': 8,
        'wood':   1,
        'plank':  8,
        'stick':  4,
        'ore':    1,
        'ingot':  6,
    }

    for tool in tools:
        if state[tool] > 1:
            return inf

    for material in materials_with_heuristic_value.keys():
        if state[material] > materials_with_heuristic_value[material]:
            return inf

    return 0

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    queue = [(0, state, None)]  # This is like the frontier from other assignments, but I don't think it's a frontier if the nodes don't represent a physical space
    cost = {state: 0}
    prev = {state: None}
    actions = {state: None}
    visited = [state]
    path = []

    # A* implementation
    while time() - start_time < limit:

        current_cost, current_state, current_action = heappop(queue)

        if is_goal(current_state):  # found the goal, now construct the path
            path.append((current_state, current_action))
            current_back_node = prev[current_state]
            while current_back_node is not None:
                path.insert(0, (current_back_node, actions[current_back_node]))
                current_back_node = prev[current_back_node]
            break

        for node_action, node_state, node_cost in graph(current_state):
            new_cost = current_cost + node_cost
            if(node_state not in cost or new_cost < cost[node_state]) and node_state not in visited:
                cost[node_state] = new_cost
                actions[node_state] = node_action
                visited.append(node_state)
                priority = new_cost + heuristic(node_state)
                heappush(queue, (priority, node_state, node_action))
                prev[node_state] = current_state

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    if path:
        return path
    print("Failed to find a path from", state, 'within time limit.')
    return None


if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
    # print('All items:', Crafting['Items'])
    #
    # # List of items in your initial inventory with amounts:
    # print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
    # print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
    # print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic)

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t', state)
            print(action)
