"""
PLATFORM HERO
A complete, original side-scrolling platformer inspired by the classic
"run, jump, stomp enemies, collect coins" genre — built with pygame.

Controls
--------
  LEFT / A    : move left
  RIGHT / D   : move right
  SPACE / UP  : jump
  P           : pause / unpause
  ENTER       : start game (from menu) / confirm
  R           : restart (after game over or win)
  ESC         : quit

Run with:  python platform_hero.py
Requires:  pip install pygame
"""

import math
import random
import sys

import pygame

# --------------------------------------------------------------------------- #
# CONSTANTS
# --------------------------------------------------------------------------- #

TILE = 48
SCREEN_WIDTH = 800        # 22 tiles
SCREEN_HEIGHT = 624         # 13 tiles
FPS = 60

GRAVITY = 0.9
MAX_FALL_SPEED = 28.0
PLAYER_SPEED = 5.5
JUMP_VELOCITY = -20.0
STOMP_BOUNCE = -11.0

ENEMY_SPEED = 1.6

PLAYER_W, PLAYER_H = 34, 46
ENEMY_W, ENEMY_H = 36, 32
COIN_SIZE = 26

INVINCIBLE_TIME = 1.6          # seconds of flashing invulnerability after a hit
STARTING_LIVES = 3
TIME_LIMIT = 300               # seconds per life

GROUND_ROW = 11                # tile row where the main ground starts (top surface)
GROUND_THICKNESS = 2           # tiles

# Colors
SKY_TOP = (92, 148, 252)
SKY_BOTTOM = (168, 208, 255)
CLOUD_COLOR = (255, 255, 255)
HILL_FAR = (60, 150, 90)
HILL_NEAR = (46, 130, 74)

GROUND_COLOR = (150, 96, 46)
GROUND_TOP_COLOR = (86, 176, 74)
BRICK_COLOR = (176, 108, 56)
BRICK_LINE = (120, 70, 34)

COIN_GOLD = (255, 205, 40)
COIN_LIGHT = (255, 236, 150)

FLAG_POLE = (230, 230, 230)
FLAG_CLOTH = (60, 190, 90)

TEXT_WHITE = (255, 255, 255)
TEXT_BLACK = (30, 30, 30)
TEXT_SHADOW = (0, 0, 0)

PLAYER_CAP = (206, 40, 40)
PLAYER_SHIRT = (206, 40, 40)
PLAYER_OVERALLS = (36, 66, 190)
PLAYER_SKIN = (250, 202, 158)
PLAYER_SHOE = (92, 58, 30)

ENEMY_BODY = (150, 82, 40)
ENEMY_BODY_DARK = (110, 58, 26)
ENEMY_FOOT = (60, 34, 16)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_WIN = "win"
STATE_GAMEOVER = "gameover"


# --------------------------------------------------------------------------- #
# LEVEL DATA
# --------------------------------------------------------------------------- #

def build_level():
    """
    Builds the level in a data-driven way (no hand-typed ASCII maps),
    which keeps geometry consistent and easy to verify.

    Returns a dict with:
      platforms   -> list of pygame.Rect (solid collidable ground/blocks)
      coins       -> list of (x, y) pixel centers
      enemies     -> list of (x, y, patrol_left_px, patrol_right_px)
      flag_pos    -> (x, y) pixel position of the flag base
      player_start-> (x, y) pixel top-left spawn for the player
      checkpoints -> list of x pixel thresholds for mid-level respawn
      level_width -> total level width in pixels
      level_height-> total level height in pixels
    """
    platforms = []
    coins = []
    enemies = []

    def ground_rect(start_tile, end_tile, row=GROUND_ROW, thickness=GROUND_THICKNESS):
        x = start_tile * TILE
        w = (end_tile - start_tile) * TILE
        y = row * TILE
        h = thickness * TILE
        r = pygame.Rect(x, y, w, h)
        platforms.append(r)
        return r

    def floating_platform(start_tile, end_tile, row):
        x = start_tile * TILE
        w = (end_tile - start_tile) * TILE
        y = row * TILE
        r = pygame.Rect(x, y, w, TILE)
        platforms.append(r)
        return r

    def add_coin_row(start_tile, end_tile, row, step=1):
        t = start_tile
        while t < end_tile:
            cx = t * TILE + TILE // 2
            cy = row * TILE + TILE // 2
            coins.append((cx, cy))
            t += step

    def add_enemy(spawn_tile, row, patrol_start_tile, patrol_end_tile):
        x = spawn_tile * TILE
        y = row * TILE - ENEMY_H
        left = patrol_start_tile * TILE
        right = patrol_end_tile * TILE - ENEMY_W
        enemies.append((x, y, left, right))

    # --- Ground segments separated by pits ------------------------------- #
    # seg1: tiles 0-18   | pit: 18-21 (3 tiles)
    # seg2: tiles 21-40  | pit: 40-44 (4 tiles)
    # seg3: tiles 44-64  | pit: 64-68 (4 tiles)
    # seg4: tiles 68-96  | flag near tile 92, level ends at 96
    seg1 = ground_rect(0, 18)
    seg2 = ground_rect(21, 40)
    seg3 = ground_rect(44, 64)
    seg4 = ground_rect(68, 96)

    LEVEL_WIDTH = 96 * TILE
    LEVEL_HEIGHT = (GROUND_ROW + GROUND_THICKNESS) * TILE

    # --- Floating bonus platforms with coins ------------------------------ #
    floating_platform(5, 8, GROUND_ROW - 3)
    add_coin_row(5, 8, GROUND_ROW - 4)

    floating_platform(25, 29, GROUND_ROW - 3)
    add_coin_row(25, 29, GROUND_ROW - 4)

    floating_platform(33, 36, GROUND_ROW - 4)
    add_coin_row(33, 36, GROUND_ROW - 5)

    # a stepping-stone platform above the wide pit2 for a two-hop crossing
    floating_platform(41, 43, GROUND_ROW - 2)

    floating_platform(48, 51, GROUND_ROW - 3)
    add_coin_row(48, 51, GROUND_ROW - 4)

    floating_platform(56, 60, GROUND_ROW - 5)
    add_coin_row(56, 60, GROUND_ROW - 6)

    floating_platform(74, 78, GROUND_ROW - 3)
    add_coin_row(74, 78, GROUND_ROW - 4)

    floating_platform(84, 88, GROUND_ROW - 4)
    add_coin_row(84, 88, GROUND_ROW - 5)

    # --- Ground-level coin trails ------------------------------------------ #
    add_coin_row(10, 15, GROUND_ROW - 2, step=1)
    add_coin_row(27, 32, GROUND_ROW - 2, step=1)
    add_coin_row(50, 55, GROUND_ROW - 2, step=1)
    add_coin_row(80, 84, GROUND_ROW - 2, step=1)

    # --- Enemies ------------------------------------------------------------ #
    add_enemy(9, GROUND_ROW, 4, 17)
    add_enemy(26, GROUND_ROW, 22, 33)
    add_enemy(34, GROUND_ROW, 22, 39)
    add_enemy(48, GROUND_ROW, 45, 55)
    add_enemy(58, GROUND_ROW, 56, 63)
    add_enemy(75, GROUND_ROW, 69, 81)
    add_enemy(88, GROUND_ROW, 82, 95)

    # --- Flag / goal --------------------------------------------------------- #
    flag_tile = 92
    flag_pos = (flag_tile * TILE + TILE // 2, GROUND_ROW * TILE)

    # --- Player spawn --------------------------------------------------------- #
    player_start = (2 * TILE, GROUND_ROW * TILE - PLAYER_H)

    # --- Checkpoints (x pixel thresholds -> respawn x) ------------------------ #
    checkpoints = [
        (0, 2 * TILE),
        (seg2.x, seg2.x + TILE),
        (seg3.x, seg3.x + TILE),
        (seg4.x, seg4.x + TILE),
    ]

    return {
        "platforms": platforms,
        "coins": coins,
        "enemies": enemies,
        "flag_pos": flag_pos,
        "player_start": player_start,
        "checkpoints": checkpoints,
        "level_width": LEVEL_WIDTH,
        "level_height": LEVEL_HEIGHT,
    }


# --------------------------------------------------------------------------- #
# ENTITIES
# --------------------------------------------------------------------------- #

class Coin:
    def __init__(self, x, y):
        self.base_x = x
        self.base_y = y
        self.rect = pygame.Rect(0, 0, COIN_SIZE, COIN_SIZE)
        self.rect.center = (x, y)
        self.alive = True
        self.phase = random.uniform(0, math.pi * 2)
        self.timer = 0.0

    def update(self, dt):
        if not self.alive:
            return
        self.timer += dt
        bob = math.sin(self.timer * 4 + self.phase) * 5
        self.rect.centery = int(self.base_y + bob)

    def draw(self, surface, cam_x):
        if not self.alive:
            return
        cx = self.rect.centerx - cam_x
        cy = self.rect.centery
        squash = abs(math.cos(self.timer * 4 + self.phase))
        w = max(4, int(COIN_SIZE * squash))
        rect = pygame.Rect(0, 0, w, COIN_SIZE)
        rect.center = (cx, cy)
        pygame.draw.ellipse(surface, COIN_GOLD, rect)
        inner = rect.inflate(-8, -8)
        if inner.width > 0 and inner.height > 0:
            pygame.draw.ellipse(surface, COIN_LIGHT, inner, 2)


class Enemy:
    def __init__(self, x, y, patrol_left, patrol_right):
        self.rect = pygame.Rect(x, y, ENEMY_W, ENEMY_H)
        self.patrol_left = min(patrol_left, patrol_right)
        self.patrol_right = max(patrol_left, patrol_right)
        self.vel_x = -ENEMY_SPEED
        self.vel_y = 0.0
        self.alive = True
        self.walk_timer = 0.0
        self.squash_timer = 0.0

    def update(self, dt, platforms):
        if not self.alive:
            return
        self.walk_timer += dt

        # Reverse direction at patrol bounds.
        if self.rect.left <= self.patrol_left and self.vel_x < 0:
            self.vel_x = ENEMY_SPEED
        elif self.rect.right >= self.patrol_right and self.vel_x > 0:
            self.vel_x = -ENEMY_SPEED

        # Horizontal movement.
        self.rect.x += int(round(self.vel_x))
        if self.rect.left < self.patrol_left:
            self.rect.left = self.patrol_left
            self.vel_x = ENEMY_SPEED
        if self.rect.right > self.patrol_right:
            self.rect.right = self.patrol_right
            self.vel_x = -ENEMY_SPEED

        # Vertical movement (gravity).
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.rect.y += int(round(self.vel_y))
        for p in platforms:
            if self.rect.colliderect(p) and self.vel_y >= 0:
                self.rect.bottom = p.top
                self.vel_y = 0.0

    def draw(self, surface, cam_x):
        if not self.alive:
            return
        r = self.rect.move(-cam_x, 0)
        step = int(self.walk_timer * 8) % 2
        foot_offset = 3 if step == 0 else -3

        # body (rounded mushroom-like shape)
        body_rect = pygame.Rect(r.x, r.y, r.width, r.height - 6)
        pygame.draw.ellipse(surface, ENEMY_BODY, body_rect)
        cap_rect = pygame.Rect(r.x - 2, r.y - 4, r.width + 4, int(r.height * 0.6))
        pygame.draw.ellipse(surface, ENEMY_BODY_DARK, cap_rect)

        # eyes
        eye_y = r.y + r.height // 2 - 2
        pygame.draw.ellipse(surface, (255, 255, 255), (r.x + 6, eye_y, 8, 10))
        pygame.draw.ellipse(surface, (255, 255, 255), (r.x + r.width - 14, eye_y, 8, 10))
        pygame.draw.circle(surface, (20, 20, 20), (r.x + 10, eye_y + 6), 2)
        pygame.draw.circle(surface, (20, 20, 20), (r.x + r.width - 10, eye_y + 6), 2)

        # angry eyebrows
        pygame.draw.line(surface, (20, 20, 20), (r.x + 4, eye_y - 2), (r.x + 14, eye_y + 1), 2)
        pygame.draw.line(surface, (20, 20, 20), (r.x + r.width - 4, eye_y - 2),
                          (r.x + r.width - 14, eye_y + 1), 2)

        # feet
        pygame.draw.ellipse(surface, ENEMY_FOOT,
                             (r.x + 2 + foot_offset, r.bottom - 8, 12, 8))
        pygame.draw.ellipse(surface, ENEMY_FOOT,
                             (r.x + r.width - 14 - foot_offset, r.bottom - 8, 12, 8))


class Flag:
    def __init__(self, x, ground_y, height_tiles=6):
        self.pole_rect = pygame.Rect(x - 3, ground_y - height_tiles * TILE, 6,
                                      height_tiles * TILE)
        self.trigger_rect = pygame.Rect(x - TILE // 2, ground_y - height_tiles * TILE,
                                         TILE, height_tiles * TILE)
        self.top = (x, ground_y - height_tiles * TILE)

    def draw(self, surface, cam_x):
        pr = self.pole_rect.move(-cam_x, 0)
        pygame.draw.rect(surface, FLAG_POLE, pr)
        pygame.draw.circle(surface, (255, 215, 60), (pr.centerx, pr.top), 6)
        flag_points = [
            (pr.centerx, pr.top + 6),
            (pr.centerx + 42, pr.top + 20),
            (pr.centerx, pr.top + 34),
        ]
        pygame.draw.polygon(surface, FLAG_CLOTH, flag_points)


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_W, PLAYER_H)
        self.prev_rect = self.rect.copy()
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing = 1  # 1 = right, -1 = left
        self.walk_timer = 0.0
        self.invincible_timer = 0.0
        self.dead_fall = False

    def reset(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.invincible_timer = INVINCIBLE_TIME
        self.dead_fall = False

    def handle_input(self, keys):
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing = -1
            moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing = 1
            moving = True
        else:
            self.vel_x = 0.0

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False

        return moving

    def apply_physics(self, dt, platforms, level_width):
        self.prev_rect = self.rect.copy()

        # Horizontal movement + collision.
        self.rect.x += int(round(self.vel_x))
        self.rect.x = max(0, min(self.rect.x, level_width - self.rect.width))
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right

        # Vertical movement + collision.
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.rect.y += int(round(self.vel_y))
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0.0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0.0

        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)

    def draw(self, surface, cam_x):
        # Flicker while invincible.
        if self.invincible_timer > 0 and int(self.invincible_timer * 20) % 2 == 0:
            return

        r = self.rect.move(-cam_x, 0)
        moving = abs(self.vel_x) > 0.1 and self.on_ground
        if moving:
            self.walk_timer += 0.25
        leg_offset = int(math.sin(self.walk_timer) * 4) if moving else 0

        flip = self.facing < 0
        cx = r.centerx

        def fx(local_x):
            # mirror an x-offset around center if facing left
            if not flip:
                return cx + local_x
            return cx - local_x

        # legs / shoes
        leg_y = r.bottom - 10
        pygame.draw.rect(surface, PLAYER_SHOE,
                          (r.x + 3, leg_y + leg_offset // 2, 12, 10), border_radius=3)
        pygame.draw.rect(surface, PLAYER_SHOE,
                          (r.right - 15, leg_y - leg_offset // 2, 12, 10), border_radius=3)

        # overalls (lower body)
        overalls_rect = pygame.Rect(r.x + 2, r.centery, r.width - 4, r.height // 2 - 6)
        pygame.draw.rect(surface, PLAYER_OVERALLS, overalls_rect, border_radius=6)

        # shirt / torso
        shirt_rect = pygame.Rect(r.x, r.y + r.height // 3, r.width, r.height // 3 + 4)
        pygame.draw.rect(surface, PLAYER_SHIRT, shirt_rect, border_radius=6)

        # overalls straps
        pygame.draw.rect(surface, PLAYER_OVERALLS, (r.x + 6, r.y + r.height // 3, 5, 12))
        pygame.draw.rect(surface, PLAYER_OVERALLS, (r.right - 11, r.y + r.height // 3, 5, 12))

        # head
        head_center = (cx, r.y + 12)
        pygame.draw.circle(surface, PLAYER_SKIN, head_center, 13)

        # cap
        cap_rect = pygame.Rect(r.x - 2, r.y - 6, r.width + 4, 16)
        pygame.draw.ellipse(surface, PLAYER_CAP, cap_rect)
        brim_x = fx(10)
        pygame.draw.ellipse(surface, PLAYER_CAP, (min(brim_x, cx) - 4, r.y + 2, 20, 8))

        # mustache
        mus_y = r.y + 15
        pygame.draw.ellipse(surface, (60, 40, 20), (cx - 8, mus_y, 16, 6))

        # eye
        eye_x = fx(5)
        pygame.draw.circle(surface, (20, 20, 20), (eye_x, r.y + 10), 2)

        # arm
        arm_x = fx(14)
        pygame.draw.line(surface, PLAYER_SHIRT, (cx, r.y + r.height // 2),
                          (arm_x, r.y + r.height // 2 + 8), 6)


# --------------------------------------------------------------------------- #
# CAMERA
# --------------------------------------------------------------------------- #

class Camera:
    def __init__(self, level_width, screen_width):
        self.level_width = level_width
        self.screen_width = screen_width
        self.x = 0

    def update(self, target_rect):
        target_x = target_rect.centerx - self.screen_width // 2
        self.x = max(0, min(target_x, max(0, self.level_width - self.screen_width)))


# --------------------------------------------------------------------------- #
# BACKGROUND (simple parallax decoration)
# --------------------------------------------------------------------------- #

def build_background(level_width):
    rng = random.Random(42)
    clouds = []
    for _ in range(24):
        x = rng.randint(0, level_width)
        y = rng.randint(30, 180)
        scale = rng.uniform(0.7, 1.4)
        clouds.append((x, y, scale))

    hills = []
    x = 0
    while x < level_width:
        w = rng.randint(220, 380)
        h = rng.randint(80, 160)
        hills.append((x, w, h))
        x += w - rng.randint(20, 60)

    return {"clouds": clouds, "hills": hills}


def draw_cloud(surface, x, y, scale):
    r = int(18 * scale)
    pygame.draw.ellipse(surface, CLOUD_COLOR, (x, y, r * 2, r))
    pygame.draw.ellipse(surface, CLOUD_COLOR, (x + r, y - r // 2, int(r * 1.6), int(r * 1.2)))
    pygame.draw.ellipse(surface, CLOUD_COLOR, (x - r // 2, y + r // 4, int(r * 1.4), r))


# --------------------------------------------------------------------------- #
# GAME
# --------------------------------------------------------------------------- #

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Platform Hero")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 64, bold=True)
        self.font_med = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 22, bold=True)

        self.state = STATE_MENU
        self.running = True

        self.score = 0
        self.lives = STARTING_LIVES
        self.time_left = TIME_LIMIT
        self.current_checkpoint = (0, 0)

        self._full_reset()

    # ----------------------------------------------------------------- #
    # Setup / reset helpers
    # ----------------------------------------------------------------- #
    def _full_reset(self):
        self.level = build_level()
        self.background = build_background(self.level["level_width"])
        self.platforms = self.level["platforms"]
        self.coins = [Coin(x, y) for x, y in self.level["coins"]]
        self.enemies = [Enemy(x, y, l, r) for x, y, l, r in self.level["enemies"]]
        self.flag = Flag(*self.level["flag_pos"])
        self.player = Player(*self.level["player_start"])
        self.camera = Camera(self.level["level_width"], SCREEN_WIDTH)
        self.score = 0
        self.lives = STARTING_LIVES
        self.time_left = TIME_LIMIT
        self.current_checkpoint = self.level["player_start"]
        self.win_bonus_applied = False

    def _respawn_level_entities(self):
        """Reset coins/enemies (used when the player loses a life mid-level,
        keeping score/lives) and put the player back at the last checkpoint."""
        self.player.reset(*self.current_checkpoint)
        self.time_left = TIME_LIMIT

    def _update_checkpoint(self):
        for threshold_x, spawn_x in self.level["checkpoints"]:
            if self.player.rect.x >= threshold_x:
                spawn_y = GROUND_ROW * TILE - PLAYER_H
                self.current_checkpoint = (spawn_x, spawn_y)

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.state = STATE_GAMEOVER
        else:
            self._respawn_level_entities()

    # ----------------------------------------------------------------- #
    # Update
    # ----------------------------------------------------------------- #
    def update(self, dt, keys):
        if self.state != STATE_PLAYING:
            return

        self.player.handle_input(keys)
        self.player.apply_physics(dt, self.platforms, self.level["level_width"])
        self._update_checkpoint()

        for coin in self.coins:
            coin.update(dt)
            if coin.alive and self.player.rect.colliderect(coin.rect):
                coin.alive = False
                self.score += 50

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            enemy.update(dt, self.platforms)
            if self.player.invincible_timer <= 0 and self.player.rect.colliderect(enemy.rect):
                stomped = (
                    self.player.vel_y > 0
                    and self.player.prev_rect.bottom <= enemy.rect.top + 12
                )
                if stomped:
                    enemy.alive = False
                    self.score += 100
                    self.player.vel_y = STOMP_BOUNCE
                else:
                    self.player.vel_y = -8.0
                    self.player.vel_x = -6.0 * self.player.facing
                    self.player.invincible_timer = INVINCIBLE_TIME
                    self.lose_life()
                    if self.state != STATE_PLAYING:
                        return

        # Flag / goal check.
        if self.player.rect.colliderect(self.flag.trigger_rect):
            if not self.win_bonus_applied:
                self.score += int(self.time_left) * 10
                self.win_bonus_applied = True
            self.state = STATE_WIN
            return

        # Fell into a pit.
        if self.player.rect.top > self.level["level_height"] + 200:
            self.lose_life()
            if self.state != STATE_PLAYING:
                return

        # Timer.
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.lose_life()
            if self.state != STATE_PLAYING:
                return

        self.camera.update(self.player.rect)

    # ----------------------------------------------------------------- #
    # Draw
    # ----------------------------------------------------------------- #
    def draw(self):
        self._draw_sky()
        self._draw_background()
        self._draw_world()
        self._draw_hud()

        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_PAUSED:
            self._draw_center_overlay("PAUSED", "Press P to resume")
        elif self.state == STATE_WIN:
            self._draw_center_overlay("LEVEL COMPLETE!", f"Score: {self.score}   Press R to play again")
        elif self.state == STATE_GAMEOVER:
            self._draw_center_overlay("GAME OVER", f"Score: {self.score}   Press R to try again")

    def _draw_sky(self):
        for i in range(SCREEN_HEIGHT):
            t = i / SCREEN_HEIGHT
            color = (
                int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t),
                int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t),
                int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t),
            )
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))

    def _draw_background(self):
        cam_x = self.camera.x
        for x, w, h in self.background["hills"]:
            sx = x - int(cam_x * 0.5)
            if sx + w < 0 or sx > SCREEN_WIDTH:
                continue
            base_y = GROUND_ROW * TILE
            pygame.draw.ellipse(self.screen, HILL_FAR, (sx, base_y - h, w, h * 2))
        for x, y, scale in self.background["clouds"]:
            sx = x - int(cam_x * 0.3)
            if sx < -80 or sx > SCREEN_WIDTH + 80:
                continue
            draw_cloud(self.screen, sx, y, scale)

    def _draw_world(self):
        cam_x = self.camera.x

        for p in self.platforms:
            r = p.move(-cam_x, 0)
            if r.right < 0 or r.left > SCREEN_WIDTH:
                continue
            pygame.draw.rect(self.screen, GROUND_COLOR, r)
            top_strip = pygame.Rect(r.x, r.y, r.width, 10)
            pygame.draw.rect(self.screen, GROUND_TOP_COLOR, top_strip)

        for coin in self.coins:
            coin.draw(self.screen, cam_x)

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        self.flag.draw(self.screen, cam_x)
        self.player.draw(self.screen, cam_x)

    def _draw_text_shadow(self, text, font, color, center):
        shadow = font.render(text, True, TEXT_SHADOW)
        shadow_rect = shadow.get_rect(center=(center[0] + 3, center[1] + 3))
        self.screen.blit(shadow, shadow_rect)
        main = font.render(text, True, color)
        main_rect = main.get_rect(center=center)
        self.screen.blit(main, main_rect)
        return main_rect

    def _draw_hud(self):
        pad = 14
        score_surf = self.font_small.render(f"SCORE  {self.score}", True, TEXT_WHITE)
        self.screen.blit(score_surf, (pad, pad))

        lives_surf = self.font_small.render(f"LIVES  {self.lives}", True, TEXT_WHITE)
        self.screen.blit(lives_surf, (pad, pad + 28))

        time_surf = self.font_small.render(f"TIME  {int(self.time_left)}", True, TEXT_WHITE)
        time_rect = time_surf.get_rect(topright=(SCREEN_WIDTH - pad, pad))
        self.screen.blit(time_surf, time_rect)

    def _draw_center_overlay(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        self._draw_text_shadow(title, self.font_big, TEXT_WHITE,
                                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self._draw_text_shadow(subtitle, self.font_small, TEXT_WHITE,
                                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

    def _draw_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        self._draw_text_shadow("PLATFORM HERO", self.font_big, TEXT_WHITE,
                                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self._draw_text_shadow("Press ENTER to start", self.font_med, TEXT_WHITE,
                                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._draw_text_shadow("Arrows/WASD to move, SPACE to jump, P to pause",
                                self.font_small, TEXT_WHITE,
                                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

    # ----------------------------------------------------------------- #
    # Event handling
    # ----------------------------------------------------------------- #
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.running = False
            elif e.key == pygame.K_RETURN and self.state == STATE_MENU:
                self.state = STATE_PLAYING
            elif e.key == pygame.K_p and self.state in (STATE_PLAYING, STATE_PAUSED):
                self.state = STATE_PAUSED if self.state == STATE_PLAYING else STATE_PLAYING
            elif e.key == pygame.K_r and self.state in (STATE_WIN, STATE_GAMEOVER):
                self._full_reset()
                self.state = STATE_PLAYING

    # ----------------------------------------------------------------- #
    # Main loop
    # ----------------------------------------------------------------- #
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # clamp to avoid huge steps if the window stalls

            for e in pygame.event.get():
                self.handle_event(e)

            keys = pygame.key.get_pressed()
            self.update(dt, keys)
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
