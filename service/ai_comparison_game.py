"""
AI Module Comparison Demo Game

Compare Rule-based vs Fuzzy Logic vs Reinforcement Learning in real-time.
"""

import tkinter as tk
from tkinter import ttk
import asyncio
import time
from adaptrehab.modules.rule_based import RuleBasedModule
from adaptrehab.modules.fuzzy_logic import FuzzyLogicModule
from adaptrehab.modules.reinforcement_learning import ReinforcementLearningModule
from adaptrehab.modules.base_module import StateVector


class ComparisonGame:
    """Side-by-side comparison of three AI modules."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Module Comparison - Adaptive Rehab AI")
        self.root.geometry("1000x700")
        
        # Modules
        self.modules = {
            'rule_based': RuleBasedModule("rule_demo"),
            'fuzzy_logic': FuzzyLogicModule("fuzzy_demo"),
            'reinforcement_learning': ReinforcementLearningModule("rl_demo", {
                'exploration_rate': 0.1,  # Low for demo
                'learning_rate': 0.3
            })
        }
        
        self.current_module_name = 'rule_based'
        self.current_module = self.modules[self.current_module_name]
        
        # Game state
        self.difficulty = 0.5
        self.round_num = 0
        self.score = 0
        self.target_clicks = 5
        self.clicks_this_round = 0
        self.round_start_time = None
        self.history = {name: [] for name in self.modules.keys()}
        
        # Initialize modules
        asyncio.run(self._init_modules())
        
        self._create_ui()
        
    async def _init_modules(self):
        """Initialize all AI modules."""
        for module in self.modules.values():
            await module.initialize({}, {})
    
    def _create_ui(self):
        """Create the UI."""
        # Title
        title = tk.Label(
            self.root,
            text="🤖 AI Module Comparison",
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=20
        )
        title.pack(fill=tk.X)
        
        # Module selector
        selector_frame = tk.Frame(self.root, bg="#ecf0f1", pady=10)
        selector_frame.pack(fill=tk.X)
        
        tk.Label(
            selector_frame,
            text="AI Module:",
            font=("Arial", 12),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=20)
        
        self.module_var = tk.StringVar(value='rule_based')
        for name, display in [
            ('rule_based', 'Rule-Based (Threshold)'),
            ('fuzzy_logic', 'Fuzzy Logic (Linguistic)'),
            ('reinforcement_learning', 'Reinforcement Learning (Q-Learn)')
        ]:
            tk.Radiobutton(
                selector_frame,
                text=display,
                variable=self.module_var,
                value=name,
                font=("Arial", 11),
                bg="#ecf0f1",
                command=self._switch_module
            ).pack(side=tk.LEFT, padx=10)
        
        # Stats panel
        stats_frame = tk.Frame(self.root, bg="#34495e", pady=15)
        stats_frame.pack(fill=tk.X)
        
        self.round_label = tk.Label(
            stats_frame,
            text="Round: 0",
            font=("Arial", 14),
            bg="#34495e",
            fg="white"
        )
        self.round_label.pack(side=tk.LEFT, padx=30)
        
        self.diff_label = tk.Label(
            stats_frame,
            text="Difficulty: 0.50",
            font=("Arial", 14),
            bg="#34495e",
            fg="#f39c12"
        )
        self.diff_label.pack(side=tk.LEFT, padx=30)
        
        self.score_label = tk.Label(
            stats_frame,
            text="Score: 0",
            font=("Arial", 14),
            bg="#34495e",
            fg="#2ecc71"
        )
        self.score_label.pack(side=tk.LEFT, padx=30)
        
        # Game area
        game_frame = tk.Frame(self.root, bg="#ecf0f1")
        game_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        instruction = tk.Label(
            game_frame,
            text=f"Click the button {self.target_clicks} times as fast as you can!",
            font=("Arial", 14),
            bg="#ecf0f1"
        )
        instruction.pack(pady=20)
        
        self.click_button = tk.Button(
            game_frame,
            text="CLICK ME!",
            font=("Arial", 20, "bold"),
            bg="#3498db",
            fg="white",
            width=15,
            height=3,
            command=self._on_click
        )
        self.click_button.pack(pady=30)
        
        self.progress_label = tk.Label(
            game_frame,
            text=f"0 / {self.target_clicks}",
            font=("Arial", 16),
            bg="#ecf0f1"
        )
        self.progress_label.pack()
        
        # AI Decision panel
        decision_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        decision_frame.pack(fill=tk.X)
        
        tk.Label(
            decision_frame,
            text="AI Decision:",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack()
        
        self.decision_label = tk.Label(
            decision_frame,
            text="Waiting for first round...",
            font=("Arial", 11),
            bg="#2c3e50",
            fg="#95a5a6",
            wraplength=900
        )
        self.decision_label.pack(pady=5)
        
        # Comparison chart
        chart_frame = tk.LabelFrame(
            self.root,
            text="Performance History",
            font=("Arial", 11, "bold"),
            bg="#ecf0f1",
            pady=10
        )
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.chart_canvas = tk.Canvas(
            chart_frame,
            bg="white",
            height=150
        )
        self.chart_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Start first round
        self._start_round()
    
    def _switch_module(self):
        """Switch to a different AI module."""
        new_module_name = self.module_var.get()
        if new_module_name != self.current_module_name:
            self.current_module_name = new_module_name
            self.current_module = self.modules[new_module_name]
            print(f"Switched to: {new_module_name}")
    
    def _start_round(self):
        """Start a new round."""
        self.round_num += 1
        self.clicks_this_round = 0
        self.round_start_time = time.time()
        
        self.round_label.config(text=f"Round: {self.round_num}")
        self.progress_label.config(text=f"0 / {self.target_clicks}")
        self.click_button.config(state=tk.NORMAL)
    
    def _on_click(self):
        """Handle button click."""
        self.clicks_this_round += 1
        self.score += 1
        
        self.progress_label.config(text=f"{self.clicks_this_round} / {self.target_clicks}")
        self.score_label.config(text=f"Score: {self.score}")
        
        if self.clicks_this_round >= self.target_clicks:
            self._end_round()
    
    def _end_round(self):
        """End the round and get AI adaptation."""
        self.click_button.config(state=tk.DISABLED)
        
        # Calculate performance
        round_time = time.time() - self.round_start_time
        expected_time = 2.0 + self.difficulty * 3.0  # Harder = more time expected
        performance = min(1.0, expected_time / round_time)  # Faster = better
        
        # Create state
        state = StateVector(
            performance_metrics={'accuracy': performance},
            sensor_data={},
            task_state={'difficulty': self.difficulty, 'round': self.round_num},
            timestamp=time.time(),
            session_id="comparison_demo"
        )
        
        # Get AI decision
        decision = asyncio.run(self.current_module.compute_adaptation(state))
        
        # Record history
        self.history[self.current_module_name].append({
            'round': self.round_num,
            'difficulty': self.difficulty,
            'performance': performance,
            'action': decision.action.value
        })
        
        # Update difficulty
        old_diff = self.difficulty
        diff_change = decision.parameters.get('difficulty_change', 0.0)
        self.difficulty = max(0.0, min(1.0, self.difficulty + diff_change))
        
        # Update UI
        self.diff_label.config(text=f"Difficulty: {self.difficulty:.2f}")
        
        # Show decision
        decision_text = (
            f"Action: {decision.action.value.upper()} | "
            f"Performance: {performance:.2f} | "
            f"Difficulty: {old_diff:.2f} → {self.difficulty:.2f} | "
            f"Time: {round_time:.2f}s\n"
            f"{decision.explanation}"
        )
        self.decision_label.config(text=decision_text)
        
        # Update chart
        self._update_chart()
        
        # Next round after delay
        self.root.after(2000, self._start_round)
    
    def _update_chart(self):
        """Update performance chart."""
        self.chart_canvas.delete("all")
        
        width = self.chart_canvas.winfo_width()
        height = self.chart_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Draw axes
        margin = 40
        self.chart_canvas.create_line(
            margin, height - margin,
            width - margin, height - margin,
            width=2
        )
        self.chart_canvas.create_line(
            margin, margin,
            margin, height - margin,
            width=2
        )
        
        # Labels
        self.chart_canvas.create_text(
            width // 2, height - 10,
            text="Round",
            font=("Arial", 9)
        )
        self.chart_canvas.create_text(
            10, height // 2,
            text="Difficulty",
            font=("Arial", 9),
            angle=90
        )
        
        # Plot data for current module
        history = self.history[self.current_module_name]
        if len(history) < 2:
            return
        
        max_rounds = max(h['round'] for h in history)
        
        points = []
        for h in history:
            x = margin + (width - 2 * margin) * (h['round'] / max_rounds)
            y = height - margin - (height - 2 * margin) * h['difficulty']
            points.append((x, y))
        
        # Draw line
        for i in range(len(points) - 1):
            self.chart_canvas.create_line(
                points[i][0], points[i][1],
                points[i + 1][0], points[i + 1][1],
                fill="#3498db",
                width=2
            )
        
        # Draw points
        for x, y in points:
            self.chart_canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill="#e74c3c",
                outline="#c0392b",
                width=2
            )
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


if __name__ == '__main__':
    app = ComparisonGame()
    app.run()
