import time
import random

from strategy.tpf_CLIFF_intersection import distance
from strategy.tpf_CLIFF_constants import *

from communication.client.client import MountainClient
from strategy.tpf_CLIFF_class_dataAnalyst import DataAnalyst
from strategy.tpf_CLIFF_class_hiker import Hiker
import argparse

def update_all_data(hikers: list[Hiker], dataAnalyst: DataAnalyst, data:dict) -> None:
    """
    Updates data of all hikers and the DataAnalyst.

    Parameters:
    - hikers: List of Hiker objects.
    - dataAnalysts: DataAnalyst object.
    - data: Data received from the server.

    Returns:
        None
    """
    for hiker in hikers:
        hiker.update_data(data)
    dataAnalyst.update_data(data)

def check_hiker_local_max(hiker: Hiker, local_maxs: list, directives: dict) -> None:
    """
    Checks if a hiker is near any local maximum and updates its strategy and directives accordingly.

    Parameters:
    - hiker: Hiker object.
    - local_maxs: list of local maximum coordinates.
    - directives: dictionary containing the directives for each hiker.

    Returns:
        None
    """
    if hiker.strat == "hike":
        for local_max in local_maxs:
            if hiker.is_near_point(local_max):
                hiker.change_strat("follow_points")
                direction, speed = hiker.strategy(local_maxs)
                directives[hiker.name]["direction"] = direction
                directives[hiker.name]["speed"] = speed

def check_hiker_stopped(hiker: Hiker, local_maxs: list, directives: dict) -> None:
    """
    Checks if a hiker has stopped and updates its strategy and directives accordingly.

    Parameters:
    - hiker: Hiker object.
    - local_maxs: List of local maximum coordinates.
    - directives: Dictionary containing the directives for each hiker.

    Returns:
        None
    """
    if hiker.last_data == hiker.data:
        if len(hiker.points) == 0:
            hiker.points.append([random.randint(-14000, 14000), random.randint(-14000, 14000)])
        hiker.strat = "follow_points"
        hiker_dir_speed = hiker.strategy(local_maxs)
        directives[hiker.name] = {'direction': hiker_dir_speed[0], 'speed': hiker_dir_speed[1]}

def update_directive(hiker: Hiker, local_maxs: list, directives: dict, strat: str) -> None:
    """
    Updates the strategy and directives for a hiker.

    Parameters:
    - hiker: Hiker object.
    - local_maxs: List of local maximum coordinates.
    - directives: Dictionary containing the directives for each hiker.
    - strat: New strategy for the hiker.

    Returns:
        None
    """
    hiker.change_strat(strat)
    direction, speed = hiker.strategy(local_maxs)
    directives[hiker.name]["direction"] = direction
    directives[hiker.name]["speed"] = speed

def check_hiker_intersect(hiker1: Hiker, hikers: list, local_maxs: list, directives: dict) -> None:
    """
    Checks if a hiker intersects with any other hiker and updates their directives accordingly.

    Parameters:
    - hiker1: Hiker object.
    - hikers: List of Hiker objects.
    - local_maxs: List of local maximum coordinates.
    - directives: Dictionary containing the directives for each hiker.

    Returns:
        None
    """
    for hiker2 in hikers:
        if hiker2 == hiker1:
            continue
        direction1 = directives[hiker1.name]["direction"]
        direction2 = directives[hiker2.name]["direction"]
        coords, is_same_dir = hiker1.going_same_max(hiker2, direction1, direction2)
        if hiker1.strat == "hike" and hiker2.strat == "hike" and is_same_dir:
            if len(coords) > 0:
                local_maxs.append(coords)
                hiker1coords = (hiker1["x"], hiker1["y"])
                hiker2coords = (hiker2["x"], hiker2["y"])
                distance_i = distance(hiker1coords, coords)
                distance_j = distance(hiker2coords, coords)
                if distance_j > distance_i:
                    update_directive(hiker2, local_maxs, directives, "follow_points")
                else:
                    update_directive(hiker1, local_maxs, directives, "follow_points")
            else:
                update_directive(hiker1, local_maxs, directives, "follow_points")

def check_hiker_out_of_bounds(hiker: Hiker, local_maxs: list, directives: dict) -> None:
    """
    Checks if a hiker is going out of bounds and updates its strategy and directives accordingly.

    Parameters:
    - hiker: Hiker object.
    - local_maxs: List of local maximum coordinates.
    - directives: Dictionary containing the directives for each hiker.

    Returns:
        None
    """
    if hiker.check_out_of_bounds():
        if len(hiker.points) != 0:
            hiker.change_strat('follow_points')
        elif hiker.strat == "descent":
            hiker.strat = "hike"
        elif hiker.strat == "hike":
            hiker.strat = "descent"
        hiker_dir_speed = hiker.strategy(local_maxs)
        directives[hiker.name] = {'direction': hiker_dir_speed[0], 'speed': hiker_dir_speed[1]}

def check_hikers(hikers: list, local_maxs: list, directives: dict) -> None:
    """
    Checks the behavior of all hikers and updates their directives if needed.

    Parameters:
    - hikers: List of Hiker objects.
    - local_maxs: List of local maximum coordinates.
    - directives: Dictionary containing the directives for each hiker.

    Returns:
        None
    """
    for hiker in hikers:
        check_hiker_local_max(hiker, local_maxs, directives)
        check_hiker_stopped(hiker, local_maxs, directives)
        check_hiker_intersect(hiker, hikers, local_maxs, directives)
        check_hiker_out_of_bounds(hiker, local_maxs, directives)


def main() -> None:
    """
    The main function is the entry point of the program and controls the execution flow.
    It initializes the necessary objects, such as the MountainClient, DataAnalyst, and a list of Hiker objects.

    The function enters a while loop that continues until the game is over.
    Within the loop, it retrieves data from the server using the get_data method of the MountainClient object.

    It then prints useful information from the DataAnalyst and the server.
    
    If no team has won yet, the hikers follow their strategy.
    If a team has won, the hikers are directed towards the win coordinates.

    Next, the function checks the behavior of the hikers and updates the directives if necessary.

    Finally, the function gives the directives to the server.

    Returns:
        None
    """

    parser = argparse.ArgumentParser(description='Command line args')

    parser.add_argument('--ip', type=str, help='IP and port', default="localhost:8080")

    args = parser.parse_args()

    ip, port = args.ip.split(':')

    try:
        port = int(port)
    except:
        print("No ha ingresado un puerto válido")
        return None

    # Initialize the Client
    c = MountainClient(ip, port)

    # Initialize DataAnalyst
    dataAnalyst = DataAnalyst(c)

    # Initialize hikers
    agent_a = Hiker('CLIFF', 'agent_a', agent_a_points, alpha=0.5, beta=0.8)
    agent_b = Hiker('CLIFF', 'agent_b', agent_b_points, alpha=0.5, beta=0.7)
    agent_c = Hiker('CLIFF', 'agent_c', agent_c_points, alpha=0.5, beta=0.99)
    agent_d = Hiker('CLIFF', 'agent_d', agent_d_points, strat="follow_points", alpha=0.5, beta=0.5)
    hikers = [agent_a, agent_b, agent_c, agent_d]

    # Initialize empty list for saving the local maximums
    local_maxs = []

    # Add and register team
    hikers_names = [hiker.name for hiker in hikers]
    c.add_team('CLIFF', hikers_names)
    c.finish_registration()

    # Instructions
    while not c.is_over():
        # Sleep server for testing
        time.sleep(0.1)

        # Ask for data of all hikers in map
        data = c.get_data()

        # Update data of our hikers
        update_all_data(hikers, dataAnalyst, data)

        # Print useful data of DataAnalyst
        dataAnalyst_info = dataAnalyst.get_all_info()
        print("\n DataAnalyst Info = ")
        for item in dataAnalyst_info:
            if item != "n_max_pos":
                print(item)
                print(dataAnalyst_info[item])

        # Print useful data received from the server
        print("\n Server Info = ")
        for hiker in data["CLIFF"]:
            print(hiker)
            print(data["CLIFF"][hiker])
        
        # If no team won, players follow their strategy.
        if not dataAnalyst.check_win()[0]:

            agent_a_new_d_and_s = agent_a.strategy(local_maxs, "G")
            agent_b_new_d_and_s = agent_b.strategy(local_maxs, "G")
            agent_c_new_d_and_s = agent_c.strategy(local_maxs, "G")
            agent_d_new_d_and_s = agent_d.strategy(local_maxs, "G")

            directives = {
                agent_a.name: {'direction': agent_a_new_d_and_s[0], 'speed': agent_a_new_d_and_s[1]},
                agent_b.name: {'direction': agent_b_new_d_and_s[0], 'speed': agent_b_new_d_and_s[1]},
                agent_c.name: {'direction': agent_c_new_d_and_s[0], 'speed': agent_c_new_d_and_s[1]},
                agent_d.name: {'direction': agent_d_new_d_and_s[0], 'speed': agent_d_new_d_and_s[1]},
            }

        # If a team wins, all our hikers go to the win coordinates
        else:  
            print(f'Alguien gano escaladores yendo a pos {dataAnalyst.check_win()[1]}')
            x_y_win = (dataAnalyst.check_win()[1][0], dataAnalyst.check_win()[1][1])
            directives = {
                agent_a.name: {'direction': agent_a.direction_p(x_y_win), 'speed': agent_a.speed_p(x_y_win)},
                agent_b.name: {'direction': agent_b.direction_p(x_y_win), 'speed': agent_b.speed_p(x_y_win)},
                agent_c.name: {'direction': agent_c.direction_p(x_y_win), 'speed': agent_c.speed_p(x_y_win)},
                agent_d.name: {'direction': agent_d.direction_p(x_y_win), 'speed': agent_d.speed_p(x_y_win)},
            }

        # Check hikers behavior and update directives if needed
        #check_hikers(hikers, local_maxs, directives)

        # Give directives to server
        c.next_iteration('CLIFF', directives)

if __name__ == "__main__":
    main()