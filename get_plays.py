import re
from functools import lru_cache

import pandas as pd

from nba_api.stats.endpoints import boxscoreadvancedv2, playbyplayv2, boxscoresummaryv2


def plays_to_json(game_id, output_path):
    boxscore = get_boxscore(game_id)
    play_by_play = get_play_by_play(game_id)
    summary = get_summary(game_id)

    h_team_id = summary[0]['HOME_TEAM_ID'].iloc[0]
    starters = get_starters(boxscore, h_team_id)

    initial_lineup = get_initial_lineup(game_id, summary, starters)

    plays = get_plays_from_pbp(initial_lineup, play_by_play)
    plays['result'] = plays.apply(parse_play_desc, axis=1)

    with open(output_path, 'a') as f:
        for row in plays.iterrows():
            if row['result']:
                f.write(row[1].to_json())
                f.write('\n')


def parse_play_desc(row):

    msg_type_to_parse_func = {
        1: parse_scoring_play,
        2: parse_scoring_play,
        3: parse_free_throw_play,
        4: parse_rebound,
        5: parse_turnover,
    }

    parse_func = msg_type_to_parse_func.get(row['msg_type'], parse_other)
    try:
        return parse_func(row)
    except:
        print('Could not parse {}: {}'.format(row['msg_type'], row['description']))


def parse_scoring_play(row):
    description = row['description']
    team = row['team']

    result = 'MAKE' if row['msg_type'] == 1 else 'MISS'

    if '3PT ' in description:
        shot_type = '3 pointer'
    elif 'BLOCK' in description:
        shot_type = 'blocked'
    else:
        pattern = r"([0-9]{1,2})'"
        m = re.findall(pattern, description)
        if len(m) == 0:
            print('No distance found for {}. Classified as layup.'.format(description))
        assert len(m) == 1
        distance = int(m[0])
        if distance <= 3:
            shot_type = 'layup'
        elif distance <= 10:
            shot_type = 'floater'
        else:
            shot_type = 'mid-range'
    return '{}: {} {}'.format(team, result, shot_type)


def parse_free_throw_play(row):
    result = 'MISS' if row['description'].startswith('MISS') else "MAKE"
    return '{}: {} {}'.format(row['team'], result, 'free throw')


def parse_rebound(row):
    return '{}: rebound'.format(row['team'])


def parse_turnover(row):
    # If the word STEAL is in the description then the team stole the ball. Otherwise the team turned it over. wtf.
    if 'STEAL' in row['description']:
        team = 'VISITOR' if row['team'] == 'HOME' else 'HOME'
    else:
        team = row['team']
    return '{}: turned ball over'.format(team)


def parse_other(row):
    return None


def get_plays_from_pbp(initial_lineup, play_by_play):
    cols = ['game_id', 'h_team_id', 'v_team_id', 'h1', 'h2', 'h3', 'h4', 'h5', 'v1', 'v2', 'v3', 'v4', 'v5',
            'team', 'description', 'msg_type']

    lineup = initial_lineup

    plays = pd.DataFrame(columns=cols)

    for _, play in play_by_play.iterrows():
        if play['EVENTMSGTYPE'] == 8:
            # Sub players
            player_out = (play['PLAYER1_ID'])
            player_in = (play['PLAYER2_ID'])

            player_cols = ['h1', 'h2', 'h3', 'h4', 'h5', 'v1', 'v2', 'v3', 'v4', 'v5']
            for col in player_cols:
                if lineup[col] == player_out:
                    lineup[col] = player_in

        else:
            team = 'VISITOR' if play['VISITORDESCRIPTION'] else 'HOME'
            lineup['description'] = play['{}DESCRIPTION'.format(team)]
            if lineup['description']:
                lineup['team'] = team
                lineup['msg_type'] = play['EVENTMSGTYPE']
                plays = plays.append(lineup, ignore_index=True)

    return plays


def get_initial_lineup(game_id, summary, starters):
    h_team_id = summary[0]['HOME_TEAM_ID'].iloc[0]
    v_team_id = summary[0]['VISITOR_TEAM_ID'].iloc[0]

    return {
            'game_id': game_id,
            'h_team_id': h_team_id,
            'v_team_id': v_team_id,
            'h1': starters['h_team']['PLAYER_ID'].iloc[0],
            'h2': starters['h_team']['PLAYER_ID'].iloc[1],
            'h3': starters['h_team']['PLAYER_ID'].iloc[2],
            'h4': starters['h_team']['PLAYER_ID'].iloc[3],
            'h5': starters['h_team']['PLAYER_ID'].iloc[4],
            'v1': starters['v_team']['PLAYER_ID'].iloc[0],
            'v2': starters['v_team']['PLAYER_ID'].iloc[1],
            'v3': starters['v_team']['PLAYER_ID'].iloc[2],
            'v4': starters['v_team']['PLAYER_ID'].iloc[3],
            'v5': starters['v_team']['PLAYER_ID'].iloc[4],
            }


@lru_cache(maxsize=16)
def get_boxscore(game_id):
    bs = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id)
    return bs.get_data_frames()[0]


@lru_cache(maxsize=16)
def get_play_by_play(game_id):
    pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
    return pbp.get_data_frames()[0]


@lru_cache(maxsize=16)
def get_summary(game_id):
    summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
    return summary.get_data_frames()


def get_starters(boxscore, h_team_id):
    keep_cols = ['TEAM_ID', 'PLAYER_ID', 'PLAYER_NAME']
    starters = boxscore[boxscore['START_POSITION'].str.len() > 0][keep_cols].reset_index()
    start_dict = {
        'h_team': starters[starters['TEAM_ID'] == h_team_id],
        'v_team': starters[starters['TEAM_ID'] != h_team_id],
    }
    assert len(start_dict['h_team'] == 5)
    assert len(start_dict['v_team'] == 5)

    return start_dict



for game_id in ('0021800541', '0021800514'):
    plays_to_json(game_id, './out/plays.json')
