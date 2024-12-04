"""
Purpose of class Load:
    1. Run load / unload operation with A*
"""

import queue
import copy

# for testing
class Container:
    def __init__(self, name = "UNUSED", weight = 0):
        self.name = name
        self.weight = weight
    
    def __lt__(self, other):
        if isinstance(other, Container):
            return self.name < other.name
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Container):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash((self.name, self.weight))



class Load:
    # function called by main program
    @staticmethod
    def run(ship_layout, unload_list, load_list):
        for i in range(len(unload_list)):
            unload_list[i] = unload_list[i] + (unload_list[i][1],)
    
        for i in range(len(load_list)):
            load_list[i] = load_list[i] + ((8, 0),)

        return Load.a_star(ship_layout, unload_list, load_list)

    
    # a star algorithm for moves to do
    @staticmethod
    def a_star(ship_layout, full_unload_list, full_load_list):
        # ASSUMPTION: unload_list and load_list stores a pair (container (name needed) and its location)

        # initialize frontier, explored, and solution
        frontier = queue.PriorityQueue()
        explored = {}
        solution_map = {}
        
        # f = g (cost) + h (heuristic)
        initial_h = Load.calc_heuristic(ship_layout, full_unload_list, full_load_list)
        frontier.put((initial_h, 0, initial_h, copy.deepcopy(ship_layout), full_unload_list, full_load_list))
        hashed_layout = tuple(tuple(row) for row in ship_layout)
        explored[hashed_layout] = True
        solution_map[hashed_layout] = None

        # loops for each state in queue
        while not frontier.empty():
            _, current_cost, current_h, current_layout, unload_list, load_list = frontier.get()

            # check goal state
            if(Load.check_goal_state(current_layout, unload_list, load_list)):
                print(f"GOAL: {current_cost}, {current_h}")
                print(f"{Load.calc_unload_h(current_layout, unload_list)}, {Load.calc_load_h(load_list)}")
                return Load.reconstruct_path(solution_map, current_layout)

            # finds all empty spots in each column. 3rd line filters
            # find all topmost containers in each column
            empty_spots = Load.find_top_empty_containers(current_layout)
            empty_spots = [cord for cord in empty_spots if cord[0] != 8]
            top_containers = [(x - 1, y) for x, y in empty_spots if x > 0]

            # Moves:
            # 1. Every container to load to empty_spots
            # 2. Every container in top_containers to empty_spots
            # 3. Every container in top_containers to unloaded

            # every load_list containers to empty_spots
            for load_index, info in enumerate(load_list):
                container, desired_cords, current_cords = info
                if(current_cords == desired_cords):
                    continue
                
                # move directly to desired_cords
                # check if empty
                r, c = desired_cords
                if(desired_cords in empty_spots):
                    new_layout = copy.deepcopy(current_layout)
                    new_layout[r][c] = container

                    new_load_list = copy.deepcopy(load_list)
                    new_load_list[load_index] = (container, desired_cords, desired_cords)

                    Load.push_new_state(frontier, explored, solution_map, new_layout, current_layout, unload_list, new_load_list, current_cost, (r,c), (8, 0), highest_empty_r=0)

            # every top_container containers to empty_spots or unload
            for container_cord in top_containers:
                r, c = container_cord

                # don't move containers on load_list
                is_on_load_list = False
                for load_index, load_container in enumerate(load_list): # TODO: doesn't deal with duplicates
                    if(load_container[0].name == current_layout[r][c].name):
                        is_on_load_list = True
                        break
                if(is_on_load_list):
                    continue

                is_on_unload_list = False
                unload_index = -1
                for idx, unload_container in enumerate(unload_list): # TODO: doesn't deal with duplicates
                    if(unload_container[0].name == current_layout[r][c].name):
                        is_on_unload_list = True
                        unload_index = idx
                        break

                # only unload containers on unload_list
                if is_on_unload_list:
                    new_layout = copy.deepcopy(current_layout)
                    new_layout[r][c] = Container()

                    unload_item = list(unload_list[unload_index])
                    unload_item[2] = (8,0)
                    unload_list[unload_index] = tuple(unload_item)
                    
                    Load.push_new_state(frontier, explored, solution_map, new_layout, current_layout, unload_list, load_list, current_cost, (8,0), (r, c), highest_empty_r=0)
                
                # move to every possible empty spot
                for empty_cord in empty_spots:
                    # if top_container and empty_spot are same col. will lead to floating container
                    if(empty_cord[1]==c):
                        continue

                    # find row of highest container between container to move and empty spot
                    highest_empty_r = Load.highest_r_between(r, c, empty_cord, empty_spots)

                    # assumes heuristic functions will take care of everything
                    if is_on_unload_list:
                        unload_item = list(unload_list[unload_index])
                        unload_item[2] = empty_cord
                        unload_list[unload_index] = tuple(unload_item)

                    # swap
                    new_layout = copy.deepcopy(current_layout)
                    new_layout[empty_cord[0]][empty_cord[1]], new_layout[r][c] = (
                        new_layout[r][c], 
                        new_layout[empty_cord[0]][empty_cord[1]]
                    )

                    Load.push_new_state(frontier, explored, solution_map, new_layout, current_layout, unload_list, load_list, current_cost, empty_cord, (r, c), highest_empty_r)

        print("solution not found")
            
    # find highest empty slot in each column
    @staticmethod
    def find_top_empty_containers(current_layout):
        empty_spots = []
        transposed_layout = zip(*current_layout)
        for col, column in enumerate(transposed_layout): # iterate through columns
            for row, item in enumerate(column):
                if(item.name == "UNUSED"):
                    empty_spots.append((row, col))
                    break
            empty_spots.append((8, col))
        return empty_spots

    # find row of the space above the highest container between container to move and empty spot
    @staticmethod
    def highest_r_between(r, c, empty_cord, empty_spots):
        highest_empty_r = r
        for col_index in range(min(c, empty_cord[1]), max(c, empty_cord[1]) + 1):
            if(col_index==c):
                continue
            highest_empty_r = max(empty_spots[col_index][0], highest_empty_r)
        return highest_empty_r

    # pushes new state to frontier
    @staticmethod
    def push_new_state(frontier, explored, solution_map, new_layout, current_layout, unload_list, load_list, current_cost, new_spot, old_spot, highest_empty_r):
        # make layout hashable
        hashable_layout = tuple(tuple(row) for row in new_layout)

        # Check if the layout has already been explored
        if explored.get(hashable_layout, False):
            return
        explored[hashable_layout] = True

        # Record the current layout as the parent of the new layout in solution_map
        solution_map[hashable_layout] = current_layout

        # Calculate the cost and heuristic
        # TODO: cost will vary
        new_r, new_c = new_spot
        old_r, old_c = old_spot

        cost = abs(highest_empty_r - old_r) + abs(new_r - highest_empty_r) + abs(old_c - new_c)
        h = Load.calc_heuristic(new_layout, unload_list, load_list)

        # Add the new state to the frontier
        # pair stores (f, g, h, state, unload_list, load_list)
        frontier.put((current_cost + cost + h, current_cost + cost, h, new_layout, unload_list, load_list))

    # reconstruct path when solution is found
    @staticmethod
    def reconstruct_path(solution_map, final_layout):
        path = []
        layout = final_layout.copy()

        while layout is not None:
            path.append(layout)
            hashable_layout = tuple(tuple(row) for row in layout)

            previous_layout = solution_map[hashable_layout]
            layout = previous_layout

        path.reverse()
        
        return path

    @staticmethod
    def equal_states(layout1, layout2):
        for r in range(8):
            for c in range(12):
                container1 = layout1[r][c]
                container2 = layout2[r][c]
                if container1.name != container2.name or container1.weight != container2.weight:
                    return False
        return True

    # check if goal state is satisfied
    @staticmethod
    def check_goal_state(ship_layout, unload_list, load_list):
        return Load.check_unload_goal(ship_layout, unload_list) & Load.check_load_goal(ship_layout, load_list)
    
    # check if containers to unload are off the ship (and buffer)
    @staticmethod
    def check_unload_goal(ship_layout, unload_list):
        ship_containers = [container.name for row in ship_layout for container in row]

        # check if every container in unload_list is in ship_containers
        for container, _, _ in unload_list:
            if container.name in ship_containers:
                return False

        return True
    
    # check if containers to load are on the ship
    def check_load_goal(ship_layout, load_list):
        # check if every container in load_list is in ship_containers
        for container, location, _ in load_list:
            x, y = location
            if ship_layout[x][y].name != container.name:
                return False

        return True

    # calculate the total heuristic
    @staticmethod
    def calc_heuristic(ship_layout, unload_list, load_list):
        return Load.calc_unload_h(ship_layout, unload_list) + Load.calc_load_h(load_list)


    # part of heuristic for unloading
    @staticmethod
    def calc_unload_h(ship_layout, unload_list):
        sum = 0
        lowest_per_col = {}

        for _, _, curr_location in unload_list:
            r, c = curr_location
            # TODO: revise this code later
            # old_low = 8

            # if c not in lowest_per_col:
            #     lowest_per_col[c] = r
            # elif r < lowest_per_col[c]:
            #     old_low = lowest_per_col[c]
            #     lowest_per_col[c] = r
            # else:
            #     old_low = lowest_per_col[c]
            #     sum -= 1

            # # Check if there are containers on top (add to h)
            # for row in range(r + 1, 8):  # Iterate above the current position
            #     if ship_layout[row][c].name != "UNUSED" and row < old_low:  # Check if empty
            #         sum += 1
            #     else:
            #         break
            # distance to (8,0)
            sum += Load.load_unload_heuristic(r, c)
        return sum


    # heuristic for an individual container to unload
    @staticmethod
    def load_unload_heuristic(x: int, y: int):
        return abs(8 - x) + y


    # part of heuristic for loading
    @staticmethod
    def calc_load_h(load_list):
        sum = 0
        for _, location, current_location in load_list:
            r, c = location
            x, y = current_location
            sum += abs(r-x) + abs(c-y)
        return sum

    @staticmethod
    def print_layout(test_layout):
        if(test_layout==None):
            print("Cannot print layout")
            return

        for x, row in enumerate(reversed(test_layout)):
            row_output = ""
            for y, container in enumerate(row):
                row_output += f"({7-x},{y}): {container.name:6}, "
            print(row_output)





# Testing
container1 = Container("A", 120)
container2 = Container("B", 200)
container3 = Container("C", 400)
container4 = Container("D", 500)
container5 = Container("E", 2200)
container6 = Container("F", 300)

# 8 x 12
test_layout = [[Container() for i in range(0,12)] for j in range(0,8)]
test_layout[0][0] = container1
# test_layout[1][0] = container2
test_layout[0][2] = container3
# test_layout[1][2] = container5

# Test case for running:
# unloading
# test_output = Load.run(test_layout, [(container1, (0, 0))], [])
# test_output = Load.run(test_layout, [(container1, (0, 0)), (container3, (0, 2))], [])
# test_output = Load.run(test_layout, [(container5, (1, 2)), (container3, (0, 2))], [])
# loading
# test_output = Load.run(test_layout, [], [(container4, (0, 3))])
# test_output = Load.run(test_layout, [], [(container4, (0, 0)), (container5, (0, 11))])
# both
# test_output = Load.run(test_layout, [(container1, (0, 0))], [(container4, (0, 10)), (container5, (0, 11))])
test_output = Load.run(test_layout, [(container1, (0, 0)), (container3, (0, 2))], [(container6, (0, 11))])


print("SOLUTION:")
for item in test_output:
    Load.print_layout(item)
    print("=============")



# Test case for heuristic: (may still be glitchy with multiple containers in the same column)
# h = Load.calc_heuristic(layout, [(unload_container, (0, 0))], [(load_container, (0, 1))])
# print(h)
# h = Load.calc_heuristic(layout, [(Container("A", 120), (2,0)), (Container("C", 400), (0,0))], [])
# print(h)

# Test case for checking goal state:
# # loading:
# result = Load.check_goal_state(layout, [], [(Container("A", 120), (0,0)), (Container("C", 400), (1,0))])
# print(result)
# # unloading:
# result = Load.check_goal_state(layout, [(Container("C", 400), (1,0))], [])
# print(result)

# Test case for finding top empty containers for each column:
# layout2 = [[Container() for i in range(0,12)] for j in range(0,8)]
# layout2[0][0] = load_container
# layout2[1][0] = load_container
# layout2[2][0] = load_container
# layout2[0][1] = load_container
# layout2[0][4] = load_container
# output = Load.find_top_empty_containers(layout2)
# for item in output:
#     cords = "(" + str(item[0]) + ", " + str(item[1]) + ")"
#     print(cords)