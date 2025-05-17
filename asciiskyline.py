#!/usr/bin/env python3

"""
Creates a little starry city skyline in your terminal, just because it's nice to look at.  Inspired by the Starry Skyline module of the After Dark screensavers of old.  Uses curses.
Original author: whelk, who couldn't sleep on the night of 2025-05-16
"""

import curses, os, random
from curses import wrapper

screen = curses.initscr()
screen.nodelay(True)

curses.cbreak()
curses.noecho()  # dont print pressed keys
curses.start_color()

helpmsg = "Commands: q: quit, d: debug, +: speed up, -: speed down, s: reset speed"

# star colors
curses.init_pair(1, 14, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(3, 11, curses.COLOR_BLACK)

# office window color
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

# flasher color
curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

num_rows, num_cols = screen.getmaxyx()


class Skyline:

    debug = False

    screen = None
    window_x = num_cols
    window_y = num_rows

    stars = []
    star_rate = 4
    star_chars = ["*"] * 1 + ["."] * 6 + ["+"] * 3
    star_max = int((window_x * window_y) / 50)

    buildings = []
    office_chars = ["#", "█"]
    office_rate = 8

    meteoroid = None

    flasher = True  # do you want the tallest building to have a blinking flasher light up top?
    flasher_char = "o"
    flasher_position = None
    flasher_rate = 100
    flasher_state = 0

    display_message = {}

    speed = 10
    tick = 0


skyline = Skyline()
skyline.default_speed = skyline.speed


def behindBuilding(position_x, position_y):
    for building in skyline.buildings:
        if position_x in range(
            building["position_x"], building["position_x"] + building["width"]
        ):
            rangey = range(num_rows - building["height"], num_rows)
            if position_y in rangey:
                return True
    return False


def makeBuilding(position_x):
    window_choices = skyline.office_chars + []
    prev = None
    if skyline.buildings:
        prev = skyline.buildings[-1]
        window_choices.remove(prev["window"])
    window = random.choice(window_choices)
    building_width = random.randint(8, 12)
    building_height = random.randint(4, 15)
    if prev and building_height in range(prev["height"] - 2, prev["height"] + 2):
        building_height = random.choice([building_height + 3, building_height + 6])
    cur_width = 0
    cur_height = 0

    unlit_min = max(1, int(building_height / 3))
    building = {
        "position_x": position_x,
        "height": building_height,
        "width": building_width,
        "window": window,
        "offices_lit": [],
        "offices_unlit": [],
        "unlit_min": unlit_min,
    }
    skyline.buildings.append(building)
    for loop in range(building_width):
        if loop + position_x > num_cols:
            break
        for loop in range(building_height):
            cur_height += 1
            if not cur_height % 2 and not (position_x + cur_width) % 2:
                building["offices_unlit"].append([cur_width, cur_height])
        cur_height = 0
        cur_width += 1
    return cur_width


#####
# make all the buildings
blds = 0
position_x = 0
while position_x < num_cols:
    blds += 1
    try:
        position_x = position_x + makeBuilding(position_x)
    except:
        break

tallest_building = None
for building in skyline.buildings:
    if not tallest_building or building["height"] > tallest_building["height"]:
        tallest_building = building
if tallest_building:
    skyline.tallest_building = tallest_building
    skyline.flasher_position = [
        tallest_building["position_x"] + int(tallest_building["width"] / 2),
        tallest_building["height"] + 1,
    ]

# make all the buildings
#####


def starLoop():
    starchar = random.choice(skyline.star_chars)
    nstar_x = random.choice(range(num_cols))
    if nstar_x >= num_cols:
        nstar_x -= 1
    nstar_y = num_rows - random.choice(range(num_rows)) - 1
    coords = [nstar_x, nstar_y]

    # add a star
    if (
        len(skyline.stars) <= skyline.star_max
        and not behindBuilding(nstar_x, nstar_y)
        and not [nstar_x, nstar_y] == skyline.flasher_position
        and coords not in skyline.stars
    ):
        skyline.stars.append(coords)
        try:
            star_color = random.choice([1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3])
            screen.addstr(nstar_y, nstar_x, starchar, curses.color_pair(star_color))
        except:
            print(f"{nstar_x=} {nstar_y=}")
            exit()

    # remove a star
    if len(skyline.stars) >= skyline.star_max:
        poofstar = random.choice(skyline.stars)
        screen.addstr(poofstar[1], poofstar[0], " ")
        skyline.stars.remove(poofstar)

    return


def officeLoop():
    for building in skyline.buildings:
        if len(building["offices_unlit"]) > building["unlit_min"]:

            # Try to avoid re-lighting the offices that just went dark
            office_choices = building["offices_unlit"] + []
            if len(office_choices) > 1:
                office_choices.remove(office_choices[-1])

            unlit = random.choice(office_choices)
            try:
                screen.addstr(
                    num_rows - unlit[1],
                    building["position_x"] + unlit[0],
                    building["window"],
                    curses.color_pair(3),
                )
                building["offices_unlit"].remove(unlit)
                building["offices_lit"].append(unlit)
            except:
                pass

        elif building["offices_lit"] and random.randint(1, 100) > 98:
            poofwindow = random.choice(building["offices_lit"])
            screen.addstr(
                num_rows - poofwindow[1],
                building["position_x"] + poofwindow[0],
                " ",
            )
            building["offices_lit"].remove(poofwindow)
            building["offices_unlit"].append(poofwindow)

    return


def flasherLoop():
    if not skyline.flasher_state:
        screen.addstr(
            num_rows - skyline.flasher_position[1],
            skyline.flasher_position[0],
            skyline.flasher_char,
            curses.color_pair(5),
        )
        skyline.flasher_state = 1
    else:
        screen.addstr(
            num_rows - skyline.flasher_position[1],
            skyline.flasher_position[0],
            " ",
        )
        skyline.flasher_state = 0

    return


def displayMessageLoop():
    for msgtype, msg in list(skyline.display_message.items()):
        screen.addstr(
            msg["y"],
            msg["x"],
            msg["text"],
        )
        msg["time"] += 1
        if msg["time"] >= msg.get("duration", 100):
            screen.addstr(
                msg["y"],
                msg["x"],
                " " * len(msg["text"]),
            )
            del skyline.display_message[msgtype]

    return


def displayMessage(message, msgtype="default", x=0, y=0, duration=0):
    # clean up previous message if it exists
    prevmsg = skyline.display_message.get(msgtype)
    if prevmsg:
        screen.addstr(
            prevmsg["y"],
            prevmsg["x"],
            " " * len(prevmsg["text"]),
        )

    # set display message for displayMessageLoop() to handle
    if not duration:
        duration = 100
        duration += len(message) * 10
    skyline.display_message[msgtype] = {
        "text": message,
        "time": 0,
        "x": x,
        "y": y,
        "duration": duration,
    }

    return


def main(screen):
    #####
    # main loop
    while True:

        curses.curs_set(0)
        skyline.tick += 1

        if not skyline.tick % skyline.star_rate:
            starLoop()

        if not skyline.tick % skyline.office_rate:
            officeLoop()

        if (
            skyline.flasher
            and skyline.flasher_position
            and not skyline.tick % skyline.flasher_rate
        ):
            flasherLoop()

        if skyline.debug:
            debugmsg = f"Stars: {len(skyline.stars)}/{skyline.star_max} Buildings: {len(skyline.buildings)}"
            displayMessage(
                debugmsg,
                msgtype="debug",
                x=num_cols - len(debugmsg),
                y=0,
                duration=10,
            )

        displayMessageLoop()

        screen.refresh()
        curses.napms(skyline.speed)
        if skyline.tick > 999:
            skyline.tick = 0

        key = screen.getch()
        # no key pressed
        if key == -1:
            pass
        # q: quit
        elif key == 113:
            exit()
        # h: hi
        elif key == 104:
            displayMessage("Hello there!", msgtype="hi", x=0, y=1)
        # s: speed to default
        elif key == 115:
            displayMessage("Speed set to default.")
            skyline.speed = skyline.default_speed + 0
        # +/=: increase speed (technically decrease wait time beetween ticks)
        elif key in [61, 43]:
            current = skyline.speed
            adjust = 1
            if current > 10:
                adjust = 10
            if skyline.speed <= 1:
                displayMessage("Can't go any faster!!")
            else:
                skyline.speed -= adjust
                displayMessage(f"Tick length is now: {skyline.speed}")
        # -/_: decrease speed (technically increase wait time beetween ticks)
        elif key in [45, 95]:
            adjust = 1
            current = skyline.speed
            if current >= 10:
                adjust = 10
            skyline.speed += adjust
            displayMessage(f"Tick length is now: {skyline.speed}")
        # d: debug
        elif key == 100:
            if skyline.debug:
                skyline.debug = False
                msg = "Debug mode: OFF"
                displayMessage(" ", msgtype="debug", x=num_cols - 1, y=0)
            else:
                skyline.debug = True
                msg = "Debug mode: ON"

            displayMessage(msg)
        # unused key: show help msg
        else:
            msg = helpmsg + ""
            if skyline.debug:
                msg += f" (key pressed: {key})"
            displayMessage(f"{msg}")
    # main loop
    #####


wrapper(main)
