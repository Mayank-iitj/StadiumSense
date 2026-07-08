import json
import urllib.request
from pathlib import Path

def generate_timeline():
    match_id = 3869685 # World Cup Final 2022
    url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json"
    print(f"Fetching events for match {match_id} directly from StatsBomb GitHub...")
    
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        events = json.loads(response.read().decode('utf-8'))
        
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
        event_type = e.get('type', {}).get('name')
        team = e.get('team', {}).get('name')
        player = e.get('player', {}).get('name', 'Unknown Player')
        minute = e.get('minute', 0)
        
        event_obj = None
        
        if event_type == 'Shot' and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
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
            replacement = e.get('substitution', {}).get('replacement', {}).get('name', 'a substitute')
            event_obj = {
                "type": "pa_announcement",
                "original": f"Substitution for {team}. {replacement} comes on for {player}.",
                "category": "match_event",
                "severity": "info"
            }
            
        elif event_type == 'Foul Committed':
            card = e.get('foul_committed', {}).get('card', {}).get('name')
            if card in ['Yellow Card', 'Red Card']:
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
            current_delay += 10
            
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
                 
    timeline.sort(key=lambda x: x['delay'])
    out_data = {"timeline": timeline}
    out_path = Path(__file__).parent / "match_timeline.json"
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(timeline)} events and saved to {out_path}")

if __name__ == '__main__':
    generate_timeline()
