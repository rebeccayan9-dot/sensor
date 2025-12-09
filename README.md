# Shake Master Game 🎮

A motion-controlled rhythm game built with ESP32-C3, featuring accelerometer-based shake detection, slot machine bonus rounds, and progressive difficulty levels.

## 🎯 Overview

**Shake Master** is an interactive motion-based game where players shake the device in specific directions to progress through 10 challenging levels. The game features:

- **3 difficulty modes** (Easy, Medium, Hard) with different time constraints and tolerance levels
- **Motion-based gameplay** using a 3-axis accelerometer
- **Interactive slot machine** bonus rounds with skip-level rewards
- **Real-time visual feedback** on OLED display
- **LED animations** for game state indication
- **Rotary encoder interface** for menu navigation

The core gameplay mechanic revolves around **precision shake counting** - players must shake the device a specific number of times within a time limit, with a tolerance range that varies by difficulty.


## 🎮 How the Game Works

### Game Flow

```
┌─────────────────┐
│  Splash Screen  │
│  "SHAKE MASTER" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select Difficulty│  ← Rotate encoder
│ [EASY] MED HARD │  ← Press to confirm
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Level 1-10    │  ← Shake to match target
│   Shake Game    │  ← Time limit varies
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │ Level 3 │
    │ Level 6 │  → Bonus Slot Machine
    │ Level 10│
    └────┬────┘
         │
         ▼
┌─────────────────┐
│   Game Result   │
│ WIN or GAME OVER│
└─────────────────┘
```

### Core Mechanics

#### 1. Shake Detection System
- **Threshold-based motion detection** using ADXL345 accelerometer
- **Direction-specific shaking**: LEFT-RIGHT, FORWARD-BACK, UP-DOWN
- **Cooldown period** (0.3s) prevents double-counting
- **Moving average filter** reduces noise and false triggers

#### 2. Counting Logic
Each level requires a target number of shakes within a time limit:

| Level | Time | Target Shakes | Tolerance (Easy) | Direction |
|-------|------|---------------|------------------|-----------|
| 1 | 20s | 10 | ±3 (7-13) | LEFT-RIGHT |
| 2 | 18s | 12 | ±3 (9-15) | FWD-BACK |
| 3 | 16s | 15 | ±4 (11-19) | UP-DOWN |
| ... | ... | ... | ... | ... |
| 9 | 10s | 30 | ±6 (24-36) | FAST SHAKE |

**Difficulty Modifiers**:
- **Easy**: 100% time, 100% tolerance
- **Medium**: 80% time, 67% tolerance (±3 → ±2)
- **Hard**: 60% time, 50% tolerance (±3 → ±1)

#### 3. Slot Machine Bonus Rounds

Appears at Levels 3, 6, and 10:

**Gameplay**:
1. Press restart button to start spinning
2. Three reels spin with symbols: `7`, `*`, `#`, `@`, `!`
3. Press restart button to stop each reel individually
4. Win condition: All 3 symbols match (JACKPOT)

**Rewards**:
- **Level 3 JACKPOT**: Skip to Level 6 (bypass 4-5)
- **Level 6 JACKPOT**: Skip to Level 10 (bypass 7-9)
- **Level 10**: Win 2 out of 3 rounds to win game

This creates strategic shortcuts - skilled players can complete the game in 5 levels instead of 10!

#### 4. Visual Feedback System

**OLED Display** (128x64):
- Real-time shake counter: `10/15`
- Time remaining with urgency indicator (`!!!` when <5s)
- Level progress: `LEVEL 3/10`
- Action type: `LEFT-RIGHT`, `UP-DOWN`, etc.

**NeoPixel LEDs** (3x RGB):
- 🔵 **Blue**: Waiting for shake
- 🟡 **Yellow**: Shaking detected
- 🟢 **Green**: Shake counted (flash)
- 🔴 **Red**: Failed level (flash)
- 🌈 **Rainbow**: Success/Jackpot

## 🔧 Hardware Components


### Pin Configuration

```
ESP32-C3 SuperMini Pinout:
┌─────────────────┐
│  D0  ← Encoder CLK
│  D1  ← Encoder DT
│  D2  ← Encoder Button
│  D4  ← I2C SDA (OLED + Accelerometer)
│  D5  ← I2C SCL (OLED + Accelerometer)
│  D6  ← Restart Button
│  D10 ← NeoPixel DIN
│  3V3 → Power
│  GND → Ground
└─────────────────┘
```

### Additional Hardware Features

#### 1. Custom Rotary Encoder Implementation
Due to ESP32-C3's lack of hardware rotary encoder support, I implemented a **software-based encoder reader** using GPIO interrupts and debouncing:

```python
class RotaryEncoder:
    def __init__(self, pin_clk, pin_dt, pull=Pull.UP, pulses_per_detent=2):
        # Software quadrature decoding
        # Handles both clockwise and counter-clockwise rotation
        # Configurable pulses per detent for different encoder types
```

**Optimization**: Single-direction mode accepts only clockwise rotation, working around hardware limitations where the encoder would sometimes miss counter-clockwise movements.

#### 2. Dual Button System
- **Encoder button** (D2): Menu navigation and confirmations
- **Independent push button** (D6): Slot machine start/stop
- Fallback: If no external button connected, encoder button handles all inputs

#### 3. I2C Bus Sharing
Both OLED and accelerometer share the same I2C bus, reducing pin usage:
- OLED address: `0x3C`
- ADXL345 address: `0x53`

This allows multiple devices on two pins, a key space-saving technique.

## 📦 Enclosure Design

### Design Philosophy

The enclosure is designed around three core principles:

1. **Ergonomics**: Comfortable to hold and shake repeatedly without hand fatigue
2. **Durability**: Withstands vigorous shaking without components coming loose or breaking
3. **Accessibility**: Easy access to all controls and clear visibility of display

### Physical Design Rationale

#### Form Factor Choice
I chose a **compact handheld design** (~80mm x 60mm x 40mm) for several reasons:

1. **Portability**: Pocket-sized for easy transport
2. **Shake efficiency**: Smaller mass requires less energy to shake, reducing player fatigue
3. **Single-handed operation**: All controls accessible with thumb while gripping
4. **Component density**: Minimizes wasted space while maintaining assembly clearance

#### Shape Development
Initial prototypes used a simple rectangular box, but I want to add some 80's -90's game box elements

### Material Selection

After testing multiple materials, I selected different materials for different parts:

| Part | Material | Reasoning |
|------|----------|-----------|
| Main body | PLA (3D printed) | Easy to prototype, adequate strength, smooth finish |


## 🚀 Setup Instructions

### Software Requirements

1. **CircuitPython 9.x** installed on ESP32-C3
2. **Required libraries** in `/lib` folder:
   - `adafruit_adxl34x.mpy`
   - `adafruit_displayio_ssd1306.mpy`
   - `adafruit_display_text/` (folder)
   - `i2cdisplaybus.mpy`
   - `neopixel.mpy`
   - Custom: `rotary_encoder.py`

### Installation Steps

1. **Install CircuitPython**:
   - Download from [circuitpython.org](https://circuitpython.org)
   - Flash to ESP32-C3 using USB

2. **Copy Files**:
   ```
   CIRCUITPY/
   ├── code.py           # Main game code
   ├── rotary_encoder.py # Custom encoder driver
   └── lib/              # Required libraries
       ├── adafruit_adxl34x.mpy
       ├── adafruit_displayio_ssd1306.mpy
       ├── adafruit_display_text/
       ├── i2cdisplaybus.mpy
       └── neopixel.mpy
   ```

3. **Hardware Assembly**:
   - Connect components according to pin configuration
   - Double-check I2C connections (common failure point)
   - Verify power (3.3V) to all components

4. **Testing**:
   - Run included test scripts to verify hardware
   - Check serial output for debugging

---

## 📖 Gameplay Guide

### Getting Started

1. **Power on** the device (USB or battery)
2. **Splash screen** displays "SHAKE MASTER"
3. **Select difficulty** using rotary encoder
4. **Press encoder button** to start

### Controls

| Input | Action |
|-------|--------|
| Rotate encoder clockwise | Cycle difficulty (EASY→MED→HARD) |
| Press encoder button | Confirm selection / Restart game |
| Press restart button | Start/Stop slot machine reels |
| Shake device | Main gameplay input |

### Level Progression

**Normal Levels (1-9)**:
1. Read the action requirement (e.g., "LEFT-RIGHT")
2. Shake in the specified direction
3. Watch shake counter increase: `5/10`
4. Complete before time runs out
5. Stay within tolerance range

**Bonus Levels (3, 6, 10)**:
1. Complete the shake challenge
2. Enter slot machine bonus round
3. Press restart to start spinning
4. Press restart to stop each reel
5. Match 3 symbols for JACKPOT
   - Level 3: Skip to Level 6
   - Level 6: Skip to Level 10

### Scoring

- **Normal level**: +100 points
- **Slot machine win**: +200 points
- **Level 10 round win**: +500 points
- **Maximum score**: 1800+ points

### Tips & Strategies

1. **Master the rhythm**: 20s for 10 shakes = shake every 2 seconds
2. **Watch the counter**: Don't overshake or undershake
3. **Use landmarks**: Count "1-2-3" while shaking
4. **Slot machine timing**: Symbols cycle every 0.05s, practice timing
5. **Skip strategy**: Win slot machines to bypass hardest levels (7-9)

---

## 🔬 Technical Details

### Software Architecture

```
main()
├── splash_screen()
└── game_loop()
    ├── select_difficulty()
    ├── detect_shake()
    ├── play_slot_machine()
    ├── game_over()
    └── game_win()
```

### Key Algorithms

#### 1. Shake Detection
```python
# Moving average filter reduces noise
delta_x = abs(current_x - average_x)

# Threshold comparison
if delta_x > threshold:
    is_shaking = True

# Edge detection (still → moving)
if is_shaking and not was_shaking:
    shake_count += 1  # Count one shake
```

#### 2. Tolerance System
```python
min_shakes = target - (tolerance * difficulty_multiplier)
max_shakes = target + (tolerance * difficulty_multiplier)

# Judge success
if min_shakes <= shake_count <= max_shakes:
    return True  # Pass
```

#### 3. Display Optimization
```python
# Only update when state changes
if current_difficulty != last_displayed_difficulty:
    clear_screen()
    draw_ui()
    last_displayed_difficulty = current_difficulty
```

---

## 🔮 Future Improvements

### Hardware Enhancements

1. **Battery power**: Rechargeable Li-ion with charging circuit
2. **Speaker**: Audio feedback for shake counts and wins
3. **Vibration motor**: Haptic feedback on shake detection
4. **Larger display**: 1.3" OLED for better visibility

### Software Features

1. **High score tracking**: EEPROM storage
2. **Custom levels**: Player-created challenges
3. **Multiplayer mode**: Bluetooth competition
4. **Sound effects**: Retro game audio

---

## 📊 Project Stats

- **Total code lines**: ~700 lines
- **Development time**: 3 weeks
- **Components used**: 7
- **3D printed parts**: 1

---

**Happy Shaking!** 🎮✨
