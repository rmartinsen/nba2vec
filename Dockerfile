from python:3.7

RUN git clone https://github.com/rmartinsen/nba2vec.git

WORKDIR nba2vec

RUN pip install -r requirements.txt

CMD [ "python", "train_vectors.py" ]