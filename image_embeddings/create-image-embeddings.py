import os
import sys
import glob
import time
import json
import argparse
from elasticsearch import Elasticsearch, SSLError
from sentence_transformers import SentenceTransformer
from elasticsearch.helpers import parallel_bulk
from PIL import Image
from tqdm import tqdm
from datetime import datetime
from exif import Image as exifImage

CLOUD_ID = "My_deployment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ5Y2I1YmQwMThlZjI0NDBkOGQ2M2U5OGE1YTJjZjQ0NyQyMmQzZDk2MmQ3Nzk0MjZhOWViYjdjMTQzNWU1NjRhMg=="
ES_USER = "elastic"
ES_PASSWORD = "T59h6ILQ9fb5vG5EadMS4oam"
ES_TIMEOUT = 3600

DEST_INDEX = "my-image-embeddings"
DELETE_EXISTING = True
CHUNK_SIZE = 100

PATH_TO_IMAGES = "./app/static/images/**/*.jp*g"
PREFIX = "../app/static/images/"

parser = argparse.ArgumentParser()
parser.add_argument('--cloud_id', dest='cloud_id', required=False, default=CLOUD_ID,
                    help="Elasticsearch Cloud ID. Default: " + CLOUD_ID)
parser.add_argument('--es_user', dest='es_user', required=False, default=ES_USER,
                    help="Elasticsearch username. Default: " + ES_USER)
parser.add_argument('--es_password', dest='es_password', required=False, default=ES_PASSWORD,
                    help="Elasticsearch password. Default: " + ES_PASSWORD)
parser.add_argument('--thread_count', dest='thread_count', required=False, default=4, type=int,
                    help="Number of indexing threads. Default: 4")
parser.add_argument('--chunk_size', dest='chunk_size', required=False, default=CHUNK_SIZE, type=int,
                    help="Default: " + str(CHUNK_SIZE))
parser.add_argument('--timeout', dest='timeout', required=False, default=ES_TIMEOUT, type=int,
                    help="Request timeout in seconds. Default: " + str(ES_TIMEOUT))
parser.add_argument('--delete_existing', dest='delete_existing', required=False, default=True,
                    action=argparse.BooleanOptionalAction,
                    help="Delete existing indices if they are present in the cluster. Default: True")
parser.add_argument('--extract_GPS_location', dest='gps_location', required=False, default=False,
                    action=argparse.BooleanOptionalAction,
                    help="[Experimental] Extract GPS location from photos if available. Default: False")

args = parser.parse_args()


def main():
    global args
    lst = []

    start_time = time.perf_counter()
    img_model = SentenceTransformer('clip-ViT-B-32')
    filenames = glob.glob(PATH_TO_IMAGES, recursive=True)
    start_time = time.perf_counter()
    for filename in tqdm(filenames, desc='Processing files', total=len(filenames)):
        image = Image.open(filename)

        doc = {}
        embedding = image_embedding(image, img_model)
        doc['image_id'] = create_image_id(filename)
        doc['image_name'] = os.path.basename(filename)
        doc['image_embedding'] = embedding.tolist()
        doc['relative_path'] = os.path.relpath(filename)
        if PREFIX in doc['relative_path']:
            doc['relative_path'] = doc['relative_path'].split(PREFIX, 1)[1]
        else:
        # Maneja el caso donde PREFIX no esté presente
            doc['relative_path'] = os.path.basename(filename)
        doc['exif'] = {}

        try:
            date = get_exif_date(filename)
            doc['exif']['date'] = get_exif_date(filename)
        except Exception as e:
            pass

        if args.gps_location:
            try:
                doc['exif']['location'] = get_exif_location(filename)
            except Exception as e:
                pass

        lst.append(doc)

    duration = time.perf_counter() - start_time
    print(f'Duration creating image embeddings = {duration}')

    es = Elasticsearch(
        cloud_id=args.cloud_id,
        basic_auth=(args.es_user, args.es_password)
    )

    es.options(request_timeout=args.timeout)

    index = DEST_INDEX
    try:
        with open("image_embeddings/image-embeddings-mappings.json", "r") as config_file:
            config = json.loads(config_file.read())
            if args.delete_existing:
                if es.indices.exists(index=index):
                    print("Deleting existing %s" % index)
                    es.indices.delete(index=index, ignore=[400, 404])

            print("Creating index %s" % index)
            es.indices.create(index=index,
                              mappings=config["mappings"],
                              settings=config["settings"],
                              ignore=[400, 404],
                              request_timeout=args.timeout)

        count = 0
        for success, info in parallel_bulk(
                client=es,
                actions=lst,
                thread_count=4,
                chunk_size=args.chunk_size,
                timeout='%ss' % 120,
                index=index
        ):
            if success:
                count += 1
                if count % args.chunk_size == 0:
                    print('Indexed %s documents' % str(count), flush=True)
                    sys.stdout.flush()
            else:
                print('Doc failed', info)

        print('Indexed %s documents' % str(count), flush=True)
        duration = time.perf_counter() - start_time
        print(f'Total duration = {duration}')
        print("Done!\n")
    except SSLError as e:
        if "SSL: CERTIFICATE_VERIFY_FAILED" in e.message:
            print("\nCERTIFICATE_VERIFY_FAILED exception. Please check the CA path configuration for the script.\n")
            raise
        else:
            raise


def image_embedding(image, model):
    return model.encode(image)

def create_image_id(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def get_exif_date(filename):
    with open(filename, 'rb') as f:
        image = exifImage(f)
        taken = f"{image.datetime_original}"
        date_object = datetime.strptime(taken, "%Y:%m:%d %H:%M:%S")
        prettyDate = date_object.isoformat()
        return prettyDate

def get_exif_location(filename):
    with open(filename, 'rb') as f:
        image = exifImage(f)
        exif = {} 
        lat = dms_coordinates_to_dd_coordinates(image.gps_latitude, image.gps_latitude_ref)
        lon = dms_coordinates_to_dd_coordinates(image.gps_longitude, image.gps_longitude_ref)
        return [lon, lat]


def dms_coordinates_to_dd_coordinates(coordinates, coordinates_ref):
    decimal_degrees = coordinates[0] + \
                      coordinates[1] / 60 + \
                      coordinates[2] / 3600
    
    if coordinates_ref == "S" or coordinates_ref == "W":
        decimal_degrees = -decimal_degrees
    
    return decimal_degrees

if __name__ == '__main__':
    main()