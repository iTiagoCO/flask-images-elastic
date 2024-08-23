from flask import Flask
from config import Config
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object(Config)
# Load model, run against the image and create image embedding
img_model = SentenceTransformer('clip-ViT-B-32')

# Configuración de Elasticsearch usando Cloud ID
cloud_id = app.config['ELASTICSEARCH_CLOUD_ID']
es = Elasticsearch(
    cloud_id=cloud_id,
    basic_auth=(app.config['ELASTICSEARCH_USER'], app.config['ELASTICSEARCH_PASSWORD']),
)

from app import routes

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=5001)