import time

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder

from get_plays import plays_to_json

nba_teams = teams.get_teams()

team_ids = [team['id'] for team in nba_teams]

processed_game_ids = []

for team_id in team_ids:
    print('Getting games for team: {}'.format(team_id))

    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]

    game_ids = games[games['GAME_DATE'] > '2018-10-15']['GAME_ID']

    for game_id in game_ids:
        print('Getting records for gameid: {}'.format(game_id))
        if game_id not in processed_game_ids:
            plays_to_json(game_id, 'out/all_plays.json')
            time.sleep(2)
            processed_game_ids.append(game_id)