import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    ELASTICSEARCH_CLOUD_ID = os.environ.get('ELASTICSEARCH_CLOUD_ID', 'your-cloud-id')
    ELASTICSEARCH_USER = os.environ.get('ELASTICSEARCH_USER', 'your-username')
    ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD', 'your-password')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH')) if os.environ.get('MAX_CONTENT_LENGTH') is not None else 1048576
