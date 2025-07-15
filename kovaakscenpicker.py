import sys
import os
import io
import random
import urllib.parse
import platform
import time
from kovaaker import KovaakerClient
# --- ADDED: Import psutil to check for running processes ---
import psutil

if os.name == 'nt':
    if hasattr(sys.stdout, "buffer") and sys.stdout is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

DIFFICULTY_THRESHOLDS = {"Easy": 0.20, "Medium": 0.50, "Hard": 0.80}


def is_kovaaks_running():
    """Checks if FPSAimTrainer.exe is in the list of running processes."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == "fpsaimtrainer.exe":
            return True
    return False


# --- MODIFIED: The launch_scenario function is now "smart" ---
def launch_scenario(scenario_name):
    """
    Launches the scenario intelligently. If KovaaK's is already running,
    it sends the command once. If not, it uses the "double tap" method.
    """
    encoded_name = urllib.parse.quote(scenario_name)
    steam_link = f"steam://run/824270/?action=jump-to-scenario;name={encoded_name};mode=challenge"

    print(f"\n🎯 Sending command to load scenario: {scenario_name}")

    if is_kovaaks_running():
        # Game is already running, just send the command once.
        print("   KovaaK's is already running. Sending command directly.")
        if platform.system() == "Windows":
            try:
                os.startfile(steam_link)
            except Exception as e:
                print(f"   ❌ Failed to open Steam link: {e}")
    else:
        # Game is not running, use the double-tap method to ensure it starts and loads.
        print("   KovaaK's is not running. Starting game and waiting...")
        if platform.system() == "Windows":
            try:
                # First command: This will start KovaaK's if it's closed.
                os.startfile(steam_link)

                # Wait for the game to initialize.
                print("   Waiting 12 seconds for game to initialize...")
                time.sleep(12)

                # Second command: This is received by the now-running game.
                print("   Sending follow-up command to ensure scenario loads.")
                os.startfile(steam_link)
            except Exception as e:
                print(f"   ❌ Failed to open Steam link: {e}")


# The rest of the file is unchanged from the last complete version.
def find_stats_folder_automatically():
    print("🔎 Searching for KovaaK's stats folder...");
    appdata_path = os.path.expandvars(os.path.join('%LOCALAPPDATA%', 'KovaaKs', 'FPSAimTrainer', 'stats'))
    if os.path.exists(appdata_path): print(f"✅ Found stats folder at: {appdata_path}"); return appdata_path
    legacy_path = os.path.join("C:", "Program Files (x86)", "Steam", "steamapps", "common", "FPSAimTrainer",
                               "FPSAimTrainer", "stats")
    if os.path.exists(legacy_path): print(f"✅ Found stats folder in legacy location: {legacy_path}"); return legacy_path
    print("❌ Automatic search failed.");
    return None


def watch_for_new_csv(stats_folder, initial_files, stop_event):
    for _ in range(80):
        if stop_event.is_set(): return None
        current_files = set(os.listdir(stats_folder));
        new_files = current_files - initial_files
        for file in new_files:
            if file.lower().endswith('.csv'): return os.path.join(stats_folder, file)
        stop_event.wait(1.5)
    return None


def parse_score_from_csv(csv_path):
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("Score:,"): score = float(line.strip().split(',')[1]); print(
                    f"   Parsed score {score} from {os.path.basename(csv_path)}"); return score
    except Exception as e:
        print(f"   Error parsing {csv_path}: {e}")
    finally:
        try:
            os.remove(csv_path); print(f"   Removed temp stats file: {os.path.basename(csv_path)}")
        except Exception as e:
            print(f"   Could not remove {csv_path}: {e}")
    return None


def get_rank_for_score(leaderboard_id, target_score):
    client = KovaakerClient()
    for page in client.scenario_leaderboard(leaderboard_id, per_page=100, by_page=True):
        for score_entry in page:
            if score_entry.score <= target_score: return score_entry.rank
    return 1_000_000


def find_unplayed_scenario(client, username, hooks):
    MAX_PAGES_TO_SEARCH = 30;
    stop_polling_event = hooks["stop_polling_event"]
    try:
        total_pages = (client.scenario_count() // 20)
    except Exception:
        total_pages = 500
    for i in range(MAX_PAGES_TO_SEARCH):
        if not hooks["is_active"](): return None
        hooks["update_status"](f"🔎 Searching for an unplayed scenario (Page {i + 1}/{MAX_PAGES_TO_SEARCH})...")
        random_page_index = random.randint(0, total_pages - 1)
        try:
            page_scenarios = next(client.scenario_search(start_page=random_page_index, per_page=20)); random.shuffle(
                page_scenarios)
        except Exception as e:
            print(f"Failed to fetch page {random_page_index}: {e}"); continue
        for scenario in page_scenarios:
            if not scenario.leaderboardId or not scenario.entries: continue
            score_obj = client.get_user_score(scenario.leaderboardId, username)
            if score_obj is None or score_obj['score'] == 0: return scenario
    return None


def get_random_scenario_object(client, per_page=20):
    try:
        total_scenarios = client.scenario_count()
        if total_scenarios == 0: return None
        random_page_index = random.randint(0, (total_scenarios // per_page) - 1)
        scenarios_on_page = next(client.scenario_search(start_page=random_page_index, per_page=per_page))
        return random.choice(scenarios_on_page) if scenarios_on_page else None
    except Exception as e:
        print(f"❌ Could not fetch a random scenario: {e}"); return None


def get_and_launch_random_scenario(hooks):
    client = KovaakerClient();
    hooks["update_status"]("🔎 Picking a random scenario...")
    selected_scenario = get_random_scenario_object(client)
    if selected_scenario:
        launch_scenario(selected_scenario.scenarioName); hooks["update_status"](
            f"✅ Launched: {selected_scenario.scenarioName}"); hooks["add_history"](
            f"(Random Pick) {selected_scenario.scenarioName}")
    else:
        hooks["update_status"]("Error: Could not find a valid scenario.")


def run_pb_challenge_loop(stats_folder, username, hooks):
    client = KovaakerClient();
    stop_event = hooks["stop_polling_event"];
    skip_event = hooks["skip_event"];
    pb_count = 0
    hooks["update_score_label"](f"PBs Achieved: {pb_count}")
    while hooks["is_active"]():
        hooks["pause_timer"]();
        hooks["update_status"]("🔎 Picking a random scenario...");
        selected_scenario = get_random_scenario_object(client)
        if not hooks["is_active"](): break
        if not selected_scenario or not selected_scenario.leaderboardId: hooks["update_status"](
            "Error finding a valid scenario. Skipping."); time.sleep(3); continue
        hooks["update_status"](f"Fetching your PB for {selected_scenario.scenarioName}...");
        initial_score_obj = client.get_user_score(selected_scenario.leaderboardId, username)
        initial_score = initial_score_obj['score'] if initial_score_obj else 0
        hooks["resume_timer"]();
        initial_files = set(os.listdir(stats_folder));
        hooks["add_history"](f"(Pending PB) {selected_scenario.scenarioName}");
        launch_scenario(selected_scenario.scenarioName)
        goal_text = f"Your PB to beat: {initial_score:.2f}" if initial_score > 0 else "No PB set. Any score is a new PB!"
        hooks["update_status"](f"▶️ Now playing: {selected_scenario.scenarioName}\n{goal_text}")
        new_csv_path = watch_for_new_csv(stats_folder, initial_files, stop_event)
        if skip_event.is_set(): hooks["update_history"](
            f"(Skipped) {selected_scenario.scenarioName}"); skip_event.clear(); continue
        if not hooks["is_active"](): hooks["update_history"](f"(Cancelled) {selected_scenario.scenarioName}"); break
        new_score = parse_score_from_csv(new_csv_path) if new_csv_path else None
        if new_score:
            result_text = f"New Score: {new_score:.2f} | Your PB: {initial_score:.2f}";
            hooks["update_history"](f"{selected_scenario.scenarioName} - {result_text}")
            if new_score > initial_score:
                pb_count += 1; hooks["update_score_label"](f"PBs Achieved: {pb_count}"); hooks["update_status"](
                    f"✅ New PB! Congratulations!\nLoading next scenario..."); time.sleep(3)
            else:
                hooks["update_status"](f"So close! No new PB this time.\nLoading next scenario..."); time.sleep(2)
        else:
            hooks["update_history"](f"(No new score) {selected_scenario.scenarioName}"); hooks["update_status"](
                f"No new score file detected. Loading next scenario..."); time.sleep(2)
    hooks["challenge_ended"]()


def run_online_challenge_loop(stats_folder, username, difficulty, hooks):
    client = KovaakerClient();
    required_percentile = DIFFICULTY_THRESHOLDS[difficulty];
    stop_event = hooks["stop_polling_event"];
    skip_event = hooks["skip_event"]
    successful_runs, unsuccessful_runs = 0, 0
    hooks["update_score_label"](f"Score: {successful_runs} Successful, {unsuccessful_runs} Unsuccessful")
    while hooks["is_active"]():
        hooks["pause_timer"]();
        selected_scenario = find_unplayed_scenario(client, username, hooks)
        if not hooks["is_active"](): break
        if not selected_scenario: hooks["update_status"](
            "❌ Could not find an unplayed scenario. Stopping challenge."); time.sleep(4); break
        hooks["resume_timer"]();
        total_entries = selected_scenario.entries;
        initial_files = set(os.listdir(stats_folder))
        hooks["add_history"](f"(Pending) {selected_scenario.scenarioName}");
        launch_scenario(selected_scenario.scenarioName)
        hooks["update_status"](
            f"▶️ Unplayed map: {selected_scenario.scenarioName}\nGoal: Set a score in the Top {(1 - required_percentile) * 100:.0f}%")
        new_csv_path = watch_for_new_csv(stats_folder, initial_files, stop_event)
        if skip_event.is_set(): hooks["update_history"](
            f"(Skipped) {selected_scenario.scenarioName}"); skip_event.clear(); continue
        if not hooks["is_active"](): hooks["update_history"](f"(Cancelled) {selected_scenario.scenarioName}"); break
        new_score = parse_score_from_csv(new_csv_path) if new_csv_path else None
        if new_score:
            hooks["update_status"](f"Score detected: {new_score:.2f}. Checking rank online...")
            achieved_rank = get_rank_for_score(selected_scenario.leaderboardId, new_score);
            percentile = 1 - (achieved_rank / total_entries)
            result_text = f"First Score: {new_score:.2f} | Approx. Rank: {achieved_rank} (Top {percentile:.1%})";
            hooks["update_history"](f"{selected_scenario.scenarioName} - {result_text}")
            if percentile >= required_percentile:
                successful_runs += 1; hooks["update_status"](
                    f"✅ Success! {result_text}\nSearching for next unplayed scenario..."); time.sleep(3)
            else:
                unsuccessful_runs += 1; hooks["update_status"](
                    f"❌ Challenge Failed. {result_text}\nNeeded Top {(1 - required_percentile) * 100:.0f}%."); break
        else:
            hooks["update_history"](f"(No new score) {selected_scenario.scenarioName}"); hooks["update_status"](
                f"Timed out waiting for new score file."); break
        hooks["update_score_label"](f"Score: {successful_runs} Successful, {unsuccessful_runs} Unsuccessful")
    hooks["challenge_ended"]()


def run_rival_challenge_loop(stats_folder, username, rival_username, hooks):
    client = KovaakerClient();
    stop_event = hooks["stop_polling_event"];
    skip_event = hooks["skip_event"];
    rival_pbs_beaten = 0
    hooks["update_score_label"](f"Rival PBs Beaten: {rival_pbs_beaten}")
    while hooks["is_active"]():
        hooks["pause_timer"]();
        hooks["update_status"]("🔎 Picking a random scenario...");
        selected_scenario = get_random_scenario_object(client)
        if not hooks["is_active"](): break
        if not selected_scenario or not selected_scenario.leaderboardId: hooks["update_status"](
            "Error finding a valid scenario. Skipping."); time.sleep(3); continue
        hooks["update_status"](f"Fetching {rival_username}'s PB for {selected_scenario.scenarioName}...");
        rival_score_obj = client.get_user_score(selected_scenario.leaderboardId, rival_username)
        rival_pb = rival_score_obj['score'] if rival_score_obj else 0
        if rival_pb == 0: hooks["update_status"](
            f"Rival has no score for {selected_scenario.scenarioName}. Skipping."); time.sleep(3); continue
        hooks["resume_timer"]();
        initial_files = set(os.listdir(stats_folder));
        hooks["add_history"](f"(vs {rival_username}) {selected_scenario.scenarioName}");
        launch_scenario(selected_scenario.scenarioName)
        hooks["update_status"](
            f"▶️ Now playing: {selected_scenario.scenarioName}\nGoal: Beat {rival_username}'s PB of {rival_pb:.2f}")
        new_csv_path = watch_for_new_csv(stats_folder, initial_files, stop_event)
        if skip_event.is_set(): hooks["update_history"](
            f"(Skipped) {selected_scenario.scenarioName}"); skip_event.clear(); continue
        if not hooks["is_active"](): hooks["update_history"](f"(Cancelled) {selected_scenario.scenarioName}"); break
        new_score = parse_score_from_csv(new_csv_path) if new_csv_path else None
        if new_score:
            result_text = f"Your Score: {new_score:.2f} | Rival's PB: {rival_pb:.2f}";
            hooks["update_history"](f"{selected_scenario.scenarioName} - {result_text}")
            if new_score > rival_pb:
                rival_pbs_beaten += 1;
                hooks["update_score_label"](f"Rival PBs Beaten: {rival_pbs_beaten}")
                hooks["update_status"](f"✅ Success! You beat {rival_username}!\nLoading next challenge...");
                time.sleep(3)
            else:
                hooks["update_status"](f"❌ Failed to beat rival's PB.\nLoading next challenge..."); time.sleep(3)
        else:
            hooks["update_history"](f"(No new score) {selected_scenario.scenarioName}"); hooks["update_status"](
                f"No new score detected. Loading next challenge..."); time.sleep(2)
    hooks["challenge_ended"]()