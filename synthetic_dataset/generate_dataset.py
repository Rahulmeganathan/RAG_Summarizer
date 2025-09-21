import json
import random
import datetime
from typing import List, Dict, Tuple, Any
from collections import Counter
import os

class MeetingDatasetGenerator:
    def __init__(self, character_profiles_path: str):
        """Initialize the dataset generator with character profiles."""
        with open(character_profiles_path, 'r') as f:
            self.characters = json.load(f)
        
        # Initialize generation parameters
        self.start_date = datetime.date(2024, 1, 1)
        self.end_date = datetime.date(2024, 6, 30)
        self.meetings_count = 0
        self.generated_meetings = []
        
        # Meeting distribution rules
        self.business_meeting_ratio = 0.65
        self.family_meeting_ratio = 0.20
        self.mixed_meeting_ratio = 0.15
        
        # Time patterns
        self.business_hours = [(9, 17)]  # 9 AM to 5 PM
        self.family_hours = [(18, 21), (7, 9)]  # Evening and early morning
        
    def generate_meeting_id(self, date: datetime.date) -> str:
        """Generate unique meeting ID."""
        self.meetings_count += 1
        return f"MTG_{date.strftime('%Y_%m_%d')}_{self.meetings_count:03d}"
    
    def select_participants_by_rules(self, meeting_type: str) -> List[Dict[str, str]]:
        """Select participants based on meeting type rules."""
        participants = [{"name": "Arjun Vasanth", "role": "founder"}]
        
        if meeting_type == "business":
            # Business meeting logic
            meeting_subtype = random.choice([
                "investor", "team", "mentor", "peer_networking"
            ])
            
            if meeting_subtype == "investor":
                # 1-2 investors + optional mentor
                investor_names = list(self.characters["investors"].keys())
                selected_investors = random.sample(investor_names, 
                                                 random.randint(1, min(2, len(investor_names))))
                for inv in selected_investors:
                    participants.append({"name": inv, "role": "investor"})
                    
                # Optional mentor
                if random.random() < 0.3:
                    mentor_names = list(self.characters["mentors"].keys())
                    mentor = random.choice(mentor_names)
                    participants.append({"name": mentor, "role": "mentor"})
                    
            elif meeting_subtype == "team":
                # 2-3 team members
                team_names = [name for name, data in self.characters["peers_team"].items() 
                             if data["role"] == "team"]
                selected_team = random.sample(team_names, 
                                            random.randint(1, min(3, len(team_names))))
                for member in selected_team:
                    participants.append({"name": member, "role": "team"})
                    
            elif meeting_subtype == "mentor":
                # 1 mentor + optional peer
                mentor_names = list(self.characters["mentors"].keys())
                mentor = random.choice(mentor_names)
                participants.append({"name": mentor, "role": "mentor"})
                
                if random.random() < 0.4:
                    peer_names = [name for name, data in self.characters["peers_team"].items()
                                 if data["role"] == "peer"]
                    if peer_names:
                        peer = random.choice(peer_names)
                        participants.append({"name": peer, "role": "peer"})
                        
            elif meeting_subtype == "peer_networking":
                # 2-4 peers
                peer_names = [name for name, data in self.characters["peers_team"].items()
                             if data["role"] == "peer"]
                selected_peers = random.sample(peer_names,
                                             random.randint(1, min(4, len(peer_names))))
                for peer in selected_peers:
                    participants.append({"name": peer, "role": "peer"})
                    
        elif meeting_type == "family":
            # Family meeting logic
            family_names = list(self.characters["family"].keys())
            selected_family = random.sample(family_names,
                                          random.randint(1, len(family_names)))
            for member in selected_family:
                participants.append({"name": member, "role": "family"})
                
        elif meeting_type == "mixed":
            # Mixed meeting: family concerns about business
            # Always include spouse, sometimes parents
            participants.append({"name": "Meera Vasanth", "role": "family"})
            
            if random.random() < 0.5:
                parents = ["Dr. Krishnan Vasanth", "Lakshmi Vasanth"]
                selected_parent = random.choice(parents)
                participants.append({"name": selected_parent, "role": "family"})
                
            # Sometimes include mentor for guidance
            if random.random() < 0.3:
                mentor_names = list(self.characters["mentors"].keys())
                mentor = random.choice(mentor_names)
                participants.append({"name": mentor, "role": "mentor"})
        
        return participants
    
    def select_topics(self, meeting_type: str) -> List[str]:
        """Select 2 topics based on meeting type and logical combinations."""
        topics = self.characters["topics"]
        
        # Define topic combinations based on meeting type
        if meeting_type == "business":
            business_topics = [
                "AI Insurance POC Development",
                "Investor Pitch & Feedback Sessions", 
                "Product Demo & Technical Reviews",
                "Market Strategy & Competition Analysis",
                "Team Building & Hiring",
                "Regulatory Compliance Discussions",
                "Customer Acquisition & Sales Pipeline",
                "Technology Infrastructure & Scaling"
            ]
            # Define complementary pairs
            complementary_pairs = [
                ("AI Insurance POC Development", "Investor Pitch & Feedback Sessions"),
                ("Product Demo & Technical Reviews", "Market Strategy & Competition Analysis"),
                ("Team Building & Hiring", "Technology Infrastructure & Scaling"),
                ("Customer Acquisition & Sales Pipeline", "Market Strategy & Competition Analysis"),
                ("AI Insurance POC Development", "Product Demo & Technical Reviews"),
                ("Investor Pitch & Feedback Sessions", "Market Strategy & Competition Analysis")
            ]
            
            if random.random() < 0.7:  # 70% chance for complementary topics
                return list(random.choice(complementary_pairs))
            else:
                return random.sample(business_topics, 2)
                
        elif meeting_type == "family":
            family_topics = [
                "Family Financial Concerns",
                "Stress Management & Work-Life Balance"
            ]
            other_topics = [
                "AI Insurance POC Development",
                "Investor Pitch & Feedback Sessions"
            ]
            # Mix family concerns with business context
            return [random.choice(family_topics), random.choice(other_topics)]
            
        elif meeting_type == "mixed":
            # Mixed meetings focus on intersection of personal and business
            return [
                "Family Financial Concerns",
                "Stress Management & Work-Life Balance"
            ]
            
        return random.sample(topics, 2)
    
    def generate_meeting_time(self, meeting_type: str, date: datetime.date) -> str:
        """Generate realistic meeting time based on type and day."""
        if meeting_type == "business":
            # Business hours: 9 AM - 5 PM
            hour = random.randint(9, 17)
            minute = random.choice([0, 15, 30, 45])  # Standard meeting times
        elif meeting_type == "family":
            # Family time: evenings or early morning weekends
            if date.weekday() >= 5:  # Weekend
                hour = random.randint(9, 20)
            else:  # Weekday
                hour = random.randint(19, 21)
            minute = random.choice([0, 30])
        else:  # mixed
            # Mixed meetings often happen in evenings
            hour = random.randint(18, 20)
            minute = random.choice([0, 30])
            
        return f"{hour:02d}:{minute:02d}"
    
    def generate_location(self, meeting_type: str, participants: List[Dict]) -> str:
        """Generate realistic location based on meeting type and participants."""
        if meeting_type == "business":
            if any(p["role"] == "investor" for p in participants):
                investor_names = [p["name"] for p in participants if p["role"] == "investor"]
                if "Priya Sharma" in investor_names:
                    return "Nexus Venture Partners Office, Bangalore"
                elif "Rajesh Gupta" in investor_names:
                    return "The Leela Palace Hotel, Bangalore"
                elif "David Chen" in investor_names:
                    return "Video Call (Singapore)"
                else:
                    return "Investor Office, Bangalore"
            elif any(p["role"] == "team" for p in participants):
                return "InsureAI Office, Koramangala, Bangalore"
            else:
                return random.choice([
                    "Café Coffee Day, HSR Layout", 
                    "The Toit Brewpub, Indiranagar",
                    "Video Call"
                ])
        elif meeting_type == "family":
            return "Home, Whitefield, Bangalore"
        else:  # mixed
            return random.choice([
                "Home, Whitefield, Bangalore",
                "Café Coffee Day near home"
            ])
    
    def generate_dialogue_simple(self, participants: List[Dict], topics: List[str], 
                                meeting_type: str) -> List[Dict[str, Any]]:
        """Generate realistic dialogue with startup jargon and emotional authenticity."""
        minutes = []
        jargon = self.characters["jargon_categories"]
        
        # Opening - Arjun usually starts
        timestamp_minutes = 0
        
        # Generate opening based on meeting type
        if meeting_type == "business" and any(p["role"] == "investor" for p in participants):
            opening_texts = [
                f"Thank you for taking this meeting. Our AI insurance POC is showing {random.randint(90, 95)}% accuracy in claims processing.",
                f"I appreciate your time today. We've made significant progress on the {random.choice(topics).lower()} front.",
                f"Thanks for the opportunity to present. Our {random.choice(jargon['technical_terms'])} is now handling real-world insurance data."
            ]
        elif meeting_type == "family":
            opening_texts = [
                "I know you're all concerned about the long hours I've been putting in...",
                "I wanted to update you on how things are progressing with the company.",
                "I understand your worries about our financial situation..."
            ]
        else:
            opening_texts = [
                f"Let's discuss the {topics[0].lower()} and where we stand.",
                f"I think we need to address both {topics[0].lower()} and {topics[1].lower()} today."
            ]
        
        minutes.append({
            "timestamp": f"00:{timestamp_minutes:02d}:00",
            "speaker": "Arjun Vasanth",
            "text": random.choice(opening_texts)
        })
        timestamp_minutes += random.randint(1, 3)
        
        # Generate responses from other participants
        for participant in participants[1:]:  # Skip Arjun
            char_data = self.get_character_data(participant["name"])
            if char_data:
                response_text = self.generate_character_response(
                    participant, char_data, topics, meeting_type, jargon
                )
                minutes.append({
                    "timestamp": f"00:{timestamp_minutes:02d}:00",
                    "speaker": participant["name"],
                    "text": response_text
                })
                timestamp_minutes += random.randint(1, 4)
        
        # Add Arjun's follow-up responses
        for i in range(random.randint(2, 4)):
            followup_text = self.generate_arjun_followup(topics, meeting_type, jargon)
            minutes.append({
                "timestamp": f"00:{timestamp_minutes:02d}:00", 
                "speaker": "Arjun Vasanth",
                "text": followup_text
            })
            timestamp_minutes += random.randint(1, 3)
            
            # Add another participant response
            if len(participants) > 1:
                participant = random.choice(participants[1:])
                char_data = self.get_character_data(participant["name"])
                if char_data:
                    response_text = self.generate_character_response(
                        participant, char_data, topics, meeting_type, jargon
                    )
                    minutes.append({
                        "timestamp": f"00:{timestamp_minutes:02d}:00",
                        "speaker": participant["name"], 
                        "text": response_text
                    })
                    timestamp_minutes += random.randint(1, 3)
        
        return minutes
    
    def get_character_data(self, name: str) -> Dict:
        """Get character data from profiles."""
        for category in ["investors", "family", "mentors", "peers_team"]:
            if name in self.characters[category]:
                return self.characters[category][name]
        return {}
    
    def generate_character_response(self, participant: Dict, char_data: Dict, 
                                   topics: List[str], meeting_type: str, 
                                   jargon: Dict) -> str:
        """Generate character-specific response."""
        role = participant["role"]
        
        if role == "investor":
            business_terms = random.sample(jargon["business_metrics"], 2)
            investor_concerns = [
                f"What's your {business_terms[0]} looking like? I need to see clear unit economics.",
                f"The {random.choice(jargon['technical_terms'])} sounds promising, but show me the {business_terms[1]} data.",
                f"How do you plan to scale this across different insurance verticals? What's your {random.choice(jargon['business_metrics'])}?",
                f"I'm seeing competition heat up in insurtech. What's your competitive moat and {random.choice(jargon['product_terms'])}?"
            ]
            base_response = random.choice(investor_concerns)
            if char_data.get("typical_phrases"):
                phrase = random.choice(char_data["typical_phrases"])
                return f"{phrase} {base_response}"
            return base_response
            
        elif role == "family":
            family_concerns = [
                "You've been working 80-hour weeks for months. This is affecting your health and our relationship.",
                "What happens to our home loan and savings if this doesn't work out?",
                "I'm worried about the stress you're under. Can you at least take Sundays off?",
                "The uncertainty is hard on all of us. Do you have a backup plan?"
            ]
            if char_data.get("typical_phrases"):
                phrase = random.choice(char_data["typical_phrases"]) 
                return f"{phrase}. {random.choice(family_concerns)}"
            return random.choice(family_concerns)
            
        elif role == "mentor":
            mentor_advice = [
                f"Focus on {random.choice(jargon['product_terms'])} first. I made similar mistakes in my early days.",
                f"Customer retention is more important than acquisition right now. Build for {random.choice(jargon['product_terms'])}.",
                f"Don't scale too early. Make sure your {random.choice(jargon['technical_terms'])} is solid first.",
                f"Investor rejections are normal. Focus on improving your {random.choice(jargon['business_metrics'])} metrics."
            ]
            return random.choice(mentor_advice)
            
        elif role == "team":
            team_updates = [
                f"Our {random.choice(jargon['technical_terms'])} is improving, showing {random.randint(85, 95)}% accuracy now.",
                f"We need more training data for the {random.choice(jargon['technical_terms'])}. Should we try a different approach?",
                f"The {random.choice(jargon['technical_terms'])} latency is concerning customers. We need to optimize.",
                f"Competition is asking about similar features. How should we differentiate our {random.choice(jargon['product_terms'])}?"
            ]
            return random.choice(team_updates)
            
        elif role == "peer":
            peer_solidarity = [
                f"We're facing similar {random.choice(jargon['technical_terms'])} challenges. Let's share learnings.",
                f"The {random.choice(jargon['business_metrics'])} struggle is real for all of us in insurtech.",
                f"Have you tried this approach for {random.choice(jargon['product_terms'])}? It worked for us.",
                f"Fundraising is tough right now. How's your {random.choice(jargon['funding_terms'])} progress?"
            ]
            return random.choice(peer_solidarity)
        
        return "I understand the challenges we're facing."
    
    def generate_arjun_followup(self, topics: List[str], meeting_type: str, jargon: Dict) -> str:
        """Generate Arjun's follow-up responses with stress and technical details."""
        stress_indicators = ["Well, I think...", "Actually, let me clarify...", "The thing is..."]
        
        if meeting_type == "business":
            business_responses = [
                f"{random.choice(stress_indicators)} our {random.choice(jargon['technical_terms'])} is showing {random.randint(90, 95)}% accuracy, and the {random.choice(jargon['business_metrics'])} is improving.",
                f"I understand the concerns about {random.choice(jargon['business_metrics'])}, but our {random.choice(jargon['product_terms'])} metrics are strong.",
                f"The {random.choice(jargon['funding_terms'])} timeline is tight, but we're confident about {random.choice(jargon['product_terms'])}.",
                f"We're addressing the {random.choice(jargon['technical_terms'])} issues and expect {random.choice(jargon['business_metrics'])} to improve next quarter."
            ]
            return random.choice(business_responses)
        elif meeting_type == "family":
            family_responses = [
                "I know the long hours are affecting us, but this round is critical for our future.",
                "The stress is temporary. Once we close this funding, things will stabilize.",
                "I'm trying to balance everything, but the investor meetings are crucial right now.",
                "Give me three more months. If we don't see progress, I'll reconsider."
            ]
            return random.choice(family_responses)
        else:  # mixed
            mixed_responses = [
                "I'm trying to balance the business demands with our family needs.",
                "The investor pressure is intense, but I don't want it to affect our relationship.",
                "Maybe we can set some boundaries - no work calls after 9 PM?",
                "I appreciate your patience. This phase won't last forever."
            ]
            return random.choice(mixed_responses)
    
    def generate_action_items(self, participants: List[Dict], topics: List[str], 
                            meeting_type: str, meeting_date: datetime.date) -> List[Dict]:
        """Generate logical action items based on meeting discussion."""
        action_items = []
        
        # Calculate due dates
        due_date_options = [
            meeting_date + datetime.timedelta(days=7),   # 1 week
            meeting_date + datetime.timedelta(days=14),  # 2 weeks
            meeting_date + datetime.timedelta(days=21),  # 3 weeks
        ]
        
        if meeting_type == "business":
            if any(p["role"] == "investor" for p in participants):
                # Investor meeting action items
                action_items.extend([
                    {
                        "assigned_to": "Arjun Vasanth",
                        "task": f"Prepare detailed CAC and LTV analysis for {random.choice(topics)}",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "high"
                    },
                    {
                        "assigned_to": "Arjun Vasanth", 
                        "task": f"Create multi-vertical scaling strategy document with TAM analysis",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "high"
                    }
                ])
            elif any(p["role"] == "team" for p in participants):
                # Team meeting action items
                action_items.extend([
                    {
                        "assigned_to": "Arjun Vasanth",
                        "task": f"Review ML pipeline optimization for improved accuracy",
                        "due_date": random.choice(due_date_options).isoformat(),
                        "priority": "medium"
                    },
                    {
                        "assigned_to": random.choice([p["name"] for p in participants if p["role"] == "team"]),
                        "task": "Implement API latency improvements and performance monitoring",
                        "due_date": random.choice(due_date_options).isoformat(), 
                        "priority": "high"
                    }
                ])
        elif meeting_type == "family":
            # Family meeting action items
            action_items.append({
                "assigned_to": "Arjun Vasanth",
                "task": "Set boundaries for work hours and family time",
                "due_date": (meeting_date + datetime.timedelta(days=3)).isoformat(),
                "priority": "medium"
            })
        elif meeting_type == "mixed":
            # Mixed meeting action items  
            action_items.extend([
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Create work-life balance plan and share with family",
                    "due_date": (meeting_date + datetime.timedelta(days=7)).isoformat(),
                    "priority": "medium"
                },
                {
                    "assigned_to": "Arjun Vasanth",
                    "task": "Schedule weekly family check-ins to discuss business progress",
                    "due_date": (meeting_date + datetime.timedelta(days=7)).isoformat(), 
                    "priority": "low"
                }
            ])
        
        return action_items[:random.randint(1, 3)]  # 1-3 action items per meeting
    
    def generate_meetings(self, total_meetings: int = 55) -> List[Dict]:
        """Generate the complete dataset of meetings."""
        meetings = []
        
        # Calculate meeting distribution
        business_count = int(total_meetings * self.business_meeting_ratio)
        family_count = int(total_meetings * self.family_meeting_ratio) 
        mixed_count = total_meetings - business_count - family_count
        
        meeting_types = (["business"] * business_count + 
                        ["family"] * family_count + 
                        ["mixed"] * mixed_count)
        random.shuffle(meeting_types)
        
        # Generate dates across the period
        total_days = (self.end_date - self.start_date).days
        dates = []
        
        for i in range(total_meetings):
            # More frequent meetings during intense periods (March-May)
            if random.random() < 0.7:  # 70% of meetings in peak period
                # Peak period: March-May 2024
                peak_start = datetime.date(2024, 3, 1)
                peak_end = datetime.date(2024, 5, 31)
                peak_days = (peak_end - peak_start).days
                day_offset = random.randint(0, peak_days)
                meeting_date = peak_start + datetime.timedelta(days=day_offset)
            else:
                # Distributed across full period
                day_offset = random.randint(0, total_days)
                meeting_date = self.start_date + datetime.timedelta(days=day_offset)
            
            dates.append(meeting_date)
        
        dates.sort()  # Chronological order
        
        # Generate meetings
        for i, (meeting_type, meeting_date) in enumerate(zip(meeting_types, dates)):
            participants = self.select_participants_by_rules(meeting_type)
            topics = self.select_topics(meeting_type) 
            meeting_time = self.generate_meeting_time(meeting_type, meeting_date)
            location = self.generate_location(meeting_type, participants)
            minutes = self.generate_dialogue_simple(participants, topics, meeting_type)
            action_items = self.generate_action_items(participants, topics, meeting_type, meeting_date)
            
            meeting = {
                "meeting_id": self.generate_meeting_id(meeting_date),
                "meeting_date": meeting_date.isoformat(),
                "meeting_time": meeting_time,
                "location": location,
                "participants": participants,
                "topics": topics,
                "meeting_type": meeting_type,
                "minutes": minutes,
                "action_items": action_items
            }
            
            meetings.append(meeting)
            
        self.generated_meetings = meetings
        return meetings
    
    def save_meetings(self, output_dir: str):
        """Save individual meeting files and summary."""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "raw_meetings"), exist_ok=True)
        
        # Save individual meeting files
        for i, meeting in enumerate(self.generated_meetings, 1):
            filename = f"meeting_{i:03d}.json"
            filepath = os.path.join(output_dir, "raw_meetings", filename)
            with open(filepath, 'w') as f:
                json.dump(meeting, f, indent=2)
        
        # Generate and save summary statistics
        summary = self.generate_summary()
        summary_path = os.path.join(output_dir, "dataset_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"Generated {len(self.generated_meetings)} meetings")
        print(f"Saved to: {output_dir}")
        print(f"Summary saved to: {summary_path}")
    
    def generate_summary(self) -> Dict:
        """Generate comprehensive summary statistics."""
        if not self.generated_meetings:
            return {}
        
        # Basic statistics
        total_meetings = len(self.generated_meetings)
        meeting_types = Counter(m["meeting_type"] for m in self.generated_meetings)
        
        # Participant statistics
        all_participants = []
        for meeting in self.generated_meetings:
            for p in meeting["participants"]:
                if p["name"] != "Arjun Vasanth":  # Exclude Arjun from counts
                    all_participants.append((p["name"], p["role"]))
        
        participant_counts = Counter(all_participants)
        role_counts = Counter(role for _, role in all_participants)
        
        # Topic statistics
        all_topics = []
        for meeting in self.generated_meetings:
            all_topics.extend(meeting["topics"])
        topic_counts = Counter(all_topics)
        
        # Date range
        dates = [datetime.datetime.fromisoformat(m["meeting_date"]).date() 
                for m in self.generated_meetings]
        
        # Action item statistics
        total_action_items = sum(len(m["action_items"]) for m in self.generated_meetings)
        
        return {
            "generation_date": datetime.datetime.now().isoformat(),
            "total_meetings": total_meetings,
            "date_range": {
                "start": min(dates).isoformat(),
                "end": max(dates).isoformat()
            },
            "meeting_type_distribution": dict(meeting_types),
            "participant_appearances": {
                f"{name} ({role})": count for (name, role), count in participant_counts.most_common()
            },
            "role_distribution": dict(role_counts),
            "topic_frequency": dict(topic_counts),
            "total_action_items": total_action_items,
            "average_action_items_per_meeting": round(total_action_items / total_meetings, 2),
            "meetings_per_month": {
                month: len([d for d in dates if d.month == month])
                for month in range(1, 7)  # Jan-June
            }
        }


def main():
    """Main function to generate the dataset."""
    # File paths
    base_dir = r"C:\Users\Ranesh RK\Downloads\projects\RetrievalPOC\synthetic_dataset"
    character_profiles_path = os.path.join(base_dir, "character_profiles.json")
    
    # Initialize generator
    generator = MeetingDatasetGenerator(character_profiles_path)
    
    # Generate meetings
    print("Generating synthetic meeting dataset...")
    meetings = generator.generate_meetings(total_meetings=55)
    
    # Save results
    generator.save_meetings(base_dir)
    
    print("\nDataset generation completed successfully!")
    print(f"Total meetings generated: {len(meetings)}")
    
    # Print summary statistics
    summary = generator.generate_summary()
    print(f"\nMeeting Distribution:")
    for meeting_type, count in summary["meeting_type_distribution"].items():
        percentage = (count / summary["total_meetings"]) * 100
        print(f"  {meeting_type.title()}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()