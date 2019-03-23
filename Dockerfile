from python:3.7

RUN git clone https://github.com/rmartinsen/nba2vec.git

WORKDIR nba2vec

RUN mkdir /root/.keras
RUN mkdir models out

COPY keras.json /root/.keras/keras.json

RUN pip install -r requirements.txt

CMD [ "python", "train_vectors.py" ]