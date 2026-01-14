"""
Simple Reaction Time Game with AI Adaptation
Click the colored buttons as quickly as possible!
"""

import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import time
import random
from typing import Optional

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule, StateVector
from adaptrehab.utils import setup_logging


class ReactionGameUI:
    """Simple reaction time game with adaptive difficulty."""
    
    COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎯 Reaction Time Game - AI Adaptive")
        self.root.geometry("800x700")
        self.root.configure(bg='#f5f7fa')
        
        # Game state
        self.difficulty = 0.0
        self.session_id = None
        self.is_session_active = False
        self.engine = None
        
        # Round tracking
        self.round_num = 0
        self.targets_shown = 0
        self.targets_hit = 0
        self.total_reaction_time = 0
        self.start_time = None
        self.current_target = None
        self.target_start_time = None
        
        # Game settings
        self.is_playing = False
        self.game_thread = None
        
        self._init_engine()
        self._create_widgets()
        
    def _init_engine(self):
        """Initialize the adaptation engine."""
        setup_logging("INFO")
        config_manager = ConfigManager()
        self.engine = AdaptationEngine(config_manager.to_dict())
        self.engine.register_module('rule_based', RuleBasedModule)
        
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title = tk.Label(
            self.root,
            text="🎯 Reaction Time Game",
            font=('Arial', 24, 'bold'),
            bg='#f5f7fa',
            fg='#2c3e50'
        )
        title.pack(pady=20)
        
        # Stats Panel
        stats_frame = tk.Frame(self.root, bg='#f5f7fa')
        stats_frame.pack(pady=10)
        
        # Round
        round_box = tk.Frame(stats_frame, bg='white', relief=tk.RAISED, bd=2)
        round_box.grid(row=0, column=0, padx=10)
        tk.Label(round_box, text="Round", font=('Arial', 10), bg='white', fg='#7f8c8d').pack(padx=20, pady=(5,0))
        self.round_label = tk.Label(round_box, text="0", font=('Arial', 24, 'bold'), bg='white', fg='#667eea')
        self.round_label.pack(padx=20, pady=(0,5))
        
        # Hit Rate
        hits_box = tk.Frame(stats_frame, bg='white', relief=tk.RAISED, bd=2)
        hits_box.grid(row=0, column=1, padx=10)
        tk.Label(hits_box, text="Hit Rate", font=('Arial', 10), bg='white', fg='#7f8c8d').pack(padx=20, pady=(5,0))
        self.hits_label = tk.Label(hits_box, text="0%", font=('Arial', 24, 'bold'), bg='white', fg='#667eea')
        self.hits_label.pack(padx=20, pady=(0,5))
        
        # Avg Speed
        speed_box = tk.Frame(stats_frame, bg='white', relief=tk.RAISED, bd=2)
        speed_box.grid(row=0, column=2, padx=10)
        tk.Label(speed_box, text="Avg Speed", font=('Arial', 10), bg='white', fg='#7f8c8d').pack(padx=20, pady=(5,0))
        self.speed_label = tk.Label(speed_box, text="0ms", font=('Arial', 24, 'bold'), bg='white', fg='#667eea')
        self.speed_label.pack(padx=20, pady=(0,5))
        
        # Score
        score_box = tk.Frame(stats_frame, bg='white', relief=tk.RAISED, bd=2)
        score_box.grid(row=0, column=3, padx=10)
        tk.Label(score_box, text="Score", font=('Arial', 10), bg='white', fg='#7f8c8d').pack(padx=20, pady=(5,0))
        self.score_label = tk.Label(score_box, text="0/0", font=('Arial', 24, 'bold'), bg='white', fg='#667eea')
        self.score_label.pack(padx=20, pady=(0,5))
        
        # Difficulty Progress
        diff_frame = tk.Frame(self.root, bg='#f5f7fa')
        diff_frame.pack(pady=10, fill=tk.X, padx=50)
        
        tk.Label(
            diff_frame,
            text="Difficulty Level",
            font=('Arial', 12, 'bold'),
            bg='#f5f7fa',
            fg='#2c3e50'
        ).pack()
        
        self.difficulty_progress = ttk.Progressbar(
            diff_frame,
            mode='determinate',
            maximum=1.0,
            value=0.0,
            length=400
        )
        self.difficulty_progress.pack(pady=5)
        
        self.difficulty_value_label = tk.Label(
            diff_frame,
            text="0.000",
            font=('Arial', 10),
            bg='#f5f7fa',
            fg='#7f8c8d'
        )
        self.difficulty_value_label.pack()
        
        # Game Area
        self.game_frame = tk.Frame(self.root, bg='#ecf0f1', width=600, height=300)
        self.game_frame.pack(pady=20, padx=50)
        self.game_frame.pack_propagate(False)
        
        self.instruction_label = tk.Label(
            self.game_frame,
            text="Click START to begin!\n\nQuick! Click the colored buttons when they appear.",
            font=('Arial', 14),
            bg='#ecf0f1',
            fg='#7f8c8d',
            justify=tk.CENTER
        )
        self.instruction_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Control Buttons
        btn_frame = tk.Frame(self.root, bg='#f5f7fa')
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Game",
            font=('Arial', 14, 'bold'),
            bg='#667eea',
            fg='white',
            padx=30,
            pady=10,
            cursor='hand2',
            relief=tk.RAISED,
            bd=3,
            command=self.start_game
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Stop Round",
            font=('Arial', 14, 'bold'),
            bg='#95a5a6',
            fg='white',
            padx=30,
            pady=10,
            cursor='hand2',
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED,
            command=self.stop_round
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # AI Status
        self.ai_message = tk.Label(
            self.root,
            text="🤖 Click Start to connect to AI adaptation engine...",
            font=('Arial', 11),
            bg='#f5f7fa',
            fg='#7f8c8d',
            wraplength=700,
            justify=tk.CENTER
        )
        self.ai_message.pack(pady=10)
        
    def start_game(self):
        """Start the game session."""
        if not self.is_session_active:
            self.session_id = f"reaction_game_{int(time.time())}"
            thread = threading.Thread(target=self._async_init_session)
            thread.start()
        else:
            self.start_new_round()
            
    def _async_init_session(self):
        """Initialize AI session asynchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        patient_profile = {
            'patient_id': 'reaction_player',
            'condition': 'motor',
            'baseline_performance': 0.5,
            'threshold_success': 0.70,  # 70%+ hit rate to increase
            'threshold_failure': 0.40    # Below 40% to decrease
        }
        
        task_config = {
            'task_type': 'reaction',
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
        self.ai_message.config(
            text="✅ AI Connected! Click Start Game to begin your first round.",
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
        """Start a new round."""
        if self.is_playing:
            return
            
        self.round_num += 1
        self.targets_shown = 0
        self.targets_hit = 0
        self.total_reaction_time = 0
        self.start_time = time.time()
        self.is_playing = True
        
        self.round_label.config(text=str(self.round_num))
        self.hits_label.config(text="0%")
        self.speed_label.config(text="0ms")
        self.score_label.config(text="0/0")
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.instruction_label.config(text="Get Ready...")
        
        print(f"\n▶️  Starting Round {self.round_num} (Difficulty: {self.difficulty:.3f})")
        
        # Start game loop in background thread
        self.game_thread = threading.Thread(target=self._game_loop)
        self.game_thread.start()
        
    def _game_loop(self):
        """Main game loop - shows targets."""
        time.sleep(1)  # Countdown
        
        # Calculate difficulty settings
        num_targets = max(5, int(10 + self.difficulty * 20))  # 5-30 targets
        target_duration = max(0.5, 2.0 - self.difficulty * 1.5)  # 2.0s to 0.5s
        gap_duration = max(0.3, 1.0 - self.difficulty * 0.7)  # 1.0s to 0.3s
        
        for i in range(num_targets):
            if not self.is_playing:
                break
                
            # Show target
            self.root.after(0, self._show_target, target_duration)
            time.sleep(target_duration + gap_duration)
            
        # Round complete
        if self.is_playing:
            self.root.after(0, self.stop_round)
            
    def _show_target(self, duration: float):
        """Show a target button."""
        if self.current_target:
            self.current_target.destroy()
            
        self.instruction_label.config(text="")
        
        # Random position and size
        size = max(50, int(120 - self.difficulty * 70))  # 120px to 50px
        x = random.randint(size, 600 - size)
        y = random.randint(size, 300 - size)
        color = random.choice(self.COLORS)
        
        self.current_target = tk.Button(
            self.game_frame,
            text="CLICK!",
            font=('Arial', 12, 'bold'),
            bg=color,
            fg='white',
            width=size//10,
            height=size//25,
            cursor='hand2',
            command=self._on_target_clicked
        )
        self.current_target.place(x=x, y=y, anchor=tk.CENTER)
        
        self.targets_shown += 1
        self.target_start_time = time.time()
        self.score_label.config(text=f"{self.targets_hit}/{self.targets_shown}")
        
        # Auto-remove after duration
        self.root.after(int(duration * 1000), self._remove_target)
        
    def _remove_target(self):
        """Remove current target."""
        if self.current_target:
            self.current_target.destroy()
            self.current_target = None
            self.target_start_time = None
            
    def _on_target_clicked(self):
        """Handle target click."""
        if self.target_start_time:
            reaction_time = time.time() - self.target_start_time
            self.total_reaction_time += reaction_time
            self.targets_hit += 1
            
            # Update stats
            hit_rate = (self.targets_hit / self.targets_shown) * 100
            avg_speed = (self.total_reaction_time / self.targets_hit) * 1000
            
            self.hits_label.config(text=f"{hit_rate:.0f}%")
            self.speed_label.config(text=f"{avg_speed:.0f}ms")
            self.score_label.config(text=f"{self.targets_hit}/{self.targets_shown}")
            
        self._remove_target()
        
    def stop_round(self):
        """Stop the current round."""
        self.is_playing = False
        self._remove_target()
        
        if self.targets_shown > 0:
            self.complete_round()
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def complete_round(self):
        """Complete the round and get AI adaptation."""
        duration = time.time() - self.start_time
        hit_rate = self.targets_hit / self.targets_shown if self.targets_shown > 0 else 0
        avg_reaction_time = self.total_reaction_time / self.targets_hit if self.targets_hit > 0 else 0
        
        self.instruction_label.config(
            text=f"Round Complete!\n{self.targets_hit}/{self.targets_shown} hits ({hit_rate*100:.0f}%)",
            fg='#2c3e50'
        )
        
        self.ai_message.config(text="🤖 AI analyzing your performance...", fg='#ff9800')
        self.root.update()
        
        # Get AI adaptation
        thread = threading.Thread(target=self._async_get_adaptation, args=(hit_rate, avg_reaction_time))
        thread.start()
        
    def _async_get_adaptation(self, hit_rate: float, avg_reaction_time: float):
        """Get adaptation decision from AI."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        old_difficulty = self.difficulty
        
        # Create state
        state = StateVector(
            performance_metrics={
                'accuracy': hit_rate,
                'success_rate': hit_rate,
                'reaction_time': avg_reaction_time,
                'speed': 1.0 / (avg_reaction_time + 0.001),
                'consistency': min(hit_rate * 1.1, 1.0)
            },
            sensor_data={},
            task_state={
                'difficulty': self.difficulty,
                'round': self.round_num,
                'targets_shown': self.targets_shown,
                'targets_hit': self.targets_hit
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
            print(f"  Hit Rate: {hit_rate*100:.1f}%")
            print(f"  Avg Reaction: {avg_reaction_time*1000:.0f}ms")
            print(f"  AI Action: {decision.action.value.upper()}")
            print(f"  Difficulty: {old_difficulty:.3f} → {self.difficulty:.3f}")
            print(f"  Change: {diff_change*100:+.1f}%")
            print(f"  Confidence: {decision.confidence*100:.1f}%")
            print(f"  Explanation: {decision.explanation}")
            print("=" * 60)
            
            # Update UI
            self.root.after(0, self._on_adaptation_received, decision, old_difficulty, diff_change)
            
            # Send feedback
            reward = (hit_rate - 0.5) * 2
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
        
        message = f"{action_emoji} {decision.explanation}"
        
        color = '#4caf50' if decision.action.value == 'increase' else '#ff9800' if decision.action.value == 'decrease' else '#2196f3'
        
        self.ai_message.config(text=message, fg=color)
        
        # Enable buttons
        self.start_btn.config(state=tk.NORMAL, text="▶ Next Round")
        self.stop_btn.config(state=tk.DISABLED)


def main():
    """Launch the reaction game UI."""
    root = tk.Tk()
    app = ReactionGameUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
