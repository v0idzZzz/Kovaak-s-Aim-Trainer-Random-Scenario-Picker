import tkinter as tk
from tkinter import messagebox, Scrollbar, Listbox, Frame, Label, Entry, Button, ttk
from tkinter import filedialog
import threading
import os
from kovaakscenpicker import (
    run_online_challenge_loop,
    get_and_launch_random_scenario,
    run_pb_challenge_loop,
    run_rival_challenge_loop,
    find_stats_folder_automatically
)


class ChallengeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KovaaK's Challenge Runner")
        self.root.geometry("550x720")
        self.root.resizable(True, True)
        self.root.minsize(550, 680)

        self.challenge_active = False;
        self.challenge_thread = None
        self.skip_event = threading.Event();
        self.stop_polling_event = threading.Event()
        self.timer_id = None;
        self.timer_paused = False;
        self.time_left_seconds = 0
        self.stats_folder_path = None

        footer_frame = Frame(root);
        footer_frame.pack(side="bottom", fill="x", pady=5)
        content_frame = Frame(root);
        content_frame.pack(side="top", fill="both", expand=True)

        Label(content_frame, text="Your KovaaK's Username:", font=("Segoe UI", 11, "bold")).pack(pady=(10, 2))
        self.username_entry = Entry(content_frame, width=30, font=("Segoe UI", 11));
        self.username_entry.pack()


        self.manual_path_frame = Frame(content_frame)
        Label(self.manual_path_frame, text="Please select your KovaaK's 'stats' folder:",
              font=("Segoe UI", 10, "bold")).pack()
        db_input_row = Frame(self.manual_path_frame)
        db_input_row.pack(fill="x", padx=10, pady=(2, 10))
        self.manual_path_entry = Entry(db_input_row, width=60, font=("Segoe UI", 9))
        self.manual_path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = Button(db_input_row, text="Browse...", command=self.browse_for_folder)
        self.browse_button.pack(side="left", padx=5)


        Label(content_frame, text="Or get a single random scenario:", font=("Segoe UI", 10)).pack(pady=(10, 2))
        self.random_button = Button(content_frame, text="🎯 Give me a random scenario!", font=("Segoe UI", 12),
                                    command=self.on_random_scenario_click);
        self.random_button.pack()

        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=15, padx=20)

        # The rest of the GUI layout is unchanged...
        time_frame = Frame(content_frame);
        time_frame.pack(pady=5)
        Label(time_frame, text="Challenge Duration:", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.time_limit_combo = ttk.Combobox(time_frame, values=["Unlimited", "5 Minutes", "10 Minutes", "20 Minutes",
                                                                 "30 Minutes"], state="readonly",
                                             font=("Segoe UI", 10));
        self.time_limit_combo.set("Unlimited");
        self.time_limit_combo.pack(side="left")
        Label(content_frame, text="Select a Game Mode:", font=("Segoe UI", 11, "bold")).pack(pady=(10, 5))
        percentile_frame = ttk.LabelFrame(content_frame, text="First Try Challenge (Unplayed Scenarios)",
                                          padding=(10, 5));
        percentile_frame.pack(pady=5, padx=10, fill="x")
        self.easy_button = Button(percentile_frame, text="Easy", font=("Segoe UI", 12),
                                  command=lambda: self.start_challenge("percentile", "Easy"));
        self.easy_button.pack(side="left", expand=True, padx=5)
        self.medium_button = Button(percentile_frame, text="Medium", font=("Segoe UI", 12),
                                    command=lambda: self.start_challenge("percentile", "Medium"));
        self.medium_button.pack(side="left", expand=True, padx=5)
        self.hard_button = Button(percentile_frame, text="Hard", font=("Segoe UI", 12),
                                  command=lambda: self.start_challenge("percentile", "Hard"));
        self.hard_button.pack(side="left", expand=True, padx=5)
        pb_frame = ttk.LabelFrame(content_frame, text="PB Challenge (Played Scenarios)", padding=(10, 5));
        pb_frame.pack(pady=5, padx=10, fill="x")
        self.pb_button = Button(pb_frame, text="Start PB Hunt", font=("Segoe UI", 12, "bold"),
                                command=lambda: self.start_challenge("pb"));
        self.pb_button.pack(side="left", expand=True)
        rival_frame = ttk.LabelFrame(content_frame, text="Beat the Rival Challenge", padding=(10, 5));
        rival_frame.pack(pady=5, padx=10, fill="x")
        rival_input_frame = Frame(rival_frame);
        rival_input_frame.pack()
        Label(rival_input_frame, text="Rival's Username:", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.rival_username_entry = Entry(rival_input_frame, width=20, font=("Segoe UI", 10));
        self.rival_username_entry.pack(side="left")
        self.rival_button = Button(rival_frame, text="Beat Rival's PB", font=("Segoe UI", 12, "bold", "italic"),
                                   fg="#8e44ad", command=lambda: self.start_challenge("rival"));
        self.rival_button.pack(pady=(5, 0))
        control_button_frame = Frame(content_frame);
        control_button_frame.pack(pady=10)
        self.skip_button = Button(control_button_frame, text="⏩ Skip", font=("Segoe UI", 12),
                                  command=self.on_skip_click, state=tk.DISABLED);
        self.skip_button.pack(side="left", padx=10)
        self.end_button = Button(control_button_frame, text="🛑 End", font=("Segoe UI", 12, "bold"),
                                 command=self.end_challenge, state=tk.DISABLED, bg="#e74c3c", fg="white");
        self.end_button.pack(side="left", padx=10)
        stats_frame = Frame(content_frame);
        stats_frame.pack(pady=(10, 0))
        self.score_label = Label(stats_frame, text="Score: 0", font=("Segoe UI", 11, "bold"), fg="#27ae60");
        self.score_label.pack(side="left", padx=10)
        self.timer_label = Label(stats_frame, text="Time Left: --:--", font=("Segoe UI", 11, "bold"), fg="#3498db");
        self.timer_label.pack(side="left", padx=10)
        self.status_label = Label(content_frame, text="Searching for KovaaK's stats folder...", font=("Segoe UI", 11),
                                  wraplength=500);
        self.status_label.pack(pady=5)
        history_frame = Frame(content_frame);
        history_frame.pack(pady=5, fill="both", expand=True, padx=10)
        scrollbar = Scrollbar(history_frame);
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox = Listbox(history_frame, width=80, height=5, yscrollcommand=scrollbar.set,
                                       font=("Segoe UI", 10));
        self.history_listbox.pack(side=tk.LEFT, fill="both", expand=True);
        scrollbar.config(command=self.history_listbox.yview)
        footer = Label(footer_frame, text="Developed by Jogurkaka and v0id_", font=("Segoe UI", 9), fg="gray");
        footer.pack()

        self.find_stats_folder()

    def find_stats_folder(self):
        found_path = find_stats_folder_automatically()
        if found_path:
            self.stats_folder_path = found_path
            self.status_label.config(text="✅ KovaaK's stats folder found! Ready to start.")
        else:

            self.manual_path_frame.pack(before=self.random_button, pady=(10, 0))
            self.status_label.config(text="⚠️ Could not find stats folder automatically. Please select it manually.")

    def browse_for_folder(self):
        """Opens a dialog to select the 'stats' folder."""

        dir_path = filedialog.askdirectory(title="Please select your KovaaK's 'stats' folder")
        if dir_path:
            self.manual_path_entry.delete(0, tk.END)
            self.manual_path_entry.insert(0, dir_path)
            self.status_label.config(text="✅ Stats folder selected. Ready to start!")

    def start_challenge(self, mode, difficulty=None):
        # --- MODIFIED: Get the path from either the automatic or manual source ---
        path = self.stats_folder_path
        if not path:  # If auto-search failed, get it from the manual entry box
            path = self.manual_path_entry.get()
            if not path: messagebox.showerror("Error",
                                              "Please select your KovaaK's stats folder using the 'Browse' button."); return

        username = self.username_entry.get()
        if not username: messagebox.showerror("Error", "Please enter your KovaaK's username."); return
        if self.challenge_active: messagebox.showwarning("In Progress", "A challenge is already running."); return
        rival_username = self.rival_username_entry.get()
        if mode == "rival" and not rival_username: messagebox.showerror("Error",
                                                                        "Please enter a Rival's username for this mode."); return

        time_selection = self.time_limit_combo.get()
        time_limit_minutes = {"Unlimited": 0, "5 Minutes": 5, "10 Minutes": 10, "20 Minutes": 20, "30 Minutes": 30}[
            time_selection]

        self.challenge_active = True;
        self.history_listbox.delete(0, tk.END);
        self.stop_polling_event.clear();
        self.toggle_buttons(active=True)
        hooks = {"is_active": lambda: self.challenge_active, "update_status": self.update_status,
                 "add_history": self.add_history, "update_history": self.update_history,
                 "update_score_label": self.update_score_label, "challenge_ended": self.on_challenge_end,
                 "skip_event": self.skip_event, "pause_timer": self.pause_timer, "resume_timer": self.resume_timer,
                 "stop_polling_event": self.stop_polling_event}

        if mode == "percentile":
            self.score_label.config(
                text="Score: 0 Successful, 0 Unsuccessful"); self.challenge_thread = threading.Thread(
                target=run_online_challenge_loop, args=(path, username, difficulty, hooks), daemon=True)
        elif mode == "pb":
            self.score_label.config(text="PBs Achieved: 0"); self.challenge_thread = threading.Thread(
                target=run_pb_challenge_loop, args=(path, username, hooks), daemon=True)
        elif mode == "rival":
            self.score_label.config(text="Rival PBs Beaten: 0"); self.challenge_thread = threading.Thread(
                target=run_rival_challenge_loop, args=(path, username, rival_username, hooks), daemon=True)

        if time_limit_minutes > 0: self.start_timer(time_limit_minutes * 60)
        self.challenge_thread.start()

    def toggle_buttons(self, active):
        s = tk.DISABLED if active else tk.NORMAL
        # Also toggle the browse button
        self.browse_button.config(state=s)
        self.random_button.config(state=s);
        self.easy_button.config(state=s);
        self.medium_button.config(state=s);
        self.hard_button.config(state=s);
        self.pb_button.config(state=s);
        self.rival_button.config(state=s)
        self.username_entry.config(state="disabled" if active else "normal");
        self.rival_username_entry.config(state="disabled" if active else "normal");
        self.time_limit_combo.config(state="disabled" if active else "readonly")
        cs = tk.NORMAL if active else tk.DISABLED;
        self.end_button.config(state=cs);
        self.skip_button.config(state=cs)

    # Other methods unchanged
    def start_timer(self, s):
        self.time_left_seconds = s; self.timer_paused = False; self.update_timer_display(); self.countdown()

    def countdown(self):
        if self.challenge_active:
            if not self.timer_paused and self.time_left_seconds > 0: self.time_left_seconds -= 1; self.update_timer_display()
            if self.time_left_seconds <= 0: self.status_label.config(
                text="⏰ Time's up! Challenge has ended."); self.end_challenge(); return
            self.timer_id = self.root.after(1000, self.countdown)

    def update_timer_display(self):
        m, s = divmod(self.time_left_seconds, 60); self.timer_label.config(text=f"Time: {m:02d}:{s:02d}")

    def pause_timer(self):
        self.timer_paused = True; self.timer_label.config(fg="#f39c12")

    def resume_timer(self):
        self.timer_paused = False; self.timer_label.config(fg="#3498db")

    def on_skip_click(self):
        self.skip_event.set(); self.stop_polling_event.set()

    def end_challenge(self):
        if self.timer_id: self.root.after_cancel(self.timer_id); self.timer_id = None
        self.challenge_active = False;
        self.stop_polling_event.set();
        self.status_label.config(text="Challenge stopped.");
        self.end_button.config(state=tk.DISABLED);
        self.skip_button.config(state=tk.DISABLED)

    def update_score_label(self, text):
        self.root.after(0, lambda: self.score_label.config(text=text))

    def on_random_scenario_click(self):
        if self.challenge_active:
            messagebox.showwarning("In Progress", "Cannot pick a random scenario while a challenge is active.")
        else:
            hooks = {"update_status": self.update_status, "add_history": self.add_history}; threading.Thread(
                target=get_and_launch_random_scenario, args=(hooks,), daemon=True).start()

    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def add_history(self, text):
        self.root.after(0, lambda: (self.history_listbox.insert(tk.END, text), self.history_listbox.yview(tk.END)))

    def update_history(self, text):
        self.root.after(0,
                        lambda: (self.history_listbox.delete(tk.END - 1) if self.history_listbox.size() > 0 else None,
                                 self.history_listbox.insert(tk.END, text), self.history_listbox.yview(tk.END)))

    def on_challenge_end(self):
        self.challenge_active = False; self.root.after(0, lambda: self.toggle_buttons(active=False))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChallengeGUI(root)
    root.mainloop()