#!/usr/bin/env python3
"""
Visual Guidance Log Plotter Application
========================================
Interactive plotting application for visual guidance system logs.
Navigate between tests (GUIDED mode sessions) and different plot types.

Usage:
    python log_plotter_app.py [log_file_path]
    
If no log file is provided, it will open the latest log file from output/logs/
"""

import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for better interactivity

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re
import os
import sys
import glob
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class LogParser:
    """Parser for visual guidance log files."""
    
    @staticmethod
    def create_empty_data_dict():
        """Create an empty dictionary for storing parsed data."""
        return {
            "frame_number": [],
            "timestamps": [],
            "interceptor_location": [],
            "target_location": [],
            "altitude": [],
            "target_altitude": [],
            "attitude": [],  # Roll, Pitch, Yaw in degrees
            "velocity": [],
            "velocity_norm": [],
            "target_velocity": [],
            "angular_velocity": [],
            "linear_velocity": [],
            "distance_to_target": [],
            "speed": [],
            "pixel_errors": [],
            "virtual_pixel_errors": [],
            "pixel_x": [],
            "pixel_y": [],
            "depth": [],
            "depth_virtual": [],
            "desired_accel_initial": [],
            "desired_accel_final": [],
            "xyz_pseudo": [],
            "control_commands": [],  # Pitch, Yaw, Roll, Thrust
            "throttle": [],
            "bs_throttle": [],
            "bs_roll": [],
            "bs_levant": [],  # Levant differentiator for throttle
            "levant_alt_state": [],  # Levant altitude state: z1_a, z1_r, z2_r
            "bs_roll_levant": [],  # Levant differentiator for roll
            "bs_state": [],  # Backstepping state data
            "error_acc": [],
            "virtual_east_accel": [],
            "virtual_down_accel": [],
            "target_heading": [],
            "error_old_xy": [],
            "error_old_z": [],
            "raw_imu": [],  # Raw IMU accelerometer data [x, y, z]
        }
    
    @staticmethod
    def parse_log_file(log_file_path):
        """
        Parse log file and segment by GUIDED mode sessions.
        Each session where mode changes to GUIDED is considered a separate test.
        """
        sessions = []
        current_session_data = None
        
        with open(log_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Detect mode change to GUIDED (start of a test)
                if "Drone Mode: GUIDED" in line:
                    if current_session_data is None:
                        current_session_data = LogParser.create_empty_data_dict()
                        sessions.append(current_session_data)
                
                # Detect mode change away from GUIDED (end of test)
                elif "Drone Mode:" in line and "GUIDED" not in line:
                    current_session_data = None
                
                # Parse data only during GUIDED mode
                if current_session_data is not None:
                    LogParser._parse_line(line, current_session_data)
        
        return sessions
    
    @staticmethod
    def _parse_line(line, data):
        """Parse a single log line and extract relevant data."""
        try:
            # Extract timestamp
            if ' - ' in line:
                timestamp_str = line.split(' - ')[0]
            else:
                timestamp_str = None
            
            # Frame Number
            if "Frame Number:" in line:
                match = re.search(r'Frame Number:\s*(\d+)', line)
                if match:
                    data["frame_number"].append(int(match.group(1)))
                    if timestamp_str:
                        data["timestamps"].append(timestamp_str)
            
            # Interceptor Location
            elif "Interceptor Location:" in line:
                match = re.search(r'\(([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\)', line)
                if match:
                    data["interceptor_location"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Altitude
            elif line.startswith("2") and "Altitude:" in line and "Target" not in line and "Relative" not in line:
                match = re.search(r'Altitude:\s*([\d\.\-]+)', line)
                if match:
                    data["altitude"].append(float(match.group(1)))
            
            # Attitude (R,P,Y)
            elif "Attitude (R,P,Y):" in line:
                match = re.search(r'\(([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\)', line)
                if match:
                    data["attitude"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Velocity
            elif "Velocity:" in line and "Target" not in line and "Angular" not in line and "Linear" not in line:
                match = re.search(r'\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    vel = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
                    data["velocity"].append(vel)
                    data["velocity_norm"].append(np.linalg.norm(vel))
            
            # Target Location
            elif "Target Location:" in line:
                match = re.search(r'\(([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\)', line)
                if match:
                    data["target_location"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Target Altitude
            elif "Target Altitude:" in line:
                match = re.search(r'Target Altitude:\s*([\d\.\-]+)', line)
                if match:
                    data["target_altitude"].append(float(match.group(1)))
            
            # Target Velocity
            elif "Target Velocity:" in line:
                match = re.search(r'Vx:\s*([\d\.\-]+),\s*Vy:\s*([\d\.\-]+),\s*Vz:\s*([\d\.\-]+)', line)
                if match:
                    data["target_velocity"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Distance to target
            elif "Distance to target:" in line:
                match = re.search(r'Distance to target:\s*([\d\.\-]+)', line)
                if match:
                    data["distance_to_target"].append(float(match.group(1)))
            
            # Speed
            elif "Speed:" in line:
                match = re.search(r'Speed:\s*([\d\.\-]+)', line)
                if match:
                    data["speed"].append(float(match.group(1)))
            
            # Angular Velocity
            elif "Angular Velocity:" in line:
                match = re.search(r'\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["angular_velocity"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Linear Velocity
            elif "Linear Velocity:" in line:
                match = re.search(r'\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["linear_velocity"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Virtual Pixel X, Y, Depth
            elif "Virtual Pixel X:" in line:
                match = re.search(r'Virtual Pixel X:\s*([\d\.\-]+),\s*Virtual Pixel Y:\s*([\d\.\-]+),\s*Depth:\s*([\d\.\-]+)', line)
                if match:
                    data["pixel_x"].append(float(match.group(1)))
                    data["pixel_y"].append(float(match.group(2)))
                    data["depth"].append(float(match.group(3)))
            
            # Depth Virtual
            elif "Depth Virtual:" in line:
                match = re.search(r'Depth Virtual:\s*([\d\.\-]+)', line)
                if match:
                    data["depth_virtual"].append(float(match.group(1)))
            
            # Pixel errors
            elif "Pixel errors:" in line and "Virtual" not in line:
                match = re.search(r'\(([\d\.\-]+),\s*([\d\.\-]+)\)', line)
                if match:
                    data["pixel_errors"].append([float(match.group(1)), float(match.group(2))])
            
            # Virtual Pixel errors
            elif "Virtual Pixel errors:" in line:
                match = re.search(r'\(([\d\.\-]+),\s*([\d\.\-]+)\)', line)
                if match:
                    data["virtual_pixel_errors"].append([float(match.group(1)), float(match.group(2))])
            
            # Desired Acceleration (initial)
            elif "Desired Acceleration (initial):" in line:
                match = re.search(r'\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["desired_accel_initial"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Accel Desired (final)
            elif "Accel Desired (final):" in line:
                match = re.search(r'\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["desired_accel_final"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # XYZPseudoFrame
            elif "XYZPseudoFrame:" in line:
                match = re.search(r'\[\s*([\d\.\-e]+)\s+([\d\.\-e]+)\s+([\d\.\-e]+)\s*\]', line)
                if match:
                    data["xyz_pseudo"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
            
            # Target Heading New
            elif "Target Heading New:" in line:
                match = re.search(r'Target Heading New:\s*([\d\.\-]+)', line)
                if match:
                    data["target_heading"].append(float(match.group(1)))
            
            # Error ACC
            elif "Error ACC:" in line:
                match = re.search(r'Error ACC:\s*([\d\.\-]+)', line)
                if match:
                    data["error_acc"].append(float(match.group(1)))
            
            # Virtual East Acceleration
            elif "Virtual East Acceleration:" in line:
                match = re.search(r'Virtual East Acceleration:\s*([\d\.\-]+)', line)
                if match:
                    data["virtual_east_accel"].append(float(match.group(1)))
            
            # Virtual Down Acceleration
            elif "Virtual Down Acceleration:" in line:
                match = re.search(r'Virtual Down Acceleration:\s*([\d\.\-]+)', line)
                if match:
                    data["virtual_down_accel"].append(float(match.group(1)))
            
            # Control Commands
            elif "Control Commands - Pitch:" in line:
                match = re.search(r'Pitch:\s*([\d\.\-]+),\s*Yaw:\s*([\d\.\-]+),\s*Roll:\s*([\d\.\-]+),\s*Thrust:\s*([\d\.\-]+)', line)
                if match:
                    data["control_commands"].append([
                        float(match.group(1)), float(match.group(2)), 
                        float(match.group(3)), float(match.group(4))
                    ])
                    data["throttle"].append(float(match.group(4)))
            
            # BS_THROTTLE
            elif "[BS_THROTTLE]" in line and "thr=" in line:
                match = re.search(r'thr=([\d\.\-]+),\s*alt_err=([\d\.\-]+)m,\s*rate_err=([\d\.\-]+)m/s,\s*a_cmd=([\d\.\-]+)', line)
                if match:
                    data["bs_throttle"].append({
                        'thr': float(match.group(1)),
                        'alt_err': float(match.group(2)),
                        'rate_err': float(match.group(3)),
                        'a_cmd': float(match.group(4))
                    })
            
            # BS_ROLL
            elif "[BS_ROLL]" in line and "LEVANT" not in line:
                match = re.search(r'phi=([\d\.\-]+)deg,\s*east_err=([\d\.\-]+)m,\s*vel_err=([\d\.\-]+)m/s,\s*a_lat=([\d\.\-]+)', line)
                if match:
                    data["bs_roll"].append({
                        'phi': float(match.group(1)),
                        'east_err': float(match.group(2)),
                        'vel_err': float(match.group(3)),
                        'a_lat': float(match.group(4))
                    })
            
            # BS_LEVANT (Levant differentiator for throttle/altitude)
            elif "[BS_LEVANT]" in line:
                match = re.search(r'rate_hat=([\d\.\-]+)m/s,\s*accel_hat=([\d\.\-]+)m/s', line)
                if match:
                    data["bs_levant"].append({
                        'rate_hat': float(match.group(1)),
                        'accel_hat': float(match.group(2))
                    })
            
            # BS_ROLL_LEVANT (Levant differentiator for roll/lateral)
            elif "[BS_ROLL_LEVANT]" in line:
                match = re.search(r'vel_hat=([\d\.\-]+)m/s,\s*accel_hat=([\d\.\-]+)m/s', line)
                if match:
                    data["bs_roll_levant"].append({
                        'vel_hat': float(match.group(1)),
                        'accel_hat': float(match.group(2))
                    })
            
            # LEVANT_ALT_OUT (Levant altitude state: z1_a, z1_r, z2_r, z2_r)
            elif "[LEVANT_ALT_OUT]" in line:
                match = re.search(r'next_state=\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["levant_alt_state"].append({
                        'z1_a': float(match.group(1)),  # Altitude estimate
                        'z1_r': float(match.group(2)),  # Rate estimate (outer)
                        'z2_r': float(match.group(3)),  # Rate estimate (inner)
                        'z2_a': float(match.group(4))   # Acceleration estimate
                    })
            
            # BS_STATE (drone state for backstepping)
            elif "[BS_STATE]" in line:
                match = re.search(r'drone_alt=([\d\.\-]+)m,\s*target_alt=([\d\.\-]+)m,\s*drone_vz=([\d\.\-]+)m/s,\s*drone_az=([\d\.\-]+)m/s', line)
                if match:
                    data["bs_state"].append({
                        'drone_alt': float(match.group(1)),
                        'target_alt': float(match.group(2)),
                        'drone_vz': float(match.group(3)),
                        'drone_az': float(match.group(4))
                    })
            
            # Error Old XY
            elif "Error Old XY:" in line:
                match = re.search(r'Error Old XY:\s*([\d\.\-e]+)', line)
                if match:
                    data["error_old_xy"].append(float(match.group(1)))
            
            # Error Old Z
            elif "Error Old Z:" in line:
                match = re.search(r'Error Old Z:\s*([\d\.\-e]+)', line)
                if match:
                    data["error_old_z"].append(float(match.group(1)))
            
            # BS_ACCEL_MEAS raw_imu
            elif "[BS_ACCEL_MEAS] raw_imu=" in line:
                match = re.search(r'raw_imu=\[([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\]', line)
                if match:
                    data["raw_imu"].append([
                        float(match.group(1)), float(match.group(2)), float(match.group(3))
                    ])
                    
        except (AttributeError, ValueError, IndexError) as e:
            pass  # Skip lines that don't match expected format


class PlotterApp:
    """Main application class for log plotting."""
    
    # Define all available plot types
    PLOT_TYPES = [
        ("3D Trajectory", "plot_3d_trajectory"),
        ("Altitude vs Time", "plot_altitude"),
        ("Distance to Target", "plot_distance"),
        ("Velocity Components", "plot_velocity"),
        ("Velocity Norm & Speed", "plot_speed"),
        ("Attitude (R,P,Y)", "plot_attitude"),
        ("Pixel Errors", "plot_pixel_errors"),
        ("Depth", "plot_depth"),
        ("Desired Acceleration (Initial)", "plot_accel_initial"),
        ("Desired Acceleration (Final)", "plot_accel_final"),
        ("XYZ Pseudo Frame", "plot_xyz_pseudo"),
        ("Control Commands", "plot_control_commands"),
        ("Throttle", "plot_throttle"),
        ("Backstepping Throttle", "plot_bs_throttle"),
        ("Backstepping Roll", "plot_bs_roll"),
        ("Levant Estimators", "plot_levant"),
        ("Levant Altitude State", "plot_levant_alt_state"),
        ("Backstepping State", "plot_bs_state"),
        ("Virtual Accelerations", "plot_virtual_accel"),
        ("Error XY & Z", "plot_errors"),
        ("Raw IMU Accelerometer", "plot_raw_imu"),
    ]
    
    def __init__(self, root, log_file_path=None):
        self.root = root
        self.root.title("Visual Guidance Log Plotter")
        self.root.geometry("1400x900")
        
        # Data storage
        self.sessions = []
        self.current_test_index = 0
        self.current_plot_index = 0
        self.log_file_path = log_file_path
        
        # Setup UI
        self._setup_ui()
        
        # Load log file if provided
        if log_file_path:
            self._load_log_file(log_file_path)
        else:
            self._load_latest_log()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel (top)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # File selection
        file_frame = ttk.LabelFrame(control_frame, text="Log File", padding="5")
        file_frame.pack(side=tk.LEFT, padx=5)
        
        self.file_label = ttk.Label(file_frame, text="No file loaded", width=50)
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(file_frame, text="Open...", command=self._open_file_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Reload", command=self._reload_file).pack(side=tk.LEFT, padx=5)
        
        # Test navigation
        test_frame = ttk.LabelFrame(control_frame, text="Test Navigation", padding="5")
        test_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="◀ Prev Test", command=self._prev_test).pack(side=tk.LEFT, padx=2)
        self.test_label = ttk.Label(test_frame, text="Test: 0/0", width=15)
        self.test_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="Next Test ▶", command=self._next_test).pack(side=tk.LEFT, padx=2)
        
        # Plot type selection
        plot_frame = ttk.LabelFrame(control_frame, text="Plot Type", padding="5")
        plot_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.plot_combo = ttk.Combobox(plot_frame, values=[p[0] for p in self.PLOT_TYPES], 
                                        state="readonly", width=30)
        self.plot_combo.current(0)
        self.plot_combo.pack(side=tk.LEFT, padx=5)
        self.plot_combo.bind("<<ComboboxSelected>>", self._on_plot_type_change)
        
        ttk.Button(plot_frame, text="◀ Prev", command=self._prev_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(plot_frame, text="Next ▶", command=self._next_plot).pack(side=tk.LEFT, padx=2)
        
        # View options
        view_frame = ttk.LabelFrame(control_frame, text="View Options", padding="5")
        view_frame.pack(side=tk.LEFT, padx=5)
        
        self.show_all_tests = tk.BooleanVar(value=False)
        ttk.Checkbutton(view_frame, text="Show all tests", variable=self.show_all_tests,
                       command=self._update_plot).pack(side=tk.LEFT, padx=5)
        
        # Figure frame (center)
        fig_frame = ttk.Frame(main_frame)
        fig_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(14, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        toolbar_frame = ttk.Frame(fig_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Status bar (bottom)
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)
        
        # Keyboard bindings
        self.root.bind("<Left>", lambda e: self._prev_plot())
        self.root.bind("<Right>", lambda e: self._next_plot())
        self.root.bind("<Up>", lambda e: self._prev_test())
        self.root.bind("<Down>", lambda e: self._next_test())
        self.root.bind("<Home>", lambda e: self._first_plot())
        self.root.bind("<End>", lambda e: self._last_plot())
    
    def _open_file_dialog(self):
        """Open file dialog to select a log file."""
        initial_dir = os.path.join(os.path.dirname(__file__), "..", "output", "logs")
        if not os.path.exists(initial_dir):
            initial_dir = os.path.dirname(__file__)
        
        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Log File",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        
        if filepath:
            self._load_log_file(filepath)
    
    def _load_latest_log(self):
        """Load the latest log file from the output/logs directory."""
        log_dir = os.path.join(os.path.dirname(__file__), "..", "output", "logs")
        if not os.path.exists(log_dir):
            self._set_status("Log directory not found. Please open a log file manually.")
            return
        
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        if not log_files:
            self._set_status("No log files found. Please open a log file manually.")
            return
        
        # Sort by modification time and get the latest
        latest_log = max(log_files, key=os.path.getmtime)
        self._load_log_file(latest_log)
    
    def _load_log_file(self, filepath):
        """Load and parse a log file."""
        self._set_status(f"Loading {os.path.basename(filepath)}...")
        self.root.update()
        
        try:
            self.sessions = LogParser.parse_log_file(filepath)
            self.log_file_path = filepath
            self.current_test_index = 0
            self.current_plot_index = 0
            
            # Update UI
            self.file_label.config(text=os.path.basename(filepath))
            self._update_test_label()
            self._update_plot()
            
            if self.sessions:
                self._set_status(f"Loaded {len(self.sessions)} test(s) from {os.path.basename(filepath)}")
            else:
                self._set_status("No GUIDED mode sessions found in log file.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load log file: {str(e)}")
            self._set_status(f"Error loading file: {str(e)}")
    
    def _reload_file(self):
        """Reload the current log file."""
        if self.log_file_path:
            self._load_log_file(self.log_file_path)
    
    def _prev_test(self):
        """Go to previous test."""
        if self.sessions and self.current_test_index > 0:
            self.current_test_index -= 1
            self._update_test_label()
            self._update_plot()
    
    def _next_test(self):
        """Go to next test."""
        if self.sessions and self.current_test_index < len(self.sessions) - 1:
            self.current_test_index += 1
            self._update_test_label()
            self._update_plot()
    
    def _prev_plot(self):
        """Go to previous plot type."""
        if self.current_plot_index > 0:
            self.current_plot_index -= 1
            self.plot_combo.current(self.current_plot_index)
            self._update_plot()
    
    def _next_plot(self):
        """Go to next plot type."""
        if self.current_plot_index < len(self.PLOT_TYPES) - 1:
            self.current_plot_index += 1
            self.plot_combo.current(self.current_plot_index)
            self._update_plot()
    
    def _first_plot(self):
        """Go to first plot type."""
        self.current_plot_index = 0
        self.plot_combo.current(0)
        self._update_plot()
    
    def _last_plot(self):
        """Go to last plot type."""
        self.current_plot_index = len(self.PLOT_TYPES) - 1
        self.plot_combo.current(self.current_plot_index)
        self._update_plot()
    
    def _on_plot_type_change(self, event=None):
        """Handle plot type selection change."""
        self.current_plot_index = self.plot_combo.current()
        self._update_plot()
    
    def _update_test_label(self):
        """Update the test navigation label."""
        if self.sessions:
            self.test_label.config(text=f"Test: {self.current_test_index + 1}/{len(self.sessions)}")
        else:
            self.test_label.config(text="Test: 0/0")
    
    def _set_status(self, message):
        """Update the status bar."""
        self.status_label.config(text=message)
    
    def _update_plot(self):
        """Update the current plot."""
        if not self.sessions:
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data available.\nPlease load a log file.", 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            self.canvas.draw()
            return
        
        # Get the plot method name
        _, method_name = self.PLOT_TYPES[self.current_plot_index]
        plot_method = getattr(self, method_name)
        
        # Clear figure and create plot
        self.fig.clear()
        
        if self.show_all_tests.get():
            plot_method(self.sessions, all_tests=True)
        else:
            plot_method([self.sessions[self.current_test_index]], 
                       test_indices=[self.current_test_index])
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    # ==================== PLOT METHODS ====================
    
    def plot_3d_trajectory(self, sessions, all_tests=False, test_indices=None):
        """Plot 3D trajectory of interceptor and target."""
        ax = self.fig.add_subplot(111, projection='3d')
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(sessions)))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["interceptor_location"]:
                locs = np.array(session["interceptor_location"])
                ax.plot(locs[:, 1], locs[:, 0], locs[:, 2], 
                       label=f'Test {idx+1} Interceptor', color=colors[i])
                ax.scatter(locs[0, 1], locs[0, 0], locs[0, 2], 
                          marker='o', s=100, color=colors[i])
                ax.scatter(locs[-1, 1], locs[-1, 0], locs[-1, 2], 
                          marker='x', s=100, color=colors[i])
            
            if session["target_location"]:
                target_locs = np.array(session["target_location"])
                ax.plot(target_locs[:, 1], target_locs[:, 0], target_locs[:, 2], 
                       linestyle='--', label=f'Test {idx+1} Target', color=colors[i], alpha=0.7)
        
        ax.set_xlabel('Longitude (East)')
        ax.set_ylabel('Latitude (North)')
        ax.set_zlabel('Altitude (m)')
        ax.set_title('3D Trajectory')
        ax.legend()
    
    def plot_altitude(self, sessions, all_tests=False, test_indices=None):
        """Plot altitude over time."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["altitude"]:
                t = np.arange(len(session["altitude"]))
                ax.plot(t, session["altitude"], label=f'Test {idx+1} Drone Alt')
            
            if session["target_altitude"]:
                t = np.arange(len(session["target_altitude"]))
                ax.plot(t, session["target_altitude"], '--', label=f'Test {idx+1} Target Alt')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Altitude (m)')
        ax.set_title('Altitude vs Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_distance(self, sessions, all_tests=False, test_indices=None):
        """Plot distance to target over time."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["distance_to_target"]:
                t = np.arange(len(session["distance_to_target"]))
                ax.plot(t, session["distance_to_target"], label=f'Test {idx+1}')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Distance (m)')
        ax.set_title('Distance to Target')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_velocity(self, sessions, all_tests=False, test_indices=None):
        """Plot velocity components."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["velocity"]:
                vel = np.array(session["velocity"])
                t = np.arange(len(vel))
                ax.plot(t, vel[:, 0], label='Vx', color='red')
                ax.plot(t, vel[:, 1], label='Vy', color='green')
                ax.plot(t, vel[:, 2], label='Vz', color='blue')
            
            ax.set_ylabel('Velocity (m/s)')
            ax.set_title(f'Test {idx+1} - Velocity Components')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_speed(self, sessions, all_tests=False, test_indices=None):
        """Plot velocity norm and speed."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["velocity_norm"]:
                t = np.arange(len(session["velocity_norm"]))
                ax.plot(t, session["velocity_norm"], label=f'Test {idx+1} Vel Norm')
            
            if session["speed"]:
                t = np.arange(len(session["speed"]))
                ax.plot(t, session["speed"], '--', label=f'Test {idx+1} Speed')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Speed (m/s)')
        ax.set_title('Velocity Norm & Speed')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_attitude(self, sessions, all_tests=False, test_indices=None):
        """Plot attitude angles."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["attitude"]:
                att = np.array(session["attitude"])
                t = np.arange(len(att))
                ax.plot(t, att[:, 0], label='Roll', color='red')
                ax.plot(t, att[:, 1], label='Pitch', color='green')
                ax.plot(t, att[:, 2], label='Yaw', color='blue')
            
            ax.set_ylabel('Angle (deg)')
            ax.set_title(f'Test {idx+1} - Attitude (R, P, Y)')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_pixel_errors(self, sessions, all_tests=False, test_indices=None):
        """Plot pixel errors."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["pixel_errors"]:
                errs = np.array(session["pixel_errors"])
                t = np.arange(len(errs))
                ax.plot(t, errs[:, 0], label='X Error', color='red')
                ax.plot(t, errs[:, 1], label='Y Error', color='blue')
            
            ax.set_ylabel('Error (pixels)')
            ax.set_title(f'Test {idx+1} - Pixel Errors')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_depth(self, sessions, all_tests=False, test_indices=None):
        """Plot depth over time."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["depth"]:
                t = np.arange(len(session["depth"]))
                ax.plot(t, session["depth"], label=f'Test {idx+1} Depth')
            
            if session["depth_virtual"]:
                t = np.arange(len(session["depth_virtual"]))
                ax.plot(t, session["depth_virtual"], '--', label=f'Test {idx+1} Depth Virtual')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Depth (m)')
        ax.set_title('Depth')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_accel_initial(self, sessions, all_tests=False, test_indices=None):
        """Plot initial desired acceleration."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["desired_accel_initial"]:
                acc = np.array(session["desired_accel_initial"])
                t = np.arange(len(acc))
                ax.plot(t, acc[:, 0], label='Ax', color='red')
                ax.plot(t, acc[:, 1], label='Ay', color='green')
                ax.plot(t, acc[:, 2], label='Az', color='blue')
            
            ax.set_ylabel('Accel (m/s²)')
            ax.set_title(f'Test {idx+1} - Desired Acceleration (Initial)')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_accel_final(self, sessions, all_tests=False, test_indices=None):
        """Plot final desired acceleration."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["desired_accel_final"]:
                acc = np.array(session["desired_accel_final"])
                t = np.arange(len(acc))
                ax.plot(t, acc[:, 0], label='Ax', color='red')
                ax.plot(t, acc[:, 1], label='Ay', color='green')
                ax.plot(t, acc[:, 2], label='Az', color='blue')
            
            ax.set_ylabel('Accel (m/s²)')
            ax.set_title(f'Test {idx+1} - Desired Acceleration (Final)')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_xyz_pseudo(self, sessions, all_tests=False, test_indices=None):
        """Plot XYZ Pseudo Frame."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["xyz_pseudo"]:
                xyz = np.array(session["xyz_pseudo"])
                t = np.arange(len(xyz))
                ax.plot(t, xyz[:, 0], label='X', color='red')
                ax.plot(t, xyz[:, 1], label='Y', color='green')
                ax.plot(t, xyz[:, 2], label='Z', color='blue')
            
            ax.set_ylabel('Position (m)')
            ax.set_title(f'Test {idx+1} - XYZ Pseudo Frame')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_control_commands(self, sessions, all_tests=False, test_indices=None):
        """Plot control commands."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["control_commands"]:
                cmd = np.array(session["control_commands"])
                t = np.arange(len(cmd))
                ax.plot(t, cmd[:, 0], label='Pitch', color='red')
                ax.plot(t, cmd[:, 1], label='Yaw', color='green')
                ax.plot(t, cmd[:, 2], label='Roll', color='blue')
            
            ax.set_ylabel('Command')
            ax.set_title(f'Test {idx+1} - Control Commands')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_throttle(self, sessions, all_tests=False, test_indices=None):
        """Plot throttle over time."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["throttle"]:
                t = np.arange(len(session["throttle"]))
                ax.plot(t, session["throttle"], label=f'Test {idx+1}')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Throttle')
        ax.set_title('Throttle')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_bs_throttle(self, sessions, all_tests=False, test_indices=None):
        """Plot backstepping throttle data."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        n_cols = 2
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["bs_throttle"]:
                bs_data = session["bs_throttle"]
                t = np.arange(len(bs_data))
                
                # Throttle
                ax1 = self.fig.add_subplot(n_sessions, n_cols, i*n_cols + 1)
                ax1.plot(t, [d['thr'] for d in bs_data], label='Throttle', color='blue')
                ax1.set_ylabel('Throttle')
                ax1.set_title(f'Test {idx+1} - BS Throttle')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Errors
                ax2 = self.fig.add_subplot(n_sessions, n_cols, i*n_cols + 2)
                ax2.plot(t, [d['alt_err'] for d in bs_data], label='Alt Err (m)', color='red')
                ax2.plot(t, [d['rate_err'] for d in bs_data], label='Rate Err (m/s)', color='green')
                ax2.set_ylabel('Error')
                ax2.set_title(f'Test {idx+1} - BS Errors')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
    
    def plot_bs_roll(self, sessions, all_tests=False, test_indices=None):
        """Plot backstepping roll data."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        n_cols = 2
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["bs_roll"]:
                bs_data = session["bs_roll"]
                t = np.arange(len(bs_data))
                
                # Roll angle
                ax1 = self.fig.add_subplot(n_sessions, n_cols, i*n_cols + 1)
                ax1.plot(t, [d['phi'] for d in bs_data], label='Phi (deg)', color='blue')
                ax1.set_ylabel('Roll (deg)')
                ax1.set_title(f'Test {idx+1} - BS Roll')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Errors
                ax2 = self.fig.add_subplot(n_sessions, n_cols, i*n_cols + 2)
                ax2.plot(t, [d['east_err'] for d in bs_data], label='East Err (m)', color='red')
                ax2.plot(t, [d['vel_err'] for d in bs_data], label='Vel Err (m/s)', color='green')
                ax2.set_ylabel('Error')
                ax2.set_title(f'Test {idx+1} - BS Roll Errors')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
    
    def plot_levant(self, sessions, all_tests=False, test_indices=None):
        """Plot Levant differentiator estimates."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            # Create 2x2 subplot grid for each test
            ax1 = self.fig.add_subplot(n_sessions, 2, i*2 + 1)
            ax2 = self.fig.add_subplot(n_sessions, 2, i*2 + 2)
            
            # Throttle Levant (altitude)
            if session["bs_levant"]:
                levant_data = session["bs_levant"]
                t = np.arange(len(levant_data))
                ax1.plot(t, [d['rate_hat'] for d in levant_data], label='Rate Hat (m/s)', color='blue')
                ax1.plot(t, [d['accel_hat'] for d in levant_data], label='Accel Hat (m/s²)', color='red')
                ax1.set_ylabel('Estimate')
                ax1.set_title(f'Test {idx+1} - Altitude Levant (BS_LEVANT)')
                ax1.legend(loc='upper right')
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No BS_LEVANT data', ha='center', va='center')
                ax1.set_title(f'Test {idx+1} - Altitude Levant')
            
            # Roll Levant (lateral)
            if session["bs_roll_levant"]:
                roll_levant_data = session["bs_roll_levant"]
                t = np.arange(len(roll_levant_data))
                ax2.plot(t, [d['vel_hat'] for d in roll_levant_data], label='Vel Hat (m/s)', color='blue')
                ax2.plot(t, [d['accel_hat'] for d in roll_levant_data], label='Accel Hat (m/s²)', color='red')
                ax2.set_ylabel('Estimate')
                ax2.set_title(f'Test {idx+1} - Lateral Levant (BS_ROLL_LEVANT)')
                ax2.legend(loc='upper right')
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No BS_ROLL_LEVANT data', ha='center', va='center')
                ax2.set_title(f'Test {idx+1} - Lateral Levant')
        
        if n_sessions > 0:
            ax1.set_xlabel('Time Steps')
            ax2.set_xlabel('Time Steps')
    
    def plot_levant_alt_state(self, sessions, all_tests=False, test_indices=None):
        """Plot Levant altitude state: z1_a (altitude), z1_r (rate), z2_r (acceleration)."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            # Create 3-subplot grid for each test: z1_a, z1_r, z2_r
            ax1 = self.fig.add_subplot(n_sessions, 3, i*3 + 1)
            ax2 = self.fig.add_subplot(n_sessions, 3, i*3 + 2)
            ax3 = self.fig.add_subplot(n_sessions, 3, i*3 + 3)
            
            if session["levant_alt_state"]:
                state_data = session["levant_alt_state"]
                t = np.arange(len(state_data))
                
                # z1_a - Altitude estimate
                ax1.plot(t, [d['z1_a'] for d in state_data], label='z1_a (Alt)', color='blue')
                ax1.set_ylabel('Altitude (m)')
                ax1.set_title(f'Test {idx+1} - z1_a (Altitude)')
                ax1.legend(loc='upper right')
                ax1.grid(True, alpha=0.3)
                
                # z1_r - Rate estimate
                ax2.plot(t, [d['z1_r'] for d in state_data], label='z1_r (Rate)', color='green')
                ax2.set_ylabel('Rate (m/s)')
                ax2.set_title(f'Test {idx+1} - z1_r (Alt Rate)')
                ax2.legend(loc='upper right')
                ax2.grid(True, alpha=0.3)
                
                # z2_r - Acceleration estimate
                ax3.plot(t, [d['z2_r'] for d in state_data], label='z2_r (Accel)', color='red')
                ax3.set_ylabel('Acceleration (m/s²)')
                ax3.set_title(f'Test {idx+1} - z2_r (Acceleration)')
                ax3.legend(loc='upper right')
                ax3.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No LEVANT_ALT_OUT data', ha='center', va='center')
                ax1.set_title(f'Test {idx+1} - z1_a (Altitude)')
                ax2.text(0.5, 0.5, 'No LEVANT_ALT_OUT data', ha='center', va='center')
                ax2.set_title(f'Test {idx+1} - z1_r (Alt Rate)')
                ax3.text(0.5, 0.5, 'No LEVANT_ALT_OUT data', ha='center', va='center')
                ax3.set_title(f'Test {idx+1} - z2_r (Acceleration)')
        
        if n_sessions > 0:
            ax1.set_xlabel('Time Steps')
            ax2.set_xlabel('Time Steps')
            ax3.set_xlabel('Time Steps')
    
    def plot_bs_state(self, sessions, all_tests=False, test_indices=None):
        """Plot backstepping state data."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            # Create 2x2 subplot grid for each test
            ax1 = self.fig.add_subplot(n_sessions, 2, i*2 + 1)
            ax2 = self.fig.add_subplot(n_sessions, 2, i*2 + 2)
            
            if session["bs_state"]:
                state_data = session["bs_state"]
                t = np.arange(len(state_data))
                
                # Altitude comparison
                ax1.plot(t, [d['drone_alt'] for d in state_data], label='Drone Alt (m)', color='blue')
                ax1.plot(t, [d['target_alt'] for d in state_data], label='Target Alt (m)', color='red', linestyle='--')
                ax1.set_ylabel('Altitude (m)')
                ax1.set_title(f'Test {idx+1} - Altitude (BS_STATE)')
                ax1.legend(loc='upper right')
                ax1.grid(True, alpha=0.3)
                
                # Velocity and acceleration
                ax2.plot(t, [d['drone_vz'] for d in state_data], label='Drone Vz (m/s)', color='green')
                ax2.plot(t, [d['drone_az'] for d in state_data], label='Drone Az (m/s²)', color='orange')
                ax2.set_ylabel('Value')
                ax2.set_title(f'Test {idx+1} - Vz & Az (BS_STATE)')
                ax2.legend(loc='upper right')
                ax2.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No BS_STATE data', ha='center', va='center')
                ax1.set_title(f'Test {idx+1} - BS_STATE Altitude')
                ax2.text(0.5, 0.5, 'No BS_STATE data', ha='center', va='center')
                ax2.set_title(f'Test {idx+1} - BS_STATE Velocity')
        
        if n_sessions > 0:
            ax1.set_xlabel('Time Steps')
            ax2.set_xlabel('Time Steps')
    
    def plot_virtual_accel(self, sessions, all_tests=False, test_indices=None):
        """Plot virtual accelerations."""
        ax = self.fig.add_subplot(111)
        
        if test_indices is None:
            test_indices = range(len(sessions))
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            if session["virtual_east_accel"]:
                t = np.arange(len(session["virtual_east_accel"]))
                ax.plot(t, session["virtual_east_accel"], label=f'Test {idx+1} East Accel')
            
            if session["virtual_down_accel"]:
                t = np.arange(len(session["virtual_down_accel"]))
                ax.plot(t, session["virtual_down_accel"], '--', label=f'Test {idx+1} Down Accel')
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Acceleration (m/s²)')
        ax.set_title('Virtual Accelerations')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_errors(self, sessions, all_tests=False, test_indices=None):
        """Plot errors XY and Z."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["error_old_xy"]:
                t = np.arange(len(session["error_old_xy"]))
                ax.plot(t, session["error_old_xy"], label='Error XY', color='red')
            
            if session["error_old_z"]:
                t = np.arange(len(session["error_old_z"]))
                ax.plot(t, session["error_old_z"], label='Error Z', color='blue')
            
            ax.set_ylabel('Error')
            ax.set_title(f'Test {idx+1} - Error XY & Z')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')
    
    def plot_raw_imu(self, sessions, all_tests=False, test_indices=None):
        """Plot raw IMU accelerometer data."""
        if test_indices is None:
            test_indices = range(len(sessions))
        
        n_sessions = len(sessions)
        
        for i, (session, idx) in enumerate(zip(sessions, test_indices)):
            ax = self.fig.add_subplot(n_sessions, 1, i+1)
            
            if session["raw_imu"]:
                imu_data = np.array(session["raw_imu"])
                t = np.arange(len(imu_data))
                ax.plot(t, imu_data[:, 0], label='IMU X (m/s²)', color='red')
                ax.plot(t, imu_data[:, 1], label='IMU Y (m/s²)', color='green')
                ax.plot(t, imu_data[:, 2], label='IMU Z (m/s²)', color='blue')
            else:
                ax.text(0.5, 0.5, 'No raw IMU data available', ha='center', va='center')
            
            ax.set_ylabel('Acceleration (m/s²)')
            ax.set_title(f'Test {idx+1} - Raw IMU Accelerometer')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        
        if n_sessions > 0:
            ax.set_xlabel('Time Steps')


def main():
    """Main entry point."""
    log_file = None
    
    # Check if log file path is provided as argument
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        if not os.path.exists(log_file):
            print(f"Error: File not found: {log_file}")
            sys.exit(1)
    
    # Create and run the application
    root = tk.Tk()
    app = PlotterApp(root, log_file)
    root.mainloop()


if __name__ == "__main__":
    main()
