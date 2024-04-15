from typing import List
from PIL import Image
from io import BytesIO

from loader import client


async def _get_photos(sizes: List[str]) -> list:
    photos = []
    for url in sizes:
        image_data = await client.request_content(url)
        photos.append(Image.open(BytesIO(image_data)))
    return photos


def _glue_horizontal(img1: Image, img2: Image, boards: bool = False, color: str = "white") -> Image:
    if img1.size[1] > img2.size[1]:
        img2 = img2.resize((int(img2.size[0] * (img1.size[1]/img2.size[1])), img1.size[1]))
    elif img1.size[1] < img2.size[1]:
        img1 = img1.resize((int(img1.size[0] * (img2.size[1] / img1.size[1])), img2.size[1]))
    img = Image.new("RGB", (img1.size[0]+img2.size[0]+boards*30, img1.size[1]), color)
    img.paste(img1, (0, 0))
    img.paste(img2, (img1.size[0]+boards*30, 0))
    return img


def _glue_vertical(img1: Image, img2: Image, boards: bool = False, color: str = "white") -> Image:
    if img1.size[0] > img2.size[0]:
        img2 = img2.resize((img1.size[0], int(img2.size[1] * (img1.size[0] / img2.size[0]))))
    elif img1.size[0] < img2.size[0]:
        img1 = img1.resize((img2.size[0], int(img1.size[1] * (img2.size[0] / img1.size[0]))))
    img = Image.new("RGB", (img1.size[0], img1.size[1] + img2.size[1] + boards * 30), color)
    img.paste(img1, (0, 0))
    img.paste(img2, (0, img1.size[1] + boards * 30))
    return img


def _glue_tile(imgs: list, columns: int = 2, boards=False, color="white") -> Image:
    intermediate_imgs = []
    if columns == 1:
        img = None
        for i in range(len(imgs)-1):
            if img is None:
                img = _glue_vertical(imgs[i], imgs[i+1], boards, color)
            else:
                img = _glue_vertical(img, imgs[i+1], boards, color)
        return img
    for i1 in range(len(imgs)//columns):
        img = None
        for i in range(columns-1):
            if img is None:
                img = _glue_horizontal(imgs[i1*columns+i], imgs[i1*columns+1+i], boards, color)
            else:
                img = _glue_horizontal(img, imgs[i1*columns+1+i], boards, color)
        intermediate_imgs.append(img)
    if len(intermediate_imgs) == 1:
        return intermediate_imgs[0]
    img_final = None
    for i in range(len(intermediate_imgs)-1):
        if img_final is None:
            img_final = _glue_vertical(intermediate_imgs[i], intermediate_imgs[i+1], boards, color)
        else:
            img_final = _glue_vertical(img_final, intermediate_imgs[i+1], boards, color)
    return img_final


async def glue(sizes: List[str], columns, upper, lower, boards, color, user_id) -> Image:
    photos = await _get_photos(sizes)
    if not upper and not lower:
        img = _glue_tile(photos, columns, boards, color)
    if upper:
        img1 = _glue_tile(photos[1:], columns, boards, color)
        img = _glue_vertical(photos[0], img1, boards, color)
    if lower:
        img1 = _glue_tile(photos[:-1], columns, boards, color)
        img = _glue_vertical(photos[-1], img1, boards, color)
    img.save(f"{user_id}.jpg")


