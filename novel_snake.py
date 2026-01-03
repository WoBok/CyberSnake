import json
import os
import random
import sys
import colorsys
import math
from array import array

import pygame

def resource_path(relative_path):
    """ 获取资源的绝对路径，适用于开发环境和 PyInstaller 打包环境 """
    try:
        # PyInstaller 创建一个临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


"""
新玩法贪吃蛇：赛博朋克版 + 技能系统

玩法说明：
1. 基本操作
   - 方向：↑ ↓ ← → 或 WASD
   - 空格：如果有能量，开启 / 关闭 幽灵模式（持续时间有限）
   - Tab：暂停并查看排行榜
   - ESC：退出游戏

2. 食物类型
   - 品红圆形：普通食物，每吃一个 +1 长度，+1 分，触发品红刷光特效
   - 黄色菱形：能量食物，增加一次"幽灵能量"（energy），触发黄色刷光特效

3. 幽灵模式（Ghost Mode）
   - 按空格消耗 1 点能量，进入幽灵模式 5 秒
   - 幽灵模式下可以穿过自己的身体、穿过荆棘障碍、穿墙传送
   - 是最强大的技能，可以无视一切障碍

4. 动态荆棘障碍
   - 每吃满 5 个普通食物，地图上随机生成一个新的荆棘障碍
   - 荆棘是永久的，非幽灵模式下碰到会死亡
   - 幽灵模式下可以穿过荆棘

5. 游戏结束
   - 非幽灵模式下：撞到边界、荆棘、或撞到自己，都会 Game Over
   - 幽灵模式下：无敌，可以穿过一切

6. 赛博朋克特效
   - 霓虹发光效果：蛇身、食物、障碍都有发光层
   - 粒子爆炸：吃到食物时触发粒子特效
   - 刷光效果：吃到食物时身体从头到尾闪过一道光

7. 依赖
   - pip install pygame
"""


# -------------------- 基本配置 --------------------
CELL_SIZE = 25
GRID_WIDTH = 25   # 网格宽度（5的倍数，确保每5格一组）
GRID_HEIGHT = 25  # 网格高度（5的倍数）
HUD_HEIGHT = 30   # 顶部 HUD 高度
BOTTOM_BAR_HEIGHT = 30 # 底部提示栏高度

SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT + HUD_HEIGHT + BOTTOM_BAR_HEIGHT # 屏幕高度 = HUD + 游戏区域 + 底部栏
GAME_AREA_Y = HUD_HEIGHT  # 游戏区域起始Y坐标

RENDER_FPS = 60             # 渲染帧率，保证输入跟手
STEP_INTERVAL_MS = 120       # 蛇移动间隔（毫秒），决定实际速度

# -------------------- 赛博朋克配色 --------------------
# 主色调：霓虹紫红、青蓝、亮黄
SNAKE_COLOR = (0, 255, 255)         # 青色霓虹
SNAKE_HEAD_COLOR = (255, 0, 255)    # 品红霓虹
SNAKE_GLOW = (0, 200, 255)          # 发光效果
FOOD_COLOR = (255, 0, 127)          # 品红食物
FOOD_GLOW = (255, 50, 150)          # 食物发光
ENERGY_FOOD_COLOR = (255, 255, 0)   # 黄色能量食物
ENERGY_GLOW = (255, 200, 0)         # 能量发光
BG_COLOR = (10, 5, 20)              # 深紫黑背景
GRID_COLOR = (50, 20, 80)           # 紫色网格
TEXT_COLOR = (0, 255, 255)          # 青色文字
TEXT_GLOW = (0, 200, 255)           # 文字发光
OBSTACLE_COLOR = (200, 0, 255)      # 紫红障碍
OBSTACLE_GLOW = (150, 0, 200)       # 障碍发光

GHOST_DURATION = 5_000  # 幽灵模式持续时间（毫秒）
FOOD_PER_OBSTACLE = 5   # 每吃多少普通食物生成一个障碍
LEADERBOARD_FILE = "snake_leaderboard.json"  # 排行榜文件
MAX_LEADERBOARD_ENTRIES = 10  # 排行榜最多保留多少条

# -------------------- 新系统配置 --------------------
# 道具颜色
MAGNET_COLOR = (255, 255, 0)      # 磁铁道具（黄色）
BOMB_COLOR = (0, 0, 0)             # 炸弹道具（黑色）
SCISSORS_COLOR = (0, 255, 0)       # 剪刀/减肥药（绿色）
ROTTEN_APPLE_COLOR = (128, 0, 128) # 腐烂苹果（紫色）

# 道具类型枚举
ITEM_MAGNET = "magnet"
ITEM_BOMB = "bomb"
ITEM_SCISSORS = "scissors"
ITEM_ROTTEN_APPLE = "rotten_apple"

MAGNET_DURATION_MIN_MS = 3_000
MAGNET_DURATION_MAX_MS = 5_000
MAGNET_PULL_RADIUS = 2
MAGNET_PULL_CHECK_INTERVAL_MS = 120

FOG_ZONE_SIZE = 3
FOG_ZONE_REFRESH_MIN_MS = 5_000
FOG_ZONE_REFRESH_MAX_MS = 8_000
FOG_ZONE_MAX_ON_MAP = 3
FOG_ZONE_ALPHA_PERIOD_MS = 1_200

# 传送门配置
PORTAL_PAIRS_MIN = 3
PORTAL_PAIRS_MAX = 5
PORTAL_REFRESH_MIN = 4_000  # 4秒
PORTAL_REFRESH_MAX = 10_000  # 10秒

# 地刺配置
SPIKE_COUNT_MIN = 3
SPIKE_COUNT_MAX = 5
SPIKE_TOGGLE_TIME = 500  # 0.5秒
SPIKE_REFRESH_MIN = 3_000  # 3秒
SPIKE_REFRESH_MAX = 5_000  # 5秒

# 迷雾模式配置
FOG_VISIBILITY_MIN = 3
FOG_VISIBILITY_MAX = 5
FOG_DURATION_MIN_MS = 3_000
FOG_DURATION_MAX_MS = 5_000

# 影子蛇配置
SHADOW_SNAKE_SPAWN_MIN = 10_000  # 10秒
SHADOW_SNAKE_SPAWN_MAX = 15_000  # 15秒

# 幽灵猎手配置
GHOST_HUNTER_COUNT_MAX = 3
GHOST_HUNTER_VISIBLE_MIN = 4_000  # 4秒
GHOST_HUNTER_VISIBLE_MAX = 7_000  # 7秒
GHOST_HUNTER_INVISIBLE_MIN = 4_000  # 4秒
GHOST_HUNTER_INVISIBLE_MAX = 8_000  # 8秒

# Boss战配置
BOSS_FOOD_THRESHOLD = 10  # 每10个食物出现Boss
BOSS_SHIELD_DURATION = 5_000  # 5秒护盾
BOSS_SIZE = 3  # Boss占据3x3格子
BOSS_BULLET_SPEED = 5  # Boss子弹速度

# 连击系统配置
COMBO_WINDOW = 2_000  # 2秒内连续吃到食物算连击

# 新系统配置
NORMAL_FOOD_TARGET = 3
ITEM_MAX_ON_MAP = 5
ITEM_SPAWN_MIN = 2_500
ITEM_SPAWN_MAX = 4_000
SHRINK_INTERVAL_MS = 120
PORTAL_TELEPORT_COOLDOWN_MS = 250
GHOST_HUNTER_MOVE_INTERVAL_MS = 260
DAMAGE_SHRINK_SEGMENTS = 5
SHOCKWAVE_CLEAR_SIZE = 10
SHOCKWAVE_DURATION_MS = 420
BOSS_KILL_SLOW_DURATION_MS = 2_000
BOSS_KILL_FLASH_DURATION_MS = 1_000
SCORE_DAMAGE_AMOUNT = 10
SCORE_ANIM_DURATION_MS = 420
SCORE_BURST_DURATION_MS = 520

DAMAGE_SLOW_DURATION_MS = 500
DAMAGE_SLOW_TIME_SCALE = 0.55
BOSS_KILL_TIME_SCALE = 0.12

DAMAGE_BLINK_INTERVAL_MS = 90
DAMAGE_BLINK_COUNT = 3
DAMAGE_BLINK_DURATION_MS = DAMAGE_BLINK_INTERVAL_MS * DAMAGE_BLINK_COUNT * 2

BOMB_VFX_DURATION_MS = 520

# -------------------- 粒子特效类 --------------------
class Particle:
    """单个粒子"""
    def __init__(self, x, y, color, vx, vy, life):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = random.randint(3, 8)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        # 添加重力和速度衰减
        self.vy += 0.2
        self.vx *= 0.98
    
    def is_alive(self):
        return self.life > 0
    
    def draw(self, surface):
        # 根据剩余生命调整透明度
        alpha = int(255 * (self.life / self.max_life))
        color_with_alpha = (*self.color, alpha)
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            # 绘制带发光效果的粒子
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color_with_alpha, (size, size), size)
            surface.blit(s, (int(self.x - size), int(self.y - size)))


class ParticleSystem:
    """粒子系统管理器"""
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, color, count=20):
        """在指定位置发射粒子"""
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(2, 8)
            vx = speed * random.uniform(-1, 1)
            vy = speed * random.uniform(-3, 0)  # 向上喷射
            life = random.randint(20, 40)
            self.particles.append(Particle(x, y, color, vx, vy, life))
    
    def update(self):
        """更新所有粒子"""
        self.particles = [p for p in self.particles if p.is_alive()]
        for p in self.particles:
            p.update()
    
    def draw(self, surface):
        """绘制所有粒子"""
        for p in self.particles:
            p.draw(surface)


# -------------------- 新系统类 --------------------
class Portal:
    """传送门"""
    def __init__(self, pos, color_id):
        self.pos = pos
        self.color_id = color_id  # 成对的传送门有相同的color_id
        self.color = self._get_color(color_id)
    
    def _get_color(self, color_id):
        """根据ID获取颜色"""
        colors = [
            (255, 0, 255),   # 品红
            (0, 255, 255),   # 青色
            (255, 255, 0),   # 黄色
            (0, 255, 0),     # 绿色
            (255, 128, 0),   # 橙色
        ]
        return colors[color_id % len(colors)]


class Spike:
    """地刺陷阱"""
    def __init__(self, pos):
        self.pos = pos
        self.visible = True
        self.last_toggle = pygame.time.get_ticks()
    
    def update(self):
        """更新地刺的显示状态"""
        now = pygame.time.get_ticks()
        if now - self.last_toggle >= SPIKE_TOGGLE_TIME:
            self.visible = not self.visible
            self.last_toggle = now


class ShadowSnake:
    """影子蛇AI"""
    def __init__(self, start_pos, length=4):
        self.snake = [start_pos]
        self.length = max(2, int(length))
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.last_move_time = pygame.time.get_ticks()
        self.move_interval = STEP_INTERVAL_MS
    
    def update(self, food_positions, obstacles, grid_width, grid_height, time_scale: float = 1.0):
        """更新影子蛇的位置（简单AI：朝最近的食物移动）"""
        now = pygame.time.get_ticks()
        ts = max(0.05, float(time_scale))
        effective_interval = self.move_interval / ts
        if now - self.last_move_time < effective_interval:
            return None
        
        self.last_move_time = now
        
        if not self.snake:
            return None
        
        head_x, head_y = self.snake[0]
        
        # 兼容：允许传入单个 (x, y)
        if food_positions and isinstance(food_positions, tuple):
            food_positions = [food_positions]

        target = None
        if food_positions:
            best_d = None
            for fx, fy in food_positions:
                d = abs(fx - head_x) + abs(fy - head_y)
                if best_d is None or d < best_d:
                    best_d = d
                    target = (fx, fy)

        # 简单AI：朝食物方向移动
        if target:
            fx, fy = target
            dx = 0
            dy = 0
            
            if fx > head_x:
                dx = 1
            elif fx < head_x:
                dx = -1
            elif fy > head_y:
                dy = 1
            elif fy < head_y:
                dy = -1
            
            # 如果无法朝食物方向移动，随机选择方向
            if dx == 0 and dy == 0:
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            
            # 避免反向移动
            if (dx, dy) == (-self.direction[0], -self.direction[1]):
                dx, dy = self.direction
            
            self.direction = (dx, dy)
        
        # 移动
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # 边界处理（穿墙）
        new_head = (new_head[0] % grid_width, new_head[1] % grid_height)
        
        ate_food = bool(target and new_head == target)

        self.snake.insert(0, new_head)
        if ate_food:
            self.length += 1

        while len(self.snake) > self.length:
            self.snake.pop()

        return new_head, ate_food


class GhostHunter:
    """幽灵猎手"""
    def __init__(self, pos):
        self.pos = pos
        self.visible = True
        self.last_toggle = pygame.time.get_ticks()
        self.visible_duration = random.randint(GHOST_HUNTER_VISIBLE_MIN, GHOST_HUNTER_VISIBLE_MAX)
        self.invisible_duration = random.randint(GHOST_HUNTER_INVISIBLE_MIN, GHOST_HUNTER_INVISIBLE_MAX)
    
    def update(self):
        """更新幽灵猎手的可见性"""
        now = pygame.time.get_ticks()
        elapsed = now - self.last_toggle
        appeared = False
        
        if self.visible:
            if elapsed >= self.visible_duration:
                self.visible = False
                self.last_toggle = now
                self.invisible_duration = random.randint(GHOST_HUNTER_INVISIBLE_MIN, GHOST_HUNTER_INVISIBLE_MAX)
        else:
            if elapsed >= self.invisible_duration:
                self.visible = True
                self.last_toggle = now
                self.visible_duration = random.randint(GHOST_HUNTER_VISIBLE_MIN, GHOST_HUNTER_VISIBLE_MAX)
                appeared = True

        return appeared
    
    def move_towards(self, target_pos, grid_width, grid_height):
        """向目标位置移动"""
        tx, ty = target_pos
        x, y = self.pos
        
        dx = 0
        dy = 0
        
        if tx > x:
            dx = 1
        elif tx < x:
            dx = -1
        
        if ty > y:
            dy = 1
        elif ty < y:
            dy = -1
        
        # 随机选择x或y方向移动（避免斜向移动）
        if dx != 0 and dy != 0:
            if random.random() < 0.5:
                dy = 0
            else:
                dx = 0
        
        new_pos = (x + dx, y + dy)
        # 允许穿墙
        new_pos = (new_pos[0] % grid_width, new_pos[1] % grid_height)
        self.pos = new_pos


class Boss:
    """Boss"""
    def __init__(self, pos):
        self.pos = pos  # 中心位置
        self.shield_active = True
        self.shield_start_time = pygame.time.get_ticks()
        self.bullets = []  # 子弹列表
        self.last_bullet_time = pygame.time.get_ticks()
        self.bullet_interval = 1_000  # 每秒发射一颗子弹
        self.last_update_time = pygame.time.get_ticks()
    
    def update(self, grid_width, grid_height, time_scale: float = 1.0):
        """更新Boss状态"""
        now = pygame.time.get_ticks()
        dt_ms = max(0, now - self.last_update_time)
        self.last_update_time = now
        ts = max(0.05, float(time_scale))
        
        # 检查护盾是否消失
        if self.shield_active:
            if now - self.shield_start_time >= BOSS_SHIELD_DURATION:
                self.shield_active = False
        
        # 发射子弹
        if now - self.last_bullet_time >= self.bullet_interval:
            self.shoot_bullet(grid_width, grid_height)
            self.last_bullet_time = now
        
        # 更新子弹
        for bullet in self.bullets[:]:
            step = (dt_ms / 1000.0) * ts
            bullet['x'] += bullet['dx'] * BOSS_BULLET_SPEED * step
            bullet['y'] += bullet['dy'] * BOSS_BULLET_SPEED * step
            
            # 移除超出边界的子弹
            if not (0 <= bullet['x'] < grid_width and 0 <= bullet['y'] < grid_height):
                self.bullets.remove(bullet)
    
    def shoot_bullet(self, grid_width, grid_height):
        """发射子弹（8个方向）"""
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]
        for dx, dy in directions:
            self.bullets.append({
                'x': self.pos[0],
                'y': self.pos[1],
                'dx': dx,
                'dy': dy
            })
    
    def get_cells(self):
        """获取Boss占据的所有格子"""
        cells = []
        for dx in range(-BOSS_SIZE//2, BOSS_SIZE//2 + 1):
            for dy in range(-BOSS_SIZE//2, BOSS_SIZE//2 + 1):
                cells.append((self.pos[0] + dx, self.pos[1] + dy))
        return cells


class SnakeGame:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("技能贪吃蛇 - 幽灵模式 + 动态障碍")

        # 设置窗口图标
        try:
            icon_path = resource_path("snake_icon.png")
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"加载图标失败: {e}")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        # 使用支持中文的字体列表，前面优先中文，后面兜底英文
        font_candidates = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "consolas"]
        self.font_small = pygame.font.SysFont(font_candidates, 18)
        self.font_medium = pygame.font.SysFont(font_candidates, 24, bold=True)  # 中等字体，用于最高分
        self.font_big = pygame.font.SysFont(font_candidates, 36, bold=True)
        self.font_xlarge = pygame.font.SysFont(font_candidates, 48, bold=True)  # 特大字体，用于标题

        # 渲染帧率（固定）
        self.fps = RENDER_FPS

        # 排行榜相关
        self.leaderboard = self.load_leaderboard()
        self.show_leaderboard = False  # 是否显示排行榜界面
        self.entering_name = False     # 是否正在输入名字
        self.player_name_input = ""    # 输入的名字
        self.paused = False            # 游戏是否暂停
        self.show_help = False
        self.help_page = 0
        self.help_paused_game = False

        # 粒子系统
        self.particle_system = ParticleSystem()

        self.audio_enabled = False
        self.sfx = {}
        self.init_audio()

        self.reset(start_with_intro=True)

    def init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.audio_enabled = True
        except Exception:
            self.audio_enabled = False
            return

        try:
            music_path = resource_path(os.path.join("audio", "pixel_fury.wav"))
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.13)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

        def make_tone(freq_hz: float, duration_ms: int, volume: float = 0.35, wave: str = "sine"):
            sr = 44100
            n = max(1, int(sr * (duration_ms / 1000.0)))
            amp = int(32767 * max(0.0, min(1.0, volume)))
            buf = array('h')
            two_pi = 2.0 * math.pi
            for i in range(n):
                t = i / sr
                ph = (t * freq_hz) % 1.0
                if wave == "square":
                    v = 1.0 if math.sin(two_pi * freq_hz * t) >= 0 else -1.0
                elif wave == "triangle":
                    v = 2.0 * abs(2.0 * ph - 1.0) - 1.0
                else:
                    v = math.sin(two_pi * freq_hz * t)
                buf.append(int(amp * v))
            return pygame.mixer.Sound(buffer=buf.tobytes())

        fallback = {
            "collect_food_01": make_tone(880, 70, volume=0.28, wave="square"),
            "collect_food_02": make_tone(1040, 70, volume=0.28, wave="square"),
            "collect_food_03": make_tone(1240, 70, volume=0.28, wave="square"),
            "collect_energy_01": make_tone(1320, 90, volume=0.30, wave="sine"),
            "energy_shackwave": make_tone(180, 160, volume=0.40, wave="square"),
            "food_stolen": make_tone(520, 120, volume=0.28, wave="triangle"),
            "energy_stolen": make_tone(420, 140, volume=0.28, wave="triangle"),
            "ghost_appear_02": make_tone(360, 180, volume=0.30, wave="sine"),
            "portal_02": make_tone(760, 150, volume=0.32, wave="triangle"),
            "poisoned_01": make_tone(320, 160, volume=0.35, wave="triangle"),
            "crack_01": make_tone(220, 80, volume=0.35, wave="square"),
            "crack_02": make_tone(180, 120, volume=1, wave="square"),
            "boss_appear_01": make_tone(240, 240, volume=0.45, wave="square"),
            "defeat_boss_03": make_tone(240, 240, volume=0.45, wave="square"),
            "bomb_01": make_tone(180, 160, volume=0.40, wave="square"),
            "fog_01": make_tone(260, 180, volume=0.30, wave="sine"),
            "magnet_01": make_tone(660, 120, volume=0.32, wave="triangle"),
            "destroy_enemy_01": make_tone(520, 140, volume=0.35, wave="square"),
            "item_scissors": make_tone(980, 120, volume=0.30, wave="square"),
        }

        def load_wav(filename: str):
            try:
                p = resource_path(os.path.join("audio", filename))
                s = pygame.mixer.Sound(p)
                return s
            except Exception:
                return None

        mapping = {
            "collect_food_01": "collect_food_01.wav",
            "collect_food_02": "collect_food_02.wav",
            "collect_food_03": "collect_food_03.wav",
            "collect_energy_01": "collect_energy_01.wav",
            "energy_shackwave": "energy_shackwave_01.wav",
            "food_stolen": "food_stolen_01.wav",
            "energy_stolen": "energy_stolen_01.wav",
            "ghost_appear_02": "ghost_appear_02.wav",
            "portal_02": "portal_02.wav",
            "poisoned_01": "poisoned_01.wav",
            "crack_01": "crack_01.wav",
            "crack_02": "crack_02.wav",
            "boss_appear_01": "boss_appear_01.wav",
            "defeat_boss_02": "defeat_boss_02.wav",
            "defeat_boss_03": "defeat_boss_03.wav",
            "bomb_01": "bomb_01.wav",
            "fog_01": "fog_01.wav",
            "magnet_01": "magnet_01.wav",
            "destroy_enemy_01": "destroy_enemy_01.wav",
        }

        self.sfx = {}
        self.sfx_base_volume = {}
        for key, fallback_sound in fallback.items():
            wav_name = mapping.get(key)
            s = load_wav(wav_name) if wav_name else None
            if s is None:
                s = fallback_sound
            try:
                s.set_volume(1.0)
            except Exception:
                pass
            self.sfx[key] = s
            self.sfx_base_volume[key] = 0.55

    def play_sfx(self, name: str, volume: float = None):
        if not self.audio_enabled:
            return
        s = self.sfx.get(name)
        if not s:
            return
        try:
            ch = s.play()
            if ch is not None:
                base_v = self.sfx_base_volume.get(name, 1.0)
                v = base_v if volume is None else float(volume)
                try:
                    ch.set_volume(v)
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------- 游戏状态初始化 --------------------
    def reset(self, start_with_intro: bool = False):
        # start_with_intro=True 表示回到启动界面，仅首次进入使用；
        # 复盘（按 R）时使用 start_with_intro=False，直接开新局。
        self.started = not start_with_intro
        self.last_move_time = pygame.time.get_ticks()
        self.step_interval_ms = STEP_INTERVAL_MS
        center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.snake = [
            center,
            (center[0] - 1, center[1]),
            (center[0] - 2, center[1]),
        ]
        self.direction = (1, 0)  # 初始向右
        self.next_direction = self.direction

        self.score = 0
        self.normal_food_eaten = 0
        self.boss_food_eaten = 0
        self.boss_spawn_progress = 0

        self.last_food_eat_time = 0
        self.combo_streak = 0
        self.combo_multiplier = 1
        self.combo_display_until = 0

        self.grow_pending = 0

        self.items = []
        self.next_item_spawn_time = 0

        self.reverse_controls_until = 0
        self.rainbow_until = 0

        self.shrink_remaining = 0
        self.last_shrink_time = pygame.time.get_ticks()

        self.magnet_flights = []
        self.magnet_active_until = 0
        self.magnet_anim_start = 0
        self.next_magnet_pull_time = 0

        self.has_spawned_rotten_apple = False
        self.has_spawned_bomb = False

        self.fog_zones = []
        self.next_fog_zone_refresh_time = 0

        self.fog_active_until = 0
        self.fog_radius = FOG_VISIBILITY_MAX

        self.portals = []
        self.portal_pairs = {}
        self.portal_lookup = {}
        self.next_portal_refresh_time = 0
        self.portal_cooldown_until = 0
        self.portal_cooldown_color_id = None

        self.spikes = []
        self.next_spike_refresh_time = 0

        self.shadow_snakes = []
        self.next_shadow_spawn_time = 0

        self.ghost_hunters = []
        self.next_ghost_spawn_time = 0
        self.last_ghost_hunter_move_time = 0

        self.boss = None

        self.obstacles = set()

        self.normal_foods = []
        self.energy_foods = []

        self.normal_food_meta = {}
        self.energy_food_meta = {}

        self.energy = 1  # 初始给一点能量试试新玩法
        self.ghost_mode = False
        self.ghost_end_time = 0

        # 刷光效果
        self.glow_effect_active = False
        self.glow_effect_start = 0
        self.glow_effect_color = None
        self.glow_effect_duration = 500  # 刷光持续时间（毫秒）

        self.shockwave_active = False
        self.shockwave_start_time = 0
        self.shockwave_color = (200, 255, 255)
        self.shockwave_center = None

        self.boss_kill_slow_until = 0
        self.boss_kill_slow_start = 0
        self.boss_kill_flash_until = 0
        self.boss_kill_flash_start = 0

        self.damage_slow_until = 0

        self.damage_blink_start = 0
        self.damage_blink_until = 0

        self.bomb_explosions = []

        self.score_anim_start = 0
        self.score_anim_end = 0
        self.score_anim_from = 0
        self.score_anim_to = 0
        self.score_burst_until = 0
        self.score_burst_start = 0

        self.spawn_food()

        self.spawn_portals()
        self.spawn_spikes()

        self.spawn_fog_zone(force=True)

        now = pygame.time.get_ticks()
        self.next_portal_refresh_time = now + random.randint(PORTAL_REFRESH_MIN, PORTAL_REFRESH_MAX)
        self.next_spike_refresh_time = now + random.randint(SPIKE_REFRESH_MIN, SPIKE_REFRESH_MAX)
        self.next_shadow_spawn_time = now + random.randint(SHADOW_SNAKE_SPAWN_MIN, SHADOW_SNAKE_SPAWN_MAX)
        self.next_ghost_spawn_time = now + random.randint(GHOST_HUNTER_INVISIBLE_MIN, GHOST_HUNTER_INVISIBLE_MAX)
        self.next_fog_zone_refresh_time = now + random.randint(FOG_ZONE_REFRESH_MIN_MS, FOG_ZONE_REFRESH_MAX_MS)

        now = pygame.time.get_ticks()
        self.next_item_spawn_time = now + random.randint(ITEM_SPAWN_MIN, ITEM_SPAWN_MAX)

        self.game_over = False
        self.game_over_reason = ""
        self.paused = False
        self.show_leaderboard = False
        self.show_help = False
        self.help_page = 0
        self.help_paused_game = False

        now = pygame.time.get_ticks()
        self.run_start_time = now if self.started else 0
        self.run_end_time = None
        self.paused_time_accum = 0
        self.pause_started_at = None

        self.clear_start_path()

    # -------------------- 排行榜相关 --------------------
    def load_leaderboard(self):
        """从文件加载排行榜，格式：[{"name": "玩家名", "score": 分数}, ...]"""
        if not os.path.exists(LEADERBOARD_FILE):
            return []
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_leaderboard(self):
        """保存排行榜到文件"""
        try:
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(self.leaderboard, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存排行榜失败: {e}")

    def is_high_score(self, score):
        """判断分数是否能进入排行榜"""
        if len(self.leaderboard) < MAX_LEADERBOARD_ENTRIES:
            return True
        return score > self.leaderboard[-1]["score"]

    def add_to_leaderboard(self, name, score):
        """添加记录到排行榜并排序"""
        self.leaderboard.append({"name": name, "score": score})
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
        self.leaderboard = self.leaderboard[:MAX_LEADERBOARD_ENTRIES]
        self.save_leaderboard()

    # -------------------- 工具函数 --------------------
    def random_empty_cell(self):
        """从空白位置里随机挑一个网格坐标"""
        occupied = set(self.snake) | self.obstacles
        if getattr(self, "fog_zones", None):
            occupied |= set(self.get_fog_zone_cells_all())
        for pos in self.normal_foods:
            occupied.add(pos)
        for pos in self.energy_foods:
            occupied.add(pos)
        for it in self.items:
            occupied.add(it["pos"])
        for p in self.portals:
            occupied.add(p.pos)
        for s in self.spikes:
            occupied.add(s.pos)
        for ss in self.shadow_snakes:
            for seg in ss.snake:
                occupied.add(seg)
        for gh in self.ghost_hunters:
            occupied.add(gh.pos)
        if self.boss:
            for cell in self.boss.get_cells():
                occupied.add(cell)

        all_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in occupied
        ]
        if not all_cells:
            return None
        return random.choice(all_cells)

    def get_fog_zone_cells(self, center):
        cx, cy = center
        half = FOG_ZONE_SIZE // 2
        return {(cx + dx, cy + dy) for dx in range(-half, half + 1) for dy in range(-half, half + 1)}

    def get_fog_zone_cells_all(self):
        cells = set()
        for z in self.fog_zones:
            cells |= self.get_fog_zone_cells(z["center"])
        return cells

    def random_empty_cell_avoid_head(self, avoid_radius: int):
        if avoid_radius <= 0:
            return self.random_empty_cell()
        hx, hy = self.snake[0]
        occupied = set(self.snake) | self.obstacles
        if getattr(self, "fog_zones", None):
            occupied |= set(self.get_fog_zone_cells_all())
        for pos in self.normal_foods:
            occupied.add(pos)
        for pos in self.energy_foods:
            occupied.add(pos)
        for it in self.items:
            occupied.add(it["pos"])
        for p in self.portals:
            occupied.add(p.pos)
        for s in self.spikes:
            occupied.add(s.pos)
        for ss in self.shadow_snakes:
            for seg in ss.snake:
                occupied.add(seg)
        for gh in self.ghost_hunters:
            occupied.add(gh.pos)
        if self.boss:
            for cell in self.boss.get_cells():
                occupied.add(cell)

        all_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in occupied and (abs(x - hx) > avoid_radius or abs(y - hy) > avoid_radius)
        ]
        if not all_cells:
            return None
        return random.choice(all_cells)

    def spawn_food(self):
        """生成普通食物和（有概率）能量食物"""
        while len(self.normal_foods) < NORMAL_FOOD_TARGET:
            cell = self.random_empty_cell()
            if cell is None:
                break
            if cell in self.normal_food_meta:
                del self.normal_food_meta[cell]
            self.normal_foods.append(cell)

        # 30% 概率生成能量食物（如果当前没有）
        if not self.energy_foods and random.random() < 0.3:
            cell = self.random_empty_cell()
            if cell is not None:
                if cell in self.energy_food_meta:
                    del self.energy_food_meta[cell]
                self.energy_foods.append(cell)

    def spawn_item(self):
        if len(self.items) >= ITEM_MAX_ON_MAP:
            return
        cell = self.random_empty_cell_avoid_head(2)
        if cell is None:
            return
        if not self.has_spawned_bomb:
            item_type = ITEM_BOMB
            self.has_spawned_bomb = True
        elif not self.has_spawned_rotten_apple:
            item_type = ITEM_ROTTEN_APPLE
            self.has_spawned_rotten_apple = True
        else:
            scissors_count = sum(1 for it in self.items if it.get("type") == ITEM_SCISSORS)
            pool = [ITEM_MAGNET, ITEM_BOMB, ITEM_ROTTEN_APPLE]
            weights = [3, 10, 4]
            if scissors_count < 3:
                pool.insert(2, ITEM_SCISSORS)
                weights.insert(2, 4)
            item_type = random.choices(pool, weights=weights, k=1)[0]
            if item_type == ITEM_ROTTEN_APPLE:
                self.has_spawned_rotten_apple = True
            if item_type == ITEM_BOMB:
                self.has_spawned_bomb = True
        self.items.append({"type": item_type, "pos": cell})

    def on_normal_food_eaten(self, pos, counts_for_boss: bool = True, color_override=None):
        now = pygame.time.get_ticks()
        if now - self.last_food_eat_time <= COMBO_WINDOW:
            self.combo_streak = min(3, self.combo_streak + 1)
        else:
            self.combo_streak = 0
        self.combo_multiplier = 2 ** self.combo_streak
        self.last_food_eat_time = now
        if self.combo_multiplier > 1:
            self.combo_display_until = now + 1_200

        self.score += self.combo_multiplier
        self.normal_food_eaten += 1

        if counts_for_boss:
            self.boss_food_eaten += 1
            if self.boss is None:
                self.boss_spawn_progress += 1

        eat_color = color_override if color_override is not None else FOOD_COLOR

        food_screen_x = pos[0] * CELL_SIZE + CELL_SIZE // 2
        food_screen_y = GAME_AREA_Y + pos[1] * CELL_SIZE + CELL_SIZE // 2
        self.particle_system.emit(food_screen_x, food_screen_y, eat_color, count=25)
        self.trigger_glow_effect(eat_color)
        if self.combo_streak <= 0:
            self.play_sfx("collect_food_01")
        elif self.combo_streak == 1:
            self.play_sfx("collect_food_02")
        else:
            self.play_sfx("collect_food_03")

        if self.normal_food_eaten % FOOD_PER_OBSTACLE == 0:
            self.spawn_obstacle()

        if self.boss is None and self.boss_spawn_progress >= BOSS_FOOD_THRESHOLD:
            self.boss_spawn_progress = 0
            self.spawn_boss()

    def spawn_portals(self):
        self.portals = []
        self.portal_pairs = {}
        self.portal_lookup = {}

        pair_count = random.randint(PORTAL_PAIRS_MIN, PORTAL_PAIRS_MAX)
        for color_id in range(pair_count):
            p1 = self.random_empty_cell_avoid_head(2)
            p2 = self.random_empty_cell_avoid_head(2)
            if p1 is None or p2 is None:
                continue
            portal1 = Portal(p1, color_id)
            portal2 = Portal(p2, color_id)
            self.portals.extend([portal1, portal2])
            self.portal_pairs[color_id] = (p1, p2)
            self.portal_lookup[p1] = color_id
            self.portal_lookup[p2] = color_id

    def refresh_one_portal_pair(self):
        if not self.portal_pairs:
            return
        color_id = random.choice(list(self.portal_pairs.keys()))
        p1 = self.random_empty_cell_avoid_head(2)
        p2 = self.random_empty_cell_avoid_head(2)
        if p1 is None or p2 is None:
            return

        old_p1, old_p2 = self.portal_pairs[color_id]
        if old_p1 in self.portal_lookup:
            del self.portal_lookup[old_p1]
        if old_p2 in self.portal_lookup:
            del self.portal_lookup[old_p2]

        self.portal_pairs[color_id] = (p1, p2)
        self.portal_lookup[p1] = color_id
        self.portal_lookup[p2] = color_id

        self.portals = []
        for cid, (a, b) in self.portal_pairs.items():
            self.portals.append(Portal(a, cid))
            self.portals.append(Portal(b, cid))

    def draw_portals(self):
        now = pygame.time.get_ticks()
        pulse = abs((now % 1000) / 500 - 1)
        slow_pulse = 0.5 + 0.5 * math.sin(now / 650.0)
        for p in self.portals:
            x, y = p.pos
            cx = x * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            base = p.color

            # vertical ellipse portal body
            w = int(CELL_SIZE * 0.66)
            h = int(CELL_SIZE * 1.00)
            outer_rect = pygame.Rect(0, 0, w, h)
            outer_rect.center = (cx, cy)

            # glow halo
            halo_pad = 18
            halo = pygame.Surface((w + halo_pad * 2, h + halo_pad * 2), pygame.SRCALPHA)
            hr = halo.get_rect()
            glow_outer = int(max(w, h) * (0.62 + 0.10 * slow_pulse))
            glow_inner = int(max(w, h) * 0.42)
            steps = 8
            for i in range(steps, 0, -1):
                # keep a baseline so halo never fully disappears
                a = int((28 + 55 * slow_pulse) * (i / steps))
                expand = int((glow_outer - glow_inner) * (1.0 - i / steps))
                rr = hr.inflate(-expand, -expand)
                pygame.draw.ellipse(halo, (*base, a), rr, width=3)
            self.screen.blit(halo, (outer_rect.centerx - hr.width // 2, outer_rect.centery - hr.height // 2))

            # portal rim
            pygame.draw.ellipse(self.screen, base, outer_rect, width=2)

            # inner void gradient-ish
            inner = outer_rect.inflate(-10, -12)
            pygame.draw.ellipse(self.screen, (10, 5, 20), inner)
            pygame.draw.ellipse(self.screen, (40, 10, 70), inner, width=2)

            # subtle highlight
            highlight = pygame.Surface((w, h), pygame.SRCALPHA)
            hl_rect = highlight.get_rect()
            a = int(24 + 38 * (1.0 - pulse))
            pygame.draw.ellipse(highlight, (255, 255, 255, a), hl_rect.inflate(-12, -18), width=2)
            self.screen.blit(highlight, outer_rect.topleft)

    def spawn_spikes(self):
        self.spikes = []
        count = random.randint(SPIKE_COUNT_MIN, SPIKE_COUNT_MAX)
        for _ in range(count):
            cell = None
            for _try in range(60):
                c = self.random_empty_cell_avoid_head(2)
                if c is None:
                    break
                cell = c
                break
            if cell is None:
                break
            self.spikes.append(Spike(cell))

    def refresh_one_spike(self):
        if not self.spikes:
            return
        spike = random.choice(self.spikes)
        cell = None
        for _try in range(60):
            c = self.random_empty_cell_avoid_head(2)
            if c is None:
                break
            cell = c
            break
        if cell is None:
            return
        spike.pos = cell
        spike.visible = True
        spike.last_toggle = pygame.time.get_ticks()

    def draw_spikes(self):
        for s in self.spikes:
            if not s.visible:
                continue
            x, y = s.pos
            cx = x * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            color = (180, 180, 180)
            for r in range(14, 6, -2):
                a = int(55 * (1 - (14 - r) / 14))
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, a), (r, r), r)
                self.screen.blit(surf, (cx - r, cy - r))
            half_w = max(4, CELL_SIZE // 6)
            pts = [
                (cx, cy - CELL_SIZE // 2 + 4),
                (cx - half_w, cy + CELL_SIZE // 4),
                (cx + half_w, cy + CELL_SIZE // 4),
            ]
            pygame.draw.polygon(self.screen, (230, 230, 230), pts)

    def draw_fog(self):
        now = pygame.time.get_ticks()
        if now >= self.fog_active_until:
            return
        radius = self.fog_radius
        hx, hy = self.snake[0]
        vis_rect = pygame.Rect(
            (hx - radius) * CELL_SIZE,
            (hy - radius) * CELL_SIZE,
            (radius * 2 + 1) * CELL_SIZE,
            (radius * 2 + 1) * CELL_SIZE,
        )

        fog = pygame.Surface((SCREEN_WIDTH, CELL_SIZE * GRID_HEIGHT), pygame.SRCALPHA)
        fog.fill((0, 0, 0, 235))
        pygame.draw.rect(fog, (0, 0, 0, 0), vis_rect)
        self.screen.blit(fog, (0, GAME_AREA_Y))

    def spawn_fog_zone(self, force: bool = False):
        if not force and len(self.fog_zones) >= FOG_ZONE_MAX_ON_MAP:
            return
        occupied = set(self.snake) | self.obstacles | set(self.normal_foods) | set(self.energy_foods)
        for it in self.items:
            occupied.add(it["pos"])
        for p in self.portals:
            occupied.add(p.pos)
        for s in self.spikes:
            occupied.add(s.pos)
        for ss in self.shadow_snakes:
            for seg in ss.snake:
                occupied.add(seg)
        for gh in self.ghost_hunters:
            occupied.add(gh.pos)
        if self.boss:
            for cell in self.boss.get_cells():
                occupied.add(cell)

        half = FOG_ZONE_SIZE // 2
        for _try in range(120):
            cx = random.randint(half, GRID_WIDTH - 1 - half)
            cy = random.randint(half, GRID_HEIGHT - 1 - half)
            cells = self.get_fog_zone_cells((cx, cy))
            hx, hy = self.snake[0]
            if any(abs(x - hx) <= 2 and abs(y - hy) <= 2 for x, y in cells):
                continue
            if any(c in occupied for c in cells):
                continue
            if any(c in self.get_fog_zone_cells_all() for c in cells):
                continue

            self.fog_zones.append({"center": (cx, cy), "spawn": pygame.time.get_ticks()})
            if len(self.fog_zones) > FOG_ZONE_MAX_ON_MAP:
                self.fog_zones = self.fog_zones[-FOG_ZONE_MAX_ON_MAP:]
            return

    def draw_fog_zone(self):
        if not self.fog_zones:
            return
        now = pygame.time.get_ticks()

        for z in self.fog_zones:
            t = (now - z["spawn"]) % FOG_ZONE_ALPHA_PERIOD_MS
            p = t / FOG_ZONE_ALPHA_PERIOD_MS
            wave = 0.5 - 0.5 * math.cos(2.0 * math.pi * p)
            spawn_fade = min(1.0, max(0.0, (now - z["spawn"]) / 350.0))
            a = int((60 + 160 * wave) * spawn_fade)
            cx, cy = z["center"]
            half = FOG_ZONE_SIZE // 2
            for x in range(cx - half, cx + half + 1):
                for y in range(cy - half, cy + half + 1):
                    if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                        continue
                    rect = pygame.Rect(x * CELL_SIZE + 3, GAME_AREA_Y + y * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
                    surf = pygame.Surface((CELL_SIZE - 6, CELL_SIZE - 6), pygame.SRCALPHA)
                    pygame.draw.rect(surf, (40, 0, 60, a), surf.get_rect(), border_radius=6)
                    pygame.draw.rect(surf, (180, 0, 255, min(255, a + 55)), surf.get_rect(), 2, border_radius=6)
                    seed = ((x << 16) ^ (y << 4) ^ (now // 90)) & 0xFFFFFFFF
                    rr = random.Random(seed)
                    for _ in range(3):
                        px = rr.randint(2, surf.get_width() - 3)
                        py = rr.randint(2, surf.get_height() - 3)
                        pr = rr.randint(2, 6)
                        pa = max(0, min(255, int(a * rr.uniform(0.22, 0.55))))
                        pygame.draw.circle(surf, (120, 0, 180, pa), (px, py), pr)
                    for _ in range(2):
                        x1 = rr.randint(0, surf.get_width())
                        y1 = rr.randint(0, surf.get_height())
                        x2 = rr.randint(0, surf.get_width())
                        y2 = rr.randint(0, surf.get_height())
                        la = max(0, min(255, int(a * rr.uniform(0.10, 0.25))))
                        pygame.draw.line(surf, (200, 80, 255, la), (x1, y1), (x2, y2), 1)
                    self.screen.blit(surf, rect.topleft)

    def clear_start_path(self):
        hx, hy = self.snake[0]
        dx, dy = self.direction
        cells = []
        for i in range(1, 6):
            x = hx + dx * i
            y = hy + dy * i
            if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                break
            cells.append((x, y))

        if not cells:
            return

        for c in cells:
            if c in self.obstacles:
                self.obstacles.remove(c)
            if c in self.normal_foods:
                self.normal_foods.remove(c)
                if c in self.normal_food_meta:
                    del self.normal_food_meta[c]
            if c in self.energy_foods:
                self.energy_foods.remove(c)
                if c in self.energy_food_meta:
                    del self.energy_food_meta[c]

        for sp in self.spikes:
            if sp.pos in cells:
                new_pos = None
                for _try in range(60):
                    c = self.random_empty_cell()
                    if c is None:
                        break
                    if c in cells:
                        continue
                    new_pos = c
                    break
                if new_pos is not None:
                    sp.pos = new_pos
                    sp.visible = True
                    sp.last_toggle = pygame.time.get_ticks()

        if self.fog_zones:
            remaining = []
            for z in self.fog_zones:
                if set(cells).intersection(self.get_fog_zone_cells(z["center"])):
                    continue
                remaining.append(z)
            self.fog_zones = remaining

        self.spawn_food()

    def spawn_shadow_snake(self):
        start = self.random_empty_cell_avoid_head(2)
        if start is None:
            return
        length = random.randint(4, 7)
        self.shadow_snakes.append(ShadowSnake(start, length=length))

    def shadow_snake_die(self, ss):
        self.play_sfx("destroy_enemy_01")
        body = list(ss.snake)
        count = max(3, len(body))
        center = body[0]
        for _ in range(count):
            for _try in range(15):
                dx = random.randint(-2, 2)
                dy = random.randint(-2, 2)
                x = max(0, min(GRID_WIDTH - 1, center[0] + dx))
                y = max(0, min(GRID_HEIGHT - 1, center[1] + dy))
                p = (x, y)
                if p in self.normal_foods or p in self.energy_foods:
                    continue
                if p in self.obstacles:
                    continue
                if p in self.snake:
                    continue
                self.normal_foods.append(p)
                self.normal_food_meta[p] = {"counts_for_boss": False, "color": (180, 180, 255)}
                break

        for seg in body:
            sx = seg[0] * CELL_SIZE + CELL_SIZE // 2
            sy = GAME_AREA_Y + seg[1] * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.emit(sx, sy, (180, 180, 255), count=10)

    def update_shadow_snakes(self, time_scale: float = 1.0):
        if not self.shadow_snakes:
            return
        food_targets = list(self.normal_foods) + list(self.energy_foods)
        for ss in self.shadow_snakes[:]:
            old_head = ss.snake[0]
            res = ss.update(food_targets, self.obstacles, GRID_WIDTH, GRID_HEIGHT, time_scale=time_scale)
            if not res:
                continue
            new_head, ate = res

            # 抢食物
            if new_head in self.normal_foods:
                self.play_sfx("food_stolen")
                self.normal_foods.remove(new_head)
                if new_head in self.normal_food_meta:
                    del self.normal_food_meta[new_head]
                self.spawn_food()
            if new_head in self.energy_foods:
                self.play_sfx("energy_stolen")
                self.energy_foods.remove(new_head)
                if new_head in self.energy_food_meta:
                    del self.energy_food_meta[new_head]
                self.spawn_food()

            # 它的头撞到你：它死
            if new_head in self.snake:
                self.shadow_snakes.remove(ss)
                self.shadow_snake_die(ss)
                continue

            # 影子蛇不会因撞到障碍死亡；穿墙已处理

    def draw_shadow_snakes(self):
        for ss in self.shadow_snakes:
            for i, (x, y) in enumerate(ss.snake):
                cx = x * CELL_SIZE + CELL_SIZE // 2
                cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
                col = (120, 120, 180) if i > 0 else (180, 180, 255)
                r = CELL_SIZE // 2 - 3 if i == 0 else int(CELL_SIZE * 0.35)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, 120), (r, r), r)
                self.screen.blit(s, (cx - r, cy - r))
                pygame.draw.circle(self.screen, col, (cx, cy), max(2, r - 2))

    def spawn_ghost_hunter(self):
        if len(self.ghost_hunters) >= GHOST_HUNTER_COUNT_MAX:
            return
        cell = self.random_empty_cell_avoid_head(2)
        if cell is None:
            return
        self.ghost_hunters.append(GhostHunter(cell))

    def update_ghost_hunters(self, time_scale: float = 1.0):
        now = pygame.time.get_ticks()
        for gh in self.ghost_hunters:
            appeared = gh.update()
            if appeared:
                self.play_sfx("ghost_appear_02")

        ts = max(0.05, float(time_scale))
        effective_interval = GHOST_HUNTER_MOVE_INTERVAL_MS / ts
        if now - self.last_ghost_hunter_move_time >= effective_interval:
            self.last_ghost_hunter_move_time = now
            target = self.snake[0]
            for gh in self.ghost_hunters:
                gh.move_towards(target, GRID_WIDTH, GRID_HEIGHT)

    def draw_ghost_hunters(self):
        for gh in self.ghost_hunters:
            x, y = gh.pos
            cx = x * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            base = (255, 0, 0)
            alpha = 150 if gh.visible else 45
            r = CELL_SIZE // 2 - 4
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*base, alpha), (r, r), r)
            # inner glow
            pygame.draw.circle(surf, (255, 120, 120, max(0, alpha - 40)), (r, r), max(2, r - 5))
            self.screen.blit(surf, (cx - r, cy - r))
            if gh.visible:
                pygame.draw.circle(self.screen, (255, 80, 80), (cx - 4, cy - 4), 3)
                pygame.draw.circle(self.screen, (255, 80, 80), (cx + 4, cy - 4), 3)
                # wispy tail
                tail = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
                tr = tail.get_rect()
                for i in range(6):
                    a = int(55 * (1 - i / 6))
                    pygame.draw.circle(tail, (255, 80, 80, a), (tr.centerx, tr.centery + 6 + i * 2), max(1, r - 3 - i * 2))
                self.screen.blit(tail, (cx - tr.centerx, cy - tr.centery + 10))

    def draw_shockwave(self):
        if not self.shockwave_active or not self.shockwave_center:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.shockwave_start_time
        if elapsed >= SHOCKWAVE_DURATION_MS:
            self.shockwave_active = False
            return
        p = max(0.0, min(1.0, elapsed / max(1, SHOCKWAVE_DURATION_MS)))

        cx, cy = self.shockwave_center
        sx = cx * CELL_SIZE + CELL_SIZE // 2
        sy = GAME_AREA_Y + cy * CELL_SIZE + CELL_SIZE // 2
        max_r = int(max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.85)
        r = int(18 + (max_r - 18) * (p ** 0.85))

        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        base = self.shockwave_color
        a0 = int(160 * (1.0 - p))
        for w in (10, 6, 3):
            a = max(0, int(a0 * (w / 10)))
            pygame.draw.circle(surf, (*base, a), (sx, sy), r, width=w)
        self.screen.blit(surf, (0, 0))

    def draw_boss_kill_flash(self):
        now = pygame.time.get_ticks()
        if now >= self.boss_kill_flash_until:
            return
        elapsed = now - self.boss_kill_flash_start
        p = max(0.0, min(1.0, elapsed / max(1, BOSS_KILL_FLASH_DURATION_MS)))
        pulse = 0.5 + 0.5 * math.sin(elapsed / 55.0)
        alpha = int((60 + 120 * pulse) * (1.0 - p))
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((255, 255, 255, alpha))
        self.screen.blit(surf, (0, 0))

    def draw_boss_kill_freeze_overlay(self):
        now = pygame.time.get_ticks()
        if now >= self.boss_kill_slow_until:
            return
        start = self.boss_kill_slow_start
        if start <= 0:
            start = max(0, self.boss_kill_slow_until - BOSS_KILL_SLOW_DURATION_MS)
        dur = max(1, int(self.boss_kill_slow_until - start))
        p = max(0.0, min(1.0, (now - start) / dur))
        fade = 0.5 - 0.5 * math.cos(2.0 * math.pi * p)
        alpha = int(120 * fade)
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((40, 80, 140, alpha))
        self.screen.blit(surf, (0, 0))

    def spawn_boss(self):
        hx, hy = self.snake[0]
        # candidate centers (boss is 3x3); avoid head 5x5
        candidates = []
        for x in range(1, GRID_WIDTH - 1):
            for y in range(1, GRID_HEIGHT - 1):
                if abs(x - hx) <= 2 and abs(y - hy) <= 2:
                    continue
                candidates.append((x, y))
        random.shuffle(candidates)

        def clear_cell(c):
            if c in self.obstacles:
                self.obstacles.remove(c)
            if c in self.normal_foods:
                self.normal_foods.remove(c)
                if c in self.normal_food_meta:
                    del self.normal_food_meta[c]
            if c in self.energy_foods:
                self.energy_foods.remove(c)
                if c in self.energy_food_meta:
                    del self.energy_food_meta[c]
            if self.items:
                self.items = [it for it in self.items if it.get("pos") != c]
            if self.spikes:
                self.spikes = [sp for sp in self.spikes if sp.pos != c]
            if self.ghost_hunters:
                self.ghost_hunters = [gh for gh in self.ghost_hunters if gh.pos != c]
            if self.fog_zones:
                self.fog_zones = [z for z in self.fog_zones if c not in self.get_fog_zone_cells(z["center"]) ]

        for pos in candidates[:80]:
            x, y = pos
            cells = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            # clear anything occupying the footprint (except snake)
            if any(c in self.snake for c in cells):
                continue
            for c in cells:
                clear_cell(c)

            if self.shadow_snakes:
                for ss in self.shadow_snakes[:]:
                    if any(seg in cells for seg in ss.snake):
                        self.shadow_snakes.remove(ss)

            self.boss = Boss(pos)
            self.play_sfx("boss_appear_01")
            return

    def draw_boss(self):
        if not self.boss:
            return
        # Boss body
        for cell in self.boss.get_cells():
            x, y = cell
            if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                continue
            rect = pygame.Rect(x * CELL_SIZE + 2, GAME_AREA_Y + y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4)

            glow_pad = 8
            glow_s = pygame.Surface((rect.width + glow_pad * 2, rect.height + glow_pad * 2), pygame.SRCALPHA)
            gr = glow_s.get_rect()
            base_rect = pygame.Rect(glow_pad, glow_pad, rect.width, rect.height)
            for i, w in enumerate((6, 4, 2)):
                a = 70 - i * 18
                rr = base_rect.inflate(i * 4, i * 4)
                pygame.draw.rect(glow_s, (255, 255, 255, a), rr, width=w, border_radius=10 + i * 2)
            self.screen.blit(glow_s, (rect.left - glow_pad, rect.top - glow_pad))

            pygame.draw.rect(self.screen, (255, 80, 0), rect, border_radius=6)
            # inner panel / texture
            inner = rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, (140, 35, 0), inner, border_radius=5)
            pygame.draw.line(self.screen, (255, 150, 80), (inner.left + 2, inner.top + 4), (inner.right - 2, inner.top + 4), 2)
            pygame.draw.line(self.screen, (255, 120, 40), (inner.left + 3, inner.bottom - 4), (inner.right - 3, inner.bottom - 4), 1)

        # core energy effect (does not change shield)
        now = pygame.time.get_ticks()
        bx, by = self.boss.pos
        core_x = bx * CELL_SIZE + CELL_SIZE // 2
        core_y = GAME_AREA_Y + by * CELL_SIZE + CELL_SIZE // 2
        pulse = 0.5 + 0.5 * math.sin(now / 120.0)
        core_r = int(CELL_SIZE * (0.22 + 0.10 * pulse))
        core = pygame.Surface((core_r * 6, core_r * 6), pygame.SRCALPHA)
        cr = core.get_rect()
        for i in range(6, 0, -1):
            a = int((35 + 80 * pulse) * (i / 6))
            pygame.draw.circle(core, (255, 220, 120, a), cr.center, int(core_r + (6 - i) * 2))
        pygame.draw.circle(core, (255, 255, 255, 220), cr.center, max(2, int(core_r * 0.45)))
        self.screen.blit(core, (core_x - cr.centerx, core_y - cr.centery))

        # Shield effect (fade)
        if self.boss.shield_active:
            now = pygame.time.get_ticks()
            t = min(1.0, (now - self.boss.shield_start_time) / max(1, BOSS_SHIELD_DURATION))
            alpha_scale = 1.0 - 0.65 * t
            flash = 0.5 + 0.5 * math.sin(now / 120.0)

            boss_cells = [c for c in self.boss.get_cells() if 0 <= c[0] < GRID_WIDTH and 0 <= c[1] < GRID_HEIGHT]
            min_x = min(c[0] for c in boss_cells)
            max_x = max(c[0] for c in boss_cells)
            min_y = min(c[1] for c in boss_cells)
            max_y = max(c[1] for c in boss_cells)

            w = (max_x - min_x + 1) * CELL_SIZE
            h = (max_y - min_y + 1) * CELL_SIZE
            pad = 14
            surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

            halo_a = int((90 + 70 * flash) * alpha_scale)
            for i in range(3):
                a = max(0, int((halo_a - i * 25) * 0.8))
                rr = pygame.Rect(pad - i * 3, pad - i * 3, w + i * 6, h + i * 6)
                pygame.draw.rect(surf, (0, 200, 255, a), rr, width=4, border_radius=22)

            hex_r = max(6, int(CELL_SIZE * 0.18))
            step_x = 1.5 * hex_r
            step_y = math.sqrt(3) * hex_r
            line_a = int((140 + 85 * flash) * alpha_scale)
            fill_a = int((35 + 25 * flash) * alpha_scale)

            inner = pygame.Rect(pad + 3, pad + 3, w - 6, h - 6)
            rows = int(h / step_y) + 3
            cols = int(w / step_x) + 3

            for r_i in range(rows):
                cy = pad + int(r_i * step_y)
                row_offset = int((r_i % 2) * (step_x / 2))
                for c_i in range(cols):
                    cx = pad + row_offset + int(c_i * step_x)
                    if not inner.collidepoint(cx, cy):
                        continue

                    pts = []
                    for k in range(6):
                        ang = math.pi / 3.0 * k + math.pi / 6.0
                        px = cx + int(hex_r * math.cos(ang))
                        py = cy + int(hex_r * math.sin(ang))
                        pts.append((px, py))
                    pygame.draw.polygon(surf, (0, 200, 255, fill_a), pts)
                    pygame.draw.polygon(surf, (200, 255, 255, line_a), pts, width=2)

            blit_x = min_x * CELL_SIZE - pad
            blit_y = GAME_AREA_Y + min_y * CELL_SIZE - pad
            self.screen.blit(surf, (blit_x, blit_y))

        # Bullets
        for bullet in self.boss.bullets:
            bx = int(round(bullet["x"]))
            by = int(round(bullet["y"]))
            if not (0 <= bx < GRID_WIDTH and 0 <= by < GRID_HEIGHT):
                continue
            cx = bx * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + by * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 4)
            pygame.draw.circle(self.screen, (255, 120, 0), (cx, cy), 8, width=2)

    def on_energy_food_eaten(self, pos, color_override=None):
        eat_color = color_override if color_override is not None else ENERGY_FOOD_COLOR
        energy_screen_x = pos[0] * CELL_SIZE + CELL_SIZE // 2
        energy_screen_y = GAME_AREA_Y + pos[1] * CELL_SIZE + CELL_SIZE // 2
        self.particle_system.emit(energy_screen_x, energy_screen_y, eat_color, count=30)
        self.trigger_glow_effect(eat_color)
        self.energy += 1
        self.play_sfx("collect_energy_01")

    def apply_item(self, item_type, head_pos):
        now = pygame.time.get_ticks()
        if item_type == ITEM_MAGNET:
            self.play_sfx("magnet_01")
            self.magnet_active_until = now + random.randint(MAGNET_DURATION_MIN_MS, MAGNET_DURATION_MAX_MS)
            self.magnet_anim_start = now
            self.next_magnet_pull_time = 0
            self.try_magnet_pull(now)

        elif item_type == ITEM_BOMB:
            self.play_sfx("bomb_01")
            radius = 2
            cells = []
            cx, cy = head_pos
            for x in range(cx - radius, cx + radius + 1):
                for y in range(cy - radius, cy + radius + 1):
                    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                        cells.append((x, y))
            cell_set = set(cells)

            removed = 0
            for c in list(cell_set):
                if c in self.obstacles:
                    self.obstacles.remove(c)
                    removed += 1
                    sx = c[0] * CELL_SIZE + CELL_SIZE // 2
                    sy = GAME_AREA_Y + c[1] * CELL_SIZE + CELL_SIZE // 2
                    self.particle_system.emit(sx, sy, (80, 80, 80), count=18)

            if self.spikes:
                self.spikes = [sp for sp in self.spikes if sp.pos not in cell_set]

            if self.ghost_hunters:
                self.ghost_hunters = [gh for gh in self.ghost_hunters if gh.pos not in cell_set]

            if self.shadow_snakes:
                for ss in self.shadow_snakes[:]:
                    if any(seg in cell_set for seg in ss.snake):
                        self.shadow_snakes.remove(ss)

            if self.fog_zones:
                self.fog_zones = [z for z in self.fog_zones if not (self.get_fog_zone_cells(z["center"]) & cell_set)]

            if self.boss:
                self.boss.bullets = [
                    b
                    for b in self.boss.bullets
                    if (int(round(b["x"])), int(round(b["y"]))) not in cell_set
                ]

            self.bomb_explosions.append({"center": head_pos, "start": now, "dur": BOMB_VFX_DURATION_MS})

            hx = head_pos[0] * CELL_SIZE + CELL_SIZE // 2
            hy = GAME_AREA_Y + head_pos[1] * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.emit(hx, hy, (30, 30, 30), count=40 + removed * 4)

        elif item_type == ITEM_SCISSORS:
            self.play_sfx("item_scissors")
            shrink_n = 3
            loud_v = 1.0 if len(self.snake) <= (shrink_n + 1) else None
            removed = self.apply_shrink(shrink_n, sfx_volume=loud_v)
            hx = head_pos[0] * CELL_SIZE + CELL_SIZE // 2
            hy = GAME_AREA_Y + head_pos[1] * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.emit(hx, hy, (0, 255, 0), count=18 + removed * 4)
            if len(self.snake) <= 1:
                self.trigger_game_over("减肥药导致身体太短了！")

        elif item_type == ITEM_ROTTEN_APPLE:
            self.play_sfx("poisoned_01")
            self.reverse_controls_until = now + 5_000
            self.rainbow_until = now + 5_000

    def try_magnet_pull(self, now):
        if now >= self.magnet_active_until:
            return
        hx, hy = self.snake[0]
        in_flight = {fl["pos"] for fl in self.magnet_flights}

        candidates_normal = [p for p in self.normal_foods if abs(p[0] - hx) <= MAGNET_PULL_RADIUS and abs(p[1] - hy) <= MAGNET_PULL_RADIUS]
        candidates_energy = [p for p in self.energy_foods if abs(p[0] - hx) <= MAGNET_PULL_RADIUS and abs(p[1] - hy) <= MAGNET_PULL_RADIUS]
        candidates_bombs = [
            it
            for it in self.items
            if it.get("type") == ITEM_BOMB
            and abs(it["pos"][0] - hx) <= MAGNET_PULL_RADIUS
            and abs(it["pos"][1] - hy) <= MAGNET_PULL_RADIUS
        ]

        for p in candidates_normal:
            if p in in_flight:
                continue
            if p in self.normal_foods:
                self.normal_foods.remove(p)
            meta = None
            if p in self.normal_food_meta:
                meta = self.normal_food_meta[p]
                del self.normal_food_meta[p]
            self.magnet_flights.append({"pos": p, "type": "normal", "start": now, "dur": random.randint(140, 240), "meta": meta})

        for p in candidates_energy:
            if p in in_flight:
                continue
            if p in self.energy_foods:
                self.energy_foods.remove(p)
            meta = None
            if p in self.energy_food_meta:
                meta = self.energy_food_meta[p]
                del self.energy_food_meta[p]
            self.magnet_flights.append({"pos": p, "type": "energy", "start": now, "dur": random.randint(140, 240), "meta": meta})

        for it in candidates_bombs:
            p = it["pos"]
            if p in in_flight:
                continue
            if it in self.items:
                self.items.remove(it)
            self.magnet_flights.append({"pos": p, "type": "bomb", "start": now, "dur": random.randint(160, 260)})

    def draw_items(self):
        for it in self.items:
            x, y = it["pos"]
            cx = x * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            t = it["type"]
            if t == ITEM_MAGNET:
                color = MAGNET_COLOR
            elif t == ITEM_BOMB:
                color = (50, 50, 50)
            elif t == ITEM_SCISSORS:
                color = SCISSORS_COLOR
            else:
                color = ROTTEN_APPLE_COLOR

            pulse = abs((pygame.time.get_ticks() % 900) / 450 - 1)
            glow_r = int(CELL_SIZE * 0.7 + pulse * 6)
            for r in range(glow_r, CELL_SIZE // 3, -2):
                a = int(50 * (1 - (glow_r - r) / max(1, glow_r)))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color, a), (r, r), r)
                self.screen.blit(s, (cx - r, cy - r))
            pygame.draw.rect(self.screen, color, pygame.Rect(x * CELL_SIZE + 5, GAME_AREA_Y + y * CELL_SIZE + 5, CELL_SIZE - 10, CELL_SIZE - 10), border_radius=6)

            # icon details
            if t == ITEM_MAGNET:
                pr = pygame.Rect(x * CELL_SIZE + 8, GAME_AREA_Y + y * CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
                head_r = max(6, pr.width // 3)
                head = pygame.Surface((head_r * 4, head_r * 4), pygame.SRCALPHA)
                hr = head.get_rect()
                pygame.draw.circle(head, (*SNAKE_HEAD_COLOR, 230), hr.center, head_r)
                pygame.draw.circle(head, (20, 20, 20, 180), hr.center, head_r, width=2)
                eye_r = max(1, head_r // 5)
                pygame.draw.circle(head, (255, 255, 255, 220), (hr.centerx - head_r // 3, hr.centery - head_r // 5), eye_r)
                pygame.draw.circle(head, (255, 255, 255, 220), (hr.centerx + head_r // 3, hr.centery - head_r // 5), eye_r)
                pygame.draw.circle(head, (0, 0, 0, 200), (hr.centerx - head_r // 3, hr.centery - head_r // 5), max(1, eye_r // 2))
                pygame.draw.circle(head, (0, 0, 0, 200), (hr.centerx + head_r // 3, hr.centery - head_r // 5), max(1, eye_r // 2))
                pygame.draw.circle(head, (255, 255, 255, 150), (hr.centerx - head_r // 3, hr.centery - head_r // 3), max(1, eye_r // 2))
                self.screen.blit(head, (cx - hr.centerx, cy - hr.centery))

                now = pygame.time.get_ticks()
                cycle_ms = 700
                tt = (now // 1) % cycle_ms
                pp = tt / cycle_ms
                r_max = int(CELL_SIZE * 0.72)
                r_min = int(CELL_SIZE * 0.32)
                ring_r = int(r_max - (r_max - r_min) * pp)
                ring_size = ring_r * 2 + 10
                ring_surf = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
                rc = ring_size // 2
                for w in (5, 3):
                    aa = int((70 + 70 * (1.0 - pp)) * (w / 5))
                    pygame.draw.circle(ring_surf, (255, 255, 0, aa), (rc, rc), ring_r, width=w)
                self.screen.blit(ring_surf, (cx - rc, cy - rc))

            elif t == ITEM_SCISSORS:
                pr = pygame.Rect(x * CELL_SIZE + 8, GAME_AREA_Y + y * CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
                pill_w = pr.width
                pill_h = max(12, int(pr.height * 0.70))
                pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
                pill_rect = pill.get_rect()
                rr = pill_h // 2

                left_col = (40, 220, 120)
                right_col = (255, 220, 80)

                # base capsule (green)
                pygame.draw.rect(pill, left_col, pill_rect, border_radius=rr)
                # overlay right half (yellow)
                right = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
                pygame.draw.rect(right, right_col, pill_rect, border_radius=rr)
                pill.blit(right, (0, 0), area=pygame.Rect(pill_w // 2, 0, pill_w - pill_w // 2, pill_h))

                # seam
                pygame.draw.line(pill, (255, 255, 255, 230), (pill_w // 2, 2), (pill_w // 2, pill_h - 3), 2)
                pygame.draw.line(pill, (0, 0, 0, 70), (pill_w // 2 + 2, 3), (pill_w // 2 + 2, pill_h - 4), 1)

                # glossy highlight (top-left)
                gloss = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
                pygame.draw.ellipse(gloss, (255, 255, 255, 85), pygame.Rect(2, 1, int(pill_w * 0.55), int(pill_h * 0.55)))
                pill.blit(gloss, (0, 0))

                # subtle shadow (bottom-right)
                shade = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
                pygame.draw.ellipse(shade, (0, 0, 0, 55), pygame.Rect(int(pill_w * 0.40), int(pill_h * 0.45), int(pill_w * 0.58), int(pill_h * 0.58)))
                pill.blit(shade, (0, 0))

                pygame.draw.rect(pill, (20, 20, 20, 190), pill_rect, width=2, border_radius=rr)
                self.screen.blit(pill, (pr.centerx - pill_w // 2, pr.centery - pill_h // 2))

            elif t == ITEM_ROTTEN_APPLE:
                # rotten apple with bite + stem
                pr = pygame.Rect(x * CELL_SIZE + 8, GAME_AREA_Y + y * CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
                body_r = pr.width // 2 - 2
                body_col = (155, 55, 175)
                shadow_col = (85, 25, 110)
                pygame.draw.circle(self.screen, body_col, pr.center, body_r)
                pygame.draw.circle(self.screen, shadow_col, (pr.centerx - 3, pr.centery + 2), max(2, body_r - 4))
                pygame.draw.circle(self.screen, (255, 185, 220), (pr.centerx - 4, pr.centery - 5), max(2, body_r // 3))

                for dx, dy, rr2, col in [
                    (-4, 2, 3, (70, 10, 90)),
                    (3, 4, 2, (60, 5, 80)),
                    (5, -1, 2, (75, 15, 95)),
                    (-1, -3, 2, (60, 8, 78)),
                ]:
                    pygame.draw.circle(self.screen, col, (pr.centerx + dx, pr.centery + dy), rr2)

                pygame.draw.circle(self.screen, BG_COLOR, (pr.centerx + pr.width // 4, pr.centery - 1), 6)
                pygame.draw.circle(self.screen, (20, 20, 20), (pr.centerx + pr.width // 4 + 3, pr.centery - 2), 3)
                pygame.draw.line(self.screen, (110, 70, 30), (pr.centerx, pr.y + 3), (pr.centerx + 2, pr.y + 10), 3)

            if t == ITEM_BOMB:
                pulse2 = abs((pygame.time.get_ticks() % 800) / 400 - 1)
                br = int(CELL_SIZE * (0.26 + 0.12 * pulse2))
                bomb_s = pygame.Surface((br * 4, br * 4), pygame.SRCALPHA)
                # black bomb body
                pygame.draw.circle(bomb_s, (0, 0, 0, 240), (br * 2, br * 2), br)
                # outline for visibility on dark background
                pygame.draw.circle(bomb_s, (140, 140, 140, 200), (br * 2, br * 2), br, width=2)
                # small highlight
                pygame.draw.circle(bomb_s, (220, 220, 220, 140), (br * 2 - 3, br * 2 - 3), max(2, br // 3))
                # red fuse
                pygame.draw.line(bomb_s, (255, 60, 60, 220), (br * 2, br * 2 - br), (br * 2, br * 2 - br - 6), 3)
                pygame.draw.circle(bomb_s, (255, 160, 80, 220), (br * 2 + 2, br * 2 - br - 8), 3)
                self.screen.blit(bomb_s, (cx - br * 2, cy - br * 2))

    def draw_bomb_explosions(self):
        if not self.bomb_explosions:
            return
        now = pygame.time.get_ticks()
        alive = []
        for ex in self.bomb_explosions:
            start = ex.get("start", 0)
            dur = max(1, int(ex.get("dur", BOMB_VFX_DURATION_MS)))
            t = (now - start) / dur
            if t >= 1.0:
                continue
            alive.append(ex)

            cx, cy = ex["center"]
            half = 2
            alpha = int(200 * (1.0 - t))
            surf = pygame.Surface((CELL_SIZE * GRID_WIDTH, CELL_SIZE * GRID_HEIGHT), pygame.SRCALPHA)

            for gx in range(cx - half, cx + half + 1):
                for gy in range(cy - half, cy + half + 1):
                    if not (0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT):
                        continue
                    # deterministic shard layout per cell
                    seed = (start ^ (gx << 8) ^ gy) & 0xFFFFFFFF
                    rr = random.Random(seed)
                    base_x = gx * CELL_SIZE
                    base_y = gy * CELL_SIZE
                    shard_count = 3 + rr.randint(0, 3)
                    for _ in range(shard_count):
                        w = rr.randint(3, 7)
                        h = rr.randint(2, 6)
                        ox = rr.randint(0, CELL_SIZE - w)
                        oy = rr.randint(0, CELL_SIZE - h)
                        jitter = int(10 * t)
                        ox += rr.randint(-jitter, jitter)
                        oy += rr.randint(-jitter, jitter)
                        col = (255, rr.randint(80, 160), rr.randint(40, 120), max(0, alpha - rr.randint(0, 80)))
                        pygame.draw.rect(surf, col, pygame.Rect(base_x + ox, base_y + oy, w, h), border_radius=2)

                    # cell outline flash
                    pygame.draw.rect(surf, (255, 220, 180, max(0, int(alpha * 0.25))), pygame.Rect(base_x + 2, base_y + 2, CELL_SIZE - 4, CELL_SIZE - 4), width=2, border_radius=4)

            self.screen.blit(surf, (0, GAME_AREA_Y))

        self.bomb_explosions = alive

    def draw_magnet_flights(self):
        now = pygame.time.get_ticks()
        if not self.magnet_flights and now >= self.magnet_active_until:
            return
        hx, hy = self.snake[0]
        end_x = hx * CELL_SIZE + CELL_SIZE // 2
        end_y = GAME_AREA_Y + hy * CELL_SIZE + CELL_SIZE // 2

        if now < self.magnet_active_until:
            cx, cy = end_x, end_y
            cycle_ms = 650
            t = (now - self.magnet_anim_start) % cycle_ms
            p = t / cycle_ms
            r_max = int(CELL_SIZE * 2.6)
            r_min = int(CELL_SIZE * 0.9)
            ring_r = int(r_max - (r_max - r_min) * p)
            ring_size = ring_r * 2 + 8
            ring_surf = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
            rc = ring_size // 2
            for w in range(6, 0, -2):
                a = int(90 * (1 - (6 - w) / 6))
                pygame.draw.circle(ring_surf, (255, 255, 0, a), (rc, rc), ring_r, width=w)
            self.screen.blit(ring_surf, (cx - rc, cy - rc))

        if not self.magnet_flights:
            return
        for fl in self.magnet_flights:
            p = fl["pos"]
            sx = p[0] * CELL_SIZE + CELL_SIZE // 2
            sy = GAME_AREA_Y + p[1] * CELL_SIZE + CELL_SIZE // 2
            dur = max(1, fl["dur"])
            t = min(1.0, (now - fl["start"]) / dur)
            ix = int(sx + (end_x - sx) * (t * t))
            iy = int(sy + (end_y - sy) * (t * t))
            if fl["type"] == "normal":
                c = FOOD_COLOR
            elif fl["type"] == "energy":
                c = ENERGY_FOOD_COLOR
            else:
                c = (60, 60, 60)
            for r in range(10, 4, -2):
                a = int(70 * (1 - (10 - r) / 10))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, a), (r, r), r)
                self.screen.blit(s, (ix - r, iy - r))
            if fl["type"] == "bomb":
                pygame.draw.circle(self.screen, (0, 0, 0), (ix, iy), 6)
                pygame.draw.circle(self.screen, (140, 140, 140), (ix, iy), 6, width=2)
            else:
                pygame.draw.circle(self.screen, c, (ix, iy), 5)

    def spawn_obstacle(self):
        cell = self.random_empty_cell_avoid_head(2)
        if cell is not None:
            self.obstacles.add(cell)

    def set_paused(self, paused: bool):
        now = pygame.time.get_ticks()
        paused = bool(paused)
        if paused and not self.paused:
            self.paused = True
            self.pause_started_at = now
        elif (not paused) and self.paused:
            self.paused = False
            if self.pause_started_at is not None:
                self.paused_time_accum += max(0, now - self.pause_started_at)
            self.pause_started_at = None

    def toggle_help(self):
        if not self.show_help:
            self.show_help = True
            self.help_page = 0
            if self.started and (not self.game_over) and (not self.paused) and (not self.show_leaderboard) and (not self.entering_name):
                self.help_paused_game = True
                self.set_paused(True)
            else:
                self.help_paused_game = False
        else:
            self.show_help = False
            if self.help_paused_game:
                self.help_paused_game = False
                if not self.show_leaderboard:
                    self.set_paused(False)

    # -------------------- 输入处理 --------------------
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self.toggle_help()
                    return

                if self.show_help:
                    if event.key == pygame.K_LEFT:
                        self.help_page = max(0, self.help_page - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.help_page = min(len(self.get_help_pages()) - 1, self.help_page + 1)
                    return

                # 如果正在输入名字
                if self.entering_name:
                    if event.key == pygame.K_RETURN:
                        # 回车确认，添加到排行榜
                        if self.player_name_input.strip():
                            self.add_to_leaderboard(self.player_name_input.strip(), self.score)
                        self.entering_name = False
                        self.player_name_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        # 退格删除
                        self.player_name_input = self.player_name_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        # ESC 取消输入
                        self.entering_name = False
                        self.player_name_input = ""
                    else:
                        # 输入字符（限制长度）
                        if len(self.player_name_input) < 15:
                            self.player_name_input += event.unicode
                    return

                # 查看排行榜（Tab 键切换，同时暂停/恢复游戏）
                if event.key == pygame.K_TAB:
                    self.show_leaderboard = not self.show_leaderboard
                    # 显示排行榜时暂停，关闭时恢复
                    if self.show_leaderboard:
                        self.set_paused(True)
                    else:
                        self.set_paused(False)
                    return

                # Game Over 界面输入
                if self.game_over and not self.entering_name:
                    if event.key == pygame.K_ESCAPE:
                        self.reset(start_with_intro=True) # 返回主界面
                    elif event.key == pygame.K_r:
                        self.reset(start_with_intro=False) # 重新开始
                    return

                # 启动画面：按空格键开始（ESC 直接退出）
                if not self.started:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_SPACE:
                        self.started = True
                        now = pygame.time.get_ticks()
                        self.run_start_time = now
                        self.run_end_time = None
                        self.paused_time_accum = 0
                        self.pause_started_at = None
                    return

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_p:
                    if (not self.game_over) and self.started and (not self.show_leaderboard) and (not self.entering_name):
                        self.set_paused(not self.paused)
                    return
                # 方向键 / WASD
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s, pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    reversed_controls = pygame.time.get_ticks() < self.reverse_controls_until
                    key = event.key
                    if key in (pygame.K_UP, pygame.K_w):
                        desired = (0, 1) if reversed_controls else (0, -1)
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        desired = (0, -1) if reversed_controls else (0, 1)
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        desired = (1, 0) if reversed_controls else (-1, 0)
                    else:
                        desired = (-1, 0) if reversed_controls else (1, 0)

                    if (desired[0], desired[1]) != (-self.direction[0], -self.direction[1]):
                        self.next_direction = desired
                # 幽灵模式开关（游戏结束时不能开启）
                elif event.key == pygame.K_SPACE:
                    if not self.game_over:
                        self.toggle_ghost_mode()


    def toggle_ghost_mode(self):
        now = pygame.time.get_ticks()
        # 已在幽灵模式：直接关闭
        if self.ghost_mode:
            self.ghost_mode = False
            self.ghost_end_time = now
            return

        # 还没开启，且有能量：开启
        if self.energy > 0 and not self.ghost_mode:
            self.energy -= 1
            self.ghost_mode = True
            self.ghost_end_time = now + GHOST_DURATION

    def trigger_game_over(self, reason):
        """触发游戏结束，判断是否进入排行榜"""
        self.game_over = True
        self.game_over_reason = reason
        self.run_end_time = pygame.time.get_ticks()
        # 判断是否进入排行榜
        if self.score > 0 and self.is_high_score(self.score):
            self.entering_name = True
            self.player_name_input = ""
    
    def trigger_glow_effect(self, color):
        """触发身体刷光效果"""
        self.glow_effect_active = True
        self.glow_effect_start = pygame.time.get_ticks()
        self.glow_effect_color = color

    def trigger_score_damage_effect(self, old_score: int, new_score: int):
        now = pygame.time.get_ticks()
        self.score_anim_from = int(old_score)
        self.score_anim_to = int(new_score)
        self.score_anim_start = now
        self.score_anim_end = now + SCORE_ANIM_DURATION_MS
        self.score_burst_start = now
        self.score_burst_until = now + SCORE_BURST_DURATION_MS

    def get_time_scale(self, now: int) -> float:
        if now < self.boss_kill_slow_until:
            return BOSS_KILL_TIME_SCALE
        if now < self.damage_slow_until:
            return DAMAGE_SLOW_TIME_SCALE
        return 1.0

    def trigger_boss_kill_effect(self):
        now = pygame.time.get_ticks()
        self.boss_kill_slow_start = now
        self.boss_kill_slow_until = now + BOSS_KILL_SLOW_DURATION_MS
        self.boss_kill_flash_until = now + BOSS_KILL_FLASH_DURATION_MS
        self.boss_kill_flash_start = now

    def trigger_shockwave(self, center_pos, color=(200, 255, 255)):
        self.shockwave_active = True
        self.shockwave_start_time = pygame.time.get_ticks()
        self.shockwave_color = color
        self.shockwave_center = center_pos

    def apply_shrink(self, count: int, sfx_volume: float = None):
        now = pygame.time.get_ticks()
        removed = 0
        while removed < count and len(self.snake) > 1:
            tail = self.snake.pop()
            self.play_sfx("crack_01", volume=sfx_volume)
            sx = tail[0] * CELL_SIZE + CELL_SIZE // 2
            sy = GAME_AREA_Y + tail[1] * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.emit(sx, sy, (120, 220, 255), count=10)
            removed += 1
        self.last_shrink_time = now
        self.shrink_remaining = 0
        return removed

    def shockwave_clear_and_refresh(self, center_pos):
        hx, hy = center_pos
        half = SHOCKWAVE_CLEAR_SIZE // 2
        cell_set = set()
        for x in range(hx - half, hx - half + SHOCKWAVE_CLEAR_SIZE):
            for y in range(hy - half, hy - half + SHOCKWAVE_CLEAR_SIZE):
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    cell_set.add((x, y))

        for c in list(cell_set):
            if c in self.obstacles:
                self.obstacles.remove(c)

        if self.normal_foods:
            for c in list(cell_set):
                if c in self.normal_foods:
                    self.normal_foods.remove(c)
                    if c in self.normal_food_meta:
                        del self.normal_food_meta[c]

        if self.energy_foods:
            for c in list(cell_set):
                if c in self.energy_foods:
                    self.energy_foods.remove(c)
                    if c in self.energy_food_meta:
                        del self.energy_food_meta[c]

        if self.items:
            self.items = [it for it in self.items if it["pos"] not in cell_set]

        if self.ghost_hunters:
            self.ghost_hunters = [gh for gh in self.ghost_hunters if gh.pos not in cell_set]

        if self.shadow_snakes:
            for ss in self.shadow_snakes[:]:
                if any(seg in cell_set for seg in ss.snake):
                    self.shadow_snakes.remove(ss)

        if self.fog_zones:
            self.fog_zones = [z for z in self.fog_zones if not (self.get_fog_zone_cells(z["center"]) & cell_set)]

        if self.boss:
            self.boss.bullets = [
                b
                for b in self.boss.bullets
                if (int(round(b["x"])), int(round(b["y"]))) not in cell_set
            ]

        if self.spikes:
            for sp in self.spikes:
                if sp.pos in cell_set:
                    new_pos = self.random_empty_cell_avoid_head(2)
                    if new_pos is not None:
                        sp.pos = new_pos
                        sp.visible = True
                        sp.last_toggle = pygame.time.get_ticks()

        if self.portal_pairs:
            for color_id, (p1, p2) in list(self.portal_pairs.items()):
                if p1 in cell_set or p2 in cell_set:
                    np1 = self.random_empty_cell_avoid_head(2)
                    np2 = self.random_empty_cell_avoid_head(2)
                    if np1 is None or np2 is None:
                        continue
                    if p1 in self.portal_lookup:
                        del self.portal_lookup[p1]
                    if p2 in self.portal_lookup:
                        del self.portal_lookup[p2]
                    self.portal_pairs[color_id] = (np1, np2)
                    self.portal_lookup[np1] = color_id
                    self.portal_lookup[np2] = color_id
            self.portals = []
            for cid, (a, b) in self.portal_pairs.items():
                self.portals.append(Portal(a, cid))
                self.portals.append(Portal(b, cid))

        self.spawn_food()
        while len(self.items) < ITEM_MAX_ON_MAP:
            self.spawn_item()
        if len(self.fog_zones) < FOG_ZONE_MAX_ON_MAP:
            self.spawn_fog_zone(force=True)

    def apply_damage_burst(self, reason: str, center_pos, score_penalty: int = SCORE_DAMAGE_AMOUNT):
        now = pygame.time.get_ticks()
        self.play_sfx("energy_shackwave")
        self.damage_slow_until = max(self.damage_slow_until, now + DAMAGE_SLOW_DURATION_MS)
        self.damage_blink_start = now
        self.damage_blink_until = now + DAMAGE_BLINK_DURATION_MS
        self.trigger_shockwave(center_pos)
        self.trigger_glow_effect((120, 220, 255))
        self.shockwave_clear_and_refresh(center_pos)

        if score_penalty and score_penalty > 0:
            old_score = int(self.score)
            self.score = max(0, int(self.score) - int(score_penalty))
            if int(self.score) != old_score:
                self.trigger_score_damage_effect(old_score, int(self.score))

        loud_v = 1.0 if len(self.snake) <= (DAMAGE_SHRINK_SEGMENTS + 1) else None
        self.apply_shrink(DAMAGE_SHRINK_SEGMENTS, sfx_volume=loud_v)
        if len(self.snake) <= 1:
            self.trigger_game_over(reason)

    # -------------------- 游戏更新逻辑 --------------------
    def update(self):
        if self.game_over:
            return

        now = pygame.time.get_ticks()
        time_scale = self.get_time_scale(now)

        if now >= self.next_portal_refresh_time:
            self.refresh_one_portal_pair()
            self.next_portal_refresh_time = now + random.randint(PORTAL_REFRESH_MIN, PORTAL_REFRESH_MAX)

        for sp in self.spikes:
            sp.update()

        if now >= self.next_spike_refresh_time:
            self.refresh_one_spike()
            self.next_spike_refresh_time = now + random.randint(SPIKE_REFRESH_MIN, SPIKE_REFRESH_MAX)

        if now >= self.next_shadow_spawn_time:
            self.spawn_shadow_snake()
            self.next_shadow_spawn_time = now + random.randint(SHADOW_SNAKE_SPAWN_MIN, SHADOW_SNAKE_SPAWN_MAX)
        self.update_shadow_snakes(time_scale=time_scale)

        if now >= self.next_ghost_spawn_time:
            self.spawn_ghost_hunter()
            self.next_ghost_spawn_time = now + random.randint(GHOST_HUNTER_INVISIBLE_MIN, GHOST_HUNTER_INVISIBLE_MAX)
        self.update_ghost_hunters(time_scale=time_scale)

        if self.boss:
            self.boss.update(GRID_WIDTH, GRID_HEIGHT, time_scale=time_scale)
            hx, hy = self.snake[0]
            if not self.ghost_mode:
                for bullet in self.boss.bullets:
                    bx = int(round(bullet["x"]))
                    by = int(round(bullet["y"]))
                    if (bx, by) == (hx, hy):
                        self.apply_damage_burst("撞到Boss子弹了！", (hx, hy))
                        return

        if not self.ghost_mode:
            for gh in self.ghost_hunters:
                if gh.visible and gh.pos == self.snake[0]:
                    self.apply_damage_burst("被幽灵猎手抓到了！", self.snake[0])
                    return

        if now >= self.next_item_spawn_time:
            self.spawn_item()
            self.next_item_spawn_time = now + random.randint(ITEM_SPAWN_MIN, ITEM_SPAWN_MAX)

        if now >= self.next_fog_zone_refresh_time:
            self.spawn_fog_zone(force=True)
            self.next_fog_zone_refresh_time = now + random.randint(FOG_ZONE_REFRESH_MIN_MS, FOG_ZONE_REFRESH_MAX_MS)

        if now < self.magnet_active_until and now >= self.next_magnet_pull_time:
            self.try_magnet_pull(now)
            self.next_magnet_pull_time = now + MAGNET_PULL_CHECK_INTERVAL_MS

        if self.shrink_remaining > 0 and now - self.last_shrink_time >= SHRINK_INTERVAL_MS:
            if len(self.snake) > 3:
                tail = self.snake.pop()
                sx = tail[0] * CELL_SIZE + CELL_SIZE // 2
                sy = GAME_AREA_Y + tail[1] * CELL_SIZE + CELL_SIZE // 2
                self.particle_system.emit(sx, sy, (120, 220, 255), count=10)
                self.shrink_remaining -= 1
            else:
                self.shrink_remaining = 0
            self.last_shrink_time = now

        if self.magnet_flights:
            hx, hy = self.snake[0]
            arrived = []
            for fl in self.magnet_flights:
                if now - fl["start"] >= fl["dur"]:
                    arrived.append(fl)
            for fl in arrived:
                self.magnet_flights.remove(fl)
                if fl["type"] == "bomb":
                    # explode at snake head
                    self.apply_item(ITEM_BOMB, (hx, hy))
                elif fl["type"] == "normal":
                    meta = fl.get("meta")
                    counts_for_boss = True
                    color_override = None
                    if meta:
                        counts_for_boss = bool(meta.get("counts_for_boss", True))
                        color_override = meta.get("color")
                    self.on_normal_food_eaten(fl["pos"], counts_for_boss=counts_for_boss, color_override=color_override)
                    self.grow_pending += 1
                else:
                    meta = fl.get("meta")
                    color_override = meta.get("color") if meta else None
                    self.on_energy_food_eaten(fl["pos"], color_override=color_override)

        # 幽灵模式计时即使在未移动时也需要更新
        if self.ghost_mode and now >= self.ghost_end_time:
            self.ghost_mode = False

        # 移动节奏控制：未到间隔则不移动
        effective_step = self.step_interval_ms / max(0.05, time_scale)
        if now - self.last_move_time < effective_step:
            return
        self.last_move_time = now

        # 更新方向
        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 边界检测：幽灵模式允许穿墙（从另一侧出来）；正常模式死亡
        if not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT):
            if self.ghost_mode:
                new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
            else:
                self.play_sfx("crack_02", volume=1.0)
                self.trigger_game_over("撞到边界了！")
                return

        if now >= self.portal_cooldown_until:
            if new_head in self.portal_lookup:
                color_id = self.portal_lookup[new_head]
                p1, p2 = self.portal_pairs.get(color_id, (None, None))
                if p1 and p2:
                    if new_head == p1:
                        new_head = p2
                    else:
                        new_head = p1
                    self.portal_cooldown_until = now + PORTAL_TELEPORT_COOLDOWN_MS
                    self.portal_cooldown_color_id = color_id
                    cx = new_head[0] * CELL_SIZE + CELL_SIZE // 2
                    cy = GAME_AREA_Y + new_head[1] * CELL_SIZE + CELL_SIZE // 2
                    self.particle_system.emit(cx, cy, (0, 255, 255), count=18)
                    self.play_sfx("portal_02")

        # 障碍检测：幽灵模式可以穿过障碍
        if new_head in self.obstacles:
            if not self.ghost_mode:
                self.apply_damage_burst("撞到荆棘了！", new_head)
                return

        # 地刺：可见时踩到会死（幽灵模式可穿过）
        if not self.ghost_mode:
            for sp in self.spikes:
                if sp.visible and sp.pos == new_head:
                    self.apply_damage_burst("踩到地刺了！", new_head)
                    return

        # Boss body collision / kill
        if self.boss:
            boss_cells = set(self.boss.get_cells())
            if new_head in boss_cells:
                if self.ghost_mode and (not self.boss.shield_active):
                    # Kill boss
                    self.play_sfx("defeat_boss_03")
                    self.trigger_boss_kill_effect()
                    boss_center = self.boss.pos
                    for cell in boss_cells:
                        sx = cell[0] * CELL_SIZE + CELL_SIZE // 2
                        sy = GAME_AREA_Y + cell[1] * CELL_SIZE + CELL_SIZE // 2
                        self.particle_system.emit(sx, sy, (255, 120, 0), count=20)
                    self.score += 10

                    drop_count = 18
                    drop_radius = 5
                    occupied = set(self.snake) | self.obstacles | set(self.normal_foods) | set(self.energy_foods)
                    for it in self.items:
                        occupied.add(it["pos"])
                    for p in self.portals:
                        occupied.add(p.pos)
                    for sp in self.spikes:
                        occupied.add(sp.pos)

                    cx, cy = boss_center
                    for _ in range(drop_count):
                        for _try in range(30):
                            x = cx + random.randint(-drop_radius, drop_radius)
                            y = cy + random.randint(-drop_radius, drop_radius)
                            if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                                continue
                            cell = (x, y)
                            if cell in occupied:
                                continue
                            self.normal_foods.append(cell)
                            self.normal_food_meta[cell] = {"counts_for_boss": False, "color": (255, 80, 0)}
                            occupied.add(cell)
                            break

                    for _ in range(3):
                        for _try in range(30):
                            x = cx + random.randint(-drop_radius, drop_radius)
                            y = cy + random.randint(-drop_radius, drop_radius)
                            if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                                continue
                            cell = (x, y)
                            if cell in occupied:
                                continue
                            self.energy_foods.append(cell)
                            self.energy_food_meta[cell] = {"counts_for_boss": False, "color": (255, 80, 0)}
                            occupied.add(cell)
                            break
                    self.boss = None
                    self.boss_spawn_progress = 0
                else:
                    self.play_sfx("energy_shackwave")
                    self.trigger_game_over("撞到Boss了！")
                    return

        # 自身碰撞（根据幽灵模式判断是否死亡）
        if new_head in self.snake:
            if not self.ghost_mode:
                self.apply_damage_burst("撞到自己了！", new_head)
                return
            # 幽灵模式下可以穿过身体：尾部仍然会移动

        # 头撞到影子蛇身体：你死（幽灵模式无视）
        if not self.ghost_mode:
            for ss in self.shadow_snakes:
                if new_head in ss.snake:
                    self.apply_damage_burst("撞到影子蛇了！", new_head)
                    return

        # 移动：在前面加新头
        self.snake.insert(0, new_head)

        if self.fog_zones:
            hit_index = None
            for i, z in enumerate(self.fog_zones):
                if new_head in self.get_fog_zone_cells(z["center"]):
                    hit_index = i
                    break
            if hit_index is not None:
                self.fog_radius = random.randint(FOG_VISIBILITY_MIN, FOG_VISIBILITY_MAX)
                self.fog_active_until = now + random.randint(FOG_DURATION_MIN_MS, FOG_DURATION_MAX_MS)
                self.fog_zones.pop(hit_index)
                self.next_fog_zone_refresh_time = now + random.randint(FOG_ZONE_REFRESH_MIN_MS, FOG_ZONE_REFRESH_MAX_MS)
                self.play_sfx("fog_01")

        ate_food = False
        # 吃普通食物
        if new_head in self.normal_foods:
            ate_food = True
            self.normal_foods.remove(new_head)
            meta = None
            if new_head in self.normal_food_meta:
                meta = self.normal_food_meta[new_head]
                del self.normal_food_meta[new_head]
            counts_for_boss = True
            color_override = None
            if meta:
                counts_for_boss = bool(meta.get("counts_for_boss", True))
                color_override = meta.get("color")
            self.on_normal_food_eaten(new_head, counts_for_boss=counts_for_boss, color_override=color_override)

        # 吃能量食物
        if new_head in self.energy_foods:
            self.energy_foods.remove(new_head)
            meta = None
            if new_head in self.energy_food_meta:
                meta = self.energy_food_meta[new_head]
                del self.energy_food_meta[new_head]
            color_override = meta.get("color") if meta else None
            self.on_energy_food_eaten(new_head, color_override=color_override)

        picked = None
        for it in self.items:
            if it["pos"] == new_head:
                picked = it
                break
        if picked:
            self.items.remove(picked)
            self.apply_item(picked["type"], new_head)

        # 如果没有吃普通食物，尾巴要前进（去掉最后一个块）
        if not ate_food:
            if self.grow_pending > 0:
                self.grow_pending -= 1
            else:
                self.snake.pop()

        # 如果食物被吃掉了，就重新生成
        if len(self.normal_foods) < NORMAL_FOOD_TARGET:
            self.spawn_food()

    # -------------------- 绘制相关 --------------------
    def draw_text_with_glow(self, text, font, color, pos, center=False):
        """绘制带发光效果的文字"""
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect()
        if center:
            text_rect.center = pos
        else:
            text_rect.topleft = pos
        
        # 绘制发光层
        glow_color = tuple(max(0, c - 50) for c in color)
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2), (0,2), (0,-2), (2,0), (-2,0)]:
            glow_surf = font.render(text, True, glow_color)
            glow_pos = (text_rect.x + offset[0], text_rect.y + offset[1])
            self.screen.blit(glow_surf, glow_pos)
        
        # 绘制主文字
        self.screen.blit(text_surf, text_rect)
        return text_rect

    def draw_text_with_glow_alpha(self, text, font, color, pos, alpha: int, center=False):
        alpha = max(0, min(255, int(alpha)))
        text_surf = font.render(text, True, color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect()
        if center:
            text_rect.center = pos
        else:
            text_rect.topleft = pos

        glow_color = tuple(max(0, c - 50) for c in color)
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2), (0, 2), (0, -2), (2, 0), (-2, 0)]:
            glow_surf = font.render(text, True, glow_color)
            glow_surf.set_alpha(max(0, min(255, int(alpha * 0.85))))
            glow_pos = (text_rect.x + offset[0], text_rect.y + offset[1])
            self.screen.blit(glow_surf, glow_pos)

        self.screen.blit(text_surf, text_rect)
        return text_rect
    
    def draw_grid(self):
        """绘制赛博朋克风格的网格（在游戏区域内，不包括底部栏）"""
        game_area_end_y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT
        
        # 绘制游戏区域的边框（上左下右）
        border_color = (100, 50, 150)
        pygame.draw.line(self.screen, border_color, (0, GAME_AREA_Y), (SCREEN_WIDTH, GAME_AREA_Y), 2)  # 上边
        pygame.draw.line(self.screen, border_color, (0, GAME_AREA_Y), (0, game_area_end_y), 2)  # 左边
        pygame.draw.line(self.screen, border_color, (0, game_area_end_y - 1), (SCREEN_WIDTH, game_area_end_y - 1), 2)  # 下边
        pygame.draw.line(self.screen, border_color, (SCREEN_WIDTH - 1, GAME_AREA_Y), (SCREEN_WIDTH - 1, game_area_end_y), 2)  # 右边
        
        # 主网格线（在游戏区域内）
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, GAME_AREA_Y), (x, game_area_end_y), 1)
        for y in range(GAME_AREA_Y, game_area_end_y, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
        
        # 每隔5格绘制高亮线
        bright_grid = (80, 40, 120)
        for x in range(0, SCREEN_WIDTH, CELL_SIZE * 5):
            pygame.draw.line(self.screen, bright_grid, (x, GAME_AREA_Y), (x, game_area_end_y), 2)
        for y in range(GAME_AREA_Y, game_area_end_y, CELL_SIZE * 5):
            pygame.draw.line(self.screen, bright_grid, (0, y), (SCREEN_WIDTH, y), 2)

    def draw_snake(self):
        """绘制蛇（圆球状，带渐变色、光泽效果和刷光效果）"""
        # 计算刷光效果进度
        glow_progress = -1  # -1表示无效，0-1表示从头到尾的进度
        if self.glow_effect_active:
            elapsed = pygame.time.get_ticks() - self.glow_effect_start
            if elapsed < self.glow_effect_duration:
                glow_progress = elapsed / self.glow_effect_duration
            else:
                self.glow_effect_active = False
        
        snake_length = len(self.snake)
        
        # 幽灵模式闪烁效果：由慢变快，提示即将结束
        ghost_blink = False
        ghost_blink_interval = 200  # 默认200ms
        if self.ghost_mode:
            time_left = max(0, self.ghost_end_time - pygame.time.get_ticks())
            # 剩余时间越少，闪烁越快
            if time_left < 2000:  # 最后2秒
                ghost_blink_interval = 50  # 很快
            elif time_left < 3000:  # 最后3秒
                ghost_blink_interval = 100  # 较快
            elif time_left < 4000:  # 最后4秒
                ghost_blink_interval = 150  # 中等
            ghost_blink = (pygame.time.get_ticks() // ghost_blink_interval) % 2 == 0
        
        rainbow_active = pygame.time.get_ticks() < self.rainbow_until

        damage_blink = False
        now = pygame.time.get_ticks()
        if now < getattr(self, "damage_blink_until", 0):
            t = now - getattr(self, "damage_blink_start", 0)
            damage_blink = (t // DAMAGE_BLINK_INTERVAL_MS) % 2 == 0

        for i, (x, y) in enumerate(self.snake):
            center_x = x * CELL_SIZE + CELL_SIZE // 2
            center_y = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            
            # 头部和身体大小不同
            if i == 0:
                # 头部：稍大
                radius = CELL_SIZE // 2 - 1
                base_color = SNAKE_HEAD_COLOR
                glow_color = SNAKE_HEAD_COLOR
            else:
                # 身体：比头部小（稍微大一点）
                radius = int(CELL_SIZE * 0.42)  # 身体半径约为头部的84%
                base_color = SNAKE_COLOR
                glow_color = SNAKE_GLOW

            # 刷光效果：检查当前节点是否应该被刷光点亮
            is_glowing = False
            if glow_progress >= 0 and snake_length > 0:
                # 计算刷光应该到达的节点索引（带点宽度，让刷光更明显）
                glow_position = glow_progress * snake_length
                glow_width = 3  # 刷光的宽度（几个节点同时亮）
                if abs(i - glow_position) < glow_width:
                    is_glowing = True
                    # 根据距离计算亮度
                    distance_factor = 1.0 - abs(i - glow_position) / glow_width
                    # 替换颜色为刷光颜色，并增加亮度
                    blend_factor = distance_factor * 0.9
                    # 混合刷光颜色，并增加整体亮度
                    base_color = tuple(
                        min(255, int((base_color[j] * (1 - blend_factor) + self.glow_effect_color[j] * blend_factor) * 1.3))
                        for j in range(3)
                    )
                    glow_color = tuple(min(255, int(c * 1.2)) for c in self.glow_effect_color)

            # 幽灵模式：半透明闪烁
            alpha = 255
            if self.ghost_mode:
                if ghost_blink:
                    alpha = 120  # 半透明
                else:
                    alpha = 200  # 稍微透明

            if damage_blink:
                alpha = min(alpha, 90)
            
            # 渐变色：从头部到尾部颜色渐变
            if snake_length > 1:
                gradient_factor = i / max(1, snake_length - 1)
                # 从头部颜色渐变到尾部颜色（稍微变暗）
                color = tuple(
                    int(base_color[j] * (1 - gradient_factor * 0.3))
                    for j in range(3)
                )
            else:
                color = base_color

            if rainbow_active:
                hue = ((pygame.time.get_ticks() * 0.0006) + (i * 0.05)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                color = (int(r * 255), int(g * 255), int(b * 255))
                glow_color = color
            
            # 绘制发光层（多层圆形，越外越淡）
            glow_intensity = 6 if is_glowing else 4  # 刷光时加强发光
            for r in range(radius + glow_intensity, radius, -1):
                alpha_glow = int((30 if is_glowing else 20) * (1 - (r - radius) / glow_intensity))
                if self.ghost_mode:
                    alpha_glow = int(alpha_glow * (alpha / 255))
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*glow_color, alpha_glow), (r, r), r)
                self.screen.blit(s, (center_x - r, center_y - r))
            
            # 绘制主体圆球（带渐变和光泽）
            # 创建渐变表面
            ball_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            
            # 绘制基础圆球
            pygame.draw.circle(ball_surf, (*color, alpha), (radius, radius), radius)
            
            # 添加光泽效果（高光）
            highlight_radius = int(radius * 0.6)
            highlight_offset_x = int(radius * 0.3)
            highlight_offset_y = int(radius * 0.3)
            highlight_color = tuple(min(c + 80, 255) for c in color)
            if alpha < 255:
                highlight_alpha = int(alpha * 0.8)
            else:
                highlight_alpha = 200
            pygame.draw.circle(
                ball_surf, (*highlight_color, highlight_alpha),
                (radius - highlight_offset_x, radius - highlight_offset_y),
                highlight_radius
            )
            
            # 添加顶部小高光点
            small_highlight_radius = int(radius * 0.3)
            small_highlight_pos_x = int(radius * 0.4)
            small_highlight_pos_y = int(radius * 0.4)
            pygame.draw.circle(
                ball_surf, (255, 255, 255, min(alpha, 180)),
                (radius - small_highlight_pos_x, radius - small_highlight_pos_y),
                small_highlight_radius
            )
            
            # 绘制到屏幕
            self.screen.blit(ball_surf, (center_x - radius, center_y - radius))
            
            # 头部添加眼睛
            if i == 0:
                # 根据方向确定眼睛位置（眼睛在移动方向的前方，左右对称）
                dx, dy = self.direction
                eye_size = max(2, radius // 4)  # 眼睛大小
                eye_forward = radius // 2  # 眼睛在移动方向前方的偏移
                eye_side = radius // 3  # 眼睛左右对称的偏移
                
                # 计算眼睛位置（在移动方向前方，左右对称）
                if dx == 1:  # 向右移动
                    eye1_x = center_x + eye_forward
                    eye1_y = center_y - eye_side
                    eye2_x = center_x + eye_forward
                    eye2_y = center_y + eye_side
                elif dx == -1:  # 向左移动
                    eye1_x = center_x - eye_forward
                    eye1_y = center_y - eye_side
                    eye2_x = center_x - eye_forward
                    eye2_y = center_y + eye_side
                elif dy == -1:  # 向上移动
                    eye1_x = center_x - eye_side
                    eye1_y = center_y - eye_forward
                    eye2_x = center_x + eye_side
                    eye2_y = center_y - eye_forward
                else:  # 向下移动 (dy == 1)
                    eye1_x = center_x - eye_side
                    eye1_y = center_y + eye_forward
                    eye2_x = center_x + eye_side
                    eye2_y = center_y + eye_forward
                
                # 绘制眼睛（白色高光，带发光效果）
                eye_alpha = min(alpha, 255)
                # 眼睛发光层
                for r in range(eye_size + 2, eye_size, -1):
                    eye_glow_alpha = int(60 * (1 - (r - eye_size) / 2))
                    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 255, 255, eye_glow_alpha), (r, r), r)
                    self.screen.blit(s, (eye1_x - r, eye1_y - r))
                    self.screen.blit(s, (eye2_x - r, eye2_y - r))
                
                # 绘制眼睛（白色）
                pygame.draw.circle(self.screen, (255, 255, 255), (eye1_x, eye1_y), eye_size)
                pygame.draw.circle(self.screen, (255, 255, 255), (eye2_x, eye2_y), eye_size)
                
                # 眼睛内部小黑点（瞳孔）
                pupil_size = max(1, eye_size // 2)
                pygame.draw.circle(self.screen, (0, 0, 0), (eye1_x, eye1_y), pupil_size)
                pygame.draw.circle(self.screen, (0, 0, 0), (eye2_x, eye2_y), pupil_size)

    def draw_foods(self):
        """绘制食物（带霓虹发光和脉冲效果）"""
        pulse = abs((pygame.time.get_ticks() % 1000) / 500 - 1)  # 0-1-0 脉冲
        
        for x, y in self.normal_foods:
            meta = self.normal_food_meta.get((x, y))
            base_color = meta.get("color") if meta else FOOD_COLOR
            glow_color = (
                min(255, int(base_color[0] * 0.7 + 80)),
                min(255, int(base_color[1] * 0.7 + 80)),
                min(255, int(base_color[2] * 0.7 + 80)),
            )
            cx = x * CELL_SIZE + CELL_SIZE // 2
            cy = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            pad = 4
            r0 = max(3, CELL_SIZE // 2 - pad)
            
            # 发光层（脉冲效果）
            glow_radius = int(r0 + 10 + pulse * 6)
            for r in range(glow_radius, r0, -2):
                alpha = int(60 * (1 - (glow_radius - r) / max(1, glow_radius)))
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*glow_color, alpha), (r, r), r)
                self.screen.blit(s, (cx - r, cy - r))
            
            # 实体
            pygame.draw.circle(self.screen, base_color, (cx, cy), r0)
            # 高光
            pygame.draw.circle(self.screen, (255, 150, 200), (cx - 3, cy - 3), max(2, r0 // 2))

        for x, y in self.energy_foods:
            meta = self.energy_food_meta.get((x, y))
            base_color = meta.get("color") if meta else ENERGY_FOOD_COLOR
            glow_color = (
                min(255, int(base_color[0] * 0.65 + 90)),
                min(255, int(base_color[1] * 0.65 + 90)),
                min(255, int(base_color[2] * 0.65 + 90)),
            )
            rect = pygame.Rect(x * CELL_SIZE, GAME_AREA_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            # 发光层（脉冲效果）
            glow_size = int(pulse * 6)
            for offset in range(6, 0, -1):
                glow_rect = pygame.Rect(
                    x * CELL_SIZE - offset - glow_size,
                    GAME_AREA_Y + y * CELL_SIZE - offset - glow_size,
                    CELL_SIZE + (offset + glow_size) * 2,
                    CELL_SIZE + (offset + glow_size) * 2
                )
                alpha_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                alpha = 40 // offset
                pygame.draw.rect(alpha_surf, (*glow_color, alpha), alpha_surf.get_rect(), border_radius=10)
                self.screen.blit(alpha_surf, glow_rect)
            
            center_x = x * CELL_SIZE + CELL_SIZE // 2
            center_y = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            pad = 5
            rr = max(6, CELL_SIZE // 2 - pad)

            now = pygame.time.get_ticks()
            blink = 0.5 + 0.5 * math.sin(now / 85.0)
            bright = 0.78 + 0.22 * blink
            fill_col = (
                min(255, int(base_color[0] * bright + 20)),
                min(255, int(base_color[1] * bright + 20)),
                min(255, int(base_color[2] * bright + 10)),
                255,
            )
            glow_a = int(60 + 160 * blink)

            bolt_size = rr * 2 + 6
            bolt = pygame.Surface((bolt_size, bolt_size), pygame.SRCALPHA)
            bx = bolt_size // 2
            by = bolt_size // 2

            pts = [
                (bx - int(rr * 0.10), by - int(rr * 1.10)),
                (bx + int(rr * 0.55), by - int(rr * 0.10)),
                (bx + int(rr * 0.15), by - int(rr * 0.10)),
                (bx + int(rr * 0.10), by + int(rr * 1.10)),
                (bx - int(rr * 0.55), by + int(rr * 0.05)),
                (bx - int(rr * 0.20), by + int(rr * 0.05)),
            ]

            # glow outline (blink)
            pygame.draw.polygon(bolt, (255, 255, 255, glow_a), pts, width=6)
            pygame.draw.polygon(bolt, (255, 255, 180, max(0, glow_a - 40)), pts, width=3)

            # solid fill
            pygame.draw.polygon(bolt, fill_col, pts)

            pygame.draw.polygon(bolt, (20, 20, 20, 170), pts, width=2)

            self.screen.blit(bolt, (center_x - bx, center_y - by))

    def draw_obstacles(self):
        """绘制荆棘障碍（赛博朋克风格）"""
        for x, y in self.obstacles:
            center_x = x * CELL_SIZE + CELL_SIZE // 2
            center_y = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
            
            # 发光层（圆形扩散）
            for r in range(18, 8, -2):
                alpha = int(60 * (18 - r) / 18)
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*OBSTACLE_GLOW, alpha), (r, r), r)
                self.screen.blit(s, (center_x - r, center_y - r))
            
            # 中心危险标志（X形）
            danger_color = OBSTACLE_COLOR
            line_width = 3
            offset = CELL_SIZE // 3
            
            # X 的两条线
            pygame.draw.line(
                self.screen, danger_color,
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y + offset),
                line_width
            )
            pygame.draw.line(
                self.screen, danger_color,
                (center_x + offset, center_y - offset),
                (center_x - offset, center_y + offset),
                line_width
            )
            
            # 四个方向的尖刺
            spike_length = CELL_SIZE // 2 - 2
            spike_width = 6
            
            # 上尖刺
            spike_top = [
                (center_x, center_y - spike_length),
                (center_x - spike_width, center_y),
                (center_x + spike_width, center_y)
            ]
            pygame.draw.polygon(self.screen, danger_color, spike_top)
            pygame.draw.polygon(self.screen, (255, 100, 255), spike_top, 2)
            
            # 下尖刺
            spike_bottom = [
                (center_x, center_y + spike_length),
                (center_x - spike_width, center_y),
                (center_x + spike_width, center_y)
            ]
            pygame.draw.polygon(self.screen, danger_color, spike_bottom)
            pygame.draw.polygon(self.screen, (255, 100, 255), spike_bottom, 2)
            
            # 左尖刺
            spike_left = [
                (center_x - spike_length, center_y),
                (center_x, center_y - spike_width),
                (center_x, center_y + spike_width)
            ]
            pygame.draw.polygon(self.screen, danger_color, spike_left)
            pygame.draw.polygon(self.screen, (255, 100, 255), spike_left, 2)
            
            # 右尖刺
            spike_right = [
                (center_x + spike_length, center_y),
                (center_x, center_y - spike_width),
                (center_x, center_y + spike_width)
            ]
            pygame.draw.polygon(self.screen, danger_color, spike_right)
            pygame.draw.polygon(self.screen, (255, 100, 255), spike_right, 2)
            
            # 中心圆点
            pygame.draw.circle(self.screen, (255, 0, 200), (center_x, center_y), 4)
            pygame.draw.circle(self.screen, (255, 150, 255), (center_x, center_y), 2)

    def draw_hud(self):
        """绘制HUD（赛博朋克风格，显示在屏幕上方）"""
        # 绘制半透明背景条
        hud_height = 30
        hud_surface = pygame.Surface((SCREEN_WIDTH, hud_height), pygame.SRCALPHA)
        hud_surface.fill((10, 5, 20, 200))  # 半透明深色背景
        self.screen.blit(hud_surface, (0, 0))
        
        # 左上角：分数 / 能量 / 幽灵剩余时间
        time_left = 0
        if self.ghost_mode:
            time_left = max(0, (self.ghost_end_time - pygame.time.get_ticks()) // 1000)

        now = pygame.time.get_ticks()
        score_now = int(self.score)
        score_part = f"分数: {score_now}"
        score_part_old = None
        score_part_new = None
        score_anim_active = (now < self.score_anim_end and now >= self.score_anim_start and self.score_anim_end > self.score_anim_start)
        if score_anim_active:
            score_part_old = f"分数: {int(self.score_anim_from)}"
            score_part_new = f"分数: {int(self.score_anim_to)}"
            score_part = score_part_new

        ghost_part = f"幽灵模式: {time_left}秒" if self.ghost_mode else "幽灵模式: 关闭"
        rest_part = f"能量: {self.energy}   {ghost_part}"

        text_height = self.font_small.render(score_part, True, TEXT_COLOR).get_height()
        hud_center_y = (HUD_HEIGHT - text_height) // 2

        score_x = 8
        if score_anim_active:
            p = (now - self.score_anim_start) / max(1, (self.score_anim_end - self.score_anim_start))
            p = max(0.0, min(1.0, p))
            dy = 10
            a_old = int(255 * (1.0 - p))
            a_new = int(255 * p)
            self.draw_text_with_glow_alpha(score_part_old, self.font_small, TEXT_COLOR, (score_x, hud_center_y + int(dy * p)), a_old)
            self.draw_text_with_glow_alpha(score_part_new, self.font_small, TEXT_COLOR, (score_x, hud_center_y - int(dy * (1.0 - p))), a_new)
            score_w = max(
                self.font_small.size(score_part_old)[0],
                self.font_small.size(score_part_new)[0],
            )
        else:
            self.draw_text_with_glow(score_part, self.font_small, TEXT_COLOR, (score_x, hud_center_y))
            score_w = self.font_small.size(score_part)[0]

        rest_x = score_x + score_w + 18
        self.draw_text_with_glow(rest_part, self.font_small, TEXT_COLOR, (rest_x, hud_center_y))

        elapsed_ms = self.get_run_elapsed_ms(now)
        mm = elapsed_ms // 60000
        ss = (elapsed_ms // 1000) % 60
        time_text = f"时间: {mm:02d}:{ss:02d}"
        time_w = self.font_small.size(time_text)[0]

        if now < self.score_burst_until:
            t = (now - self.score_burst_start) / max(1, (self.score_burst_until - self.score_burst_start))
            t = max(0.0, min(1.0, t))
            cx = score_x + int(score_w * 0.55)
            cy = hud_center_y + text_height // 2
            burst = pygame.Surface((SCREEN_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)
            base_a = int(160 * (1.0 - t))
            r0 = int(6 + 16 * t)
            for w in (10, 7, 4, 2):
                a = max(0, int(base_a * (w / 10)))
                pygame.draw.circle(burst, (255, 120, 80, a), (cx, cy), r0 + (10 - w), width=max(1, w // 2))
            core_a = max(0, int(110 * (1.0 - t)))
            pygame.draw.circle(burst, (255, 120, 80, core_a), (cx, cy), max(1, int(7 * (1.0 - t))))
            self.screen.blit(burst, (0, 0))

        # 连击显示（短暂）
        if now < self.combo_display_until and self.combo_multiplier > 1:
            combo_text = f"连击 x{self.combo_multiplier}"
            self.draw_text_with_glow(combo_text, self.font_small, (255, 255, 0), (SCREEN_WIDTH // 2 - 40, hud_center_y))

        # 右上角显示最高分
        if self.leaderboard:
            high_score_text = f"最高分: {self.leaderboard[0]['score']}"
            high_score_surf = self.font_small.render(high_score_text, True, (255, 215, 0))
            high_score_height = high_score_surf.get_height()
            high_score_y = (HUD_HEIGHT - high_score_height) // 2

            high_score_w = self.font_small.size(high_score_text)[0]
            high_score_x = max(8, SCREEN_WIDTH - 8 - high_score_w)
            time_x = max(8, high_score_x - 18 - time_w)
            self.draw_text_with_glow(time_text, self.font_small, (180, 220, 255), (time_x, hud_center_y))
            self.draw_text_with_glow(high_score_text, self.font_small, (255, 215, 0), (high_score_x, high_score_y))
        else:
            time_x = max(8, SCREEN_WIDTH - 8 - time_w)
            self.draw_text_with_glow(time_text, self.font_small, (180, 220, 255), (time_x, hud_center_y))

    def get_run_elapsed_ms(self, now: int) -> int:
        if not getattr(self, "run_start_time", 0):
            return 0
        end = self.run_end_time if self.run_end_time is not None else now
        paused_extra = 0
        if self.pause_started_at is not None:
            paused_extra = max(0, end - self.pause_started_at)
        return max(0, int(end - self.run_start_time - self.paused_time_accum - paused_extra))

    def get_help_pages(self):
        return [
            [
                "操作帮助 (H 打开/关闭)",
                "",
                "移动: 方向键 / WASD",
                "幽灵模式: 空格 (消耗能量)",
                "暂停: P",
                "排行榜: Tab (同时暂停)",
                "翻页: ← / →",
                "",
                "开始界面: 空格开始  ESC退出",
                "游戏结束: R重开  ESC回到开始",
            ],
            [
                "道具机制", 
                "",
                "磁铁: 吸附近食物/能量/炸弹到蛇头",
                "炸弹: 在蛇头处爆炸 (5x5范围清除)",
                "减肥药: 触发受伤效果(缩短身体)",
                "腐烂苹果: 反向控制 + 彩虹效果(短时间)",
                "传送门: 进入后传到对应出口",
            ],
            [
                "敌人 / Boss", 
                "",
                "幽灵猎手: 会靠近你，碰到会受伤",
                "影子蛇: 追踪移动，碰到会受伤",
                "Boss本体: 碰到直接死亡",
                "Boss子弹: 碰到会受伤并短暂慢动作",
                "",
                "提示: 受伤会闪烁并扣分/缩短身体",
            ],
        ]

    def draw_help_overlay(self):
        pages = self.get_help_pages()
        if not pages:
            return
        idx = max(0, min(int(self.help_page), len(pages) - 1))
        self.help_page = idx
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 5, 20, 230))
        self.screen.blit(overlay, (0, 0))

        center_x = SCREEN_WIDTH // 2
        title = f"帮助 {idx + 1}/{len(pages)}"
        self.draw_text_with_glow(title, self.font_big, (255, 255, 0), (center_x, 60), center=True)
        self.draw_text_with_glow("←/→ 翻页   H 关闭", self.font_small, (200, 200, 220), (center_x, 105), center=True)

        x = 60
        y = 150
        max_w = SCREEN_WIDTH - 120
        for line in pages[idx]:
            if not line:
                y += 14
                continue
            if self.font_small.size(line)[0] <= max_w:
                self.draw_text_with_glow(line, self.font_small, TEXT_COLOR, (x, y))
                y += 26
                continue

            words = list(line)
            buf = ""
            for ch in words:
                test = buf + ch
                if self.font_small.size(test)[0] > max_w and buf:
                    self.draw_text_with_glow(buf, self.font_small, TEXT_COLOR, (x, y))
                    y += 26
                    buf = ch
                else:
                    buf = test
            if buf:
                self.draw_text_with_glow(buf, self.font_small, TEXT_COLOR, (x, y))
                y += 26

    def draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 5, 20, 120))
        self.screen.blit(overlay, (0, 0))
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        self.draw_text_with_glow("PAUSED", self.font_big, (255, 255, 0), (center_x, center_y - 20), center=True)
        self.draw_text_with_glow("按 P 继续", self.font_small, (200, 200, 220), (center_x, center_y + 30), center=True)

    def draw_game_over(self):
        """绘制Game Over界面（赛博朋克风格）"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((10, 5, 20))
        self.screen.blit(overlay, (0, 0))

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        # 标题带闪烁效果
        blink = (pygame.time.get_ticks() // 500) % 2
        title_color = (255, 0, 127) if blink else (255, 50, 150)
        self.draw_text_with_glow("游戏结束", self.font_big, title_color, (center_x, center_y - 60), center=True)
        
        self.draw_text_with_glow(self.game_over_reason, self.font_small, TEXT_COLOR, (center_x, center_y - 10), center=True)
        self.draw_text_with_glow(f"最终得分: {self.score}", self.font_small, (255, 255, 0), (center_x, center_y + 60), center=True)
        
        # 显示最高分（在中间区域，字体更大，和开始界面一样，位置再往下一点）
        if self.leaderboard:
            high_score_text = f"最高分: {self.leaderboard[0]['score']} ({self.leaderboard[0]['name']})"
            self.draw_text_with_glow(high_score_text, self.font_medium, (255, 215, 0), (center_x, center_y + 90), center=True)
        else:
            self.draw_text_with_glow("暂无最高分", self.font_medium, (150, 150, 150), (center_x, center_y + 90), center=True)
        
        # 提示移到屏幕下方
        self.draw_text_with_glow("按 R 重新开始，Tab 查看排行榜，ESC 返回开始界面", self.font_small, (200, 200, 220), (center_x, SCREEN_HEIGHT - 40), center=True)

    def draw_start_screen(self):
        """绘制开始界面（赛博朋克风格）"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(210)
        overlay.fill((10, 5, 20))
        self.screen.blit(overlay, (0, 0))

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        # 标题带脉冲效果
        pulse = abs((pygame.time.get_ticks() % 2000) / 1000 - 1)
        title_color = (
            int(255),
            int(100 + pulse * 100),
            int(200 + pulse * 55)
        )
        self.draw_text_with_glow("技能贪吃蛇", self.font_xlarge, title_color, (center_x, center_y - 60), center=True)
        self.draw_text_with_glow("幽灵模式 + 动态障碍", self.font_small, TEXT_COLOR, (center_x, center_y - 10), center=True)
        
        # 显示最高分（在中间区域，字体更大，位置再往下一点）
        if self.leaderboard:
            high_score_text = f"最高分: {self.leaderboard[0]['score']} ({self.leaderboard[0]['name']})"
            self.draw_text_with_glow(high_score_text, self.font_medium, (255, 215, 0), (center_x, center_y + 80), center=True)
        else:
            self.draw_text_with_glow("暂无记录", self.font_medium, (150, 150, 150), (center_x, center_y + 40), center=True)
        
        # 提示文字移到屏幕下方（带闪烁）
        blink = (pygame.time.get_ticks() // 800) % 2
        tip_alpha = 220 if blink else 150
        tip_color = (tip_alpha, tip_alpha, 255)
        # 按空格开始提示
        self.draw_text_with_glow("按空格键开始 (ESC 退出)", self.font_small, tip_color, (center_x, SCREEN_HEIGHT - 60), center=True)
        # 操作提示
        self.draw_text_with_glow("方向键/WASD 移动；空格开启幽灵模式；Tab 暂停并查看排行榜", self.font_small, (190, 190, 210), (center_x, SCREEN_HEIGHT - 35), center=True)

    def draw_leaderboard(self):
        """绘制排行榜界面（赛博朋克风格）"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(230)
        overlay.fill((10, 5, 20))
        self.screen.blit(overlay, (0, 0))

        center_x = SCREEN_WIDTH // 2
        self.draw_text_with_glow("排行榜 TOP 10", self.font_big, (255, 215, 0), (center_x, 40), center=True)
        
        # 只在游戏进行中时显示暂停提示
        if self.started and not self.game_over:
            self.draw_text_with_glow("(游戏已暂停)", self.font_small, (180, 180, 210), (center_x, 75), center=True)
            y_start = 110
        else:
            y_start = 90

        if not self.leaderboard:
            self.draw_text_with_glow("暂无记录", self.font_small, TEXT_COLOR, (center_x, y_start + 40), center=True)
        else:
            y_offset = y_start
            current_time = pygame.time.get_ticks()
            for i, entry in enumerate(self.leaderboard[:MAX_LEADERBOARD_ENTRIES]):
                rank_text = f"{i+1}. {entry['name']}"
                score_text = f"{entry['score']}"
                
                # 前三名用不同颜色和特效
                if i == 0:
                    # 第一名：金色，闪烁效果（与第二名交换）
                    blink = (current_time // 300) % 2
                    if blink:
                        color = (255, 215, 0)  # 亮金色
                    else:
                        color = (200, 180, 0)  # 暗金色
                    # 添加发光边框
                    for glow_offset in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                        glow_surf = self.font_small.render(rank_text, True, (255, 200, 50))
                        self.screen.blit(glow_surf, (center_x - 150 + glow_offset[0], y_offset + glow_offset[1]))
                        glow_surf2 = self.font_small.render(score_text, True, (255, 200, 50))
                        self.screen.blit(glow_surf2, (center_x + 100 + glow_offset[0], y_offset + glow_offset[1]))
                elif i == 1:
                    # 第二名：紫色，脉冲效果（与第一名交换，颜色改为紫色）
                    pulse = abs((current_time % 1500) / 750 - 1)
                    color = (
                        int(200 + pulse * 55),
                        int(100 + pulse * 100),
                        int(255)
                    )
                    # 添加额外的发光效果
                    for glow_offset in range(3, 0, -1):
                        glow_alpha = int(40 * pulse / glow_offset)
                        glow_color = tuple(min(255, c + 50) for c in color)
                        glow_surf = self.font_small.render(rank_text, True, glow_color)
                        glow_surf.set_alpha(glow_alpha)
                        self.screen.blit(glow_surf, (center_x - 150 - glow_offset, y_offset - glow_offset))
                        glow_surf2 = self.font_small.render(score_text, True, glow_color)
                        glow_surf2.set_alpha(glow_alpha)
                        self.screen.blit(glow_surf2, (center_x + 100 - glow_offset, y_offset - glow_offset))
                elif i == 2:
                    # 第三名：品红，无特效
                    color = (255, 0, 255)  # 品红色
                else:
                    color = TEXT_COLOR

                self.draw_text_with_glow(rank_text, self.font_small, color, (center_x - 150, y_offset))
                self.draw_text_with_glow(score_text, self.font_small, color, (center_x + 100, y_offset))
                y_offset += 30

        self.draw_text_with_glow("按 Tab 返回", self.font_small, (200, 200, 220), (center_x, SCREEN_HEIGHT - 40), center=True)

    def draw_bottom_bar(self):
        """绘制底部技能提示栏"""
        if self.energy > 0 and not self.game_over:
            # 只有在有能量且游戏进行中时显示
            bar_y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT
            
            # 绘制半透明背景
            bar_surface = pygame.Surface((SCREEN_WIDTH, BOTTOM_BAR_HEIGHT), pygame.SRCALPHA)
            bar_surface.fill((10, 5, 20, 180))
            self.screen.blit(bar_surface, (0, bar_y))

            # 提示文字闪烁
            blink = (pygame.time.get_ticks() // 400) % 2
            if blink:
                prompt_text = "按空格使用幽灵模式技能"
                prompt_color = (255, 255, 0) # Yellow
                center_x = SCREEN_WIDTH // 2
                center_y = bar_y + BOTTOM_BAR_HEIGHT // 2
                self.draw_text_with_glow(prompt_text, self.font_small, prompt_color, (center_x, center_y), center=True)

    def draw_name_input(self):
        """绘制输入名字界面（赛博朋克风格）"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((10, 5, 20))
        self.screen.blit(overlay, (0, 0))

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        # 恭喜文字带闪烁
        blink = (pygame.time.get_ticks() // 300) % 2
        congrats_color = (255, 215, 0) if blink else (255, 255, 0)
        self.draw_text_with_glow("新纪录！", self.font_big, congrats_color, (center_x, center_y - 80), center=True)
        self.draw_text_with_glow("请输入你的名字：", self.font_small, TEXT_COLOR, (center_x, center_y - 30), center=True)
        
        # 输入框（霓虹边框）
        input_box_width = 300
        input_box_height = 40
        input_box = pygame.Rect(center_x - input_box_width//2, center_y, input_box_width, input_box_height)
        
        # 绘制发光边框
        for offset in range(3, 0, -1):
            glow_rect = input_box.inflate(offset * 2, offset * 2)
            pygame.draw.rect(self.screen, (0, 100, 200, 80 // offset), glow_rect, 2, border_radius=5)
        
        pygame.draw.rect(self.screen, (30, 20, 50), input_box, border_radius=3)
        pygame.draw.rect(self.screen, (0, 255, 255), input_box, 2, border_radius=3)
        
        # 显示输入的文字
        cursor_blink = "_" if (pygame.time.get_ticks() // 500) % 2 else " "
        self.draw_text_with_glow(self.player_name_input + cursor_blink, self.font_small, (255, 255, 255), (input_box.x + 10, input_box.y + 10))

        self.draw_text_with_glow("回车确认，ESC 跳过", self.font_small, (200, 200, 220), (center_x, center_y + 60), center=True)

    # -------------------- 主循环 --------------------
    def run(self):
        while True:
            self.handle_input()

            # 启动画面：未开始时仅渲染，不更新逻辑
            if not self.started:
                self.screen.fill(BG_COLOR)
                self.draw_grid()
                self.draw_obstacles()
                self.draw_foods()
                self.draw_snake()
                self.draw_hud()
                self.draw_start_screen()
                
                # 启动画面也可以查看排行榜
                if self.show_leaderboard:
                    self.draw_leaderboard()

                if self.show_help:
                    self.draw_help_overlay()
                
                pygame.display.flip()
                self.clock.tick(self.fps)
                continue

            # Game Over input is now handled in handle_input()
            if self.game_over and not self.entering_name:
                pass # All input is handled in handle_input() now

            # 只在游戏进行中且未暂停时更新逻辑
            if not self.game_over and not self.paused:
                self.update()
            
            # 粒子系统始终更新（即使游戏暂停）
            self.particle_system.update()

            self.screen.fill(BG_COLOR)
            self.draw_grid()
            self.draw_obstacles()
            self.draw_fog_zone()
            self.draw_foods()
            self.draw_items()
            self.draw_portals()
            self.draw_spikes()
            self.draw_shadow_snakes()
            self.draw_ghost_hunters()
            self.draw_boss()
            self.draw_magnet_flights()
            self.draw_snake()
            
            # 绘制粒子特效（在蛇上面）
            self.particle_system.draw(self.screen)

            self.draw_bomb_explosions()

            self.draw_shockwave()
            self.draw_boss_kill_freeze_overlay()
            self.draw_boss_kill_flash()
            
            self.draw_hud()
            self.draw_bottom_bar() # Draw the new bottom bar

            # 迷雾遮罩（放在HUD前后都可，这里放HUD后，保证HUD可见）
            self.draw_fog()

            if (not self.game_over) and self.paused and (not self.show_leaderboard) and (not self.entering_name):
                self.draw_pause_overlay()

            if self.game_over:
                self.draw_game_over()

            # 显示排行榜（覆盖在游戏画面上）
            if self.show_leaderboard:
                self.draw_leaderboard()

            # 显示名字输入界面（覆盖在 game over 上）
            if self.entering_name:
                self.draw_name_input()

            if self.show_help:
                self.draw_help_overlay()

            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == "__main__":
    # 防止多次导入时自动运行
    game = SnakeGame()
    game.run()


