import board
import busio
import time
import random
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x
from digitalio import DigitalInOut, Direction, Pull
import neopixel

# Import custom RotaryEncoder class
try:
    from rotary_encoder import RotaryEncoder
    USE_CUSTOM_ENCODER = True
    print("Using custom RotaryEncoder")
except ImportError:
    try:
        import rotaryio
        USE_CUSTOM_ENCODER = False
        USE_ROTARY = True
        print("Using built-in rotaryio")
    except ImportError:
        USE_CUSTOM_ENCODER = False
        USE_ROTARY = False
        print("Using GPIO fallback")

# ========== Hardware Initialization ==========
displayio.release_displays()

# I2C Bus (D4=SDA, D5=SCL)
i2c = busio.I2C(board.D5, board.D4)

# OLED Display (using your working method)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create main display group
main_group = displayio.Group()
display.root_group = main_group

# Accelerometer
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# Rotary Encoder
if USE_CUSTOM_ENCODER:
    encoder = RotaryEncoder(board.D0, board.D1, pull=Pull.UP, pulses_per_detent=2)
elif USE_ROTARY:
    encoder = rotaryio.IncrementalEncoder(board.D0, board.D1)
else:
    class SimpleEncoder:
        def __init__(self):
            self.position = 0
        def update(self):
            pass
    encoder = SimpleEncoder()

encoder_button = DigitalInOut(board.D2)
encoder_button.direction = Direction.INPUT
encoder_button.pull = Pull.UP

# Independent restart button (optional - if not connected, only encoder_button will work)
try:
    restart_button = DigitalInOut(board.D6)  # Warning: if no push button, auto-disable
    restart_button.direction = Direction.INPUT
    restart_button.pull = Pull.UP
    HAS_RESTART_BUTTON = True
except:
    HAS_RESTART_BUTTON = False
    print("Warning: Restart button not found on D6")

# NeoPixel LED (3 LEDs)
# Some versions only accept 2 required parameters (pin, n)
pixels = neopixel.NeoPixel(board.D10, 3)
pixels.brightness = 0.3
pixels.auto_write = False

# ========== Game Configuration ==========
DIFFICULTY_LEVELS = ["EASY", "MED", "HARD"]
difficulty_multipliers = {"EASY": 1.0, "MED": 0.8, "HARD": 0.6}
tolerance_multipliers = {"EASY": 1.0, "MED": 0.67, "HARD": 0.5}  # MED -33%, HARD -50%

LEVELS = [
    {"level": 1, "action": "LEFT-RIGHT", "time": 20, "target_shakes": 10, "tolerance": 3, "threshold": 1.5},
    {"level": 2, "action": "FWD-BACK", "time": 18, "target_shakes": 12, "tolerance": 3, "threshold": 1.5},
    {"level": 3, "action": "UP-DOWN", "time": 16, "target_shakes": 15, "tolerance": 4, "threshold": 1.5},
    {"level": 4, "action": "LEFT-RIGHT", "time": 15, "target_shakes": 18, "tolerance": 4, "threshold": 1.8},
    {"level": 5, "action": "FWD-BACK", "time": 14, "target_shakes": 20, "tolerance": 4, "threshold": 1.8},
    {"level": 6, "action": "UP-DOWN", "time": 13, "target_shakes": 22, "tolerance": 5, "threshold": 1.8},
    {"level": 7, "action": "ANY SHAKE", "time": 12, "target_shakes": 25, "tolerance": 5, "threshold": 2.0},
    {"level": 8, "action": "RANDOM", "time": 11, "target_shakes": 28, "tolerance": 5, "threshold": 2.2},
    {"level": 9, "action": "FAST SHAKE", "time": 10, "target_shakes": 30, "tolerance": 6, "threshold": 2.5},
    {"level": 10, "action": "SLOT", "time": 0, "target_shakes": 0, "tolerance": 0, "threshold": 0}
]

SLOT_SYMBOLS = ["7", "*", "#", "@", "!"]

current_difficulty = 0
current_level = 0
score = 0

# ========== Filter ==========
class MovingAverageFilter:
    def __init__(self, window_size=5):
        self.window_size = window_size
        # CircuitPython's deque doesn't support maxlen parameter, use list instead
        self.x_data = []
        self.y_data = []
        self.z_data = []
    
    def update(self, x, y, z):
        self.x_data.append(x)
        self.y_data.append(y)
        self.z_data.append(z)
        
        # Manually limit list length
        if len(self.x_data) > self.window_size:
            self.x_data.pop(0)
        if len(self.y_data) > self.window_size:
            self.y_data.pop(0)
        if len(self.z_data) > self.window_size:
            self.z_data.pop(0)
    
    def get_average(self):
        if len(self.x_data) == 0:
            return (0, 0, 0)
        return (
            sum(self.x_data) / len(self.x_data),
            sum(self.y_data) / len(self.y_data),
            sum(self.z_data) / len(self.z_data)
        )

accel_filter = MovingAverageFilter()

# ========== Display Functions ==========
def clear_screen():
    """Clear screen"""
    while len(main_group):
        main_group.pop()

def show_text(lines):
    """Display multiple lines of text"""
    clear_screen()
    y = 5
    for line in lines:
        text_area = label.Label(terminalio.FONT, text=line[:21], color=0xFFFFFF, x=0, y=y)
        main_group.append(text_area)
        y += 10

def show_centered(text, y):
    """Display centered text"""
    x = max(0, (128 - len(text) * 6) // 2)
    text_area = label.Label(terminalio.FONT, text=text[:21], color=0xFFFFFF, x=x, y=y)
    main_group.append(text_area)

# ========== LED Functions ==========
def set_all_pixels(color):
    pixels.fill(color)
    pixels.show()

def rainbow_pulse():
    colors = [(255, 0, 0), (255, 127, 0), (0, 255, 0), (0, 0, 255)]
    for color in colors:
        set_all_pixels(color)
        time.sleep(0.1)
    set_all_pixels((0, 0, 0))

def win_animation():
    for _ in range(5):
        set_all_pixels((0, 255, 0))
        time.sleep(0.1)
        set_all_pixels((0, 0, 0))
        time.sleep(0.1)

def lose_animation():
    for _ in range(3):
        set_all_pixels((255, 0, 0))
        time.sleep(0.2)
        set_all_pixels((0, 0, 0))
        time.sleep(0.2)

# ========== Difficulty Selection ==========
def select_difficulty():
    global current_difficulty
    
    if USE_CUSTOM_ENCODER:
        encoder.update()
        last_position = encoder.position
    elif USE_ROTARY:
        last_position = encoder.position
    else:
        last_position = 0
    
    # Initial display
    last_displayed_difficulty = -1
    
    while True:
        if USE_CUSTOM_ENCODER:
            encoder.update()
        elif not USE_ROTARY:
            encoder.update()
        
        current_position = encoder.position
        
        if current_position != last_position:
            diff = current_position - last_position
            print(f"Encoder: pos={current_position}, diff={diff}, difficulty={current_difficulty}")
            
            # Only accept positive direction (clockwise) rotation
            if diff > 0:
                current_difficulty = (current_difficulty + 1) % len(DIFFICULTY_LEVELS)
            # Ignore negative direction (counter-clockwise)
            
            last_position = current_position
        
        # Only update display when difficulty actually changes
        if current_difficulty != last_displayed_difficulty:
            clear_screen()
            show_centered("SELECT DIFFICULTY", 10)
            
            # Fixed positions for three difficulty texts
            difficulties = ["EASY", "MED", "HARD"]
            x_positions = [10, 50, 95]  # Fixed X coordinates
            y = 30
            
            # First display all text (without brackets)
            for i, (diff_text, x) in enumerate(zip(difficulties, x_positions)):
                text_area = label.Label(terminalio.FONT, text=diff_text, color=0xFFFFFF, x=x, y=y)
                main_group.append(text_area)
            
            # Then draw brackets around selected option
            selected_x = x_positions[current_difficulty]
            bracket_left = label.Label(terminalio.FONT, text="[", color=0xFFFFFF, x=selected_x-6, y=y)
            bracket_right = label.Label(terminalio.FONT, text="]", color=0xFFFFFF, x=selected_x+len(difficulties[current_difficulty])*6, y=y)
            main_group.append(bracket_left)
            main_group.append(bracket_right)
            
            show_centered("PRESS START", 50)
            
            last_displayed_difficulty = current_difficulty
        
        # Check button
        if not encoder_button.value:
            time.sleep(0.05)
            if not encoder_button.value:
                while not encoder_button.value:
                    time.sleep(0.01)
                break
        
        time.sleep(0.01)  # Faster update rate: 10ms instead of 50ms
    
    set_all_pixels((0, 255, 0))
    time.sleep(0.3)
    set_all_pixels((0, 0, 0))
    
    return DIFFICULTY_LEVELS[current_difficulty]

# ========== Shake Detection ==========
def detect_shake(action, duration, threshold, target_shakes, tolerance):
    """
    New game logic: shake specified number of times within time limit
    target_shakes: target count
    tolerance: error tolerance (±tolerance counts as pass)
    """
    start_time = time.monotonic()
    shake_count = 0
    is_shaking = False
    last_shake_time = 0
    shake_cooldown = 0.3  # At least 0.3s between shakes
    
    base_x, base_y, base_z = accelerometer.acceleration
    accel_filter.update(base_x, base_y, base_z)
    
    min_shakes = target_shakes - tolerance
    max_shakes = target_shakes + tolerance
    
    while True:
        current_time = time.monotonic()
        elapsed = current_time - start_time
        remaining = duration - elapsed
        
        # Read acceleration
        x, y, z = accelerometer.acceleration
        accel_filter.update(x, y, z)
        avg_x, avg_y, avg_z = accel_filter.get_average()
        
        delta_x = abs(x - avg_x)
        delta_y = abs(y - avg_y)
        delta_z = abs(z - avg_z)
        
        # Detect if shaking
        is_moving = False
        if "LEFT-RIGHT" in action:
            is_moving = delta_x > threshold
        elif "FWD-BACK" in action:
            is_moving = delta_y > threshold
        elif "UP-DOWN" in action:
            is_moving = delta_z > threshold
        elif "ANY" in action or "FAST" in action:
            is_moving = delta_x > threshold or delta_y > threshold or delta_z > threshold
        elif "RANDOM" in action:
            is_moving = delta_x > threshold or delta_y > threshold
        
        # Count logic: from still to moving counts as one
        if is_moving and not is_shaking:
            # Check cooldown time
            if current_time - last_shake_time > shake_cooldown:
                shake_count += 1
                last_shake_time = current_time
                is_shaking = True
                set_all_pixels((0, 255, 0))  # Green flash indicates count
                time.sleep(0.1)
        elif not is_moving:
            is_shaking = False
        
        # LED indication
        if is_moving:
            set_all_pixels((255, 255, 0))  # Yellow - shaking
        else:
            set_all_pixels((0, 0, 255))  # Blue - waiting for shake
        
        # Update display
        clear_screen()
        
        # Top: level info
        show_centered("=" * 21, 0)
        show_centered(f"LEVEL {current_level + 1}/10", 10)
        show_centered("=" * 21, 18)
        
        # Middle: action and progress
        show_centered(action, 28)
        show_centered(f"{shake_count}/{target_shakes}", 40)
        
        # Bottom: time
        if remaining <= 5:
            show_centered(f"TIME: {int(remaining)}s !!!", 54)
        else:
            show_centered(f"Time: {int(remaining)}s", 54)
        
        # Check if time is up
        if elapsed >= duration:
            set_all_pixels((0, 0, 0))
            
            # Judge success: shake count within range
            if min_shakes <= shake_count <= max_shakes:
                return True, shake_count
            else:
                return False, shake_count
        
        time.sleep(0.01)

# ========== Slot Machine ==========
def play_slot_machine():
    """
    Slot machine game:
    1. Press restart button to start spinning
    2. Each reel spins separately
    3. Press restart button again to stop current reel
    4. After all 3 reels stop, judge result
    """
    clear_screen()
    show_centered("SLOT MACHINE!", 10)
    show_centered("Press RESTART", 30)
    show_centered("to START", 45)
    
    # Wait for button to start
    while True:
        if not restart_button.value:
            time.sleep(0.05)
            if not restart_button.value:
                while not restart_button.value:
                    time.sleep(0.01)
                break
        time.sleep(0.1)
    
    # State of 3 reels
    reels = [None, None, None]  # Final result
    current_reel = 0  # Current spinning reel
    reel_symbols = [SLOT_SYMBOLS[0], SLOT_SYMBOLS[0], SLOT_SYMBOLS[0]]  # Current displayed symbols
    
    # Spinning animation
    spinning = True
    animation_counter = 0
    
    clear_screen()
    show_centered("SLOT MACHINE!", 5)
    show_centered("Press to STOP", 55)
    
    while current_reel < 3:
        # Update current reel symbol (spinning effect)
        if reels[current_reel] is None:  # Still spinning
            reel_symbols[current_reel] = SLOT_SYMBOLS[animation_counter % len(SLOT_SYMBOLS)]
            animation_counter += 1
        
        # Display 3 reels
        clear_screen()
        show_centered("SLOT MACHINE!", 5)
        
        # Display symbols, mark unstopped reels with []
        display_parts = []
        for i in range(3):
            if reels[i] is None and i == current_reel:
                display_parts.append(f"[{reel_symbols[i]}]")  # Current spinning reel
            else:
                display_parts.append(f" {reel_symbols[i]} ")  # Stopped reel
        
        result = "".join(display_parts)
        show_centered(result, 30)
        show_centered("Press to STOP", 55)
        
        # Detect button to stop current reel
        if not restart_button.value:
            time.sleep(0.05)
            if not restart_button.value:
                while not restart_button.value:
                    time.sleep(0.01)
                
                # Stop current reel
                reels[current_reel] = reel_symbols[current_reel]
                
                # LED flash indicates stop
                set_all_pixels((0, 255, 0))
                time.sleep(0.1)
                set_all_pixels((0, 0, 0))
                
                current_reel += 1
                animation_counter = 0
        
        time.sleep(0.05)  # Control spinning speed
    
    # All reels stopped, show final result
    time.sleep(0.5)
    clear_screen()
    show_centered("SLOT MACHINE!", 10)
    result = f" {reels[0]}   {reels[1]}   {reels[2]} "
    show_centered(result, 30)
    
    # Judge if win
    if reels[0] == reels[1] == reels[2]:
        show_centered("JACKPOT!!!", 50)
        win_animation()
        rainbow_pulse()
        time.sleep(2)
        return True
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        show_centered("2 Match!", 50)
        set_all_pixels((255, 165, 0))  # Orange
        time.sleep(1)
        set_all_pixels((0, 0, 0))
        time.sleep(1)
        return False
    else:
        show_centered("No Match", 50)
        lose_animation()
        time.sleep(2)
        return False

# ========== Game Main Loop ==========
def game_loop():
    global current_level, score
    
    difficulty = select_difficulty()
    difficulty_mult = difficulty_multipliers[difficulty]
    tolerance_mult = tolerance_multipliers[difficulty]  # Tolerance multiplier
    
    rainbow_pulse()
    clear_screen()
    show_centered("=" * 21, 5)
    show_centered("SHAKE GAME", 18)
    show_centered("=" * 21, 28)
    show_centered("Hit the target", 38)
    show_centered("number!", 48)
    time.sleep(2.5)
    
    current_level = 0
    score = 0
    
    while current_level < len(LEVELS):
        level_data = LEVELS[current_level]
        
        # Special handling: slot machine for levels 3, 6, 10
        if level_data["level"] in [3, 6, 10]:
            # First complete current level
            if level_data["level"] != 10:
                action = level_data["action"]
                time_limit = level_data["time"] * difficulty_mult
                threshold = level_data["threshold"]
                target_shakes = level_data["target_shakes"]
                tolerance = int(level_data["tolerance"] * tolerance_mult)  # Apply difficulty multiplier
                
                success, shake_count = detect_shake(action, time_limit, threshold, target_shakes, tolerance)
                
                if not success:
                    game_over()
                    return
                
                score += 100
            
            # Enter slot machine phase
            if level_data["level"] == 10:
                # Level 10: 3 rounds of slot machine
                wins = 0
                for i in range(3):
                    clear_screen()
                    show_centered("*" * 21, 10)
                    show_centered(f"ROUND {i+1}/3", 25)
                    show_centered("*" * 21, 38)
                    time.sleep(1)
                    
                    if play_slot_machine():
                        wins += 1
                        score += 500
                
                if wins >= 2:  # Win at least 2 rounds
                    game_win()
                    return
                else:
                    game_over()
                    return
            else:
                # Single round slot machine (Level 3 or Level 6)
                clear_screen()
                show_centered("~" * 21, 10)
                show_centered("BONUS ROUND", 25)
                show_centered("~" * 21, 38)
                time.sleep(1)
                
                slot_win = play_slot_machine()
                
                if slot_win:
                    score += 200
                    
                    # Skip level reward!
                    if level_data["level"] == 3:
                        # Level 3 slot machine win -> skip to Level 6
                        clear_screen()
                        show_centered("+" * 21, 5)
                        show_centered("BONUS!", 18)
                        show_centered("SKIP TO LV6", 32)
                        show_centered("+" * 21, 42)
                        rainbow_pulse()
                        time.sleep(2)
                        current_level = 5  # Jump to Level 6 (index 5)
                    elif level_data["level"] == 6:
                        # Level 6 slot machine win -> skip to Level 10
                        clear_screen()
                        show_centered("*" * 21, 5)
                        show_centered("MEGA BONUS!", 18)
                        show_centered("SKIP TO LV10", 32)
                        show_centered("*" * 21, 42)
                        rainbow_pulse()
                        time.sleep(2)
                        current_level = 9  # Jump to Level 10 (index 9)
        else:
            # Normal level
            action = level_data["action"]
            time_limit = level_data["time"] * difficulty_mult
            threshold = level_data["threshold"]
            target_shakes = level_data["target_shakes"]
            tolerance = int(level_data["tolerance"] * tolerance_mult)  # Apply difficulty multiplier
            
            success, shake_count = detect_shake(action, time_limit, threshold, target_shakes, tolerance)
            
            if success:
                score += 100
                clear_screen()
                show_centered("*" * 21, 5)
                show_centered("SUCCESS!", 20)
                show_centered("*" * 21, 30)
                show_centered(f"Got: {shake_count}", 42)
                show_centered(f"Score: {score}", 54)
                win_animation()
                time.sleep(1.5)
            else:
                game_over()
                return
        
        current_level += 1
    
    game_win()

# ========== Game Over ==========
def game_over():
    lose_animation()
    clear_screen()
    
    # Top divider
    show_centered("X" * 21, 5)
    show_centered("GAME OVER", 18)
    show_centered("X" * 21, 28)
    
    # Score
    show_centered(f"Score: {score}", 40)
    
    # Bottom prompt
    show_centered("Press Button", 54)
    
    time.sleep(0.5)
    while True:
        # Check encoder button
        if not encoder_button.value:
            time.sleep(0.05)
            if not encoder_button.value:
                while not encoder_button.value:
                    time.sleep(0.01)
                restart_game()
                return
        
        # If has restart button, also check it
        if HAS_RESTART_BUTTON:
            if not restart_button.value:
                time.sleep(0.05)
                if not restart_button.value:
                    while not restart_button.value:
                        time.sleep(0.01)
                    restart_game()
                    return
        
        time.sleep(0.1)

def game_win():
    win_animation()
    rainbow_pulse()
    
    clear_screen()
    
    # Top
    show_centered("*" * 21, 5)
    show_centered("YOU WIN!", 18)
    show_centered("*" * 21, 28)
    
    # Score
    show_centered(f"Score: {score}", 40)
    
    # Bottom prompt
    show_centered("Press Button", 54)
    
    time.sleep(0.5)
    while True:
        # Check encoder button
        if not encoder_button.value:
            time.sleep(0.05)
            if not encoder_button.value:
                while not encoder_button.value:
                    time.sleep(0.01)
                restart_game()
                return
        
        # If has restart button, also check it
        if HAS_RESTART_BUTTON:
            if not restart_button.value:
                time.sleep(0.05)
                if not restart_button.value:
                    while not restart_button.value:
                        time.sleep(0.01)
                    restart_game()
                    return
        
        time.sleep(0.1)

def restart_game():
    set_all_pixels((0, 0, 0))
    clear_screen()
    show_centered("RESTARTING...", 30)
    time.sleep(1)
    game_loop()

# ========== Splash Screen ==========
def splash_screen():
    """Boot animation"""
    rainbow_pulse()
    
    for _ in range(3):
        clear_screen()
        show_centered("SHAKE", 20)
        show_centered("MASTER", 35)
        time.sleep(0.3)
        clear_screen()
        time.sleep(0.2)
    
    clear_screen()
    show_centered("SHAKE", 20)
    show_centered("MASTER", 35)
    time.sleep(1)

# ========== Main Program ==========
def main():
    splash_screen()
    game_loop()

if __name__ == "__main__":
    main()
