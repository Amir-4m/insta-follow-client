import io

from PIL import Image


# def resize_image(image_file):
#     box = None
#     dim = min(image_file.height, image_file.width)
#     pad = (max(image_file.height, image_file.width) - dim) // 2
#     if image_file.width > image_file.height:
#         box = (pad, 0, pad + dim, dim)
#     if image_file.height > image_file.width:
#         box = (0, pad, dim, pad + dim)
#
#     im = Image.open(image_file.path)
#     im_resized = im.crop(box)
#     buf = io.BytesIO()
#     im_resized.save(buf, format='JPEG')
#     return im_resized, buf.getvalue(), buf.tell()

def stories_shaper(fname):
    """
    Find out the size of the uploaded image. Processing is not needed if the
    image is already 1080x1920 pixels. Otherwise, the image height should be
    1920 pixels. Substrate formation: Crop the image under 1080x1920 pixels
    and apply a Gaussian Blur filter. Centering the image depending on its
    aspect ratio and paste it onto the substrate. Save the image.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError as e:
        print("ERROR: {err}".format(err=e))
        print(
            "Required module `PIL` not installed\n"
            "Install with `pip install Pillow` and retry"
        )
        return False
    buf = io.BytesIO()
    img = Image.open(fname)
    if (img.size[0], img.size[1]) == (1080, 1920):
        print("Image is already 1080x1920. Just converting image.")
        new_fname = "{fname}.STORIES.jpg".format(fname=fname)
        new = Image.new("RGB", (img.size[0], img.size[1]), (255, 255, 255))
        new.paste(img, (0, 0, img.size[0], img.size[1]))
        new.save(buf, quality=95, format='JPEG')
        return new, buf.getvalue(), buf.tell()
    else:
        min_width = 1080
        min_height = 1920
        if img.size[1] != 1920:
            height_percent = min_height / float(img.size[1])
            width_size = int(float(img.size[0]) * float(height_percent))
            img = img.resize((width_size, min_height), Image.ANTIALIAS)
        else:
            pass
        if img.size[0] < 1080:
            width_percent = min_width / float(img.size[0])
            height_size = int(float(img.size[1]) * float(width_percent))
            img_bg = img.resize((min_width, height_size), Image.ANTIALIAS)
        else:
            pass
        img_bg = img.crop(
            (
                int((img.size[0] - 1080) / 2),
                int((img.size[1] - 1920) / 2),
                int(1080 + ((img.size[0] - 1080) / 2)),
                int(1920 + ((img.size[1] - 1920) / 2)),
            )
        ).filter(ImageFilter.GaussianBlur(100))
        if img.size[1] > img.size[0]:
            height_percent = min_height / float(img.size[1])
            width_size = int(float(img.size[0]) * float(height_percent))
            img = img.resize((width_size, min_height), Image.ANTIALIAS)
            if img.size[0] > 1080:
                width_percent = min_width / float(img.size[0])
                height_size = int(float(img.size[1]) * float(width_percent))
                img = img.resize((min_width, height_size), Image.ANTIALIAS)
                img_bg.paste(
                    img, (int(540 - img.size[0] / 2), int(960 - img.size[1] / 2))
                )
            else:
                img_bg.paste(img, (int(540 - img.size[0] / 2), 0))
        else:
            width_percent = min_width / float(img.size[0])
            height_size = int(float(img.size[1]) * float(width_percent))
            img = img.resize((min_width, height_size), Image.ANTIALIAS)
            img_bg.paste(img, (int(540 - img.size[0] / 2), int(960 - img.size[1] / 2)))
        new_fname = "{fname}.STORIES.jpg".format(fname=fname)
        print(
            "Saving new image w:{w} h:{h} to `{f}`".format(
                w=img_bg.size[0], h=img_bg.size[1], f=new_fname
            )
        )
        new = Image.new("RGB", (img_bg.size[0], img_bg.size[1]), (255, 255, 255))
        new.paste(img_bg, (0, 0, img_bg.size[0], img_bg.size[1]))
        new.save(buf, quality=95, format='JPEG')
        return new, buf.getvalue(), buf.tell()


def compatible_aspect_ratio(size):
    min_ratio, max_ratio = 4.0 / 5.0, 90.0 / 47.0
    width, height = size
    ratio = width * 1.0 / height * 1.0
    print("FOUND: w:{w} h:{h} r:{r}".format(w=width, h=height, r=ratio))
    return min_ratio <= ratio <= max_ratio


def resize_image(fname):
    from math import ceil

    try:
        from PIL import Image, ExifTags
    except ImportError as e:
        print("ERROR: {err}".format(err=e))
        print(
            "Required module `PIL` not installed\n"
            "Install with `pip install Pillow` and retry"
        )
        return False
    print("Analizing `{fname}`".format(fname=fname))
    h_lim = {"w": 90.0, "h": 47.0}
    v_lim = {"w": 4.0, "h": 5.0}
    img = Image.open(fname)
    (w, h) = img.size
    deg = 0
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = dict(img._getexif().items())
        o = exif[orientation]
        if o == 3:
            deg = 180
        if o == 6:
            deg = 270
        if o == 8:
            deg = 90
        if deg != 0:
            print("Rotating by {d} degrees".format(d=deg))
            img = img.rotate(deg, expand=True)
            (w, h) = img.size
    except (AttributeError, KeyError, IndexError) as e:
        print("No exif info found (ERR: {err})".format(err=e))
        pass
    img = img.convert("RGBA")
    ratio = w * 1.0 / h * 1.0
    print("FOUND w:{w}, h:{h}, ratio={r}".format(w=w, h=h, r=ratio))
    if w > h:
        print("Horizontal image")
        if ratio > (h_lim["w"] / h_lim["h"]):
            print("Cropping image")
            cut = int(ceil((w - h * h_lim["w"] / h_lim["h"]) / 2))
            left = cut
            right = w - cut
            top = 0
            bottom = h
            img = img.crop((left, top, right, bottom))
            (w, h) = img.size
        if w > 1080:
            print("Resizing image")
            nw = 1080
            nh = int(ceil(1080.0 * h / w))
            img = img.resize((nw, nh), Image.ANTIALIAS)
    elif w < h:
        print("Vertical image")
        if ratio < (v_lim["w"] / v_lim["h"]):
            print("Cropping image")
            cut = int(ceil((h - w * v_lim["h"] / v_lim["w"]) / 2))
            left = 0
            right = w
            top = cut
            bottom = h - cut
            img = img.crop((left, top, right, bottom))
            (w, h) = img.size
        if h > 1080:
            print("Resizing image")
            nw = int(ceil(1080.0 * w / h))
            nh = 1080
            img = img.resize((nw, nh), Image.ANTIALIAS)
    else:
        print("Square image")
        if w > 1080:
            print("Resizing image")
            img = img.resize((1080, 1080), Image.ANTIALIAS)
    (w, h) = img.size
    new_fname = "{fname}.CONVERTED.jpg".format(fname=fname)
    print("Saving new image w:{w} h:{h} to `{f}`".format(w=w, h=h, f=new_fname))
    new = Image.new("RGB", img.size, (255, 255, 255))
    new.paste(img, (0, 0, w, h), img)
    buf = io.BytesIO()
    new.save(buf, quality=95, format='JPEG')

    return new, buf.getvalue(), buf.tell()
