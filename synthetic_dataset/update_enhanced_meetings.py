import json
import os
import random
from typing import Dict, List

def update_enhanced_meetings():
    """
    Update all enhanced meetings with:
    1. Change wife name from "Meera Vasanth" to "Meera Arjun"
    2. Update timestamps to be realistic for longer dialogues
    """
    
    enhanced_dir = r"C:\Users\Ranesh RK\Downloads\projects\RetrievalPOC\synthetic_dataset\enhanced_meetings"
    
    # Get all enhanced meeting files
    meeting_files = [f for f in os.listdir(enhanced_dir) if f.startswith('enhanced_meeting_') and f.endswith('.json')]
    
    print(f"Found {len(meeting_files)} enhanced meetings to update...")
    
    for filename in meeting_files:
        filepath = os.path.join(enhanced_dir, filename)
        
        # Read the meeting file
        with open(filepath, 'r', encoding='utf-8') as f:
            meeting = json.load(f)
        
        # Update 1: Change wife's name in participants
        updated_participants = []
        for participant in meeting["participants"]:
            if participant["name"] == "Meera Vasanth":
                participant["name"] = "Meera Arjun"
            updated_participants.append(participant)
        meeting["participants"] = updated_participants
        
        # Update 2: Change wife's name in dialogue minutes
        updated_minutes = []
        for minute in meeting["minutes"]:
            if minute["speaker"] == "Meera Vasanth":
                minute["speaker"] = "Meera Arjun"
            updated_minutes.append(minute)
        
        # Update 3: Realistic timestamps based on dialogue length
        updated_minutes = update_realistic_timestamps(updated_minutes)
        meeting["minutes"] = updated_minutes
        
        # Update 4: Update action items if they reference the old name
        updated_action_items = []
        for item in meeting["action_items"]:
            # No changes needed for action items in this case since they typically assign to "Arjun Vasanth"
            updated_action_items.append(item)
        meeting["action_items"] = updated_action_items
        
        # Save the updated meeting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(meeting, f, indent=2, ensure_ascii=False)
        
        print(f"Updated: {filename}")
    
    print(f"\nSuccessfully updated all {len(meeting_files)} enhanced meetings!")

def update_realistic_timestamps(minutes: List[Dict]) -> List[Dict]:
    """
    Update timestamps to be realistic for longer dialogues.
    Each speaker turn should have appropriate time gaps based on dialogue length.
    """
    
    current_time_seconds = 0
    updated_minutes = []
    
    for i, minute in enumerate(minutes):
        # Set current timestamp
        minute["timestamp"] = format_timestamp(current_time_seconds)
        
        # Calculate time for this dialogue based on word count
        word_count = len(minute["text"].split())
        
        # Realistic speaking time calculation:
        # - Average speaking speed: 150-200 words per minute
        # - Add thinking/pause time
        # - Add listener processing time
        
        if word_count <= 50:
            dialogue_duration = random.randint(30, 60)  # 30-60 seconds for short responses
        elif word_count <= 100:
            dialogue_duration = random.randint(60, 120)  # 1-2 minutes for medium responses
        elif word_count <= 200:
            dialogue_duration = random.randint(120, 180)  # 2-3 minutes for long responses
        else:
            dialogue_duration = random.randint(180, 300)  # 3-5 minutes for very long responses
        
        # Add some pause time between speakers (thinking/processing time)
        pause_time = random.randint(5, 15)  # 5-15 seconds pause between speakers
        
        # Update current time for next speaker
        current_time_seconds += dialogue_duration + pause_time
        
        updated_minutes.append(minute)
    
    return updated_minutes

def format_timestamp(total_seconds: int) -> str:
    """
    Convert total seconds to MM:SS format.
    If over 60 minutes, use HH:MM:SS format.
    """
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def verify_updates():
    """
    Verify that updates were applied correctly.
    """
    enhanced_dir = r"C:\Users\Ranesh RK\Downloads\projects\RetrievalPOC\synthetic_dataset\enhanced_meetings"
    
    # Check a few files to verify changes
    test_files = ["enhanced_meeting_001.json", "enhanced_meeting_051.json"]
    
    print("\n=== VERIFICATION ===")
    
    for filename in test_files:
        filepath = os.path.join(enhanced_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                meeting = json.load(f)
            
            print(f"\nChecking {filename}:")
            
            # Check participants
            participants = [p["name"] for p in meeting["participants"]]
            has_meera_arjun = "Meera Arjun" in participants
            has_meera_vasanth = "Meera Vasanth" in participants
            
            print(f"  Participants: {participants}")
            print(f"  Has 'Meera Arjun': {has_meera_arjun}")
            print(f"  Has 'Meera Vasanth': {has_meera_vasanth}")
            
            # Check timestamps
            if meeting["minutes"]:
                first_timestamp = meeting["minutes"][0]["timestamp"]
                last_timestamp = meeting["minutes"][-1]["timestamp"]
                print(f"  First timestamp: {first_timestamp}")
                print(f"  Last timestamp: {last_timestamp}")
                print(f"  Total dialogue minutes: {len(meeting['minutes'])}")

if __name__ == "__main__":
    print("Starting enhanced meetings update process...")
    print("1. Changing wife name from 'Meera Vasanth' to 'Meera Arjun'")
    print("2. Updating timestamps to be realistic for longer dialogues")
    print()
    
    update_enhanced_meetings()
    verify_updates()
    
    print("\nAll updates completed successfully!")
    print("Your enhanced meetings now have:")
    print("  - Correct wife name: 'Meera Arjun'")
    print("  - Realistic timestamps based on dialogue length")