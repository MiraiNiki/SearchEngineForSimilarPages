from gensim.models import word2vec
import logging

# wikipediaのデータをmecabで分割したdata.txtをコーパスとしたモデルを生成
# creating model from corpus of wikipedia
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
sentences = word2vec.Text8Corpus('data.txt')

model = word2vec.Word2Vec(sentences, size=200, min_count=20, window=15)
model.save("wiki.model")