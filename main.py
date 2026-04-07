import pygame
import sys
import math
import random

from config import *
from lot import ParkingLot


# ── Background ─────────────────────────────────────────────────────────────────

def draw_background(surf):
    surf.fill(DARK_GRAY)

    # ── Vertical external road (LEFT side, full screen height) ─────────────────
    pygame.draw.rect(surf, ROAD_COL, (ROAD_X, 0, ROAD_W, SCREEN_H))

    # Lane divider (vertical dashed line between entry and exit lanes)
    road_mid = ROAD_X + ROAD_W // 2
    for y in range(0, SCREEN_H, 28):
        pygame.draw.rect(surf, MARKING, (road_mid - 1, y, 2, 16))

    # Direction arrows on the vertical road
    for y in range(60, SCREEN_H - 40, 100):
        # ↑ entry lane arrow (left lane, cars go UP)
        ex = ROAD_ENTRY_LX
        pts_up = [(ex, y), (ex - 6, y + 14), (ex + 6, y + 14)]
        pygame.draw.polygon(surf, MARKING, pts_up)
        # ↓ exit lane arrow (right lane, cars go DOWN)
        dx = ROAD_EXIT_LX
        pts_dn = [(dx, y + 14), (dx - 6, y), (dx + 6, y)]
        pygame.draw.polygon(surf, MARKING, pts_dn)

    # Gate labels on the vertical road
    _rfont  = pygame.font.SysFont("consolas", 10, bold=True)
    _rfont2 = pygame.font.SysFont("consolas",  9)
    road_mid = ROAD_X + ROAD_W // 2

    # "IN" above entry lane (left half), "OUT" below exit lane (right half)
    for text, col, x_anchor, y_off in [
            ("IN",  LED_ON_G, ROAD_ENTRY_LX, ENTRY_GATE_Y - 22),
            ("OUT", LED_ON_R, ROAD_EXIT_LX,  EXIT_GATE_Y  +  8),
    ]:
        lbl = _rfont.render(text, True, col)
        surf.blit(lbl, (x_anchor - lbl.get_width() // 2, y_off))

    # "GATE" centred on road, between the two gate Y positions
    gate_y = (ENTRY_GATE_Y + EXIT_GATE_Y) // 2
    sg = _rfont2.render("SECURITY", True, YELLOW)
    gt = _rfont2.render("  GATE",   True, YELLOW)
    surf.blit(sg, (ROAD_X + 2, gate_y - 9))
    surf.blit(gt, (ROAD_X + 2, gate_y + 1))

    # ── Entry/exit arrow indicators at the lot wall opening ────────────────────
    ax = LOT_X + 22   # just inside lot entrance
    # → entry arrow (green)
    pygame.draw.polygon(surf, LED_ON_G,
                        [(ax, ENTRY_GATE_Y),
                         (ax - 11, ENTRY_GATE_Y - 7),
                         (ax - 11, ENTRY_GATE_Y + 7)])
    # ← exit arrow (red)
    pygame.draw.polygon(surf, LED_ON_R,
                        [(ax - 11, EXIT_GATE_Y),
                         (ax,      EXIT_GATE_Y - 7),
                         (ax,      EXIT_GATE_Y + 7)])

    # ── Lot base ───────────────────────────────────────────────────────────────
    pygame.draw.rect(surf, ASPHALT, (LOT_X, LOT_Y, LOT_W, LOT_H))

    # ── Internal horizontal road ───────────────────────────────────────────────
    pygame.draw.rect(surf, INT_ROAD_COL,
                     (LOT_X, INT_ROAD_TOP, LOT_W, INT_ROAD_H))
    for x in range(LOT_X + 10, LOT_X + LOT_W - 10, 28):
        pygame.draw.rect(surf, MARKING, (x, INT_ROAD_CY - 1, 16, 2))

    # ── Aisle regions ──────────────────────────────────────────────────────────
    for ax in (AISLE0_X, AISLE1_X):
        pygame.draw.rect(surf, AISLE_COL,
                         (ax, SLOT_AREA_TOP, AISLE_W, SLOT_AREA_H))

    # Lane dividers within aisles — drawn in small dashes, leaving gaps at each
    # slot row so backing-out cars don't visually clip the centre line.
    for ax in (AISLE0_X, AISLE1_X):
        mid = ax + AISLE_W // 2
        for r in range(N_ROWS):
            row_cy = SLOT_AREA_TOP + SLOT_W // 2 + r * SLOT_STEP_Y
            seg_top = row_cy - SLOT_W // 2 + 8
            seg_bot = row_cy + SLOT_W // 2 - 8
            for y in range(seg_top, seg_bot, 14):
                pygame.draw.rect(surf, MARKING, (mid - 1, y, 2, 8))

    # Direction arrows in aisles
    for ax in (AISLE0_X, AISLE1_X):
        entry_x = ax + AISLE_W // 4
        exit_x  = ax + 3 * AISLE_W // 4
        for y in range(SLOT_AREA_TOP + 30, SLOT_AREA_BOTTOM - 20, 80):
            pts_up = [(entry_x,     y + 14),
                      (entry_x - 7, y + 24),
                      (entry_x + 7, y + 24)]
            pygame.draw.polygon(surf, MARKING, pts_up)
            pts_dn = [(exit_x,     y + 24),
                      (exit_x - 7, y + 14),
                      (exit_x + 7, y + 14)]
            pygame.draw.polygon(surf, MARKING, pts_dn)

    # Centre divider between COL1 and COL2
    mid_x = COL1_X + SLOT_DEPTH
    pygame.draw.line(surf, CURB_COL,
                     (mid_x, SLOT_AREA_TOP), (mid_x, SLOT_AREA_BOTTOM), 3)

    # Lot border / curb
    pygame.draw.rect(surf, CURB_COL, (LOT_X, LOT_Y, LOT_W, LOT_H), 3)

    # Opening in left wall spanning the full internal road height
    pygame.draw.rect(surf, INT_ROAD_COL,
                     (LOT_X - (ROAD_W - 4), INT_ROAD_TOP, ROAD_W - 4, INT_ROAD_H))

    # ── Security booth – straddles the left lot wall at the horizontal road ────
    _bx = LOT_X - 5
    _bw = 20
    pygame.draw.rect(surf, (14, 16, 24),  (_bx, INT_ROAD_TOP, _bw, INT_ROAD_H), border_radius=2)
    # Windows on north and south faces (visible from the aisles)
    pygame.draw.rect(surf, (48, 68, 108), (_bx + 3,       INT_ROAD_TOP + 8, _bw - 6, 16), border_radius=1)
    pygame.draw.rect(surf, (48, 68, 108), (_bx + 3,       INT_ROAD_TOP + INT_ROAD_H - 24, _bw - 6, 16), border_radius=1)
    pygame.draw.rect(surf, (40, 42, 52),  (_bx, INT_ROAD_TOP, _bw, INT_ROAD_H), 1, border_radius=2)


# ── Slots ──────────────────────────────────────────────────────────────────────

def draw_slots(surf, lot, font):
    for slot in lot.slots:
        if slot.occupied:
            col = SLOT_OCC
        elif slot.car_nearby:
            col = ORANGE
        else:
            col = SLOT_FREE
        r   = pygame.Rect(slot.x, slot.y, SLOT_DEPTH, SLOT_W)
        pygame.draw.rect(surf, col, r, border_radius=3)
        pygame.draw.rect(surf, CURB_COL, r, 1, border_radius=3)

        # Slot label
        lbl = font.render(f"P{slot.index + 1}", True, WHITE)
        surf.blit(lbl, (slot.cx - lbl.get_width()  // 2,
                        slot.cy - lbl.get_height() // 2))

        # IR sensor LED (corner closest to aisle)
        led_col = LED_ON_R if slot.ir_sensor_triggered else LED_ON_G
        # Aisle-facing edge: right for col 0 & 2, left for col 1 & 3
        if slot.col in (0, 2):
            lx = slot.x + SLOT_DEPTH - 8
        else:
            lx = slot.x + 8
        ly = slot.y + 8
        pygame.draw.circle(surf, led_col, (lx, ly), 4)
        pygame.draw.circle(surf, WHITE,   (lx, ly), 4, 1)


# ── Barriers ───────────────────────────────────────────────────────────────────

def draw_barrier(surf, barrier):
    """
    Gates sit on the HORIZONTAL internal road.
    angle=0  → arm VERTICAL   (closed – blocks east/west traffic)
    angle=82 → arm HORIZONTAL (open   – parallel to road, out of way)
    Entry post: top road edge, arm swings south  (lift_sign=+1).
    Exit  post: bot road edge, arm swings north  (lift_sign=-1).
    Both rotate east when opening (direction=+1).
    """
    px, py  = barrier.post_x, barrier.post_y
    arm_len = INT_ROAD_H // 2 - 2   # reaches exactly to road centre-line
    rad = math.radians(barrier.angle)
    # sin grows as arm tilts from vertical → horizontal (east)
    # cos shrinks correspondingly
    ex = px + barrier.direction * int(arm_len * math.sin(rad))
    ey = py + barrier.lift_sign  * int(arm_len * math.cos(rad))
    col = GREEN if barrier.is_open else RED

    # Arm: coloured body + white centre stripe (real boom-gate look)
    pygame.draw.line(surf, col,             (px, py), (ex, ey), 6)
    pygame.draw.line(surf, (215, 218, 225), (px, py), (ex, ey), 2)
    # Hinge pivot + tip ball
    pygame.draw.circle(surf, (72, 75, 88), (px, py), 5)
    pygame.draw.circle(surf, col, (ex, ey), 4)


# ── Controller panel ───────────────────────────────────────────────────────────

def draw_panel(surf, lot, font_s, font_m, speed_mult=1.0):
    ps = pygame.Surface((PANEL_W, PANEL_H))
    ps.fill(PANEL_BG)
    y = 10

    # Title
    t = font_m.render("[ CONTROLLER ]", True, PANEL_HL)
    ps.blit(t, (PANEL_W // 2 - t.get_width() // 2, y));  y += 28
    pygame.draw.line(ps, PANEL_HL, (4, y), (PANEL_W - 4, y), 1);  y += 10

    # ── Slot register: 4-col × 8-row grid ─────────────────────────────────────
    ps.blit(font_s.render("SLOT REGISTER", True, PANEL_DIM), (6, y));  y += 15

    label_w  = 22    # width reserved for row label
    cell_w   = (PANEL_W - 12 - label_w) // N_COLS   # ~63
    cell_h   = 14
    row_step = cell_h + 4

    # Column headers
    for c in range(N_COLS):
        hdr = font_s.render(f"C{c + 1}", True, PANEL_DIM)
        cx_ = 6 + label_w + c * cell_w + cell_w // 2 - hdr.get_width() // 2
        ps.blit(hdr, (cx_, y))
    y += 14

    # Grid rows
    for r in range(N_ROWS):
        rl = font_s.render(f"R{r + 1}", True, PANEL_DIM)
        ps.blit(rl, (6, y + 1))
        for c in range(N_COLS):
            slot = lot.slots[c * N_ROWS + r]   # col-major indexing
            if slot.occupied:
                bc = LED_ON_R
                bit_text = "1"
            elif slot.reserved:
                bc = ORANGE
                bit_text = "R"
            else:
                bc = LED_ON_G
                bit_text = "0"
            bx   = 6 + label_w + c * cell_w
            pygame.draw.rect(ps, bc, (bx, y, cell_w - 4, cell_h), border_radius=2)
            bit = font_s.render(bit_text, True, BLACK)
            ps.blit(bit, (bx + (cell_w - 4) // 2 - bit.get_width() // 2, y + 1))
        y += row_step

    y += 4
    pygame.draw.line(ps, PANEL_DIM, (4, y), (PANEL_W - 4, y), 1);  y += 8

    # ── Gate status ────────────────────────────────────────────────────────────
    ps.blit(font_s.render("GATE STATUS", True, PANEL_DIM), (6, y));  y += 15
    for b in lot.barriers:
        gc = LED_ON_G if b.is_open else LED_ON_R
        gs = "OPEN  " if b.is_open else "CLOSED"
        ps.blit(font_s.render(f"  {b.name}: {gs}", True, gc), (6, y));  y += 15
    pygame.draw.line(ps, PANEL_DIM, (4, y), (PANEL_W - 4, y), 1);  y += 8

    # ── Stats ──────────────────────────────────────────────────────────────────
    stats = [
        ("TOTAL SLOTS", str(lot.total_slots)),
        ("AVAILABLE",   str(lot.available_count)),
        ("RESERVED",    str(lot.reserved_count)),
        ("OCCUPIED",    str(lot.occupied_count)),
        ("CARS IN",     str(lot.cars_in)),
        ("CARS OUT",    str(lot.cars_out)),
    ]
    for k, v in stats:
        kl = font_s.render(f"  {k}", True, PANEL_DIM)
        vl = font_s.render(v, True, WHITE)
        ps.blit(kl, (6, y))
        ps.blit(vl, (PANEL_W - vl.get_width() - 8, y))
        y += 16
    pygame.draw.line(ps, PANEL_DIM, (4, y), (PANEL_W - 4, y), 1);  y += 8

    # ── Algorithm ──────────────────────────────────────────────────────────────
    ps.blit(font_s.render("ALGORITHM", True, PANEL_DIM), (6, y));  y += 15
    ps.blit(font_s.render("  Nearest-First", True, PANEL_HL), (6, y));  y += 20
    pygame.draw.line(ps, PANEL_DIM, (4, y), (PANEL_W - 4, y), 1);  y += 8

    # ── Speed ──────────────────────────────────────────────────────────────────
    ps.blit(font_s.render("SPEED", True, PANEL_DIM), (6, y))
    sc = PANEL_HL if speed_mult != 1.0 else PANEL_DIM
    sv = font_s.render(f"{speed_mult:.1f}x", True, sc)
    ps.blit(sv, (PANEL_W - sv.get_width() - 8, y));  y += 16
    pygame.draw.line(ps, PANEL_DIM, (4, y), (PANEL_W - 4, y), 1);  y += 8

    # ── Controls ───────────────────────────────────────────────────────────────
    for line in ["[SPACE]  Spawn car",
                 "[T]      Toggle panel",
                 "[+/-]    Speed",
                 "[ESC]    Quit"]:
        ps.blit(font_s.render(line, True, PANEL_DIM), (6, y));  y += 15

    surf.blit(ps, (PANEL_X, PANEL_Y))
    pygame.draw.rect(surf, PANEL_HL, (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), 1)


# ── HUD ────────────────────────────────────────────────────────────────────────

def draw_hud(surf, lot, font_m):
    surf.blit(font_m.render(TITLE, True, WHITE), (LOT_X, 18))
    free = lot.available_count
    tot  = lot.total_slots
    col  = GREEN if free > tot // 4 else (YELLOW if free > 0 else RED)
    al   = font_m.render(f"Available: {free} / {tot}", True, col)
    surf.blit(al, (LOT_X + LOT_W - al.get_width(), 18))


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    font_s = pygame.font.SysFont("consolas", 12)
    font_m = pygame.font.SysFont("consolas", 15, bold=True)

    lot         = ParkingLot()
    show_panel  = True
    spawn_timer = 0.0
    next_spawn  = random.uniform(SPAWN_MIN, SPAWN_MAX)
    speed_mult  = 1.0   # simulation speed multiplier (0.5 – 4×)

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif event.key == pygame.K_t:
                    show_panel = not show_panel
                elif event.key == pygame.K_SPACE:
                    lot.try_spawn()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_mult = min(round(speed_mult * 1.5, 2), 4.0)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_mult = max(round(speed_mult / 1.5, 2), 0.5)

        sdt = dt * speed_mult          # scaled delta-time
        spawn_timer += sdt
        if spawn_timer >= next_spawn:
            lot.try_spawn()
            spawn_timer = 0.0
            next_spawn  = random.uniform(SPAWN_MIN, SPAWN_MAX)

        lot.update(sdt)

        draw_background(screen)
        draw_slots(screen, lot, font_s)
        for b in lot.barriers:
            draw_barrier(screen, b)
        for car in lot.cars:
            car.draw(screen, font_s)
        if show_panel:
            draw_panel(screen, lot, font_s, font_m, speed_mult)
        draw_hud(screen, lot, font_m)

        pygame.display.flip()


if __name__ == "__main__":
    main()
