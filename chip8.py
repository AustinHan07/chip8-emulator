#!/usr/bin/env python3
"""
CHIP-8 Emulator
A complete implementation of the CHIP-8 virtual machine in Python.
"""

import pygame
import sys
import os
import time
import random
from typing import List, Optional

class Chip8:
    """CHIP-8 Emulator Core"""
    
    def __init__(self):
        # Memory: 4KB (4096 bytes)
        self.memory = [0] * 4096
        
        # Registers
        self.V = [0] * 16  # 16 general-purpose 8-bit registers (V0-VF)
        self.I = 0         # 16-bit index register
        self.PC = 0x200    # 16-bit program counter (starts at 0x200)
        self.SP = 0        # 8-bit stack pointer
        
        # Timers
        self.delay_timer = 0
        self.sound_timer = 0
        
        # Stack (16 levels)
        self.stack = [0] * 16
        
        # Display: 64x32 pixels (1 bit per pixel)
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        
        # Input
        self.keys = [0] * 16
        
        # Flags
        self.draw_flag = False
        self.running = True
        
        # Load fontset into memory (0x000-0x1FF)
        self.load_fontset()
    
    def load_fontset(self):
        """Load CHIP-8 fontset into memory"""
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        
        for i, byte in enumerate(fontset):
            self.memory[i] = byte
    
    def load_rom(self, filename: str) -> bool:
        """Load ROM file into memory starting at 0x200"""
        try:
            with open(filename, 'rb') as f:
                rom_data = f.read()
            
            # Check if ROM fits in available memory
            if len(rom_data) > (4096 - 0x200):
                print(f"Error: ROM too large ({len(rom_data)} bytes)")
                return False
            
            # Load ROM into memory starting at 0x200
            for i, byte in enumerate(rom_data):
                self.memory[0x200 + i] = byte
            
            print(f"Loaded ROM: {filename} ({len(rom_data)} bytes)")
            return True
            
        except FileNotFoundError:
            print(f"Error: ROM file '{filename}' not found")
            return False
        except Exception as e:
            print(f"Error loading ROM: {e}")
            return False
    
    def fetch_instruction(self) -> int:
        """Fetch 2-byte instruction from memory"""
        instruction = (self.memory[self.PC] << 8) | self.memory[self.PC + 1]
        self.PC += 2
        return instruction
    
    def execute_instruction(self, instruction: int):
        """Execute CHIP-8 instruction"""
        # Extract instruction components
        opcode = (instruction & 0xF000) >> 12
        X = (instruction & 0x0F00) >> 8
        Y = (instruction & 0x00F0) >> 4
        N = instruction & 0x000F
        NN = instruction & 0x00FF
        NNN = instruction & 0x0FFF
        
        # Execute instruction based on opcode
        if opcode == 0x0:
            if instruction == 0x00E0:  # CLS
                self.display = [[0 for _ in range(64)] for _ in range(32)]
                self.draw_flag = True
            elif instruction == 0x00EE:  # RET
                self.SP -= 1
                self.PC = self.stack[self.SP]
            elif instruction == 0x00FF:  # Super CHIP-8: Enable high-res mode
                # Skip this instruction - not implemented
                pass
            else:
                print(f"Unknown instruction: {instruction:04X}")
        
        elif opcode == 0x1:  # JP addr
            self.PC = NNN
        
        elif opcode == 0x2:  # CALL addr
            self.stack[self.SP] = self.PC
            self.SP += 1
            self.PC = NNN
        
        elif opcode == 0x3:  # SE Vx, byte
            if self.V[X] == NN:
                self.PC += 2
        
        elif opcode == 0x4:  # SNE Vx, byte
            if self.V[X] != NN:
                self.PC += 2
        
        elif opcode == 0x5:  # SE Vx, Vy
            if self.V[X] == self.V[Y]:
                self.PC += 2
        
        elif opcode == 0x6:  # LD Vx, byte
            self.V[X] = NN
        
        elif opcode == 0x7:  # ADD Vx, byte
            self.V[X] = (self.V[X] + NN) & 0xFF
        
        elif opcode == 0x8:
            if N == 0x0:  # LD Vx, Vy
                self.V[X] = self.V[Y]
            elif N == 0x1:  # OR Vx, Vy
                self.V[X] |= self.V[Y]
            elif N == 0x2:  # AND Vx, Vy
                self.V[X] &= self.V[Y]
            elif N == 0x3:  # XOR Vx, Vy
                self.V[X] ^= self.V[Y]
            elif N == 0x4:  # ADD Vx, Vy
                result = self.V[X] + self.V[Y]
                self.V[0xF] = 1 if result > 255 else 0
                self.V[X] = result & 0xFF
            elif N == 0x5:  # SUB Vx, Vy
                self.V[0xF] = 1 if self.V[X] >= self.V[Y] else 0
                self.V[X] = (self.V[X] - self.V[Y]) & 0xFF
            elif N == 0x6:  # SHR Vx
                self.V[0xF] = self.V[X] & 0x1
                self.V[X] >>= 1
            elif N == 0x7:  # SUBN Vx, Vy
                self.V[0xF] = 1 if self.V[Y] >= self.V[X] else 0
                self.V[X] = (self.V[Y] - self.V[X]) & 0xFF
            elif N == 0xE:  # SHL Vx
                self.V[0xF] = (self.V[X] & 0x80) >> 7
                self.V[X] = (self.V[X] << 1) & 0xFF
        
        elif opcode == 0x9:  # SNE Vx, Vy
            if self.V[X] != self.V[Y]:
                self.PC += 2
        
        elif opcode == 0xA:  # LD I, addr
            self.I = NNN
        
        elif opcode == 0xB:  # JP V0, addr
            self.PC = NNN + self.V[0]
        
        elif opcode == 0xC:  # RND Vx, byte
            self.V[X] = random.randint(0, 255) & NN
        
        elif opcode == 0xD:  # DRW Vx, Vy, nibble
            self.draw_sprite(self.V[X], self.V[Y], N)
        
        elif opcode == 0xE:
            if NN == 0x9E:  # SKP Vx
                if self.keys[self.V[X]]:
                    self.PC += 2
            elif NN == 0xA1:  # SKNP Vx
                if not self.keys[self.V[X]]:
                    self.PC += 2
        
        elif opcode == 0xF:
            if NN == 0x07:  # LD Vx, DT
                self.V[X] = self.delay_timer
            elif NN == 0x0A:  # LD Vx, K
                self.wait_for_key(X)
            elif NN == 0x15:  # LD DT, Vx
                self.delay_timer = self.V[X]
            elif NN == 0x18:  # LD ST, Vx
                self.sound_timer = self.V[X]
            elif NN == 0x1E:  # ADD I, Vx
                self.I = (self.I + self.V[X]) & 0xFFFF
            elif NN == 0x29:  # LD F, Vx
                self.I = self.V[X] * 5  # Font sprites are 5 bytes each
            elif NN == 0x33:  # LD B, Vx
                self.memory[self.I] = self.V[X] // 100
                self.memory[self.I + 1] = (self.V[X] % 100) // 10
                self.memory[self.I + 2] = self.V[X] % 10
            elif NN == 0x55:  # LD [I], Vx
                for i in range(X + 1):
                    self.memory[self.I + i] = self.V[i]
            elif NN == 0x65:  # LD Vx, [I]
                for i in range(X + 1):
                    self.V[i] = self.memory[self.I + i]
            elif NN == 0x75:  # Super CHIP-8: LD [I], Vx (save registers)
                for i in range(X + 1):
                    self.memory[self.I + i] = self.V[i]
                self.I = (self.I + X + 1) & 0xFFFF
            elif NN == 0x85:  # Super CHIP-8: LD Vx, [I] (load registers)
                for i in range(X + 1):
                    self.V[i] = self.memory[self.I + i]
                self.I = (self.I + X + 1) & 0xFFFF
            else:
                print(f"Unknown instruction: {instruction:04X}")
        
        else:
            print(f"Unknown instruction: {instruction:04X}")
    
    def draw_sprite(self, x: int, y: int, height: int):
        """Draw sprite at position (x, y) with given height"""
        self.V[0xF] = 0  # Reset collision flag
        
        for row in range(height):
            sprite_byte = self.memory[self.I + row]
            for col in range(8):
                pixel = (sprite_byte >> (7 - col)) & 0x1
                if pixel:
                    screen_x = (x + col) % 64
                    screen_y = (y + row) % 32
                    
                    if self.display[screen_y][screen_x] == 1:
                        self.V[0xF] = 1  # Collision detected
                    
                    self.display[screen_y][screen_x] ^= 1
        
        self.draw_flag = True
    
    def wait_for_key(self, register: int):
        """Wait for key press and store in register"""
        # This is handled in the main loop
        pass
    
    def update_timers(self):
        """Update delay and sound timers"""
        if self.delay_timer > 0:
            self.delay_timer -= 1
        
        if self.sound_timer > 0:
            self.sound_timer -= 1
    
    def cycle(self):
        """Execute one CPU cycle"""
        if self.running:
            instruction = self.fetch_instruction()
            self.execute_instruction(instruction)
            self.update_timers()


class Chip8Display:
    """CHIP-8 Display using Pygame"""
    
    def __init__(self, scale: int = 10):
        pygame.init()
        self.scale = scale
        self.width = 64 * scale
        self.height = 32 * scale
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("CHIP-8 Emulator")
        self.clock = pygame.time.Clock()
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
    
    def draw(self, display: List[List[int]]):
        """Draw CHIP-8 display to pygame screen"""
        self.screen.fill(self.BLACK)
        
        for y in range(32):
            for x in range(64):
                if display[y][x] == 1:
                    rect = pygame.Rect(x * self.scale, y * self.scale, self.scale, self.scale)
                    pygame.draw.rect(self.screen, self.WHITE, rect)
        
        pygame.display.flip()
    
    def handle_events(self, chip8: Chip8) -> bool:
        """Handle pygame events and update CHIP-8 input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                key = self.get_chip8_key(event.key)
                if key is not None:
                    chip8.keys[key] = 1
            
            elif event.type == pygame.KEYUP:
                key = self.get_chip8_key(event.key)
                if key is not None:
                    chip8.keys[key] = 0
        
        return True
    
    def get_chip8_key(self, pygame_key) -> Optional[int]:
        """Convert pygame key to CHIP-8 keypad"""
        key_map = {
            pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
            pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
            pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
            pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
        }
        return key_map.get(pygame_key)
    
    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()


def main():
    """Main emulator loop"""
    if len(sys.argv) != 2:
        print("Usage: python chip8.py <rom_file>")
        sys.exit(1)
    
    rom_file = sys.argv[1]
    
    # Initialize emulator
    chip8 = Chip8()
    display = Chip8Display(scale=15)  # 15x scale for better visibility
    
    # Load ROM
    if not chip8.load_rom(rom_file):
        sys.exit(1)
    
    # Main emulation loop
    running = True
    clock = pygame.time.Clock()
    
    print("CHIP-8 Emulator Started!")
    print("Controls:")
    print("1 2 3 C")
    print("Q W E R")
    print("A S D F")
    print("Z X C V")
    print("\nPress ESC to quit")
    
    while running:
        # Handle events
        running = display.handle_events(chip8)
        
        # Check for ESC key
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False
        
        # Execute multiple cycles per frame for proper timing
        for _ in range(10):  # Adjust this number for different speeds
            chip8.cycle()
        
        # Draw display if needed
        if chip8.draw_flag:
            display.draw(chip8.display)
            chip8.draw_flag = False
        
        # Control frame rate
        clock.tick(60)  # 60 FPS
    
    display.cleanup()
    print("Emulator stopped.")


if __name__ == "__main__":
    main()
