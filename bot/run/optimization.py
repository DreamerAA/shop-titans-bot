from os import listdir
from os.path import isfile, join

import cv2
from utility import color_filter, load_cv_image

from bot.matching.ocr import extract_number_with_commas
from bot.settings import get_settings


def find_best_g(folder):
    settings = get_settings()
    methods = {
        "default": lambda x: cv2.threshold(x, 165, 175, cv2.THRESH_BINARY)[1],
        "coloring": lambda x: color_filter(x, settings.rgb_raise_unav),
    }
    best_result = None
    best_g = None
    print("Start")
    results = {}
    results_counter = {}
    full_folder = join("bot", "data", "test_images", folder)
    expecteds = [f[:-4] for f in listdir(full_folder) if isfile(join(full_folder, f))]
    count_files = len(expecteds)
    for name in expecteds:
        part_screen = load_cv_image(join(folder, name))
        for mname, method in methods.items():
            result = extract_number_with_commas(part_screen, preprocess_func=method)
            if len(result) != 1:
                continue
            result = result[0]
            expected = name[:-2]
            if result[0] != expected:
                continue
            nr = result[2] / count_files
            if mname in results:
                results[mname] += nr
                results_counter[mname] += 1
            else:
                results[mname] = nr
                results_counter[mname] = 1
        # print("results: ", results)
    for k, v in results_counter.items():
        if v != count_files:
            results[k] = 0
    best_result = max(results.values())
    best_g = max(results, key=results.get)
    print("Best result: ", best_result, best_g)


find_best_g("unavaliable_raise")
