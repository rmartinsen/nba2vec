import time
import json

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder

from get_plays import plays_to_json

def get_processed_game_ids():
    with open('out/all_plays.json') as f:
        game_ids = [json.loads(row)['game_id'] for row in f.readlines()]
        return game_ids

nba_teams = teams.get_teams()

team_ids = [team['id'] for team in nba_teams]

processed_game_ids = get_processed_game_ids()

for team_id in team_ids:
    print('Getting games for team: {}'.format(team_id))

    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]

    game_ids = games[games['GAME_DATE'] > '2018-10-15']['GAME_ID']

    for game_id in game_ids:
        if game_id not in processed_game_ids:
            try:
                print('Getting records for gameid: {}'.format(game_id))
                plays_to_json(game_id, 'out/all_plays.json')
                time.sleep(5)
                processed_game_ids.append(game_id)
            except Exception as e:
                print('ERROR: {}'.format(e))