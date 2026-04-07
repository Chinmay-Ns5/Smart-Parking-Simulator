import random
import math
from config import *
from car import Car, MOVING, PARKED, DEPARTING, EXITING, EXITED


class Slot:
    SENSOR_RANGE = 45

    def __init__(self, index, col, row, x, y):
        self.index     = index
        self.col       = col
        self.row       = row
        self.x, self.y = x, y
        self.cx        = x + SLOT_DEPTH // 2
        self.cy        = y + SLOT_W     // 2
        self.reserved  = False
        self.occupied  = False
        self.car_ref   = None
        self.ir_sensor_triggered = False
        self._sensor_debounce = -0.15
        self._sensor_noise = 0.0
        self.car_nearby = False

    def update_sensor(self, dt):
        if self.car_ref is None:
            self.ir_sensor_triggered = False
            self._sensor_debounce = -0.15
            self._sensor_noise = 0.0
            self.car_nearby = False
            return

        car = self.car_ref
        dist = math.hypot(car.x - self.cx, car.y - self.cy)
        self.car_nearby = dist < self.SENSOR_RANGE * 2
        
        if car.state == PARKED:
            in_range = dist < self.SENSOR_RANGE
        elif car.state == DEPARTING:
            in_range = dist < self.SENSOR_RANGE * 1.5
        elif car.state == EXITING:
            in_range = dist < self.SENSOR_RANGE * 0.8
        else:
            # A slot is not occupied while the car is still approaching it.
            in_range = False

        self._sensor_noise += (random.random() - 0.5) * 0.3
        self._sensor_noise = max(-0.2, min(0.2, self._sensor_noise))
        raw_signal = in_range + self._sensor_noise
        threshold = 0.5

        if raw_signal >= threshold:
            self._sensor_debounce = min(0.15, self._sensor_debounce + dt)
        else:
            self._sensor_debounce = max(-0.15, self._sensor_debounce - dt)

        if self._sensor_debounce >= 0.15:
            self.ir_sensor_triggered = True
        elif self._sensor_debounce <= -0.15:
            self.ir_sensor_triggered = False


class Barrier:
    _OPEN_ANGLE  = 82.0
    _CLOSE_ANGLE = 0.0
    _ROT_SPEED   = 130.0
    _AUTO_CLOSE  = 2.8

    def __init__(self, name, post_x, post_y, direction=1, lift_sign=-1):
        self.name      = name
        self.post_x    = post_x
        self.post_y    = post_y
        self.direction = direction   # +1 arm extends east, -1 arm extends west
        self.lift_sign = lift_sign   # -1 opens upward, +1 opens downward
        self.angle     = 0.0
        self.is_open   = False
        self._timer    = 0.0

    def open(self):
        self.is_open = True
        self._timer  = 0.0

    def update(self, dt):
        if self.is_open:
            self._timer += dt
            self.angle = min(self._OPEN_ANGLE,
                             self.angle + self._ROT_SPEED * dt)
            if self._timer >= self._AUTO_CLOSE:
                self.is_open = False
        else:
            self.angle = max(self._CLOSE_ANGLE,
                             self.angle - self._ROT_SPEED * dt)


class ParkingLot:
    def __init__(self):
        self.slots    = self._build_slots()
        # Gates are on the HORIZONTAL internal road at the lot entrance.
        # Arms are VERTICAL when closed (blocking east-west traffic)
        # and rotate to HORIZONTAL (east) when open.
        # Entry post at top edge of road (arm swings south to close),
        # Exit  post at bottom edge     (arm swings north to close).
        _bx = LOT_X + 5
        self.barriers = [
            Barrier("ENTRY", _bx, INT_ROAD_TOP    + 2, direction=+1, lift_sign=+1),
            Barrier("EXIT",  _bx, INT_ROAD_BOTTOM - 2, direction=+1, lift_sign=-1),
        ]
        self.cars     = []
        self.cars_in  = 0
        self.cars_out = 0

    # ── Slot setup ──────────────────────────────────────────────────────────────
    def _build_slots(self):
        slots = []
        idx   = 0
        for col in range(N_COLS):
            sx = COL_X[col]
            for row in range(N_ROWS):
                sy = SLOT_AREA_TOP + row * SLOT_STEP_Y
                slots.append(Slot(idx, col, row, sx, sy))
                idx += 1
        return slots   # 32 slots: col-major order

    # ── Slot selection ──────────────────────────────────────────────────────────
    def _nearest_slot(self, prefer_col=None):
        """
        Nearest-first: Manhattan driving distance from entry point to slot centre.
        Right-aisle slots carry a horizontal-crossing penalty.
        prefer_col: if set, only consider slots in cols < 2 ("left") or cols >= 2 ("right").
        """
        free = [s for s in self.slots if not s.occupied and not s.reserved]
        if prefer_col is not None:
            free = [s for s in free if (s.col < 2) == (prefer_col == "left")]
        if not free:
            return None
        return min(free, key=lambda s: abs(s.cx - ROAD_ENTRY_LX) + abs(s.cy - INT_ROAD_CY))

    # ── Traffic checks ──────────────────────────────────────────────────────────
    def _entry_corridor_busy(self):
        """External segment (below entry gate) is occupied by an entering car."""
        return any(c.state == MOVING and c.wp_idx == 0 for c in self.cars)

    def _exit_corridor_busy(self):
        """Vertical road exit segment occupied — both path types now share same wp structure."""
        # wp_idx >= 2: car has reached exit gate and is heading down the vertical road
        return any(c.state == EXITING and c.wp_idx >= 2 for c in self.cars)

    def _left_aisle_backing_out(self):
        """A car is mid-back-out across the left aisle (blocks entire aisle width)."""
        return any(
            c.state == EXITING and c.path_type == "left" and c.wp_idx == 0
            for c in self.cars
        )

    def _right_aisle_backing_out(self):
        """A car is mid-back-out across the right aisle."""
        return any(
            c.state == EXITING and c.path_type == "right" and c.wp_idx == 0
            for c in self.cars
        )

    def _left_aisle_entering(self):
        """An entering car is currently driving up the left entry lane (wp_idx==2)."""
        return any(
            c.state == MOVING and c.path_type == "left" and c.wp_idx == 2
            for c in self.cars
        )

    def _right_aisle_entering(self):
        """An entering car is currently driving up the right entry lane (wp_idx==2)."""
        return any(
            c.state == MOVING and c.path_type == "right" and c.wp_idx == 2
            for c in self.cars
        )

    def _left_aisle_exit_lane_busy(self):
        """A car is already in the left exit lane (backing out OR driving down)."""
        return any(
            c.state == EXITING and c.path_type == "left" and c.wp_idx <= 1
            for c in self.cars
        )

    def _right_aisle_exit_lane_busy(self):
        """A car is already in the right exit lane (backing out OR driving down)."""
        return any(
            c.state == EXITING and c.path_type == "right" and c.wp_idx <= 1
            for c in self.cars
        )

    # ── Public API ──────────────────────────────────────────────────────────────
    def try_spawn(self):
        if self._entry_corridor_busy():
            return  # entry gate corridor is occupied

        # Try left aisle first (unless it's backing out), then right
        slot = None
        if not self._left_aisle_backing_out():
            slot = self._nearest_slot(prefer_col="left")
        if slot is None and not self._right_aisle_backing_out():
            slot = self._nearest_slot(prefer_col="right")
        if slot is None:
            return  # all aisles busy or lot full

        slot.reserved = True
        car = Car(slot.index)
        car.park_duration = random.uniform(PARK_MIN, PARK_MAX)
        car.set_entry_path(slot)
        slot.car_ref = car
        self.cars.append(car)
        self.cars_in += 1
        self.barriers[0].open()

    def update(self, dt):
        for b in self.barriers:
            b.update(dt)

        # Keep exit barrier open while any car is still exiting
        if any(c.state == EXITING for c in self.cars):
            self.barriers[1].open()

        for car in self.cars:
            prev_state = car.state
            car.update(dt)

            if prev_state == MOVING and car.state == PARKED:
                slot = self.slots[car.slot_index]
                slot.reserved = False
                slot.occupied = True

            # Handle DEPARTING → EXITING when conditions allow
            if car.state == DEPARTING:
                self._try_start_exit(car)

        # Update IR sensors for all slots
        for slot in self.slots:
            slot.update_sensor(dt)

        # Remove fully exited cars
        exited = [c for c in self.cars if c.state == EXITED]
        for car in exited:
            self.cars.remove(car)
            self.cars_out += 1

    def _try_start_exit(self, car):
        """Attempt to move car from DEPARTING to EXITING if aisle is clear."""
        if self._exit_corridor_busy():
            return  # external exit corridor occupied

        if car.path_type == "left":
            if self._left_aisle_exit_lane_busy() or self._left_aisle_entering():
                return
        else:
            if self._right_aisle_exit_lane_busy() or self._right_aisle_entering():
                return

        slot = self.slots[car.slot_index]
        slot.occupied = False
        slot.reserved = False
        slot.car_ref  = None
        car.set_exit_path(slot)
        car.state = EXITING
        self.barriers[1].open()

    @property
    def free_count(self):
        return self.available_count

    @property
    def available_count(self):
        return sum(1 for s in self.slots if not s.occupied and not s.reserved)

    @property
    def occupied_count(self):
        return sum(1 for s in self.slots if s.occupied)

    @property
    def reserved_count(self):
        return sum(1 for s in self.slots if s.reserved and not s.occupied)

    @property
    def total_slots(self):
        return len(self.slots)
