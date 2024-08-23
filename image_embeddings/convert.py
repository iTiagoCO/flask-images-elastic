from PIL import Image
import os
import glob

# Ruta de las imágenes originales
PATH_TO_IMAGES = "../app/static/images/**/*.*"
# Carpeta donde se guardarán las imágenes convertidas
CONVERTED_IMAGES_DIR = "./converted_images/"

# Crea el directorio de destino si no existe
if not os.path.exists(CONVERTED_IMAGES_DIR):
    os.makedirs(CONVERTED_IMAGES_DIR)

# Encuentra y convierte las imágenes
filenames = glob.glob(PATH_TO_IMAGES, recursive=True)

for filename in filenames:
    try:
        # Abre la imagen
        image = Image.open(filename)
        
        # Convierte la imagen a RGB si es necesario (algunos formatos como PNG pueden tener un canal alfa)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Genera el nuevo nombre del archivo con extensión .jpg
        base_name = os.path.splitext(os.path.basename(filename))[0]
        converted_filename = os.path.join(CONVERTED_IMAGES_DIR, f"{base_name}.jpg")
        
        # Guarda la imagen en formato JPG
        image.save(converted_filename, "JPEG")
        print(f"Convertido: {filename} -> {converted_filename}")
    except Exception as e:
        print(f"Error al convertir {filename}: {e}")
