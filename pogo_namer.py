from ppadb.client import Client
from PIL import Image
import numpy
import time
import collections
import pytesseract
import cv2
from datetime import datetime
from Pokemon import Pokemon
import json
import sys

# phone
HEIGHT = 1920
WIDTH = 1080

# coordinates
BACKSPACE_COORD = (990, 1550)
EDIT_COORD = (WIDTH / 2, 855)
KEYBOARD_OK = (941, 1021)
POGO_OK = (570, 983)
OPTIONS = (940, 1640)
APPRAISE = (925, 1280)
SAFE = (WIDTH / 2, 200)
TEXTBOX = (40, 1500, 1000, 1740)


# IV coordinates
y_ATTACK_COORD = 1283 + 7
y_DEFENSE_COORD = 1379 + 7
y_HEALTH_COORD = 1475 + 7
x_IV_OFFSET = 130
x_IV_WIDTH = 325

# pixel number for IV bars
pxl_ATTACK = (
    y_ATTACK_COORD * WIDTH + x_IV_OFFSET,
    y_ATTACK_COORD * WIDTH + x_IV_OFFSET + x_IV_WIDTH,
)
pxl_DEFENSE = (
    y_DEFENSE_COORD * WIDTH + x_IV_OFFSET,
    y_DEFENSE_COORD * WIDTH + x_IV_OFFSET + x_IV_WIDTH,
)
pxl_HEALTH = (
    y_HEALTH_COORD * WIDTH + x_IV_OFFSET,
    y_HEALTH_COORD * WIDTH + x_IV_OFFSET + x_IV_WIDTH,
)

# IV RGBA value
IV_COLOR = (238, 146, 25, 255)
PERFECT_IV_COLOR = (225, 128, 121, 255)


def tap_keyboard_ok():
    device.input_tap(*KEYBOARD_OK)


def tap_pogo_ok():
    device.input_tap(*POGO_OK)


def tap_safe():
    device.input_tap(*SAFE)


def tap_options():
    device.input_tap(*OPTIONS)


def tap_appraise():
    device.input_tap(*APPRAISE)


def delete_name():
    device.input_swipe(*BACKSPACE_COORD, *BACKSPACE_COORD, 1500)


def next_mon():
    device.input_swipe(1000, 1000, 250, 1000, 1000)


def edit_name():
    device.input_tap(*EDIT_COORD)


def write_name(name):
    device.input_text(name)


def iv_count(li):
    if PERFECT_IV_COLOR in li:
        return 15

    return round(li.count(IV_COLOR) / 20.15)


def recreate_image(px):
    image_out = Image.new(image.mode, image.size)
    image_out.putdata(px)
    image_out.save("test_out.png")


def name_builder(IV):
    iv_string = "-".join(map(str, IV))
    percent = round(sum(IV) / 45 * 100)
    if percent == 69:
        percent += 1

    if sum(IV) == 0:
        return "error"

    return "-".join([iv_string, str(percent) + "%"])


def replace_pixels(px, _range, color):
    for i in range(_range[0], _range[1]):
        px[i] = color
    return px


def get_date(date_str):
    return datetime.strptime(date_str, "%m/%d/%Y").date()


def get_location(info):
    return info[info.index("around") + 1 :]


def total_IV(iv_px):
    appraisal_offset = 0
    if px[1000 + 1080 * 1525] == (255, 255, 255, 255):
        appraisal_offset = 60 * 1080
        print("offset")

    return [
        iv_count(
            px[pxl_ATTACK[0] - appraisal_offset : pxl_ATTACK[1] - appraisal_offset]
        ),
        iv_count(
            px[pxl_DEFENSE[0] - appraisal_offset : pxl_DEFENSE[1] - appraisal_offset]
        ),
        iv_count(
            px[pxl_HEALTH[0] - appraisal_offset : pxl_HEALTH[1] - appraisal_offset]
        ),
    ]


# main
trading = False
if sys.argv[1] == "trading":
    trading = True


previous_IVs = collections.deque([-1, -2, -3], 3)

# create connection
adb = Client(host="127.0.0.1", port=5037)
devices = adb.devices()

if len(devices) == 0:
    print("no device attached")
    quit()

device = devices[0]

json_file = open("dict.json")
my_dict = json.load(json_file)
json_file.close()

with open("poke_log.txt", "a") as log:
    log.write("\n\n")

    if trading:
        log.write(
            "RELABLING FOR TRADES - "
            + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            + "\n"
        )
    else:
        log.write(
            "RELABLING WITH IVS - "
            + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            + "\n"
        )

    log.write("---------------------")

    while True:
        tap_options()
        time.sleep(1)
        tap_appraise()
        time.sleep(0.5)
        tap_safe()
        time.sleep(1)
        image = device.screencap()
        tap_safe()

        with open("screen.png", "wb") as f:
            f.write(image)

        image = Image.open("screen.png")

        # use tesseract to read the textbox on the appraisal screen
        info = (
            pytesseract.image_to_string(image.crop(TEXTBOX))
            .replace("\n", " ")
            .split(sep=" ")
        )

        # sometimes tesseract reads 'around' as 'arounc' - not sure how to train yet
        if "arounc" in info:
            info[info.index("arounc")] = "around"

        # sometimes the phone lags and a screen shot is taken before the appraisal is ready
        if len(info) < 5 or "around" not in info:
            print("bad screenshot")
            continue

        # Get list of pixels in image
        px = list(image.getdata())

        # create pokemon
        Poke = Pokemon(info, total_IV(px), my_dict)

        # track last 3 ivs to check if at the end poke list
        previous_IVs.append(Poke.IVs)
        if previous_IVs[0] == previous_IVs[1] == previous_IVs[2]:
            print("done")
            exit()

        # edit the name
        # IV format: "atk-def-hp-total%"
        # trade format: "_<location_code>"
        time.sleep(1)
        edit_name()
        time.sleep(0.5)
        delete_name()

        if trading:
            write_name("_" + Poke.code)
        else:
            write_name(name_builder(Poke.IVs))

        tap_keyboard_ok()
        time.sleep(0.5)
        tap_pogo_ok()
        time.sleep(1)
        print(Poke)
        log.write(str(Poke) + "\n")

        next_mon()
