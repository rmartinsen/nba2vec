import datetime
import json
import pickle

import pandas as pd
from keras.layers import Embedding, Flatten

from sklearn.preprocessing import LabelBinarizer

from data_gathering.s3 import pull_from_s3, push_object_to_s3

PLAYER_COLS = ['v1', 'v2', 'v3', 'v4', 'v5', 'h1', 'h2', 'h3', 'h4', 'h5']


def fit_model(X, y):
    from keras.models import Sequential
    from keras.layers import Dense, Activation

    model = Sequential([
        Embedding(X.shape[0], 8, input_length=10),
        Flatten(),
        Dense(128),
        Activation('relu'),
        Dense(128),
        Activation('relu'),
        Dense(25),
        Activation('softmax')
    ]
    )

    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.fit(X, y, epochs=1, batch_size=64, validation_split=.1)
    return model


def read_data(data_path, n=None):
    plays = []
    with open(data_path, 'r') as f:
        if n:
            for i in range(n):
                plays.append(json.loads(f.readline()))
        else:
            for line in f.readlines():
                play = json.loads(line)
                play['year'] = play['game_id'][3:5]
                plays.append(play)

    output_col = 'result'

    plays_df = pd.DataFrame(plays)

    player_2_nba = create_play_id_map(plays_df)
    nba_2_player = {v: k for k, v in player_2_nba.items()}

    X = pd.DataFrame(columns=PLAYER_COLS)
    for col in PLAYER_COLS:
        X[col] = plays_df[col].apply(lambda x: nba_2_player[x])

    labeler = LabelBinarizer()
    y_raw = plays_df[output_col].values
    y = labeler.fit_transform(y_raw)

    with open('./models/data.pickle', 'wb') as f:
        pickle.dump((X, y, nba_2_player), f)

    return X, y, nba_2_player


def create_play_id_map(X):
    player_ids = pd.unique(X[PLAYER_COLS].values.ravel('K'))
    player_2_nba = dict(enumerate(player_ids))
    return player_2_nba


def download_play_data(local_path):
    data_bucket = 'nba2vec'
    data_key = 'input_data/all_plays.json'

    pull_from_s3(data_bucket, data_key, local_path)


def main():
    timestamp = datetime.datetime.now()
    data_local_path = 'out/all_plays.json'

    model_bucket = 'nba2vec'
    model_key = 'models/models_metrics_{}'.format(timestamp)

    download_play_data(data_local_path)
    X, y, nba_2_player = read_data(data_local_path)

    model = fit_model(X, y)

    metrics = json.dumps(model.history.history)

    push_object_to_s3(metrics, model_bucket, model_key)


if __name__ == '__main__':
    main()
