import json
import random
import pandas as pd
from pathlib import Path

def generate_timeline():
    csv_path = r"C:\Users\MS\Downloads\fifadataset\train.csv"
    print(f"Loading dataset from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    # Filter for the most recent version (e.g. 2018)
    latest_year = df['version'].max()
    df_latest = df[df['version'] == latest_year]
    
    # Pick two high-profile teams
    top_teams = df_latest.sort_values(by='fifa_rank_pre_tournament').head(2)
    team_a = top_teams.iloc[0]['team']
    team_b = top_teams.iloc[1]['team']
    
    # Simple goal probability based on goals_scored_last_4y
    goals_a = int(top_teams.iloc[0]['goals_scored_last_4y'] / 30)
    goals_b = int(top_teams.iloc[1]['goals_scored_last_4y'] / 40)
    
    if goals_a == 0: goals_a = 1
    if goals_b == 0: goals_b = 1
    
    print(f"Simulating match: {team_a} vs {team_b}")
    print(f"Expected outcome: {team_a} {goals_a} - {goals_b} {team_b}")
    
    timeline = []
    
    # Add an initial welcome announcement
    timeline.append({
        "delay": 2,
        "event": {
            "type": "pa_announcement",
            "original": f"Welcome to the stadium! Today's highly anticipated match is between {team_a} and {team_b}.",
            "category": "wayfinding",
            "severity": "info"
        }
    })
    
    current_delay = 10
    score_a = 0
    score_b = 0
    
    events_to_schedule = []
    
    for _ in range(goals_a):
        minute = random.randint(5, 89)
        events_to_schedule.append((minute, team_a))
        
    for _ in range(goals_b):
        minute = random.randint(5, 89)
        events_to_schedule.append((minute, team_b))
        
    for _ in range(2):
        minute = random.randint(10, 85)
        events_to_schedule.append((minute, 'Card'))
        
    events_to_schedule.sort(key=lambda x: x[0])
    
    for minute, event_type in events_to_schedule:
        if event_type == team_a:
            score_a += 1
            event_obj = {
                "type": "match_event",
                "original": f"GOAL! {team_a} scores in the {minute}th minute! Score is now {team_a} {score_a} - {score_b} {team_b}.",
                "category": "match_event",
                "severity": "crowd",
                "team_a": team_a,
                "team_b": team_b,
                "minute": minute,
                "scorer": f"A player from {team_a}",
                "description": f"GOAL! {team_a} takes their chance!"
            }
        elif event_type == team_b:
            score_b += 1
            event_obj = {
                "type": "match_event",
                "original": f"GOAL! {team_b} scores in the {minute}th minute! Score is now {team_a} {score_a} - {score_b} {team_b}.",
                "category": "match_event",
                "severity": "crowd",
                "team_a": team_a,
                "team_b": team_b,
                "minute": minute,
                "scorer": f"A player from {team_b}",
                "description": f"GOAL! {team_b} responds with a brilliant strike!"
            }
        else:
            team = random.choice([team_a, team_b])
            event_obj = {
                "type": "pa_announcement",
                "original": f"Yellow card shown to a player from {team} in the {minute}th minute.",
                "category": "match_event",
                "severity": "warning"
            }
            
        timeline.append({
            "delay": current_delay,
            "event": event_obj
        })
        current_delay += 10
        
        # Interleave stadium announcements
        if len(timeline) == 3:
            timeline.append({
                "delay": current_delay,
                "event": {
                    "type": "pa_announcement",
                    "original": "Medical team to Section 114, row 8. Medical team to Section 114.",
                    "category": "medical",
                    "severity": "warning"
                }
            })
            current_delay += 8
        elif len(timeline) == 5:
            timeline.append({
                "delay": current_delay,
                "event": {
                    "type": "staff_broadcast",
                    "original": "Please keep aisles clear near Section 114. Move to your seats.",
                    "category": "wayfinding",
                    "severity": "info"
                }
            })
            current_delay += 8
        elif len(timeline) == 7:
             timeline.append({
                "delay": current_delay,
                "event": {
                    "type": "evacuation_drill",
                    "original": "ATTENTION: This is an evacuation drill. Please proceed calmly to the nearest exit.",
                    "category": "evacuation",
                    "severity": "critical",
                    "location": "East exit"
                }
            })
             current_delay += 8
             
    timeline.sort(key=lambda x: x['delay'])
    out_data = {"timeline": timeline}
    out_path = Path(__file__).parent / "match_timeline.json"
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(timeline)} events and saved to {out_path}")

if __name__ == '__main__':
    generate_timeline()
