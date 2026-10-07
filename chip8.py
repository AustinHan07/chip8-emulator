#!/usr/bin/env python3
"""
CHIP-8 Emulator
A complete implementation of the CHIP-8 virtual machine in Python.
"""

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
