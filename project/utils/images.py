import io

from PIL import Image


def resize_image(image_file):
    box = None
    dim = min(image_file.height, image_file.width)
    pad = (max(image_file.height, image_file.width) - dim) // 2
    if image_file.width > image_file.height:
        box = (pad, 0, pad+dim, dim)
    if image_file.height > image_file.width:
        box = (0, pad, dim, pad+dim)

    im = Image.open(image_file.path)
    im_resized = im.crop(box)
    buf = io.BytesIO()
    im_resized.save(buf, format='JPEG')
    return im_resized, buf.getvalue()
