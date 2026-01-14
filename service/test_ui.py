"""
Python UI Test for Adaptive Rehab AI

Simple Tkinter GUI to test the adaptation engine interactively.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
import time
from datetime import datetime

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule, StateVector
from adaptrehab.utils import setup_logging


class AdaptiveRehabTestUI:
    """Interactive GUI for testing the adaptation engine."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Adaptive Rehab AI - Test Interface")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize engine
        setup_logging("INFO")
        config_manager = ConfigManager()
        self.engine = AdaptationEngine(config_manager.to_dict())
        self.engine.register_module('rule_based', RuleBasedModule)
        
        # Session state
        self.session_id = None
        self.difficulty = 0.0
        self.round_num = 0
        self.is_session_active = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create all UI widgets."""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#667eea', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🧠 Adaptive Rehab AI - Test Interface",
            font=('Arial', 18, 'bold'),
            bg='#667eea',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Controls
        left_frame = tk.LabelFrame(
            main_frame,
            text="Controls",
            font=('Arial', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Session controls
        session_frame = tk.Frame(left_frame, bg='white')
        session_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = tk.Button(
            session_frame,
            text="▶ Start Session",
            command=self.start_session,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            cursor='hand2'
        )
        self.start_btn.pack(pady=5)
        
        self.end_btn = tk.Button(
            session_frame,
            text="⏹ End Session",
            command=self.end_session,
            bg='#f44336',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.end_btn.pack(pady=5)
        
        # Performance sliders
        perf_frame = tk.LabelFrame(
            left_frame,
            text="Simulate Performance",
            font=('Arial', 11, 'bold'),
            bg='white',
            padx=10,
            pady=10
        )
        perf_frame.pack(fill=tk.X, pady=20)
        
        # Accuracy slider
        tk.Label(perf_frame, text="Accuracy:", bg='white', font=('Arial', 10)).pack(anchor=tk.W)
        self.accuracy_var = tk.DoubleVar(value=0.5)
        self.accuracy_slider = tk.Scale(
            perf_frame,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.accuracy_var,
            bg='white',
            length=250
        )
        self.accuracy_slider.pack(fill=tk.X, pady=5)
        
        # Success rate slider
        tk.Label(perf_frame, text="Success Rate:", bg='white', font=('Arial', 10)).pack(anchor=tk.W, pady=(10, 0))
        self.success_var = tk.DoubleVar(value=0.5)
        self.success_slider = tk.Scale(
            perf_frame,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.success_var,
            bg='white',
            length=250
        )
        self.success_slider.pack(fill=tk.X, pady=5)
        
        # Reaction time slider
        tk.Label(perf_frame, text="Reaction Time (s):", bg='white', font=('Arial', 10)).pack(anchor=tk.W, pady=(10, 0))
        self.reaction_var = tk.DoubleVar(value=2.0)
        self.reaction_slider = tk.Scale(
            perf_frame,
            from_=0.5,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.reaction_var,
            bg='white',
            length=250
        )
        self.reaction_slider.pack(fill=tk.X, pady=5)
        
        # Adapt button
        self.adapt_btn = tk.Button(
            perf_frame,
            text="🤖 Get Adaptation",
            command=self.get_adaptation,
            bg='#667eea',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=25,
            height=2,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.adapt_btn.pack(pady=15)
        
        # Current stats
        stats_frame = tk.LabelFrame(
            left_frame,
            text="Current State",
            font=('Arial', 11, 'bold'),
            bg='white',
            padx=10,
            pady=10
        )
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.round_label = tk.Label(
            stats_frame,
            text="Round: 0",
            bg='white',
            font=('Arial', 12),
            anchor=tk.W
        )
        self.round_label.pack(fill=tk.X, pady=3)
        
        self.diff_label = tk.Label(
            stats_frame,
            text="Difficulty: 0.000",
            bg='white',
            font=('Arial', 12),
            anchor=tk.W
        )
        self.diff_label.pack(fill=tk.X, pady=3)
        
        # Difficulty progress bar
        self.diff_progress = ttk.Progressbar(
            stats_frame,
            mode='determinate',
            length=250,
            maximum=1.0
        )
        self.diff_progress.pack(fill=tk.X, pady=10)
        
        # Right panel - Log
        right_frame = tk.LabelFrame(
            main_frame,
            text="Adaptation Log",
            font=('Arial', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            width=50,
            height=30,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.log_text.tag_config('header', foreground='#569cd6', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('warning', foreground='#ce9178')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('info', foreground='#9cdcfe')
        
        self.log("Application initialized. Click 'Start Session' to begin.", 'info')
        
    def log(self, message, tag='info'):
        """Add message to log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'header')
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        
    def start_session(self):
        """Initialize a new adaptation session."""
        self.session_id = f"test_ui_{int(time.time())}"
        self.round_num = 0
        self.difficulty = 0.0
        
        # Run async initialization
        thread = threading.Thread(target=self._async_start_session)
        thread.start()
        
    def _async_start_session(self):
        """Async session initialization."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        patient_profile = {
            'patient_id': 'test_user',
            'condition': 'stroke',
            'baseline_performance': 0.5
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
            self.root.after(0, self._update_session_ui, True)
            self.root.after(0, self.log, f"✅ Session started: {self.session_id}", 'success')
            self.root.after(0, self.log, f"Starting difficulty: {self.difficulty:.3f}", 'info')
        else:
            self.root.after(0, self.log, "❌ Failed to start session", 'error')
            
        loop.close()
        
    def _update_session_ui(self, active):
        """Update UI based on session state."""
        if active:
            self.start_btn.config(state=tk.DISABLED)
            self.end_btn.config(state=tk.NORMAL)
            self.adapt_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.end_btn.config(state=tk.DISABLED)
            self.adapt_btn.config(state=tk.DISABLED)
            
    def get_adaptation(self):
        """Request adaptation decision."""
        if not self.is_session_active:
            self.log("⚠️ No active session", 'warning')
            return
            
        self.round_num += 1
        
        # Get slider values
        accuracy = self.accuracy_var.get()
        success_rate = self.success_var.get()
        reaction_time = self.reaction_var.get()
        
        # Run async adaptation
        thread = threading.Thread(
            target=self._async_get_adaptation,
            args=(accuracy, success_rate, reaction_time)
        )
        thread.start()
        
    def _async_get_adaptation(self, accuracy, success_rate, reaction_time):
        """Async adaptation computation."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create state
        state = StateVector(
            performance_metrics={
                'accuracy': accuracy,
                'success_rate': success_rate,
                'reaction_time': reaction_time,
                'error_rate': 1 - accuracy,
                'consistency': max(0.5, accuracy)
            },
            sensor_data={},
            task_state={
                'difficulty': self.difficulty,
                'round': self.round_num
            },
            timestamp=time.time(),
            session_id=self.session_id
        )
        
        # Get decision
        old_difficulty = self.difficulty
        decision = loop.run_until_complete(
            self.engine.compute_adaptation(self.session_id, state)
        )
        
        if decision:
            self.difficulty = decision.parameters.get('difficulty', self.difficulty)
            diff_change = self.difficulty - old_difficulty
            
            # Update UI
            self.root.after(0, self._update_adaptation_ui, decision, old_difficulty, diff_change)
            
            # Send feedback
            reward = (accuracy - 0.5) * 2
            loop.run_until_complete(
                self.engine.update_feedback(self.session_id, reward)
            )
        else:
            self.root.after(0, self.log, "❌ Failed to get adaptation", 'error')
            
        loop.close()
        
    def _update_adaptation_ui(self, decision, old_difficulty, diff_change):
        """Update UI with adaptation results."""
        # Log separator
        self.log("=" * 50, 'header')
        self.log(f"Round {self.round_num} Complete", 'header')
        self.log(f"  Accuracy: {self.accuracy_var.get():.2f}", 'info')
        self.log(f"  Success Rate: {self.success_var.get():.2f}", 'info')
        self.log(f"  Reaction Time: {self.reaction_var.get():.1f}s", 'info')
        
        # Action
        action_emoji = {
            'increase': '📈',
            'decrease': '📉',
            'maintain': '➡️'
        }.get(decision.action.value, '❓')
        
        action_tag = {
            'increase': 'success',
            'decrease': 'warning',
            'maintain': 'info'
        }.get(decision.action.value, 'info')
        
        self.log(f"{action_emoji} AI Action: {decision.action.value.upper()}", action_tag)
        
        # Difficulty change
        change_percent = diff_change * 100
        change_tag = 'success' if diff_change > 0 else 'warning' if diff_change < 0 else 'info'
        self.log(f"  Difficulty: {old_difficulty:.3f} → {self.difficulty:.3f}", 'info')
        self.log(f"  Change: {change_percent:+.1f}%", change_tag)
        self.log(f"  Confidence: {decision.confidence:.2f}", 'info')
        self.log(f"  📝 {decision.explanation}", 'info')
        
        # Update labels
        self.round_label.config(text=f"Round: {self.round_num}")
        self.diff_label.config(text=f"Difficulty: {self.difficulty:.3f}")
        self.diff_progress['value'] = self.difficulty
        
    def end_session(self):
        """End the current session."""
        if not self.is_session_active:
            return
            
        thread = threading.Thread(target=self._async_end_session)
        thread.start()
        
    def _async_end_session(self):
        """Async session termination."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.engine.end_session(self.session_id))
        
        self.is_session_active = False
        self.root.after(0, self._update_session_ui, False)
        self.root.after(0, self.log, f"⏹ Session ended. Total rounds: {self.round_num}", 'warning')
        
        loop.close()


def main():
    """Launch the UI."""
    root = tk.Tk()
    app = AdaptiveRehabTestUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
