import json
import os
from pathlib import Path

# Try importing statsbombpy
try:
    from statsbombpy import sb
except ImportError:
    print("Please install statsbombpy (pip install statsbombpy)")
    exit(1)

def generate_timeline():
    match_id = 3869685 # World Cup Final 2022
    print(f"Fetching events for match {match_id} from StatsBomb...")
    
    events_df = sb.events(match_id=match_id)
    
    # Convert to list of dicts
    events = events_df.to_dict('records')
    
    timeline = []
    
    # Add an initial welcome announcement
    timeline.append({
        "delay": 2,
        "event": {
            "type": "pa_announcement",
            "original": "Welcome to Lusail Stadium for the FIFA World Cup Final! Concession stands are open.",
            "category": "wayfinding",
            "severity": "info"
        }
    })
    
    current_delay = 10
    
    for e in events:
        event_type = e.get('type')
        team = e.get('team')
        player = e.get('player')
        minute = e.get('minute', 0)
        
        event_obj = None
        
        if event_type == 'Shot' and e.get('shot_outcome') == 'Goal':
            # It's a goal
            scorer = player
            event_obj = {
                "type": "match_event",
                "original": f"GOAL! {team} scores! {scorer} finds the net in the {minute}th minute.",
                "category": "match_event",
                "severity": "crowd",
                "team_a": "Argentina",
                "team_b": "France",
                "minute": minute,
                "scorer": scorer,
                "description": f"GOAL for {team} by {scorer}! The crowd goes wild!"
            }
            
        elif event_type == 'Substitution':
            replacement = e.get('substitution_replacement')
            event_obj = {
                "type": "pa_announcement",
                "original": f"Substitution for {team}. {replacement} comes on for {player}.",
                "category": "match_event",
                "severity": "info"
            }
            
        elif event_type == 'Foul Committed' and e.get('foul_committed_card') in ['Yellow Card', 'Red Card']:
            card = e.get('foul_committed_card')
            event_obj = {
                "type": "pa_announcement",
                "original": f"{card} shown to {player} of {team}.",
                "category": "match_event",
                "severity": "warning"
            }
            
        if event_obj:
            timeline.append({
                "delay": current_delay,
                "event": event_obj
            })
            current_delay += 10 # Add 10s delay between major events
            
            # Interleave some synthetic announcements
            if len(timeline) == 4:
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
            elif len(timeline) == 8:
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
            elif len(timeline) == 12:
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
                 
    # Sort timeline by delay just in case
    timeline.sort(key=lambda x: x['delay'])
    
    out_data = {"timeline": timeline}
    
    out_path = Path(__file__).parent / "match_timeline.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(timeline)} events and saved to {out_path}")

if __name__ == '__main__':
    generate_timeline()
