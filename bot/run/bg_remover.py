import os

import cv2
import numpy as np
from rembg import remove


def remove_bg_ai(image_path, output_path):
    with open(image_path, "rb") as inp_file:
        input_image = inp_file.read()
    output_image = remove(input_image)
    with open(output_path, "wb") as out_file:
        out_file.write(output_image)


def extract_object_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    # Находим самый крупный контур
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

    # Формируем изображение с альфа-каналом
    b, g, r = cv2.split(img)
    result = cv2.merge([b, g, r, mask])
    return result


for type in ["armor", "accessories", "weapon"]:
    path = f"./bot/data/templates/obj/{type}"
    dir_list = os.listdir(path)
    for file in dir_list:
        if not file.endswith(".png"):
            continue
        input_path = os.path.join(path, file)
        output_path = input_path.replace("obj", "obj_no_bg")
        # remove_bg_ai(input_path, output_path)


# # Вывод списка
# for file in dir_list:
#     print(file)

# remove_bg_ai(
#     "./bot/data/templates/obj/armor/ash_trees.png",
#     "./bot/data/templates/obj_no_bg/armor/ash_trees_no_bg.png",
# )
