import json

import pandas as pd
from keras.layers import Embedding, Flatten

from sklearn.preprocessing import LabelBinarizer

PLAYER_COLS = ['v1', 'v2', 'v3', 'v4', 'v5', 'h1', 'h2', 'h3', 'h4', 'h5']


def fit_model(X, y):
    from keras.models import Sequential
    from keras.layers import Dense, Activation

    model = Sequential([
        Embedding(X.shape[0], 4, input_length=10),
        Flatten(),
        Dense(128),
        Activation('relu'),
        Dense(128),
        Activation('relu'),
        Dense(25),
        Activation('softmax')
    ]
    )

    model.compile(optimizer='rmsprop',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.fit(X, y, epochs=5, batch_size=32)
    return model


def read_data(n=None):
    plays = []
    with open('out/all_plays.json', 'r') as f:
        if n:
            for i in range(n):
                plays.append(json.loads(f.readline()))
        else:
            for line in f.readlines():
                plays.append(json.loads(line))


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
    return X, y, nba_2_player


def create_play_id_map(X):
    player_ids = pd.unique(X[PLAYER_COLS].values.ravel('K'))
    player_2_nba = dict(enumerate(player_ids))
    return player_2_nba

X, y, nba_2_player = read_data()

model = fit_model(X, y)

model.save('/Users/admin/Projects/nba2vec/models/v1.model')

print('da')



