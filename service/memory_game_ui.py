"""
Memory Card Game with AI Adaptation - Python Tkinter UI

A complete memory matching game that uses the Adaptive Rehab AI engine
to adjust difficulty based on player performance.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import time
import random
from datetime import datetime
from typing import List, Optional

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule, StateVector
from adaptrehab.utils import setup_logging


class MemoryCard:
    """Represents a single memory card."""
    
    def __init__(self, emoji: str, card_id: int):
        self.emoji = emoji
        self.card_id = card_id
        self.is_flipped = False
        self.is_matched = False
        self.button: Optional[tk.Button] = None


class MemoryGameUI:
    """Memory card matching game with AI adaptation."""
    
    EMOJIS = ['🎨', '🎭', '🎪', '🎬', '🎮', '🎯', '🎲', '🎰', 
              '🎳', '🎸', '🎹', '🎺', '🎻', '🎼', '🎵', '🎶',
              '🏀', '⚽', '🏈', '⚾', '🎾', '🏐', '🏉', '🎱',
              '🏓', '🏸', '🏒', '🏑', '🥊', '🥋', '⛳', '🏹']
    
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Adaptive Memory Game - Rehab AI")
        self.root.geometry("1000x750")
        self.root.configure(bg='#667eea')
        
        # Initialize AI engine
        setup_logging("INFO")
        config_manager = ConfigManager()
        self.engine = AdaptationEngine(config_manager.to_dict())
        self.engine.register_module('rule_based', RuleBasedModule)
        
        # Game state
        self.session_id = None
        self.difficulty = 0.0
        self.round_num = 0
        self.matches = 0
        self.attempts = 0
        self.cards: List[MemoryCard] = []
        self.flipped_cards: List[MemoryCard] = []
        self.is_processing = False
        self.is_session_active = False
        self.start_time = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create all UI widgets."""
        
        # Top bar with title
        top_frame = tk.Frame(self.root, bg='#667eea', height=80)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        title = tk.Label(
            top_frame,
            text="🧠 Adaptive Memory Game",
            font=('Arial', 24, 'bold'),
            bg='#667eea',
            fg='white'
        )
        title.pack(pady=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Stats panel
        stats_frame = tk.Frame(content_frame, bg='#f5f5f5', relief=tk.RAISED, bd=2)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Stats grid
        stats_grid = tk.Frame(stats_frame, bg='#f5f5f5')
        stats_grid.pack(pady=15, padx=20)
        
        # Round
        round_box = tk.Frame(stats_grid, bg='white', relief=tk.RAISED, bd=1)
        round_box.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
        tk.Label(round_box, text="Round", bg='white', fg='#666', font=('Arial', 9)).pack(pady=(5,0))
        self.round_label = tk.Label(round_box, text="0", bg='white', fg='#667eea', font=('Arial', 20, 'bold'))
        self.round_label.pack(pady=(0,5))
        
        # Matches
        match_box = tk.Frame(stats_grid, bg='white', relief=tk.RAISED, bd=1)
        match_box.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        tk.Label(match_box, text="Matches", bg='white', fg='#666', font=('Arial', 9)).pack(pady=(5,0))
        self.matches_label = tk.Label(match_box, text="0", bg='white', fg='#667eea', font=('Arial', 20, 'bold'))
        self.matches_label.pack(pady=(0,5))
        
        # Accuracy
        acc_box = tk.Frame(stats_grid, bg='white', relief=tk.RAISED, bd=1)
        acc_box.grid(row=0, column=2, padx=10, pady=5, sticky='ew')
        tk.Label(acc_box, text="Accuracy", bg='white', fg='#666', font=('Arial', 9)).pack(pady=(5,0))
        self.accuracy_label = tk.Label(acc_box, text="0%", bg='white', fg='#667eea', font=('Arial', 20, 'bold'))
        self.accuracy_label.pack(pady=(0,5))
        
        # Grid Size
        grid_box = tk.Frame(stats_grid, bg='white', relief=tk.RAISED, bd=1)
        grid_box.grid(row=0, column=3, padx=10, pady=5, sticky='ew')
        tk.Label(grid_box, text="Grid Size", bg='white', fg='#666', font=('Arial', 9)).pack(pady=(5,0))
        self.grid_label = tk.Label(grid_box, text="3×3", bg='white', fg='#667eea', font=('Arial', 20, 'bold'))
        self.grid_label.pack(pady=(0,5))
        
        # Difficulty indicator
        diff_frame = tk.Frame(stats_frame, bg='#f5f5f5')
        diff_frame.pack(pady=(0, 10), padx=20, fill=tk.X)
        tk.Label(diff_frame, text="Difficulty Level", bg='#f5f5f5', font=('Arial', 10, 'bold')).pack()
        
        # Progress bar for difficulty
        self.difficulty_progress = ttk.Progressbar(
            diff_frame,
            mode='determinate',
            length=400,
            maximum=1.0
        )
        self.difficulty_progress.pack(pady=5)
        self.difficulty_value_label = tk.Label(diff_frame, text="0.000", bg='#f5f5f5', font=('Arial', 9))
        self.difficulty_value_label.pack()
        
        # Game board container
        self.board_container = tk.Frame(content_frame, bg='white')
        self.board_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Control buttons
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(pady=15)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Game",
            command=self.start_game,
            bg='#667eea',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=15,
            height=2,
            cursor='hand2',
            relief=tk.RAISED,
            bd=3
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.new_round_btn = tk.Button(
            button_frame,
            text="🔄 New Round",
            command=self.start_new_round,
            bg='#f5f5f5',
            fg='#333',
            font=('Arial', 14, 'bold'),
            width=15,
            height=2,
            cursor='hand2',
            state=tk.DISABLED,
            relief=tk.RAISED,
            bd=3
        )
        self.new_round_btn.pack(side=tk.LEFT, padx=10)
        
        # AI status box
        ai_frame = tk.Frame(content_frame, bg='#e8eaf6', relief=tk.RAISED, bd=2)
        ai_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            ai_frame,
            text="🤖 AI Adaptation Engine",
            bg='#e8eaf6',
            font=('Arial', 11, 'bold'),
            fg='#667eea'
        ).pack(anchor=tk.W, padx=15, pady=(10, 5))
        
        self.ai_message = tk.Label(
            ai_frame,
            text="Click 'Start Game' to connect to the AI adaptation engine...",
            bg='#e8eaf6',
            font=('Arial', 10),
            fg='#666',
            wraplength=900,
            justify=tk.LEFT
        )
        self.ai_message.pack(anchor=tk.W, padx=15, pady=(0, 10))
        
    def start_game(self):
        """Initialize game session."""
        self.session_id = f"memory_ui_{int(time.time())}"
        self.round_num = 0
        self.difficulty = 0.0
        
        self.ai_message.config(text="🔌 Connecting to AI adaptation engine...")
        self.root.update()
        
        # Run async initialization
        thread = threading.Thread(target=self._async_start_game)
        thread.start()
        
    def _async_start_game(self):
        """Async game initialization."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        patient_profile = {
            'patient_id': 'memory_player',
            'condition': 'cognitive',
            'baseline_performance': 0.5,
            'threshold_success': 0.65,  # Need 65%+ accuracy to increase difficulty
            'threshold_failure': 0.35    # Below 35% accuracy to decrease difficulty
        }
        
        task_config = {
            'task_type': 'memory',
            'safety_bounds': {
                'difficulty': {'min': 0.0, 'max': 1.0}
            }
        }
        
        success = loop.run_until_complete(
            self.engine.initialize_session(
                self.session_id,
                'rule_based',
                patient_profile,
                task_config
            )
        )
        
        if success:
            self.is_session_active = True
            print(f"🧠 AI Engine Connected! Session: {self.session_id}")
            print(f"Starting Difficulty: {self.difficulty:.3f}")
            self.root.after(0, self._on_session_started)
        else:
            self.root.after(0, self._on_session_failed)
            
        loop.close()
        
    def _on_session_started(self):
        """Called when session starts successfully."""
        self.start_btn.config(state=tk.DISABLED)
        self.new_round_btn.config(state=tk.NORMAL)
        self.ai_message.config(
            text="✅ Connected! AI adaptation engine is ready. Starting your first round...",
            fg='#4caf50'
        )
        self.start_new_round()
        
    def _on_session_failed(self):
        """Called when session fails."""
        self.ai_message.config(
            text="❌ Connection failed. Please try again.",
            fg='#f44336'
        )
        
    def start_new_round(self):
        """Start a new game round."""
        if not self.is_session_active:
            return
            
        self.round_num += 1
        self.matches = 0
        self.attempts = 0
        self.flipped_cards = []
        self.start_time = time.time()
        
        print(f"\n▶️  Starting Round {self.round_num} (Difficulty: {self.difficulty:.3f})")
        
        # Update UI
        self.round_label.config(text=str(self.round_num))
        self.matches_label.config(text="0")
        self.accuracy_label.config(text="0%")
        
        # Create board
        self.create_board()
        
        self.new_round_btn.config(state=tk.DISABLED)
        self.ai_message.config(
            text=f"Round {self.round_num} started! Match all the cards. Difficulty: {self.difficulty*100:.0f}%",
            fg='#666'
        )
        
    def create_board(self):
        """Create game board based on difficulty."""
        # Clear existing board
        for widget in self.board_container.winfo_children():
            widget.destroy()
            
        # Determine grid size
        if self.difficulty < 0.3:
            grid_size = 3  # 3x3
        elif self.difficulty < 0.5:
            grid_size = 4  # 4x4
        elif self.difficulty < 0.7:
            grid_size = 6  # 6x6
        else:
            grid_size = 8  # 8x8
            
        self.grid_label.config(text=f"{grid_size}×{grid_size}")
        
        # Create cards
        total_cards = grid_size * grid_size
        num_pairs = total_cards // 2
        
        selected_emojis = random.sample(self.EMOJIS, num_pairs)
        card_emojis = selected_emojis * 2
        
        # Add extra card for odd grids
        if total_cards % 2 != 0:
            card_emojis.append(random.choice(self.EMOJIS))
            
        random.shuffle(card_emojis)
        
        # Create card objects
        self.cards = [MemoryCard(emoji, i) for i, emoji in enumerate(card_emojis)]
        
        # Create game board frame
        board_frame = tk.Frame(self.board_container, bg='white')
        board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Calculate button size based on grid
        btn_size = max(60, 400 // grid_size)
        font_size = max(20, 60 // grid_size)
        
        # Create buttons
        for i, card in enumerate(self.cards):
            row = i // grid_size
            col = i % grid_size
            
            btn = tk.Button(
                board_frame,
                text="?",
                font=('Arial', font_size, 'bold'),
                width=3,
                height=1,
                bg='#667eea',
                fg='white',
                command=lambda c=card: self.flip_card(c),
                cursor='hand2',
                relief=tk.RAISED,
                bd=3
            )
            btn.grid(row=row, column=col, padx=3, pady=3)
            card.button = btn
            
    def flip_card(self, card: MemoryCard):
        """Handle card flip."""
        if self.is_processing or card.is_flipped or card.is_matched:
            return
            
        # Flip card
        card.is_flipped = True
        card.button.config(text=card.emoji, bg='white', fg='#333')
        self.flipped_cards.append(card)
        
        # Check if two cards flipped
        if len(self.flipped_cards) == 2:
            self.attempts += 1
            self.is_processing = True
            
            card1, card2 = self.flipped_cards
            
            if card1.emoji == card2.emoji and card1.card_id != card2.card_id:
                # Match!
                self.root.after(500, lambda: self._on_match(card1, card2))
            else:
                # No match
                self.root.after(1000, lambda: self._on_no_match(card1, card2))
                
    def _on_match(self, card1: MemoryCard, card2: MemoryCard):
        """Handle successful match."""
        card1.is_matched = True
        card2.is_matched = True
        card1.button.config(bg='#4caf50', state=tk.DISABLED)
        card2.button.config(bg='#4caf50', state=tk.DISABLED)
        
        self.matches += 1
        self.matches_label.config(text=str(self.matches))
        self._update_accuracy()
        
        self.flipped_cards = []
        self.is_processing = False
        
        # Check if round complete - count total matched cards
        matched_count = len([c for c in self.cards if c.is_matched])
        total_cards = len(self.cards)
        
        # Round is complete when all or all-but-one cards are matched (for odd grids)
        if matched_count >= total_cards - 1:
            self.complete_round()
            
    def _on_no_match(self, card1: MemoryCard, card2: MemoryCard):
        """Handle failed match."""
        card1.is_flipped = False
        card2.is_flipped = False
        card1.button.config(text="?", bg='#667eea', fg='white')
        card2.button.config(text="?", bg='#667eea', fg='white')
        
        self._update_accuracy()
        
        self.flipped_cards = []
        self.is_processing = False
        
    def _update_accuracy(self):
        """Update accuracy display."""
        if self.attempts > 0:
            accuracy = (self.matches / self.attempts) * 100
            self.accuracy_label.config(text=f"{accuracy:.0f}%")
            
    def complete_round(self):
        """Called when round is complete."""
        duration = time.time() - self.start_time
        accuracy = self.matches / self.attempts if self.attempts > 0 else 0
        
        self.ai_message.config(text="🤖 AI analyzing your performance...", fg='#ff9800')
        self.root.update()
        
        # Get AI adaptation
        thread = threading.Thread(target=self._async_get_adaptation, args=(accuracy, duration))
        thread.start()
        
    def _async_get_adaptation(self, accuracy: float, duration: float):
        """Get adaptation decision from AI."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        old_difficulty = self.difficulty
        
        # Create state
        state = StateVector(
            performance_metrics={
                'accuracy': accuracy,
                'success_rate': accuracy,
                'reaction_time': duration / max(self.matches, 1),
                'error_rate': 1 - accuracy,
                'consistency': min(accuracy * 1.2, 1.0)
            },
            sensor_data={},
            task_state={
                'difficulty': self.difficulty,
                'round': self.round_num,
                'duration': duration
            },
            timestamp=time.time(),
            session_id=self.session_id
        )
        
        # Get decision
        decision = loop.run_until_complete(
            self.engine.compute_adaptation(self.session_id, state)
        )
        
        if decision:
            self.difficulty = decision.parameters.get('difficulty', self.difficulty)
            diff_change = self.difficulty - old_difficulty
            
            # Log to console
            print("=" * 60)
            print(f"Round {self.round_num} Complete:")
            print(f"  Accuracy: {accuracy*100:.1f}%")
            print(f"  AI Action: {decision.action.value.upper()}")
            print(f"  Difficulty: {old_difficulty:.3f} → {self.difficulty:.3f}")
            print(f"  Change: {diff_change*100:+.1f}%")
            print(f"  Confidence: {decision.confidence*100:.1f}%")
            print(f"  Explanation: {decision.explanation}")
            print("=" * 60)
            
            # Update UI
            self.root.after(0, self._on_adaptation_received, decision, old_difficulty, diff_change)
            
            # Send feedback
            reward = (accuracy - 0.5) * 2
            loop.run_until_complete(
                self.engine.update_feedback(self.session_id, reward)
            )
            
        loop.close()
        
    def _on_adaptation_received(self, decision, old_difficulty, diff_change):
        """Update UI with adaptation results."""
        # Update difficulty display
        self.difficulty_progress['value'] = self.difficulty
        self.difficulty_value_label.config(text=f"{self.difficulty:.3f}")
        
        # Create AI message
        action_emoji = {
            'increase': '📈',
            'decrease': '📉',
            'maintain': '➡️'
        }.get(decision.action.value, '❓')
        
        message = f"{action_emoji} {decision.explanation} (Confidence: {decision.confidence*100:.0f}%)"
        
        color = '#4caf50' if decision.action.value == 'increase' else '#ff9800' if decision.action.value == 'decrease' else '#2196f3'
        
        self.ai_message.config(text=message, fg=color)
        
        # Enable new round button
        self.new_round_btn.config(state=tk.NORMAL)


def main():
    """Launch the memory game UI."""
    root = tk.Tk()
    app = MemoryGameUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
