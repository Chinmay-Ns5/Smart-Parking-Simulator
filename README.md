# Smart Parking Simulator

A real-time, Pygame-based smart parking lot simulation that models the full lifecycle of vehicles entering, being assigned slots, parking, and exiting — with animated boom barriers, IR-style slot sensors, aisle traffic-control logic, and a live controller panel dashboard.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements & Installation](#requirements--installation)
4. [Running the Simulator](#running-the-simulator)
5. [Controls](#controls)
6. [Project Structure](#project-structure)
7. [Architecture & Module Breakdown](#architecture--module-breakdown)
   - [config.py — Constants & Geometry](#configpy--constants--geometry)
   - [car.py — Car State Machine & Rendering](#carpy--car-state-machine--rendering)
   - [lot.py — Parking Lot Model & Control Logic](#lotpy--parking-lot-model--control-logic)
   - [main.py — Application Loop & Rendering](#mainpy--application-loop--rendering)
8. [Parking Lot Layout](#parking-lot-layout)
9. [Slot Allocation Algorithm](#slot-allocation-algorithm)
10. [Car State Machine (Full Detail)](#car-state-machine-full-detail)
11. [Traffic Safety System](#traffic-safety-system)
12. [Sensor Simulation](#sensor-simulation)
13. [Barrier / Gate System](#barrier--gate-system)
14. [Controller Panel & HUD](#controller-panel--hud)
15. [Full Simulation Flow (Step-by-Step)](#full-simulation-flow-step-by-step)
16. [Key Constants Reference](#key-constants-reference)
17. [Possible Extensions](#possible-extensions)
18. [License](#license)

---

## Overview

The simulator models a **32-slot parking lot** divided into two aisles (left and right), each served by a dedicated entry lane and exit lane. A vertical external road on the left side of the screen acts as the main arterial — cars spawn at the bottom, drive up, pass through the entry gate into the lot's internal horizontal road, travel up an aisle, and park.

When the parking timer expires the car backs out, travels down the exit lane, crosses the internal road, passes through the exit gate, and drives off-screen at the bottom.

The simulation demonstrates several "smart" concepts:

- **Nearest-first slot allocation** prioritises the closest available slot to the entry point.
- **Reservation system** prevents double-booking while a car is still driving to its slot.
- **Per-aisle traffic checks** prevent conflicts in narrow aisle lanes.
- **Simulated IR sensors** with noise and debounce mimic real occupancy sensors.
- **Animated boom barriers** that auto-close after a configurable delay.

---

## Features

- 32 parking slots across 4 columns and 8 rows
- Two independent aisles, each with separate entry and exit lanes
- Nearest-first slot assignment with left-aisle preference
- Slot reservation to prevent race conditions between arriving cars
- IR-style slot sensors with random noise and debounce timer
- Animated boom barrier gates (entry and exit) with auto-close
- Per-aisle and corridor-level traffic safety checks
- Controller panel displaying a live slot register, gate status, counters, and algorithm label
- HUD showing title and available/total slot count with colour-coded urgency
- Adjustable simulation speed from 0.5× to 4.0×
- Manual car spawning via keyboard
- Colour-coded top-down car rendering with rotation, windshields, wheels, and ID labels

---

## Requirements & Installation

- **Python 3.x**
- **Pygame**

Install Pygame:

```bash
pip install pygame
```

No other third-party libraries are needed.

---

## Running the Simulator

```bash
python main.py
```

The 1100 × 720 window opens immediately and begins auto-spawning cars within the first few seconds.

---

## Controls

| Key | Action |
|-----|--------|
| `Space` | Manually spawn a car (if entry corridor and a slot are both free) |
| `T` | Toggle the controller panel on/off |
| `+` / `=` / numpad `+` | Increase simulation speed (up to 4.0×, multiplied by 1.5 each press) |
| `-` / numpad `-` | Decrease simulation speed (down to 0.5×, divided by 1.5 each press) |
| `Esc` | Quit |

Cars also spawn automatically. Each time a car spawns (manual or automatic), the next automatic spawn delay is re-randomised between `SPAWN_MIN` (2.0 s) and `SPAWN_MAX` (5.0 s) at the current simulation timescale.

---

## Project Structure

```
smart-parking-simulator/
├── main.py       # Application entry point, event loop, all drawing functions
├── lot.py        # Parking lot model: slots, barriers, traffic checks, spawn/exit logic
├── car.py        # Car class: state machine, waypoint movement, rendering
├── config.py     # All constants: screen, geometry, colours, timing, panel layout
├── LICENSE       # Apache License 2.0
└── README.md     # This file
```

---

## Architecture & Module Breakdown

The four Python modules have clean separation of concerns. `config.py` defines all numbers. `car.py` defines individual car behaviour. `lot.py` orchestrates the parking system. `main.py` handles rendering and user input. No module other than `main.py` imports Pygame — keeping the model layer pure Python.

### config.py — Constants & Geometry

`config.py` is imported by every other module via `from config import *`. Changing a value here propagates automatically to the rest of the simulation.

**Screen settings**

```python
SCREEN_W = 1100    # Window width in pixels
SCREEN_H = 720     # Window height in pixels
FPS      = 60      # Target frame rate
TITLE    = "Smart Parking Simulator"
```

**Colour palette**

All colours are RGB tuples. Key rendering colours:

| Name | RGB | Used For |
|------|-----|----------|
| `ASPHALT` | (66, 68, 74) | Lot base fill |
| `ROAD_COL` | (82, 84, 92) | External vertical road |
| `AISLE_COL` | (55, 57, 64) | Internal aisle strips |
| `INT_ROAD_COL` | (76, 78, 86) | Horizontal internal road |
| `MARKING` | (232, 228, 152) | Lane markings and arrows |
| `SLOT_FREE` | (32, 148, 70) | Free parking slot fill |
| `SLOT_OCC` | (148, 32, 32) | Occupied parking slot fill |
| `LED_ON_G` | (0, 255, 80) | Green sensor LED / open gate |
| `LED_ON_R` | (255, 58, 58) | Red sensor LED / closed gate |
| `PANEL_HL` | (0, 208, 148) | Controller panel highlight (teal) |

**External road geometry**

The external road is a vertical 85 px wide strip on the far left of the screen:

```
ROAD_X        = 10     # left edge of the road strip
ROAD_W        = 85     # total road width (two lanes)
ROAD_ENTRY_LX = 31     # centre of left (entry/upward) lane
ROAD_EXIT_LX  = 73     # centre of right (exit/downward) lane
```

**Parking lot geometry**

The lot starts 10 px to the right of the road:

```
LOT_X     = 105    # left edge of the lot
LOT_Y     = 40     # top edge of the lot
SLOT_DEPTH = 110   # length of each parking slot (perpendicular to aisle)
SLOT_W     = 52    # width of each parking slot
SLOT_GAP   = 5     # vertical gap between slots in the same column
N_ROWS     = 8     # rows of slots per column
N_COLS     = 4     # columns of slots (two per aisle)
AISLE_W    = 130   # width of each aisle (fits two lanes + clearance)
```

**Column X positions** (left edges)

```python
COL0_X   = 115    # Left column of left aisle
AISLE0_X = 225    # Left aisle strip
COL1_X   = 355    # Right column of left aisle
COL2_X   = 465    # Left column of right aisle
AISLE1_X = 575    # Right aisle strip
COL3_X   = 705    # Right column of right aisle
```

**Aisle lane centres**

Each aisle is divided into an entry lane (left quarter) and an exit lane (right quarter):

```python
AISLE0_ENTRY_LX = 257    # Left aisle entry lane centre
AISLE0_EXIT_LX  = 322    # Left aisle exit lane centre
AISLE1_ENTRY_LX = 607    # Right aisle entry lane centre
AISLE1_EXIT_LX  = 672    # Right aisle exit lane centre
```

**Internal horizontal road** (inside the lot, below the slot area)

```python
INT_ROAD_TOP    = 509    # Top Y of the internal road
INT_ROAD_CY     = 559    # Centre Y of the internal road
INT_ROAD_BOTTOM = 609    # Bottom Y of the internal road
INT_ROAD_H      = 100    # Road height in pixels
```

The internal road has two lanes divided at the centre line. Cars enter from the left, drive eastward through the entry lane, then turn north into an aisle. Exiting cars drive westward through the exit lane:

```python
INT_ROAD_ENTRY_Y = 534   # Upper (entry/eastward) lane centre
INT_ROAD_EXIT_Y  = 584   # Lower (exit/westward) lane centre
```

**Gate and spawn positions**

```python
ENTRY_GATE_Y     = 534   # Y where cars pass through the entry gate
EXIT_GATE_Y      = 584   # Y where cars pass through the exit gate
ROAD_SPAWN_Y     = 659   # Y where new cars are placed (below the lot)
ROAD_OFFSCREEN_Y = 800   # Y where exiting cars are considered gone
```

**Car dimensions and speed**

```python
CAR_W, CAR_H = 38, 58    # Width and height of the car sprite in pixels
CAR_SPEED    = 110        # Movement speed in pixels per second
```

**Timing**

```python
SPAWN_MIN, SPAWN_MAX = 2.0, 5.0    # Auto-spawn interval range (seconds, sim time)
PARK_MIN,  PARK_MAX  = 8.0, 22.0   # Parking duration range (seconds, sim time)
```

---

### car.py — Car State Machine & Rendering

`car.py` defines the `Car` class and the five state constants. It does not know about the lot; it only knows how to move along a list of waypoints and draw itself.

**State constants**

```python
MOVING    = "moving"     # Driving toward assigned slot via entry waypoints
PARKED    = "parked"     # Stationary; park timer is counting down
DEPARTING = "departing"  # Park time expired; waiting for lot to clear exit path
EXITING   = "exiting"    # Driving out via exit waypoints
EXITED    = "exited"     # Off-screen; safe to delete from cars list
```

**Car identity**

`Car._counter` is a class-level integer that increments each time a `Car` is constructed. This gives every car a globally unique `id` independent of spawn order, used for the on-car label and for the colour palette lookup:

```python
Car._counter += 1
self.id    = Car._counter
self.color = _PALETTE[(self.id - 1) % len(_PALETTE)]
```

Eight colours cycle in the palette: red, blue, green, yellow, purple, orange, cyan, and pink.

**Entry path (`set_entry_path`)**

The method receives the assigned `Slot` object and builds a four-waypoint list that routes the car from its spawn position into the slot:

For a **left-aisle** slot (col < 2):

```
(ROAD_ENTRY_LX, ENTRY_GATE_Y)    # Drive up the external road to the entry gate
(AISLE0_ENTRY_LX, ENTRY_GATE_Y)  # Turn right into the left aisle entry lane
(AISLE0_ENTRY_LX, slot.cy)       # Drive north up the entry lane to the slot row
(slot.cx, slot.cy)                # Turn into the slot and park
```

For a **right-aisle** slot (col >= 2):

```
(ROAD_ENTRY_LX, ENTRY_GATE_Y)    # Drive up to entry gate
(AISLE1_ENTRY_LX, ENTRY_GATE_Y)  # Turn right all the way across to the right aisle
(AISLE1_ENTRY_LX, slot.cy)       # Drive north up right entry lane
(slot.cx, slot.cy)                # Turn into slot
```

`path_type` is set to `"left"` or `"right"` here; this label is used by `lot.py` for traffic checks.

**Exit path (`set_exit_path`)**

The method builds a four-waypoint exit route when called by `lot.py` once the aisle is clear:

For a **left-aisle** slot:

```
(AISLE0_EXIT_LX, slot.cy)        # Back out laterally to the left exit lane
(AISLE0_EXIT_LX, EXIT_GATE_Y)    # Drive south down the exit lane
(ROAD_EXIT_LX, EXIT_GATE_Y)      # Turn left through the exit gate onto the road
(ROAD_EXIT_LX, ROAD_OFFSCREEN_Y) # Drive off-screen
```

**`update(dt)` logic**

- If `PARKED`: increment `park_timer`. Transition to `DEPARTING` when `park_timer >= park_duration`.
- If `MOVING` or `EXITING`: advance toward the current waypoint. When within 1.5 px, snap to the waypoint and increment `wp_idx`. Record the normalised direction vector `(_dx, _dy)` for rotation.
- When all waypoints are consumed: if was `MOVING` → become `PARKED`; if was `EXITING` → become `EXITED`.

**`draw(surf, font)` logic**

1. Creates a 38 × 58 px `SRCALPHA` surface.
2. Draws the car body (rounded rectangle in the car's colour).
3. Draws a semi-transparent windshield at the front and a smaller rear window.
4. Draws four black 5 × 13 px wheel rectangles at the corners.
5. Renders the car ID number centred on the body.
6. Calculates rotation angle from `(_dx, _dy)` using `atan2`, then rotates the surface so the car faces its direction of travel.
7. Blits the rotated surface centred on `(self.x, self.y)`.

Cars in the `EXITED` state skip drawing entirely.

---

### lot.py — Parking Lot Model & Control Logic

`lot.py` is the brain of the simulation. It contains three classes: `Slot`, `Barrier`, and `ParkingLot`.

#### `Slot` — One Parking Space

Each slot stores its grid position and tracks occupancy, reservation, and the IR sensor:

```python
self.index     # Sequential slot index (0–31)
self.col, self.row  # Grid coordinates
self.x, self.y      # Pixel top-left corner
self.cx, self.cy    # Pixel centre point
self.reserved  # True while a car is en route but not yet parked
self.occupied  # True while a car is stationary in the slot
self.car_ref   # Reference to the Car currently assigned to this slot
self.ir_sensor_triggered  # Simulated IR sensor boolean output
```

`Slot.update_sensor(dt)` is described in detail in the [Sensor Simulation](#sensor-simulation) section.

#### `Barrier` — Animated Boom Gate

Each barrier stores position and animation state:

```python
self.name      # "ENTRY" or "EXIT"
self.post_x, self.post_y  # Hinge pixel position
self.direction  # +1 arm extends east, -1 arm extends west
self.lift_sign  # -1 arm swings upward (north), +1 swings downward (south)
self.angle      # Current arm angle in degrees (0 = closed vertical, 82 = open horizontal)
self.is_open    # Whether the barrier is in the open state
self._timer     # Time elapsed since opening, used for auto-close
```

`Barrier.open()` sets `is_open = True` and resets `_timer`, restarting the auto-close countdown.

`Barrier.update(dt)` rotates toward 82° when open (at 130°/s) and back toward 0° when closed.

Auto-close fires after `_AUTO_CLOSE = 2.8` seconds. The exit barrier is kept open as long as any car is in the `EXITING` state — `lot.update()` calls `barriers[1].open()` each frame while this is true.

#### `ParkingLot` — System Orchestrator

**`_build_slots()`** constructs 32 `Slot` objects in column-major order:

```python
slot index = col * N_ROWS + row    # 0..31
```

Column 0 row 0 is slot 0; column 0 row 7 is slot 7; column 1 row 0 is slot 8, and so on.

**`try_spawn()`** is the main entry point for creating a new car:

1. Check `_entry_corridor_busy()` — abort if another car is still on the external approach.
2. Prefer left aisle: if `_left_aisle_backing_out()` is False, try `_nearest_slot(prefer_col="left")`.
3. Fall back to right aisle: if `_right_aisle_backing_out()` is False, try `_nearest_slot(prefer_col="right")`.
4. If a slot was found: mark it `reserved`, create a `Car`, assign a random `park_duration`, call `car.set_entry_path(slot)`, append the car to `self.cars`, increment `cars_in`, and open the entry barrier.

**`update(dt)`** runs every frame:

1. Updates all barriers.
2. Keeps exit barrier open if any car is exiting.
3. Calls `car.update(dt)` for each car, watching for the `MOVING → PARKED` transition to promote the slot from reserved to occupied.
4. For any `DEPARTING` car, calls `_try_start_exit(car)`.
5. Updates IR sensors for all slots.
6. Removes `EXITED` cars from `self.cars` and increments `cars_out`.

**`_try_start_exit(car)`** promotes a `DEPARTING` car to `EXITING`:

1. Check `_exit_corridor_busy()` — abort if the external exit segment is occupied.
2. Check aisle-specific conditions (exit lane busy or a car currently entering the same aisle).
3. If all clear: free the slot (`occupied = False`, `car_ref = None`), call `car.set_exit_path(slot)`, set `car.state = EXITING`, and open the exit barrier.

---

### main.py — Application Loop & Rendering

`main.py` is the application entry point. It contains five pure drawing functions and the `main()` loop. It is the only file that imports Pygame.

**`draw_background(surf)`**

Draws the static scene layer (called every frame, no state dependency):

- Vertical external road with a dashed centre lane divider and direction arrows.
- "IN" and "OUT" labels and "SECURITY GATE" text near the gate region.
- Green right-arrow and red left-arrow indicators at the lot wall opening.
- Lot base fill (asphalt colour).
- Internal horizontal road with a dashed centre line.
- Both aisle strips with per-row dashed centre lines (gaps at each slot row for visual clarity).
- Direction arrows (up/down) inside each aisle.
- Centre divider line between columns 1 and 2.
- Lot border / curb rectangle.
- Security booth rectangle straddling the lot entry wall, with two blue windows.

**`draw_slots(surf, lot, font)`**

Iterates over all 32 slots and for each one:

- Fills the slot rectangle in `SLOT_OCC` (dark red) if occupied, `ORANGE` if `car_nearby` but not yet occupied, or `SLOT_FREE` (green) otherwise.
- Draws a curb-coloured border.
- Renders a "P1" – "P32" label centred in the slot.
- Draws the IR sensor LED (red if `ir_sensor_triggered`, green otherwise) at the aisle-facing corner of the slot.

**`draw_barrier(surf, barrier)`**

Draws each boom gate arm:

- Computes the arm tip position from the hinge using `sin(angle)` for horizontal offset and `cos(angle)` for vertical offset, scaled by `INT_ROAD_H // 2 - 2` pixels.
- Draws a 6 px wide coloured line (green if open, red if closed) from hinge to tip.
- Overlays a 2 px white stripe for the boom-gate stripe effect.
- Draws a dark hinge circle and a small coloured ball at the arm tip.

**`draw_panel(surf, lot, font_s, font_m, speed_mult)`**

Renders the controller panel into a dedicated `Surface` at `(PANEL_X, PANEL_Y)`:

- Title bar "[ CONTROLLER ]" in teal.
- Slot register: a 4-column × 8-row grid. Each cell shows `1` (red) for occupied, `R` (orange) for reserved, or `0` (green) for free.
- Gate status: `ENTRY` and `EXIT` gate open/closed state in matching colours.
- Statistics: total slots, available, reserved, occupied, cars in, cars out.
- Algorithm label: "Nearest-First".
- Speed multiplier (highlighted in teal when not 1.0×).
- Keyboard reference.

**`draw_hud(surf, lot, font_m)`**

Draws the title text and a colour-coded `Available: X / 32` counter at the top of the screen. The colour is green when more than 8 slots remain, yellow when 1–8 remain, and red when full.

**`main()` loop**

```
pygame.init()
Create window (1100×720), fonts (Consolas 12 and 15pt bold), clock, ParkingLot
Set show_panel = True, spawn_timer = 0, next_spawn = random(2..5), speed_mult = 1.0

while True:
    dt = min(clock.tick(60) / 1000, 0.05)   # raw frame delta, capped at 50 ms

    Handle events:
        QUIT / ESC  → exit
        T           → toggle show_panel
        SPACE       → lot.try_spawn()
        +           → speed_mult = min(speed_mult * 1.5, 4.0)
        -           → speed_mult = max(speed_mult / 1.5, 0.5)

    sdt = dt * speed_mult                    # scaled delta time

    spawn_timer += sdt
    if spawn_timer >= next_spawn:
        lot.try_spawn()
        spawn_timer = 0
        next_spawn = random(SPAWN_MIN, SPAWN_MAX)

    lot.update(sdt)

    draw_background → draw_slots → draw_barrier × 2 → draw car × N
    → draw_panel (if shown) → draw_hud

    pygame.display.flip()
```

The raw delta time is capped at 50 ms (0.05 s) to prevent large physics jumps after the window is un-paused or the system is slow.

---

## Parking Lot Layout

```
 SCREEN (1100 × 720)
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  Road  │                  Parking Lot (LOT_X=105, W=720)                    │ Panel│
 │  85px  │                                                                    │243px │
 │        │  COL0   AISLE0    COL1   COL2   AISLE1   COL3                     │      │
 │  ↑ IN  │  ┌──┐  ┌──────┐  ┌──┐  ┌──┐  ┌──────┐  ┌──┐                    │      │
 │        │  │  │  │ ↑  ↓ │  │  │  │  │  │ ↑  ↓ │  │  │                    │      │
 │  ↓OUT  │  │P1│  │entry │  │P9│  │P17│  │entry │  │P25│                   │      │
 │        │  │  │  │ exit │  │  │  │  │  │ exit │  │   │                    │      │
 │[GATE]  │  └──┘  └──────┘  └──┘  └──┘  └──────┘  └──┘                    │      │
 │        │  ──── Internal Horizontal Road ────────────────                   │      │
 └──────────────────────────────────────────────────────────────────────────────┘
```

Slot numbering (column-major):

```
Col 0: P1–P8    Col 1: P9–P16    Col 2: P17–P24    Col 3: P25–P32
```

- **Left aisle** (AISLE0) serves columns 0 and 1.
- **Right aisle** (AISLE1) serves columns 2 and 3.
- Within each aisle the **left lane** is the entry (northbound) lane and the **right lane** is the exit (southbound) lane.

---

## Slot Allocation Algorithm

The `_nearest_slot()` method implements **nearest-first allocation**:

```python
def _nearest_slot(self, prefer_col=None):
    free = [s for s in self.slots if not s.occupied and not s.reserved]
    if prefer_col is not None:
        free = [s for s in free if (s.col < 2) == (prefer_col == "left")]
    if not free:
        return None
    return min(free, key=lambda s: abs(s.cx - ROAD_ENTRY_LX) + abs(s.cy - INT_ROAD_CY))
```

**Distance metric:** Manhattan driving distance from the entry junction `(ROAD_ENTRY_LX, INT_ROAD_CY)` to the slot centre. This approximates the actual path length a car must travel.

**Aisle preference:** `try_spawn()` always tries the left aisle first. This naturally fills the lot inward from the entry side. Only if the left aisle is blocked by a backing-out car (or has no free slots) does it fall back to the right aisle.

**Reservation:** Immediately after a slot is chosen, `slot.reserved = True` is set. Subsequent calls to `_nearest_slot()` skip reserved slots, ensuring no two cars are ever assigned the same slot concurrently.

---

## Car State Machine (Full Detail)

```
                spawn
                  │
                  ▼
             ┌─────────┐
             │ MOVING  │◄─── following entry waypoints
             └────┬────┘
                  │ all entry waypoints consumed
                  ▼
             ┌─────────┐
             │ PARKED  │◄─── park_timer counting (8–22 s)
             └────┬────┘
                  │ park_timer >= park_duration
                  ▼
            ┌──────────┐
            │DEPARTING │◄─── waiting for safe exit path
            └────┬─────┘
                 │ _try_start_exit succeeds
                 ▼
            ┌─────────┐
            │ EXITING │◄─── following exit waypoints
            └────┬────┘
                 │ all exit waypoints consumed
                 ▼
            ┌─────────┐
            │ EXITED  │◄─── removed from simulation
            └─────────┘
```

State transitions are driven by `Car.update()` (for `MOVING → PARKED` and `PARKED → DEPARTING`) and by `ParkingLot._try_start_exit()` (for `DEPARTING → EXITING`) and again `Car.update()` (for `EXITING → EXITED`).

A car never skips states. A `DEPARTING` car may wait for an arbitrarily long time if the aisle remains busy.

---

## Traffic Safety System

`ParkingLot` maintains eight boolean helper methods that check live car positions and states to prevent collisions in shared-use zones:

| Method | Checks |
|--------|--------|
| `_entry_corridor_busy()` | Any car in `MOVING` state with `wp_idx == 0` (still on the external approach road below the gate) |
| `_exit_corridor_busy()` | Any car in `EXITING` state with `wp_idx >= 2` (on the external road heading off-screen) |
| `_left_aisle_backing_out()` | Any `EXITING` left-path car with `wp_idx == 0` (pulling sideways out of the slot into the aisle) |
| `_right_aisle_backing_out()` | Same but for right-aisle cars |
| `_left_aisle_entering()` | Any `MOVING` left-path car with `wp_idx == 2` (driving northbound up the left entry lane) |
| `_right_aisle_entering()` | Same but for right-aisle cars |
| `_left_aisle_exit_lane_busy()` | Any `EXITING` left-path car with `wp_idx <= 1` (in the left exit lane) |
| `_right_aisle_exit_lane_busy()` | Same but for right-aisle cars |

**Spawn gate:** A new car will not be spawned if `_entry_corridor_busy()` is true. This prevents cars from stacking on the external approach.

**Exit gate:** A `DEPARTING` car cannot start exiting if `_exit_corridor_busy()` is true (prevents merge conflict on the external road) OR if its aisle exit lane is busy OR if a car is currently entering the same aisle (they would be in opposing lanes of the same strip, but the backing-out manoeuvre needs the full aisle width).

These checks together ensure that at most one car occupies each narrow critical zone at any time.

---

## Sensor Simulation

Each `Slot` simulates an infrared proximity sensor in `update_sensor(dt)`. The sensor does not use a simple boolean distance check. Instead:

1. **Distance** between the associated car and the slot centre is computed with `math.hypot`.

2. **Range varies by state:**

   | Car state | Detection range |
   |-----------|-----------------|
   | `PARKED` | `SENSOR_RANGE` (45 px) |
   | `DEPARTING` | `SENSOR_RANGE × 1.5` (67.5 px) — slot appears occupied slightly longer |
   | `EXITING` | `SENSOR_RANGE × 0.8` (36 px) — slot clears faster once the car starts leaving |
   | Any other (approaching) | 0 — sensor is off while car is still en route |

3. **Noise:** A small random value in ±0.15 is added to `_sensor_noise` each frame, clamped to ±0.2. This is added to the binary `in_range` signal to produce `raw_signal`.

4. **Debounce:** `_sensor_debounce` is a value in [−0.15, +0.15]. Each frame it moves toward +0.15 if `raw_signal >= 0.5`, or toward −0.15 otherwise, at a rate of `dt` per second. The sensor output only flips when the debounce reaches its limit. This prevents rapid toggling on the boundary.

5. **LED output:** `ir_sensor_triggered` is the final boolean, displayed as a red LED on the slot when True and green when False.

If `car_ref` is `None`, the sensor resets immediately to False.

---

## Barrier / Gate System

Two `Barrier` objects exist:

| Name | Post position | Arm direction | Lift direction |
|------|---------------|---------------|----------------|
| `ENTRY` | `(LOT_X+5, INT_ROAD_TOP+2)` | East (+1) | South (+1) — arm hangs downward when closed |
| `EXIT` | `(LOT_X+5, INT_ROAD_BOTTOM-2)` | East (+1) | North (−1) — arm hangs upward when closed |

When closed (`angle = 0°`) the arm is vertical, blocking traffic through the internal road opening. When fully open (`angle = 82°`) the arm is nearly horizontal, parallel to the road, out of the path of traffic.

The arm rotates at `_ROT_SPEED = 130°/s`. Full open/close takes approximately 0.63 seconds.

**Auto-close:** After `_AUTO_CLOSE = 2.8` seconds the barrier begins closing automatically. The exit barrier is exempt — `ParkingLot.update()` calls `barriers[1].open()` every frame while any car is `EXITING`, effectively keeping it open until the last exiting car clears.

---

## Controller Panel & HUD

**Controller panel** (right side, toggled with `T`):

- **Slot Register:** 4 × 8 grid of coloured cells mirroring the physical lot. `1` (red) = occupied, `R` (orange) = reserved, `0` (green) = free. Uses the same column-major indexing as `_build_slots()`.
- **Gate Status:** Live open/closed state for ENTRY and EXIT barriers.
- **Statistics:** Total, available, reserved, occupied counts; total cars in and cars out since launch.
- **Algorithm:** Labels the active allocation strategy ("Nearest-First").
- **Speed:** Current multiplier, highlighted in teal when not 1.0×.
- **Controls reference:** Keyboard shortcuts.

**HUD** (top of screen, always visible):

- Left: simulation title.
- Right: `Available: X / 32` — green when plenty of spaces remain (> 8), yellow when few remain (1–8), red when the lot is full (0).

---

## Full Simulation Flow (Step-by-Step)

1. `main()` initialises Pygame, creates the `ParkingLot`, and starts the frame loop.
2. Each frame, raw delta time `dt` is computed from `clock.tick(60)` and capped at 50 ms.
3. Keyboard events are processed. Speed changes adjust `speed_mult` immediately.
4. `spawn_timer` increments by scaled `dt`. When it reaches `next_spawn`, `lot.try_spawn()` is called.
5. **`try_spawn()`:**
   - Checks that the external entry corridor is free.
   - Finds the nearest free slot, left aisle preferred.
   - Marks the slot `reserved`.
   - Creates a new `Car` with a random parking duration.
   - Assigns the entry waypoint path.
   - Opens the entry barrier.
   - Increments `cars_in`.
6. **`lot.update(sdt)`:**
   - Rotates barrier arms.
   - Keeps exit barrier open if any car is exiting.
   - For each car: calls `car.update(sdt)`. Watches for `MOVING → PARKED` to flip slot from reserved to occupied. Calls `_try_start_exit()` for `DEPARTING` cars.
   - Updates all 32 slot sensors.
   - Removes `EXITED` cars; increments `cars_out`.
7. The full scene is redrawn: background, slots, barriers, cars (front-to-back draw order matches list order), controller panel, HUD.
8. `pygame.display.flip()` swaps buffers.
9. When a parked car's timer expires it becomes `DEPARTING`. Each subsequent frame, `_try_start_exit()` polls the traffic checks. When the aisle clears, the car gets its exit path and becomes `EXITING`. The exit barrier opens.
10. Once the car reaches `ROAD_OFFSCREEN_Y` it becomes `EXITED`, is removed, and `cars_out` increments.

---

## Key Constants Reference

| Constant | Value | Meaning |
|----------|-------|---------|
| `SCREEN_W / SCREEN_H` | 1100 / 720 | Window dimensions |
| `FPS` | 60 | Target frame rate |
| `N_COLS / N_ROWS` | 4 / 8 | Lot grid dimensions |
| `SLOT_DEPTH / SLOT_W` | 110 / 52 | Slot pixel size |
| `AISLE_W` | 130 | Aisle width (two lanes) |
| `CAR_W / CAR_H` | 38 / 58 | Car sprite size |
| `CAR_SPEED` | 110 px/s | Car movement speed |
| `SPAWN_MIN / SPAWN_MAX` | 2.0 / 5.0 s | Auto-spawn interval range |
| `PARK_MIN / PARK_MAX` | 8.0 / 22.0 s | Parking duration range |
| `Barrier._OPEN_ANGLE` | 82° | Barrier arm fully open angle |
| `Barrier._ROT_SPEED` | 130°/s | Barrier rotation speed |
| `Barrier._AUTO_CLOSE` | 2.8 s | Auto-close delay |
| `Slot.SENSOR_RANGE` | 45 px | IR sensor base detection radius |

---

## Possible Extensions

- **requirements.txt:** Add a `requirements.txt` file containing `pygame` for simpler environment setup.
- **Collision detection:** Add per-car bounding box checks rather than only lane-zone checks.
- **Alternative allocation strategies:** Random assignment, farthest-first, priority lanes for reserved/VIP spots.
- **Manual slot control:** Allow the user to click a slot to force it occupied or free for testing.
- **Data logging:** Record cars in/out, average occupancy over time, average parking duration, and export to CSV.
- **Priority vehicles:** Model ambulances or disabled bays that bypass normal queue logic.
- **Sound effects:** Gate open/close sounds, car engine hum, arrival chime.
- **Dashboard graphs:** Real-time occupancy history chart drawn on the right panel using Pygame drawing primitives.
- **Multiple entry/exit gates:** Support a second entry point on the right side of the lot.

---

## License

This project is released under the **Apache License 2.0**. See the `LICENSE` file for the full text.
