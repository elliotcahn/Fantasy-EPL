import numpy as np
import pandas as pd
import random

#In-season functions: once you have a fantasy team, these functions can help with picking starters, a captain, and transferring players

#get_captain() returns the name of the highest scoring player on a fantasy team and doubles his points per game
def get_captain(team_df):
    captain = team_df[team_df["points_per_game"] == max(team_df["points_per_game"])]
    if len(captain.index) > 1:
        captain = captain[captain["now_cost"] == max(captain["now_cost"])]
        if len(captain.index) > 1:
            captain = captain.iloc[0]
    return (captain["full_name"].item(), 2*captain["points_per_game"].item())

#get_starters() returns the names of players from a fantasy team who should be starters
def get_starters(team_df, exclude_list, pos = [2,3,4], num_players = 1): #position default does not include gk
    team_df2 = team_df[~team_df["full_name"].isin(exclude_list)]
    position = team_df2[team_df2["position"].isin(pos)]
    while num_players > 0:
        starters = []
        starting_player = position[position["points_per_game"] == max(position["points_per_game"])]
        if len(starting_player) > num_players:
            starting_player = starting_player[starting_player["now_cost"] ==
                                      max(starting_player["now_cost"])] #price is assumed to be a reflection of quality/potential, so more expensive players are preferred
            if len(starting_player) > num_players:
                index = random.sample(range(0, len(starting_player)), num_players)
                starting_player = starting_player.iloc[index]
                starters.append(starting_player["full_name"].item())
                team_df2[~team_df2["full_name"].isin(starters)]
                num_players -= len(starting_player)
            else:
                starters.append(starting_player["full_name"].item())
                team_df2[~team_df2["full_name"].isin(starters)]
                num_players -= len(starting_player)
        else:
            starters.append(starting_player["full_name"].item())
            team_df2[~team_df2["full_name"].isin(starters)]
            num_players -= len(starting_player)
    return starters  

#exp_score() returns a list of suggested bench players and a string giving the expected score of the team per week,
#    the suggested captain, and suggested vice-captain. Amazingly, it is easier to pick fantasy starters when
#    the bench players are known.
def exp_score(team_list, players_df):
    team_df = players_df[players_df["full_name"].isin(team_list)]
    starter_list = []
    starter_list.extend(get_starters(team_df, starter_list, pos = [1]))
    starter_list.extend(get_starters(team_df, starter_list, pos = [4]))
    starter_list.extend(get_starters(team_df, starter_list, pos = [2], num_players = 3))
    num_players = len(starter_list)
    while num_players < 11:
        starter_list.extend(get_starters(team_df, starter_list))
        num_players += 1
    starter_df = team_df[team_df["full_name"].isin(starter_list)]
    team_points = sum(starter_df["points_per_game"])
    bench_df = team_df[(~team_df["full_name"].isin(starter_list))]
    bench_points = sum(bench_df["points_per_game"])
    captain = get_captain(starter_df)
    vice_captain = get_captain(starter_df[~starter_df["full_name"].isin([captain[0]])])
    return ("Bench : {}".format(list(bench_df["full_name"])),
            "This squad is projected to score {} points. The captain should be {}, who is expected to score {} points. The vice captain should be {}. The non-gk bench is expected to score {} points.".
          format(round(team_points + captain[1]/2, 1), captain[0], captain[1], vice_captain[0], round(bench_points, 1)))

#get_transfers() assesses options for replacing a player by considering
#    the price of the player, his position, and the budget remaining.
#    The first data frame returns players ordered by points per pound (efficient)
#    and the second returns players ordered by points per game (points).
def get_transfers(player_name, players_df, starter_list, rem_budget = 0, results_length = 5, play_time = 0.25):
    #play_time is minimum percent of games played for a player to be considered
    if player_name in starter_list: starter_list.remove(player_name)
    players_df = players_df[(players_df["game_guess"] >= play_time*max(players_df["game_guess"])) &
                          (~players_df["full_name"].isin(starter_list))]
    player_info = players_df[players_df["full_name"] == player_name]
    move_budget = player_info["now_cost"].item() + rem_budget
    player_options = players_df[(players_df["now_cost"] <= move_budget) &
                              (players_df["position"] == player_info["position"].values[0])]
    #efficient players
    efficient_players = player_options.sort_values(['points_per_pound_std'], ascending=False)
    efficient_players_list = list(efficient_players["full_name"])[:results_length]
    efficient_df = player_options[player_options["full_name"].isin(efficient_players_list) |
                                (player_options["full_name"].str.match(player_name))].drop_duplicates()
    #top scoring players (points)
    points_players = player_options.sort_values(['points_per_game'], ascending=False)
    points_players_list = list(efficient_players["full_name"])[:results_length]
    points_df = player_options[player_options["full_name"].isin(points_players_list) |
                                (player_options["full_name"].str.match(player_name))].drop_duplicates()
    cols_to_keep = ["full_name", "position", "now_cost", "points_per_pound_std", "points_per_game", "game_guess", "bps"]
    return (efficient_df[cols_to_keep].sort_values(['points_per_pound_std'], ascending=False),
           points_df[cols_to_keep].sort_values(['points_per_game'], ascending=False))



#Team-building functions: used to assemble an optimal team.
#NOTE: The data does not include the club of a player. This function may return more than 3 players from
#    one club, which is not allowed in Fantasy Premier League.

#get_star() returns the name and info of a star player, who is usually the recommended captain
def get_star(players_df):
    star_df = players_df[players_df["now_cost"] > 8]
    star = star_df[star_df["points_per_game"] == max(star_df["points_per_game"])]
    if len(star) > 1:
        star = star_df[star_df["bps"] == max(star_df["bps"])]
        if len(star) > 1:
            star = star[(star["now_cost"] == max(star["now_cost"]))]
            if len(star) > 1:
                star = star.sample(n = 1)
                return (star["full_name"].item(), star["now_cost"].item(), star["position"].item())
            else:
                return (star["full_name"].item(), star["now_cost"].item(), star["position"].item())
        else:
            return (star["full_name"].item(), star["now_cost"].item(), star["position"].item())
    else:
        return (star["full_name"].item(), star["now_cost"].item(), star["position"].item())

#get_efficient() returns the name and info of the most cost-efficient player available
def get_efficient(players_df, budget, exclude_list = [], pos = [2,3,4]):
    players_df = players_df[(~players_df["full_name"].isin(exclude_list)) &
                          (players_df["now_cost"] <= budget) &
                          (players_df["position"].isin(pos))]
    eff_player = players_df[players_df["points_per_pound_std"] == max(players_df["points_per_pound_std"])]
    if len(eff_player) > 1:
        eff_player = eff_player[eff_player["bps"] == max(eff_player["bps"])]
        if len(eff_player) > 1:
            eff_player = eff_player[(eff_player["now_cost"] == max(eff_player["now_cost"]))]
            if len(eff_player) > 1:
                eff_player = eff_player.sample(n = 1)
                return (eff_player["full_name"].item(), eff_player["now_cost"].item(), eff_player["position"].item())
            else:
                return (eff_player["full_name"].item(), eff_player["now_cost"].item(), eff_player["position"].item())
        else:
            return (eff_player["full_name"].item(), eff_player["now_cost"].item(), eff_player["position"].item())
    else:
        return (eff_player["full_name"].item(), eff_player["now_cost"].item(), eff_player["position"].item())

#get_points() returns the name and info of the best points per game player not already on the fantasy team.
#    If there is a points per game tie, preference is given to players with the most bonus points
#    then to players who are more expensive.
def get_points(players_df, budget, exclude_list = [], pos = [2,3,4]):
    players_df = players_df[(~players_df["full_name"].isin(exclude_list)) &
                          (players_df["now_cost"] <= budget) &
                          (players_df["position"].isin(pos))]
    points_player = players_df[players_df["points_per_game"] == max(players_df["points_per_game"])]
    if len(points_player) > 1:
        points_player = points_player[points_player["bps"] == max(points_player["bps"])]
        if len(points_player) > 1:
            points_player = points_player[(points_player["now_cost"] == max(points_player["now_cost"]))]
            if len(points_player) > 1:
                points_player = points_player.sample(n = 1)
                return (points_player["full_name"].item(), points_player["now_cost"].item(), points_player["position"].item())
            else:
                return (points_player["full_name"].item(), points_player["now_cost"].item(), points_player["position"].item())
        else:
            return (points_player["full_name"].item(), points_player["now_cost"].item(), points_player["position"].item())
    else:
        return (points_player["full_name"].item(), points_player["now_cost"].item(), points_player["position"].item())

#get_efficient_team() returns a list of players on the optimal team and the budget remaining.
#It is recommended that you use get_efficient_team() with exp_score() to determine how many plus_stars
#are needed to maximize expected points.
def get_efficient_team(players_full_df, save_per_starter = 5, plus_stars = 2, budget = 100, bench_budget = 19, play_time = 0.25):
    if plus_stars > 9: plus_stars = 9
    [fw, mid, defs, gk] = [3, 5, 5, 2]
    players_df = players_full_df[players_full_df["game_guess"] >= play_time*max(players_full_df["game_guess"])]
    starter_budget = budget - bench_budget
    efficient_team = []
    pos_list = [2, 3, 4]

    #pick a star captain
    star_player = get_star(players_df)
    efficient_team.append(star_player[0])
    starter_budget -= star_player[1]
    if star_player[2] == 2:
        defs -= 1
    elif star_player[2] == 3:
        mid -= 1
    elif star_player[2] == 4:
        fw -= 1
    else:
        gk -= 1
        
    #pick a starting goalkeeper
    if gk == 2:
        player_budget = starter_budget - (save_per_starter*9)
        goalie = get_efficient(players_df, player_budget, exclude_list = efficient_team, pos = [1])
        efficient_team.append(goalie[0])
        starter_budget -= goalie[1]
        gk -= 1
        
    #pick starters
    change_mid = 0
    while len(efficient_team) < 11 - plus_stars:
        if (defs == 0) & (2 in pos_list):
            pos_list.remove(2)
        if (mid == 0) & (3 in pos_list):
            pos_list.remove(3)
        if (fw == 0) & (4 in pos_list):
            pos_list.remove(4)
        player_budget = starter_budget - save_per_starter*(10 - len(efficient_team) - plus_stars)
        player_to_add = get_efficient(players_df, player_budget, exclude_list = efficient_team, pos = pos_list)
        efficient_team.append(player_to_add[0])
        starter_budget -= player_to_add[1]
        if player_to_add[2] == 2:
            defs -= 1
        elif player_to_add[2] == 3:
            mid -= 1
        else:
            fw -= 1
        if (fw == 1) & (mid == 0) & (len(efficient_team) < 10 - plus_stars):
            change_mid = -1
            pos_list.remove(4)
        elif (fw == 0) & (mid == 1) & (len(efficient_team) < 10 - plus_stars):
            change_mid = 1
            pos_list.remove(3)
            
    if change_mid == 1:
        pos_list.append(3)
    elif change_mid == -1:
        pos_list.append(4)
        
    #pick backup goalkeeper
    cheap_goalie_df = players_df[(players_df["position"] == 1) &
                            (~players_df["full_name"].isin(efficient_team))].nsmallest(5, "now_cost") 
    backup_gk_budget = max(cheap_goalie_df[ "now_cost"])
    backup_gk = get_efficient(players_df, backup_gk_budget, exclude_list = efficient_team, pos = [1])
    efficient_team.append(backup_gk[0])
    bench_budget -= backup_gk[1]
    gk -= 1
   
   #pick backup players
    for i in list(reversed(range(3))):
        if (defs == 0) & (2 in pos_list):
            pos_list.remove(2)
        if (mid == 0) & (3 in pos_list):
            pos_list.remove(3)
        if (fw == 0) & (4 in pos_list):
            pos_list.remove(4)
        bench_player_budget = bench_budget - 4.5*i
        player_to_add = get_efficient(players_df, bench_player_budget, exclude_list = efficient_team, pos = pos_list)
        efficient_team.append(player_to_add[0])
        bench_budget -= player_to_add[1]
        if player_to_add[2] == 2:
            defs -= 1
        elif player_to_add[2] == 3:
            mid -= 1
        else:
            fw -= 1
    
    #spend remaining budget on starter-level players based on points per game ("plus stars")
    remain_budget = starter_budget + bench_budget + backup_gk_budget
    for i in list(reversed(range(plus_stars))):
        if (defs == 0) & (2 in pos_list):
            pos_list.remove(2)
        if (mid == 0) & (3 in pos_list):
            pos_list.remove(3)
        if (fw == 0) & (4 in pos_list):
            pos_list.remove(4)
        player_to_add = get_points(players_df, remain_budget - i*save_per_starter,
                                  exclude_list = efficient_team, pos = pos_list)
        efficient_team.append(player_to_add[0])
        remain_budget -= player_to_add[1]
        if player_to_add[2] == 2:
            defs -= 1
        elif player_to_add[2] == 3:
            mid -= 1
        else:
            fw -= 1
    return (efficient_team, round(remain_budget, 1))
#Logic behind get_efficient_team():
#Budget:
#    A specified amount is reserved for the 4 bench players (default: 190)
#    A specified amount is reserved for each individual starter yet to be selected (default: 50 per starter)
#Picking players:
#    A star player to be captain (and thus score double points) is chosen first
#    Price efficient starters and bench players are chosen
#    The remaining budget is totalled and then spent on a specified number of "plus stars,"
#        players chosen for points per game and not points per pound