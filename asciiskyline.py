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

helpmsg = "Commands: r:reset skyline, f:firework, q:quit, +:speed up, -:speed down, s:reset speed, F:toggle flasher, d:debug"

# star colors
curses.init_pair(1, 14, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(3, 11, curses.COLOR_BLACK)

# office window color
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

# flasher color
curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

# dead firework color
curses.init_pair(6, 8, curses.COLOR_BLACK)

# fireworks colors
curses.init_pair(7, 9, curses.COLOR_BLACK)
curses.init_pair(8, 21, curses.COLOR_BLACK)
curses.init_pair(9, 7, curses.COLOR_BLACK)
curses.init_pair(10, 10, curses.COLOR_BLACK)
curses.init_pair(11, 199, curses.COLOR_BLACK)
curses.init_pair(12, 129, curses.COLOR_BLACK)


rows, cols = screen.getmaxyx()


class Skyline:

    debug = False

    screen = None

    rows, cols = rows, cols

    stars = []
    star_rate = 4
    star_chars = ["*"] * 1 + ["."] * 6 + ["+"] * 3
    star_max = int((cols * rows) / 50)

    buildings = []
    office_chars = ["#", "█"]
    office_rate = 8

    meteoroid = None

    flasher = True  # do you want the tallest building to have a blinking flasher light up top?
    flasher_char = "o"
    flasher_position = None
    flasher_rate = 100
    flasher_state = 0

    fireworks = []
    firework_rate = 15

    display_message = {}

    speed = 10
    default_speed = 10
    tick = 0


skyline = Skyline()


def behindBuilding(position_x, position_y):
    for building in skyline.buildings:
        if position_x in range(
            building["position_x"], building["position_x"] + building["width"]
        ):
            rangey = range(skyline.rows - building["height"], skyline.rows)
            if position_y in rangey:
                return True
    return False


def drawSym(x, y, symbol, color=None, background=True):
    if background and behindBuilding(x, y):
        return
    if color:
        color = curses.color_pair(color)
        try:
            screen.addstr(
                y,
                x,
                symbol,
                color,
            )
        except:
            pass
    else:
        try:
            screen.addstr(
                y,
                x,
                symbol,
            )
        except:
            pass

    return


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
        if loop + position_x > skyline.cols:
            break
        for loop in range(building_height):
            cur_height += 1
            if not cur_height % 2 and not (position_x + cur_width) % 2:
                building["offices_unlit"].append([cur_width, cur_height])
        cur_height = 0
        cur_width += 1
    return cur_width


def setupSkyline():

    #####
    # make all the buildings
    skyline.buildings = []
    skyline.stars = []
    skyline.fireworks = []
    skyline.flasher_position = None
    skyline.flasher_state = 0
    blds = 0
    position_x = 0
    while position_x < skyline.cols:
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


setupSkyline()


def starLoop():
    starchar = random.choice(skyline.star_chars)
    nstar_x = random.choice(range(skyline.cols))
    if nstar_x >= skyline.cols:
        nstar_x -= 1
    nstar_y = skyline.rows - random.choice(range(skyline.rows)) - 1
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
                    skyline.rows - unlit[1],
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
                skyline.rows - poofwindow[1],
                building["position_x"] + poofwindow[0],
                " ",
            )
            building["offices_lit"].remove(poofwindow)
            building["offices_unlit"].append(poofwindow)

    return


def flasherLoop():
    if not skyline.flasher_state:
        if skyline.flasher:
            screen.addstr(
                skyline.rows - skyline.flasher_position[1],
                skyline.flasher_position[0],
                skyline.flasher_char,
                curses.color_pair(5),
            )
            skyline.flasher_state = 1
    else:
        screen.addstr(
            skyline.rows - skyline.flasher_position[1],
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


def spawnFirework(x=0, y=0, color=None):
    if not color:
        color = random.randint(7, 12)

    if not x and not y:
        x = random.randint(1, skyline.cols)
        y = skyline.rows - (random.randint(skyline.flasher_position[1], skyline.rows))

    skyline.fireworks.append(
        {
            "x": x,
            "y": y,
            "color": color,
            "stage": 0,
            "rays": [],
        }
    )


def fireworks():
    for firework in list(skyline.fireworks):
        fw_x = firework["x"]
        fw_y = firework["y"]
        if firework["stage"] == 0:
            drawSym(
                fw_x,
                fw_y,
                ".",
                firework["color"],
            )
        elif firework["stage"] == 1:
            drawSym(
                fw_x,
                fw_y,
                "o",
                firework["color"],
            )
        elif firework["stage"] == 2:
            drawSym(
                fw_x,
                fw_y,
                "*",
                firework["color"],
            )
            ray_x = fw_x - 1
            ray_y = fw_y - 1
            for ray in ["\\", "|", "/"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 1

            ray_x = fw_x - 1
            ray_y = fw_y + 0
            for ray in ["-", "-"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 2

            ray_x = fw_x - 1
            ray_y = fw_y + 1
            for ray in ["/", "|", "\\"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 1

        elif firework["stage"] == 3:
            for ray in list(firework["rays"]):
                drawSym(ray[0], ray[1], " ")
                firework["rays"].remove(ray)

            drawSym(
                fw_x,
                fw_y,
                " ",
                firework["color"],
            )
            ray_x = fw_x - 2
            ray_y = fw_y - 2
            for ray in ["\\", "|", "/"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 2

            ray_x = fw_x - 3
            ray_y = fw_y + 0
            for ray in ["-", "-"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 6

            ray_x = fw_x - 2
            ray_y = fw_y + 2
            for ray in ["/", "|", "\\"]:
                firework["rays"].append([ray_x, ray_y])
                drawSym(
                    ray_x,
                    ray_y,
                    ray,
                    firework["color"],
                )
                ray_x += 2

        elif firework["stage"] == 4:
            for ray in firework["rays"]:
                drawSym(
                    ray[0],
                    ray[1],
                    ".",
                    firework["color"],
                )
        elif firework["stage"] == 5:
            for ray in firework["rays"]:
                drawSym(ray[0], ray[1], " ")
                drawSym(
                    ray[0],
                    ray[1] + 1,
                    ".",
                    firework["color"],
                )
        elif firework["stage"] == 6:
            for ray in firework["rays"]:
                drawSym(ray[0], ray[1] + 1, " ")
                drawSym(
                    ray[0],
                    ray[1] + 2,
                    ".",
                    firework["color"],
                )
        elif firework["stage"] == 7:
            for ray in firework["rays"]:
                drawSym(ray[0], ray[1] + 2, " ")
                drawSym(ray[0], ray[1] + 3, ".", 6)

        else:

            for ray in list(firework["rays"]):
                drawSym(ray[0], ray[1] + 3, " ")
                firework["rays"].remove(ray)

            drawSym(fw_x, fw_y, " ")
            skyline.fireworks.remove(firework)

        firework["stage"] += 1

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

        if skyline.flasher_position and not skyline.tick % skyline.flasher_rate:
            flasherLoop()

        if not skyline.tick % skyline.firework_rate:
            fireworks()

        if skyline.debug:
            debugmsg = f"Stars:{len(skyline.stars)}/{skyline.star_max} Bldgs:{len(skyline.buildings)} Size:{skyline.cols}x{skyline.rows}"
            displayMessage(
                debugmsg,
                msgtype="debug",
                x=skyline.cols - len(debugmsg),
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
        elif key in [113, 27]:
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
        # F: toggle tallest building flasher
        elif key == 70:
            if skyline.flasher:
                skyline.flasher = False
                displayMessage(f"Tallest building flasher OFF.")
            else:
                skyline.flasher = True
                displayMessage(f"Tallest building flasher ON.")
        # r: reset skyline
        elif key in [114, curses.KEY_RESIZE]:
            screen.clear()
            skyline.rows, skyline.cols = screen.getmaxyx()
            setupSkyline()
            msg = "Skyline reset."
            if key == curses.KEY_RESIZE:
                msg = f"Terminal size changed: {msg}"
            displayMessage(msg)
        # f: firework
        elif key == 102:
            spawnFirework()
        # ?: help
        elif key in [47, 63]:
            displayMessage(helpmsg)
        # d: debug
        elif key == 100:
            if skyline.debug:
                skyline.debug = False
                msg = "Debug mode: OFF"
                displayMessage(" ", msgtype="debug", x=skyline.cols - 1, y=0)
            else:
                skyline.debug = True
                msg = "Debug mode: ON"

            displayMessage(msg)
        # unused key: prompt to press ? for help
        else:
            msg = "(Press ? for help)"
            if skyline.debug:
                msg += f" (key pressed: {key})"
            displayMessage(f"{msg}")
    # main loop
    #####


wrapper(main)
