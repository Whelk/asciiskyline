#!/usr/bin/env python3

"""
Creates a little starry city skyline in your terminal, just because it's nice to look at.  Inspired by the Starry Skyline module of the After Dark screensavers of old.  Uses curses.
Original author: whelk, who couldn't sleep on the night of 2025-05-16
"""

import curses, math, os, random, time
from curses import wrapper

screen = curses.initscr()
screen.nodelay(True)

curses.cbreak()
curses.noecho()  # dont print pressed keys
curses.start_color()

helpmsg = "Commands: f:firework, m:meteor, M:meteor shower, r:rain, R: reset skyline, q:quit, +:speed up, -:speed down, s:snow, S:reset speed, a:alien rave, d:debug"

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
firework_colors = [7, 8, 9, 10, 11, 12]

meteor_colors = [1]

# alien rave colors:
rave_colors = []
for pair, (lit, unlit) in enumerate(
    [
        (198, 89),
        (201, 54),
        (51, 23),
        (196, 52),
        (208, 94),
        (46, 22),
        (141, 60),
        (226, 58),
    ]
):
    curses.init_pair(13 + pair * 2, lit, curses.COLOR_BLACK)
    curses.init_pair(14 + pair * 2, unlit, curses.COLOR_BLACK)
    rave_colors.append((13 + pair * 2, 14 + pair * 2))
curses.init_pair(29, 231, curses.COLOR_BLACK)
rave_flash = 29

# mothership:
mothership = [
    "        __________________        ",
    "    ,-''                  ''-,    ",
    "  ,'   .   .   .   .   .   .   ', ",
    " /______________________________\\ ",
    " \\    o       o       o       o / ",
    "  '----------------------------'  ",
]

rows, cols = screen.getmaxyx()


class Skyline:

    debug = False

    screen = None

    rows, cols = rows, cols

    stars = []
    star_rate = 4
    star_chars = ["*"] * 1 + ["."] * 6 + ["+"] * 3
    star_max = int((cols * rows) / 50)
    star_looks = {}  # (x, y): (char, color), so a star can be redrawn

    buildings = []
    office_chars = ["#", "█"]
    office_rate = 8

    flasher = True  # do you want the tallest building to have a blinking flasher light up top?
    flasher_char = "o"
    flasher_position = None
    flasher_rate = 100
    flasher_state = 0

    meteor_shower = 0  # is there currently a meteor shower?
    meteors = []
    meteor_rate = 2

    snowing = False  # is it currently snowing?
    snowing_duration = 0
    snowflake_char = "*"
    snowflakes = []
    snowflake_rate = 10

    fireworks = []
    firework_rate = 15

    display_message = {}

    speed = 10
    default_speed = 10
    tick = 0

    raining = False  # is it currently raining?
    raining_duration = 0  # to have rain ramp up/down gradually
    raindrop_char = "\\"
    raindrops = []
    raindrop_rate = 4

    raving = False  # is there currently an alien rave?
    rave_bpm = 141
    rave_star_boost = 6  # the sky fills up with this many times the stars
    rave_start = 0
    rave_step = None  # the part of the beat the sky was last painted for
    rave_drawn = 0
    rave_cells = {}  # (x, y): (char, color) of the beams and craft on screen


skyline = Skyline()


def behindBuilding(position_x, position_y):
    for building in skyline.buildings:
        if position_x in range(
            building["position_x"], building["position_x"] + building["width"]
        ):
            rangey = range(skyline.rows - building["height"], skyline.rows + 1)
            if position_y in rangey:
                return building
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


def clearFluff(x, y):
    # Clear a coordinate and redraw a star or building window if necessary
    building = behindBuilding(x, y)
    if building and [x, y] in building["offices_lit"]:
        screen.addstr(
            y,
            x,
            building["window"],
            curses.color_pair(3),
        )
    else:
        drawSym(x, y, " ", background=False)


def makeBuilding(position_x):
    window_choices = skyline.office_chars + []
    prev = None
    if skyline.buildings:
        prev = skyline.buildings[-1]
        window_choices.remove(prev["window"])
    window = random.choice(window_choices)
    building_width = random.choice([8, 10, 12, 14])
    building_height = random.choice([4, 6, 8, 10, 12, 14])
    if prev and building_height in range(prev["height"] - 2, prev["height"] + 2):
        building_height = random.choice([building_height + 2, building_height + 6])
    cur_width = 0
    cur_height = 0

    unlit_min = max(1, int(building_height / random.randint(1, 4)))
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
                x = position_x + cur_width
                y = skyline.rows - cur_height
                building["offices_unlit"].append([x, y])
        cur_height = 0
        cur_width += 1
    return cur_width


def setupSkyline():

    #####
    # make all the buildings
    skyline.buildings = []
    skyline.stars = []
    skyline.star_looks = {}
    skyline.rave_cells = {}
    skyline.rave_step = None
    skyline.fireworks = []
    skyline.raindrops = []
    skyline.raining = False
    skyline.raining_duration = 0
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

        flasher_x = tallest_building["position_x"] + int(tallest_building["width"] / 2)
        flasher_x -= 1
        flasher_x = min([flasher_x, skyline.cols - 1])
        flasher_x = max([flasher_x, 1])

        flasher_y = tallest_building["height"] + 2
        flasher_y = min([flasher_y, skyline.rows - 1])
        flasher_y = max([flasher_y, 1])

        skyline.flasher_position = [flasher_x, flasher_y]

    # make all the buildings
    #####


setupSkyline()


def starLoop():
    starchar = random.choice(skyline.star_chars)
    nstar_x = random.choice(range(skyline.cols - 1))
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
            skyline.star_looks[(nstar_x, nstar_y)] = (starchar, star_color)
            screen.addstr(nstar_y, nstar_x, starchar, curses.color_pair(star_color))
        except:
            print(f"{nstar_x=} {nstar_y=}")
            exit()

    # remove a star
    if len(skyline.stars) >= skyline.star_max:
        poofstar = random.choice(skyline.stars)
        screen.addstr(poofstar[1], poofstar[0], " ")
        skyline.stars.remove(poofstar)
        skyline.star_looks.pop((poofstar[0], poofstar[1]), None)

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
                    unlit[1],
                    unlit[0],
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
                poofwindow[1],
                poofwindow[0],
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


def spawnMeteor(x=0, direction=None, color=None):
    if not direction:
        direction = random.choice(["right", "left"])
    if not color:
        color = random.choice(meteor_colors)
    if not x:
        x = random.randint(1, skyline.cols)
    y = 0

    meteor = {"x": x, "y": y, "direction": direction, "color": color}
    skyline.meteors.append(meteor)


def meteorLoop():
    meteor_chance = 2
    if skyline.meteor_shower:
        meteor_chance = 150
    if random.randint(1, 1000) <= meteor_chance:
        spawnMeteor()
    for meteor in list(skyline.meteors):
        drawSym(
            meteor["x"],
            meteor["y"],
            " ",
        )
        drawSym(
            meteor["x"] - 1,
            meteor["y"] - 1,
            " ",
        )
        drawSym(
            meteor["x"] - 2,
            meteor["y"] - 2,
            " ",
        )

        meteor["x"] += 1
        meteor["y"] += 1
        if meteor["y"] >= 14:
            meteor["color"] = 6

        if (
            meteor["y"] >= 20
            or meteor["x"] > skyline.cols
            or meteor["y"] > skyline.rows
        ):
            skyline.meteors.remove(meteor)
            continue

        drawSym(
            meteor["x"],
            meteor["y"],
            "*",
            meteor["color"],
        )
        drawSym(
            meteor["x"] - 1,
            meteor["y"] - 1,
            "\\",
            meteor["color"],
        )
        drawSym(
            meteor["x"] - 2,
            meteor["y"] - 2,
            "\\",
            meteor["color"],
        )


def spawnFirework(x=0, y=0, color=None):
    if not color:
        colorchoice = list(firework_colors)

        # avoid same color firework twice in a row
        if skyline.fireworks:
            colorchoice.remove(skyline.fireworks[-1]["color"])

        color = random.choice(colorchoice)

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


def fireworkLoop():
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


def rainLoop():

    #####
    # produce new raindrops
    if skyline.raining or skyline.raining_duration:

        duration_max = 1000

        # rain density ramp up/down over time rather than immediate start/stop
        if skyline.raining and skyline.raining_duration < duration_max:
            # ramp up slowly
            skyline.raining_duration += 2
        elif not skyline.raining and skyline.raining_duration:
            # ramp down more quickly but still gradual
            skyline.raining_duration -= 10
            if skyline.raining_duration < 0:
                skyline.raining_duration = 0

        last_drop = 0  # to have minimum space between raindrops
        raindrop_chance = duration_max - (skyline.raining_duration / 35)

        raindrop_y = 0 if skyline.rows % 2 else 1  # avoid window collisions

        # produce raindrops across top of screen
        for col in range(skyline.cols):
            last_drop -= 1
            if last_drop <= 0 and random.randint(1, duration_max) > raindrop_chance:
                raindrop = {"x": col, "y": raindrop_y}
                skyline.raindrops.append(raindrop)
                last_drop = 20

        # produce raindrops along left side so there's not a bare patch there
        # (since they're moving slightly to the right as they fall)
        for row in range(skyline.rows):
            last_drop -= 1
            if last_drop <= 0 and random.randint(1, 1000) > raindrop_chance:
                raindrop_y = row
                # fixes window collisions for odd-height screen
                if raindrop_y % 2 and skyline.rows % 2:
                    raindrop_y += 1
                # fixes window collisions for even-height screen
                elif not raindrop_y % 2 and not skyline.rows % 2:
                    raindrop_y += 1
                raindrop = {"x": 0, "y": raindrop_y}
                skyline.raindrops.append(raindrop)
                last_drop = 20
    # produce new raindrops
    #####

    #####
    # draw/move existing raindrops
    for drop in list(skyline.raindrops):

        # remove previous drawing of raindrop if exists
        if "prev_x" in drop:
            drawSym(drop["prev_x"], drop["prev_y"], " ", background=False)

        # remove raindrop if it's beyond the screen edge
        if drop["x"] > skyline.cols or drop["y"] > skyline.rows:
            skyline.raindrops.remove(drop)
            continue

        drawSym(drop["x"], drop["y"], skyline.raindrop_char, background=False)

        # remember current location of drop and set next location
        drop["prev_x"] = drop["x"] + 0
        drop["prev_y"] = drop["y"] + 0
        drop["x"] += 1
        drop["y"] += 2
    # draw/move existing raindrops
    #####

    return


def snowLoop():

    #####
    # produce new snowflakes
    if skyline.snowing or skyline.snowing_duration:

        duration_max = 1000

        # snow density ramp up/down over time rather than immediate start/stop
        if skyline.snowing and skyline.snowing_duration < duration_max:
            # ramp up slowly
            skyline.snowing_duration += 2
        elif not skyline.snowing and skyline.snowing_duration:
            # ramp down more quickly but still gradual
            skyline.snowing_duration -= 10
            if skyline.snowing_duration < 0:
                skyline.snowing_duration = 0

        last_snowflake = 0  # to have minimum space between snowflakes
        snowflake_chance = duration_max - (skyline.snowing_duration / 35)

        snowflake_y = 0 if skyline.rows % 2 else 1  # avoid window collisions

        # produce snowflakes across top of screen
        for col in range(skyline.cols):
            last_snowflake -= 1
            if (
                last_snowflake <= 0
                and random.randint(1, duration_max) > snowflake_chance
            ):
                snowflake = {"x": col, "y": snowflake_y}
                skyline.snowflakes.append(snowflake)
                last_snowflake = 20

    # produce new snowflakes
    #####

    #####
    # draw/move existing snowflakes
    for snowflake in list(skyline.snowflakes):

        # remove snowflake if it's beyond the screen edge
        if snowflake["x"] > skyline.cols or snowflake["y"] > skyline.rows:
            skyline.snowflakes.remove(snowflake)
            continue

        building = behindBuilding(snowflake["x"], snowflake["y"])

        poof_previous = True

        if building and [snowflake["x"], snowflake["y"]] in building["offices_lit"]:
            pass
        else:
            drawSym(
                snowflake["x"],
                snowflake["y"],
                skyline.snowflake_char,
                color=2,
                background=False,
            )

        if building and snowflake["y"] == skyline.rows - building["height"]:
            poof_previous = False

        if poof_previous:
            # remove previous drawing of snowflake if exists
            if "prev_x" in snowflake and snowflake["y"] < skyline.rows:
                clearFluff(snowflake["prev_x"], snowflake["prev_y"])

        # remember current location of snowflake and set next location
        snowflake["prev_x"] = snowflake["x"] + 0
        snowflake["prev_y"] = snowflake["y"] + 0
        snowflake["x"] += random.randint(-1, 1)
        snowflake["y"] += 1
    # draw/move existing snowflakes
    #####

    return

    # Alien rave:
    # Beams and craft are over the city
def raveCell(cells, x, y, char, color):
    if 0 <= x < skyline.cols and 0 <= y < skyline.rows and not behindBuilding(x, y):
        cells[(x, y)] = (char, color)

    # Ravebeams across sky
def raveBeams(cells, t):
    for k in range(4):
        a = math.sin(t * (0.09 + k * 0.031) + k * 2.1)
        col = int((0.5 + 0.5 * a) * (skyline.cols - 1))
        color = rave_colors[(k + int(t / 4)) % len(rave_colors)][0]
        char = "\\" if a > 0.25 else ("/" if a < -0.25 else "|")
        for y in range(skyline.rows):
            raveCell(cells, col + int((skyline.rows - y) * a * 1.9), y, char, color)

    # Flying Saucers
def raveSaucers(cells, now, t, sky):
    for k in range(3):
        drift = (now * (0.03 + k * 0.012) + k * 0.37) % 1.0
        x = int(drift * (skyline.cols + 12)) - 6
        y = 1 + (k * 5 + 2) % max(1, sky - 2)
        for i, char in enumerate("<-o->"):
            color = rave_flash
            if char == "-":
                color = rave_colors[(i + int(t * 2)) % len(rave_colors)][0]
            raveCell(cells, x + i, y, char, color)

    # Mothership
def raveMothership(cells, since, t, sky):
    k = ((since - 8) % 300) / 115
    if k >= 1:
        return
    width = len(mothership[0])
    x0 = int(k * (skyline.cols + width)) - width
    y0 = 1 + int(0.18 * sky)
    lights = int(t * 2)
    for r, line in enumerate(mothership):
        for c, char in enumerate(line):
            if char == " " and r in (0, len(mothership) - 1):
                continue
            color = 9
            if char in "o.":
                color = rave_colors[(c + lights) % len(rave_colors)][0]
            raveCell(cells, x0 + c, y0 + r, char, color)


    # Landing beam that occasionally stops
def raveLandingBeam(cells, since, now):
    k = (since - 40) % 90
    if k >= 8:
        return
    picked = int((since - 40) // 90) * 7 % len(skyline.buildings)
    building = skyline.buildings[picked]
    x0 = building["position_x"] + int(building["width"] / 2)
    half = max(1, int(2 * min(1, k, (8 - k) / 1.5)))
    color = rave_flash
    if not int(now * 6) % 2:
        color = rave_colors[int(now) % len(rave_colors)][0]
    for x in range(x0 - half, x0 + half + 1):
        for y in range(skyline.rows):
            raveCell(cells, x, y, "|" if x == x0 else ":", color)

    # Put back what a beam or craft was covering
def raveRestoreCell(cell):
    look = skyline.star_looks.get(cell)
    if look:
        drawSym(cell[0], cell[1], look[0], look[1], background=False)
    else:
        drawSym(cell[0], cell[1], " ", background=False)


def ravePaintCity(state, t):
    for (x, y), look in skyline.star_looks.items():
        color = rave_flash
        if state != "flash":
            tube = rave_colors[(x * 3 + y * 7 + int(t)) % len(rave_colors)]
            color = tube[0] if state == "on" else tube[1]
        drawSym(x, y, look[0], color, background=False)
    color = {"flash": rave_flash, "on": 3, "off": 4}[state]
    for building in skyline.buildings:
        for office in building["offices_lit"]:
            drawSym(office[0], office[1], building["window"], color, background=False)


def raveLoop():
    if not skyline.raving:
        if len(skyline.stars) > skyline.star_max:
            for loop in range(30):
                starLoop()
        return

    now = time.monotonic()
    t = now * skyline.rave_bpm / 60.0

    # fill up the sky
    if len(skyline.stars) < skyline.star_max:
        for loop in range(max(1, int(skyline.star_max / 100))):
            starLoop()

    # four to the floor
    if (int(t) // 4) % 8 == 7 and int(t * 6) % 2:
        state = "flash"
    elif t % 1.0 < 0.13:
        state = "flash"
    else:
        state = "on" if t % 1.0 < 0.55 else "off"

    step = (state, int(t))
    if step == skyline.rave_step and now - skyline.rave_drawn < 0.03:
        return
    if step != skyline.rave_step:
        skyline.rave_step = step
        ravePaintCity(state, t)
    skyline.rave_drawn = now

    since = now - skyline.rave_start
    sky = skyline.rows - skyline.tallest_building["height"]
    cells = {}
    raveBeams(cells, t)
    raveSaucers(cells, now, t, sky)
    raveMothership(cells, since, t, sky)
    raveLandingBeam(cells, since, now)

    for cell in skyline.rave_cells:
        if cell not in cells:
            raveRestoreCell(cell)
    for (x, y), (char, color) in cells.items():
        drawSym(x, y, char, color, background=False)
    skyline.rave_cells = cells

    return


def raveOff():
    skyline.raving = False
    skyline.star_max = int(skyline.star_max / skyline.rave_star_boost)
    skyline.rave_step = None
    for cell in skyline.rave_cells:
        raveRestoreCell(cell)
    skyline.rave_cells = {}
    for (x, y), look in skyline.star_looks.items():
        drawSym(x, y, look[0], look[1], background=False)
    for building in skyline.buildings:
        for office in building["offices_lit"]:
            drawSym(office[0], office[1], building["window"], 3, background=False)



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
            fireworkLoop()

        if not skyline.tick % skyline.raindrop_rate:
            rainLoop()

        if not skyline.tick % skyline.snowflake_rate:
            snowLoop()

        if not skyline.tick % skyline.meteor_rate:
            meteorLoop()

        raveLoop()

        if skyline.debug:
            debugmsg = f"Stars:{len(skyline.stars)}/{skyline.star_max} Bldgs:{len(skyline.buildings)} Size:{skyline.cols}x{skyline.rows}"
            if skyline.raining_duration:
                debugmsg += f" RainDur:{skyline.raining_duration}"
            if skyline.fireworks:
                debugmsg += f" Fireworks:{len(skyline.fireworks)}"
            if skyline.meteors:
                debugmsg += f" Meteors:{len(skyline.meteors)}"
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
        # s: toggle snow
        elif key == 115:
            if skyline.snowing:
                skyline.snowing = False
                displayMessage("Snow OFF.")
            else:
                skyline.raining = False
                skyline.snowing = True
                displayMessage("Snow ON.")
        # S: speed to default
        elif key == 83:
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
            if skyline.speed >= 100:
                displayMessage("Can't go any slower ...")
            else:
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
        # R: reset skyline
        elif key in [82, curses.KEY_RESIZE]:
            screen.clear()
            skyline.rows, skyline.cols = screen.getmaxyx()
            setupSkyline()
            msg = "Skyline reset."
            if key == curses.KEY_RESIZE:
                msg = f"Terminal size changed: {msg}"
            displayMessage(msg)
        # r: toggle rain
        elif key == 114:
            if skyline.raining:
                skyline.raining = False
                displayMessage("Rain OFF.")
            else:
                skyline.snowing = False
                skyline.raining = True
                displayMessage("Rain ON.")
        # f: firework
        elif key == 102:
            spawnFirework()
        # m: meteor
        elif key == 109:
            spawnMeteor()
        # M: toggle meteor shower
        elif key == 77:
            if skyline.meteor_shower:
                skyline.meteor_shower = False
                displayMessage("Meteor shower OFF.")
            else:
                skyline.meteor_shower = True
                displayMessage("Meteor shower ON.")
        # a: toggle alien rave
        elif key == 97:
            if skyline.raving:
                raveOff()
                displayMessage("Alien rave OFF.")
            else:
                skyline.raving = True
                skyline.rave_start = time.monotonic()
                skyline.star_max *= skyline.rave_star_boost
                displayMessage("~ something over the city ~")
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
        # C: clear messages
        elif key == 67:
            for msgtype in skyline.display_message:
                displayMessage(" ", msgtype=msgtype)
        # unused key: prompt to press ? for help
        else:
            msg = "(Press ? for help)"
            if skyline.debug:
                msg += f" (key pressed: {key})"
            displayMessage(f"{msg}")
    # main loop
    #####


wrapper(main)
