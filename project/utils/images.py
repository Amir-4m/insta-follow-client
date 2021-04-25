import io

from PIL import Image


def resize_image(image_file):
    img = Image.open(image_file)
    width = image_file.width
    height = image_file.height
    resized_image = img.resize((width, width))
    b = io.BytesIO()
    resized_image.save(b, format='JPEG')
    return b.getvalue()
