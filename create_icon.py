import pygame
from PIL import Image

# --- 配置 ---
SNAKE_HEAD_COLOR = (255, 0, 255)    # 品红霓虹
SNAKE_COLOR = (0, 255, 255)         # 青色霓虹
BG_COLOR = (10, 5, 20)              # 深紫黑背景
ICON_SIZE = 256

def create_icon_surface():
    """使用 Pygame 绘制图标表面"""
    pygame.init()
    surface = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))  # 透明背景

    center = ICON_SIZE // 2
    radius = ICON_SIZE // 3

    # 绘制蛇头（圆球状，带光泽）
    head_color = SNAKE_HEAD_COLOR
    pygame.draw.circle(surface, head_color, (center, center), radius)

    # 高光
    highlight_radius = int(radius * 0.6)
    highlight_offset = int(radius * 0.3)
    highlight_color = tuple(min(c + 80, 255) for c in head_color)
    pygame.draw.circle(
        surface, (*highlight_color, 200),
        (center - highlight_offset, center - highlight_offset),
        highlight_radius
    )
    # 顶部小高光
    small_highlight_radius = int(radius * 0.3)
    pygame.draw.circle(
        surface, (255, 255, 255, 180),
        (center - int(radius * 0.4), center - int(radius * 0.4)),
        small_highlight_radius
    )

    # 眼睛
    eye_size = max(4, radius // 4)
    eye_forward = radius // 2
    eye_side = radius // 3
    eye1_pos = (center + eye_forward, center - eye_side)
    eye2_pos = (center + eye_forward, center + eye_side)
    pygame.draw.circle(surface, (255, 255, 255), eye1_pos, eye_size)
    pygame.draw.circle(surface, (255, 255, 255), eye2_pos, eye_size)
    pupil_size = max(2, eye_size // 2)
    pygame.draw.circle(surface, (0, 0, 0), eye1_pos, pupil_size)
    pygame.draw.circle(surface, (0, 0, 0), eye2_pos, pupil_size)

    pygame.quit()
    return surface

def save_as_ico_and_png(surface, ico_filename="snake_icon.ico", png_filename="snake_icon.png"):
    """将 Pygame Surface 保存为 .ico 和 .png 文件"""
    # 1. 保存为 PNG
    pygame.image.save(surface, png_filename)
    print(f"PNG 图标 '{png_filename}' 已成功创建！")

    # 2. 将 Pygame Surface 转换为 Pillow Image 并保存为 ICO
    img_str = pygame.image.tostring(surface, 'RGBA', False)
    img = Image.frombytes('RGBA', (ICON_SIZE, ICON_SIZE), img_str)

    # 指定需要的图标尺寸
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_filename, format='ICO', sizes=sizes)
    print(f"ICO 图标 '{ico_filename}' 已成功创建！")

if __name__ == "__main__":
    icon_surface = create_icon_surface()
    save_as_ico_and_png(icon_surface)
