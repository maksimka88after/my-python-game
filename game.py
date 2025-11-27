"""
Образовательная игра на Python 3.12
Разработана в рамках индивидуального итогового проекта
МБОУ "Гимназия №75", г. Казань
"""

import pygame
import sys
import math
from typing import List, Tuple, Dict, Any

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
FPS = 60

# Цвета
class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 120, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    BROWN = (139, 69, 19)
    GRAY = (128, 128, 128)
    LIGHT_BLUE = (173, 216, 230)
    PURPLE = (128, 0, 128)
    SKIN = (255, 220, 177)
    DARK_GREEN = (0, 100, 0)
    DARK_RED = (139, 0, 0)
    DARK_BLUE = (0, 0, 139)
    GOLD = (255, 215, 0)
    LIGHT_GREEN = (144, 238, 144)  # Светло-зеленый для фона инструкций

# Создание окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Платформер на Python 3.12")
clock = pygame.time.Clock()

# Инициализация шрифтов
try:
    font_large = pygame.font.SysFont('Arial', 36, bold=True)
    font_medium = pygame.font.SysFont('Arial', 24)
    font_small = pygame.font.SysFont('Arial', 18)
except:
    font_large = pygame.font.Font(None, 36)
    font_medium = pygame.font.Font(None, 24)
    font_small = pygame.font.Font(None, 18)


class Player(pygame.sprite.Sprite):
    """Класс игрока с физикой движения и анимацией"""

    def __init__(self, start_x: int = 100, start_y: int = None):
        super().__init__()
        self.image = pygame.Surface((35, 50), pygame.SRCALPHA)
        self._draw_character()
        self.rect = self.image.get_rect()

        # Устанавливаем позицию игрока
        if start_y is None:
            start_y = HEIGHT - 100
        self.rect.center = (start_x, start_y)

        self.velocity_y = 0.0
        self.jumping = False
        self.speed = 4
        self.score = 0
        self.lives = 2
        self.invincible = False
        self.invincible_timer = 0

    def _draw_character(self) -> None:
        """Отрисовка персонажа"""
        # Тело
        pygame.draw.rect(self.image, Colors.BLUE, (5, 10, 25, 30), border_radius=5)
        # Голова
        pygame.draw.circle(self.image, Colors.SKIN, (17, 8), 8)
        # Глаза
        pygame.draw.circle(self.image, Colors.BLACK, (13, 6), 2)
        pygame.draw.circle(self.image, Colors.BLACK, (21, 6), 2)
        # Ноги
        pygame.draw.rect(self.image, Colors.BROWN, (8, 40, 8, 10))
        pygame.draw.rect(self.image, Colors.BROWN, (19, 40, 8, 10))

    def update(self) -> None:
        """Обновление физики персонажа"""
        # Гравитация
        self.velocity_y += 0.5
        self.rect.y += int(self.velocity_y)

        # Ограничение падения
        if self.rect.bottom > HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.jumping = False
            self.velocity_y = 0

        # Ограничение выхода за границы
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)

        # Обновление таймера неуязвимости
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def jump(self) -> None:
        """Прыжок персонажа"""
        if not self.jumping:
            self.velocity_y = -12
            self.jumping = True

    def move_left(self) -> None:
        """Движение влево"""
        self.rect.x -= self.speed

    def move_right(self) -> None:
        """Движение вправо"""
        self.rect.x += self.speed

    def take_damage(self) -> bool:
        """Получение урона, возвращает True если игрок умер"""
        if not self.invincible:
            self.lives -= 1
            self.invincible = True
            self.invincible_timer = 60
            return self.lives <= 0
        return False


class Coin(pygame.sprite.Sprite):
    """Класс собираемой монетки с анимацией"""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((25, 25), pygame.SRCALPHA)
        self._draw_coin()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.original_y = y

    def _draw_coin(self) -> None:
        """Отрисовка монетки"""
        # Внешний круг
        pygame.draw.circle(self.image, Colors.YELLOW, (12, 12), 12)
        # Внутренний круг
        pygame.draw.circle(self.image, (255, 215, 0), (12, 12), 8)
        # Блики
        pygame.draw.ellipse(self.image, (255, 255, 200), (5, 5, 8, 4))

    def update(self) -> None:
        """Анимация подпрыгивания"""
        self.rect.y = self.original_y + int(math.sin(pygame.time.get_ticks() * 0.005) * 3)


class Enemy(pygame.sprite.Sprite):
    """Класс врага с патрулированием по платформе"""

    def __init__(self, platform_rect: pygame.Rect, speed: int = 2, custom_bounds: Tuple[int, int] = None, color: Tuple[int, int, int] = Colors.RED):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.color = color
        self._draw_enemy()
        self.rect = self.image.get_rect()

        # Позиционируем врага на платформе
        self.platform_rect = platform_rect
        self.rect.bottom = platform_rect.top
        self.rect.centerx = platform_rect.centerx

        # Уменьшаем скорость на 30%
        self.speed = max(1, int(speed * 0.7))
        self.direction = 1

        # Настраиваем границы патрулирования
        if custom_bounds:
            self.left_bound, self.right_bound = custom_bounds
        else:
            self.left_bound = platform_rect.left + 20
            self.right_bound = platform_rect.right - 20

    def _draw_enemy(self) -> None:
        """Отрисовка врага"""
        # Тело
        pygame.draw.circle(self.image, self.color, (20, 20), 18)
        # Глаза
        pygame.draw.circle(self.image, Colors.WHITE, (14, 14), 5)
        pygame.draw.circle(self.image, Colors.WHITE, (26, 14), 5)
        pygame.draw.circle(self.image, Colors.BLACK, (14, 14), 2)
        pygame.draw.circle(self.image, Colors.BLACK, (26, 14), 2)
        # Рот
        pygame.draw.arc(self.image, Colors.BLACK, (10, 18, 20, 15), 0, math.pi, 2)

    def update(self) -> None:
        """Обновление патрулирования по платформе"""
        self.rect.x += self.speed * self.direction

        # Изменение направления при достижении границ платформы
        if self.rect.right >= self.right_bound or self.rect.left <= self.left_bound:
            self.direction *= -1

        # Гарантируем, что враг остается на платформе
        self.rect.bottom = self.platform_rect.top


class Platform(pygame.sprite.Sprite):
    """Класс игровой платформы"""

    def __init__(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int] = Colors.GRAY, border_color: Tuple[int, int, int] = Colors.BROWN):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.color = color
        self.border_color = border_color
        self._draw_platform(width, height)

    def _draw_platform(self, width: int, height: int) -> None:
        """Отрисовка платформы с текстурой"""
        self.image.fill(self.color)
        pygame.draw.rect(self.image, self.border_color, (0, 0, width, height), 2)
        # Текстура платформы
        for i in range(0, width, 15):
            pygame.draw.line(self.image, (max(0, self.color[0]-30), max(0, self.color[1]-30), max(0, self.color[2]-30)),
                           (i, 0), (i, height), 1)


class Ground(pygame.sprite.Sprite):
    """Класс земли/основания"""

    def __init__(self, x: int, y: int, width: int, height: int, ground_color: Tuple[int, int, int] = Colors.BROWN, grass_color: Tuple[int, int, int] = Colors.GREEN):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.ground_color = ground_color
        self.grass_color = grass_color
        self._draw_ground(width, height)

    def _draw_ground(self, width: int, height: int) -> None:
        """Отрисовка земли с травой"""
        self.image.fill(self.ground_color)
        pygame.draw.rect(self.image, self.grass_color, (0, 0, width, 10))
        # Детали травы
        for i in range(0, width, 20):
            pygame.draw.line(self.image, (max(0, self.grass_color[0]-50), max(0, self.grass_color[1]-50), max(0, self.grass_color[2]-50)),
                           (i, 0), (i + 10, -5), 2)


class FinishFlag(pygame.sprite.Sprite):
    """Класс финишного флага"""

    def __init__(self, x: int, y: int, flag_color: Tuple[int, int, int] = Colors.PURPLE):
        super().__init__()
        self.image = pygame.Surface((30, 50), pygame.SRCALPHA)
        self.flag_color = flag_color
        self._draw_flag()
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x

    def _draw_flag(self) -> None:
        """Отрисовка флага"""
        # Флагшток
        pygame.draw.rect(self.image, Colors.BROWN, (12, 0, 6, 50))
        # Флаг
        flag_points = [(18, 10), (18, 30), (28, 20)]
        pygame.draw.polygon(self.image, self.flag_color, flag_points)


class Game:
    """Основной класс игры"""

    def __init__(self):
        self.reset_game_state()

    def reset_game_state(self):
        """Полный сброс состояния игры"""
        self.player: Player = None
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.finish_flag = None
        self.coin_positions: List[Tuple[int, int]] = []
        self.game_over = False
        self.game_won = False
        self.current_level = 1
        self.in_menu = True
        self.level_complete = False

    def create_level_1(self) -> None:
        """Создание первого игрового уровня (дневной)"""
        # Сброс состояния перед созданием уровня
        self.reset_game_state()
        self.in_menu = False
        self.current_level = 1

        # Создание игрока
        self.player = Player()
        self.all_sprites.add(self.player)

        # Создание земли
        ground = Ground(0, HEIGHT - 50, WIDTH, 50)
        self.platforms.add(ground)
        self.all_sprites.add(ground)

        # Платформы
        platform_data = [
            (100, 450, 200, 20),
            (400, 400, 150, 20),
            (200, 300, 100, 20),
            (600, 450, 150, 20),
            (500, 250, 100, 20)
        ]

        platforms_list = []
        for x, y, width, height in platform_data:
            platform = Platform(x, y, width, height)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
            platforms_list.append(platform)

        # Монетки (убраны те, что находятся прямо друг над другом)
        self.coin_positions = [
            (150, 420), (250, 420), (350, 370),
            (450, 370), (550, 420), (650, 420),
            # Убраны: (250, 270), (150, 370),
            (700, 420),
            (100, 520), (300, 520), (400, 420),
            (650, 370)  # Оставлена только одна из двух монеток на этой позиции
        ]

        for x, y in self.coin_positions:
            coin = Coin(x, y)
            self.coins.add(coin)
            self.all_sprites.add(coin)

        # Враги
        enemy_data = [
            (platforms_list[0].rect, 2, None, Colors.RED),
            (platforms_list[1].rect, 3, None, Colors.RED),
            (platforms_list[3].rect, 2, None, Colors.RED)
        ]

        for platform_rect, speed, custom_bounds, color in enemy_data:
            enemy = Enemy(platform_rect, speed, custom_bounds, color)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        # Финишный флаг
        self.finish_flag = FinishFlag(550, 250, Colors.PURPLE)
        self.all_sprites.add(self.finish_flag)

    def create_level_2(self) -> None:
        """Создание второго игрового уровня (ночной)"""
        # Сброс состояния перед созданием уровня
        self.reset_game_state()
        self.in_menu = False
        self.current_level = 2

        # Создание игрока (появляется слева от первой платформы на земле)
        self.player = Player(start_x=50, start_y=HEIGHT - 100)
        self.all_sprites.add(self.player)

        # Создание земли (темные цвета)
        ground = Ground(0, HEIGHT - 50, WIDTH, 50, Colors.DARK_RED, Colors.DARK_GREEN)
        self.platforms.add(ground)
        self.all_sprites.add(ground)

        # Платформы (поднята самая нижняя платформа)
        platform_data = [
            (100, 480, 200, 20),    # Левая нижняя (поднята с 500 до 480)
            (500, 450, 200, 20),    # Правая нижняя
            (200, 350, 150, 20),    # Левая средняя
            (450, 250, 180, 20)     # Правая верхняя (финиш)
        ]

        platforms_list = []
        for x, y, width, height in platform_data:
            platform = Platform(x, y, width, height, Colors.DARK_BLUE, Colors.BLUE)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
            platforms_list.append(platform)

        # Монетки (убраны две монетки у финиша)
        self.coin_positions = [
            (150, 450), (250, 450),  # На первой платформе (координаты обновлены)
            (550, 420), (650, 420),  # На второй платформе
            (250, 320), (300, 320),  # На третьей платформе
            # Убраны две монетки у финиша: (500, 220), (550, 220)
            (350, 520),              # На земле
            (750, 520),              # На земле
            (400, 400),              # Между платформами
            (300, 200)               # В воздухе
        ]

        for x, y in self.coin_positions:
            coin = Coin(x, y)
            self.coins.add(coin)
            self.all_sprites.add(coin)

        # Враги
        enemy_data = [
            (platforms_list[0].rect, 2, None, Colors.ORANGE),
            (platforms_list[1].rect, 3, None, Colors.ORANGE),
            (platforms_list[2].rect, 2, None, Colors.ORANGE)
        ]

        for platform_rect, speed, custom_bounds, color in enemy_data:
            enemy = Enemy(platform_rect, speed, custom_bounds, color)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        # Финишный флаг
        self.finish_flag = FinishFlag(530, 250, Colors.GOLD)
        self.all_sprites.add(self.finish_flag)

    def draw_background(self) -> None:
        """Отрисовка фона в зависимости от уровня"""
        if self.current_level == 1:
            # Дневной фон для уровня 1
            screen.fill(Colors.LIGHT_BLUE)

            # Облака
            current_time = pygame.time.get_ticks()
            for i in range(5):
                x = (current_time // 50 + i * 200) % (WIDTH + 200) - 100
                y = 80 + i * 40
                pygame.draw.ellipse(screen, Colors.WHITE, (x, y, 100, 40))
                pygame.draw.ellipse(screen, Colors.WHITE, (x + 30, y - 20, 80, 40))
                pygame.draw.ellipse(screen, Colors.WHITE, (x + 60, y, 70, 30))

            # Солнце
            pygame.draw.circle(screen, (255, 255, 100), (700, 80), 40)

        else:
            # Ночной фон для уровня 2 (сделан светлее)
            screen.fill((40, 40, 100))  # Более светлый темно-синий ночное небо

            # Звезды
            star_positions = [(100, 50), (200, 80), (350, 40), (450, 70),
                            (600, 30), (700, 60), (750, 90), (300, 120)]
            for x, y in star_positions:
                pygame.draw.circle(screen, Colors.WHITE, (x, y), 2)
                # Мерцание звезд
                if pygame.time.get_ticks() % 1000 < 500:
                    pygame.draw.circle(screen, Colors.YELLOW, (x, y), 1)

            # Луна
            pygame.draw.circle(screen, (220, 220, 220), (100, 80), 30)
            pygame.draw.circle(screen, (40, 40, 100), (115, 65), 25)

    def draw_menu(self) -> None:
        """Отрисовка главного меню"""
        # Фон меню
        screen.fill((30, 30, 80))

        # Заголовок
        title_text = font_large.render("ВЫБЕРИТЕ УРОВЕНЬ", True, Colors.WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Информация об уровнях
        level1_text = font_medium.render("Уровень 1: Дневной мир", True, Colors.LIGHT_BLUE)
        level2_text = font_medium.render("Уровень 2: Ночное приключение", True, Colors.ORANGE)

        screen.blit(level1_text, (WIDTH // 2 - level1_text.get_width() // 2, 180))
        screen.blit(level2_text, (WIDTH // 2 - level2_text.get_width() // 2, 220))

        # Кнопки выбора уровня
        pygame.draw.rect(screen, Colors.BLUE, (WIDTH // 2 - 150, 280, 300, 60), border_radius=10)
        pygame.draw.rect(screen, Colors.DARK_BLUE, (WIDTH // 2 - 150, 360, 300, 60), border_radius=10)

        level1_btn = font_medium.render("ИГРАТЬ УРОВЕНЬ 1", True, Colors.WHITE)
        level2_btn = font_medium.render("ИГРАТЬ УРОВЕНЬ 2", True, Colors.WHITE)

        screen.blit(level1_btn, (WIDTH // 2 - level1_btn.get_width() // 2, 300))
        screen.blit(level2_btn, (WIDTH // 2 - level2_btn.get_width() // 2, 380))

        # Управление (перекрашено в цвет травы)
        controls_bg = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, Colors.LIGHT_GREEN, controls_bg)

        controls_text = font_small.render("Управление: ← → двигаться, ↑ прыжок, R перезапуск уровня, ESC меню", True, Colors.BLACK)
        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT - 30))

        # Если уровень завершен, показываем сообщение
        if self.level_complete:
            complete_text = font_medium.render("Уровень завершен! Выберите следующий уровень", True, Colors.GREEN)
            screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, 450))

    def handle_menu_events(self) -> bool:
        """Обработка событий в меню"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Проверка нажатия на кнопку уровня 1
                if WIDTH // 2 - 150 <= x <= WIDTH // 2 + 150 and 280 <= y <= 340:
                    self.create_level_1()
                # Проверка нажатия на кнопку уровня 2
                elif WIDTH // 2 - 150 <= x <= WIDTH // 2 + 150 and 360 <= y <= 420:
                    self.create_level_2()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Предотвращаем выход из меню по ESC
                pass
        return True

    def handle_events(self) -> bool:
        """Обработка событий игры"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and not self.game_over and not self.game_won:
                    self.player.jump()
                if event.key == pygame.K_r and (self.game_over or self.game_won):
                    self.restart_level()
                if event.key == pygame.K_ESCAPE:  # Возврат в меню по ESC
                    self.in_menu = True
                    # Не сбрасываем level_complete при выходе в меню
        return True

    def check_collisions(self) -> None:
        """Проверка всех столкновений в игре"""
        # Проверка столкновений с платформами
        platform_hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
        on_ground = False

        for platform in platform_hits:
            # Игнорируем столкновение с землей при проверке прыжка
            if isinstance(platform, Ground):
                continue

            # Столкновение сверху (игрок падает на платформу)
            if (self.player.velocity_y > 0 and
                    self.player.rect.bottom > platform.rect.top and
                    self.player.rect.top < platform.rect.top):
                self.player.rect.bottom = platform.rect.top
                self.player.jumping = False
                self.player.velocity_y = 0
                on_ground = True

            # Столкновение снизу (игрок ударяется головой о платформу)
            elif (self.player.velocity_y < 0 and
                  self.player.rect.top < platform.rect.bottom and
                  self.player.rect.bottom > platform.rect.bottom):
                self.player.rect.top = platform.rect.bottom
                self.player.velocity_y = 0

        # Если игрок не на земле и не на платформе, он в воздухе
        if not on_ground and self.player.rect.bottom < HEIGHT - 50:
            self.player.jumping = True

    def update_game_state(self) -> None:
        """Обновление состояния игры"""
        if self.game_over or self.game_won or self.in_menu:
            return

        # Обработка управления
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.move_left()
        if keys[pygame.K_RIGHT]:
            self.player.move_right()

        # Обновление объектов
        self.player.update()
        self.enemies.update()
        self.coins.update()

        # Проверка столкновений
        self.check_collisions()

        # Сбор монеток
        coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
        for _ in coin_hits:
            self.player.score += 10

        # Столкновение с врагами
        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if enemy_hits:
            if self.player.take_damage():
                self.game_over = True

        # Проверка достижения финиша
        if self.finish_flag and pygame.sprite.collide_rect(self.player, self.finish_flag):
            self.game_won = True
            self.level_complete = True

    def draw_ui(self) -> None:
        """Отрисовка пользовательского интерфейса"""
        # Счет
        score_text = font_medium.render(f"Очки: {self.player.score}", True, Colors.WHITE if self.current_level == 2 else Colors.BLACK)
        screen.blit(score_text, (10, 10))

        # Жизни
        lives_text = font_medium.render(f"Жизни: {self.player.lives}", True, Colors.RED)
        screen.blit(lives_text, (WIDTH - 120, 10))

        # Уровень
        level_text = font_medium.render(f"Уровень: {self.current_level}", True, Colors.WHITE if self.current_level == 2 else Colors.BLACK)
        screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 10))

        # Управление (перекрашено в цвет травы)
        controls_bg = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, Colors.LIGHT_GREEN, controls_bg)

        controls_text = font_small.render(
            "Управление: ← → двигаться, ↑ прыжок, R перезапуск, ESC меню",
            True, Colors.BLACK
        )
        screen.blit(controls_text, (10, HEIGHT - 30))

        # Мигание при неуязвимости
        if self.player.invincible and self.player.invincible_timer % 10 < 5:
            blink_surface = pygame.Surface((self.player.rect.width, self.player.rect.height), pygame.SRCALPHA)
            blink_surface.fill((255, 255, 255, 128))
            screen.blit(blink_surface, self.player.rect)

    def draw_game_over(self) -> None:
        """Отрисовка экрана завершения игры"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        game_over_text = font_large.render("ИГРА ОКОНЧЕНА!", True, Colors.RED)
        restart_text = font_medium.render("Нажми R для перезапуска уровня", True, Colors.WHITE)
        menu_text = font_medium.render("Нажми ESC для выхода в меню", True, Colors.WHITE)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 50))

    def draw_victory(self) -> None:
        """Отрисовка экрана победы"""
        # Определение количества звезд
        total_coins = len(self.coin_positions)
        collected_coins = self.player.score // 10

        if collected_coins >= total_coins * 0.8:
            stars = 3
        elif collected_coins >= total_coins * 0.5:
            stars = 2
        else:
            stars = 1

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Тексты победы
        texts = [
            font_large.render("УРОВЕНЬ ПРОЙДЕН!", True, Colors.GREEN),
            font_medium.render(f"Звезды: {stars}", True, Colors.YELLOW),
            font_medium.render(f"Собрано монет: {collected_coins}/{total_coins}", True, Colors.WHITE),
            font_medium.render("Нажми ESC для выхода в меню", True, Colors.WHITE),
            font_medium.render("Нажми R для перезапуска уровня", True, Colors.WHITE)
        ]

        # Расположение текстов
        y_positions = [HEIGHT // 2 - 80, HEIGHT // 2 - 30, HEIGHT // 2 + 10, HEIGHT // 2 + 50, HEIGHT // 2 + 90]
        for text, y in zip(texts, y_positions):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))

        # Отрисовка звезд
        for i in range(stars):
            star_x = WIDTH // 2 - (stars * 25) + i * 50
            self._draw_star(star_x, HEIGHT // 2 + 130)

    def _draw_star(self, x: int, y: int) -> None:
        """Отрисовка звезды"""
        points = [
            (x, y), (x + 10, y - 20), (x + 20, y),
            (x + 5, y + 10), (x + 15, y + 30),
            (x, y + 15), (x - 15, y + 30),
            (x - 5, y + 10), (x - 20, y),
            (x - 10, y - 20)
        ]
        pygame.draw.polygon(screen, Colors.YELLOW, points)

    def restart_level(self) -> None:
        """Перезапуск текущего уровня"""
        if self.current_level == 1:
            self.create_level_1()
        else:
            self.create_level_2()

    def run(self) -> None:
        """Основной игровой цикл"""
        running = True

        while running:
            clock.tick(FPS)

            if self.in_menu:
                # Режим меню
                running = self.handle_menu_events()
                self.draw_menu()
            else:
                # Режим игры
                running = self.handle_events()
                self.update_game_state()

                # Отрисовка
                self.draw_background()
                self.all_sprites.draw(screen)
                self.draw_ui()

                # Отрисовка экранов завершения
                if self.game_over:
                    self.draw_game_over()
                elif self.game_won:
                    self.draw_victory()

            pygame.display.flip()

        pygame.quit()


def main():
    """Точка входа в программу"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
