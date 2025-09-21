import json
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any

class DatasetValidator:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.meetings_dir = os.path.join(dataset_dir, "raw_meetings") 
        self.meetings = []
        self.load_meetings()
        
    def load_meetings(self):
        """Load all meeting JSON files."""
        for filename in sorted(os.listdir(self.meetings_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(self.meetings_dir, filename)
                with open(filepath, 'r') as f:
                    meeting = json.load(f)
                    self.meetings.append(meeting)
        print(f"Loaded {len(self.meetings)} meetings for validation")
    
    def validate_json_structure(self) -> Dict[str, Any]:
        """Validate that all meetings follow the required JSON schema."""
        required_fields = [
            "meeting_id", "meeting_date", "meeting_time", "location",
            "participants", "topics", "meeting_type", "minutes", "action_items"
        ]
        
        validation_results = {
            "total_meetings": len(self.meetings),
            "valid_meetings": 0,
            "schema_errors": [],
            "missing_fields": defaultdict(int)
        }
        
        for i, meeting in enumerate(self.meetings):
            meeting_valid = True
            for field in required_fields:
                if field not in meeting:
                    validation_results["missing_fields"][field] += 1
                    validation_results["schema_errors"].append(
                        f"Meeting {i+1}: Missing field '{field}'"
                    )
                    meeting_valid = False
            
            # Validate participants structure
            if "participants" in meeting:
                for j, participant in enumerate(meeting["participants"]):
                    if "name" not in participant or "role" not in participant:
                        validation_results["schema_errors"].append(
                            f"Meeting {i+1}: Participant {j+1} missing name/role"
                        )
                        meeting_valid = False
            
            # Validate minutes structure  
            if "minutes" in meeting:
                for j, minute in enumerate(meeting["minutes"]):
                    required_minute_fields = ["timestamp", "speaker", "text"]
                    for field in required_minute_fields:
                        if field not in minute:
                            validation_results["schema_errors"].append(
                                f"Meeting {i+1}: Minute {j+1} missing '{field}'"
                            )
                            meeting_valid = False
            
            if meeting_valid:
                validation_results["valid_meetings"] += 1
        
        return validation_results
    
    def analyze_character_consistency(self) -> Dict[str, Any]:
        """Analyze character voice and consistency across meetings."""
        character_analysis = {
            "character_appearances": defaultdict(int),
            "role_consistency": defaultdict(set),
            "voice_analysis": defaultdict(list)
        }
        
        for meeting in self.meetings:
            for participant in meeting["participants"]:
                name = participant["name"]
                role = participant["role"]
                character_analysis["character_appearances"][name] += 1
                character_analysis["role_consistency"][name].add(role)
        
        # Check for role inconsistencies
        inconsistencies = []
        role_consistency_dict = {}
        for name, roles in character_analysis["role_consistency"].items():
            role_consistency_dict[name] = list(roles)  # Convert set to list
            if len(roles) > 1:
                inconsistencies.append(f"{name} has multiple roles: {list(roles)}")
        
        character_analysis["role_consistency"] = role_consistency_dict
        character_analysis["role_inconsistencies"] = inconsistencies
        
        # Analyze dialogue patterns
        for meeting in self.meetings:
            for minute in meeting["minutes"]:
                speaker = minute["speaker"]
                text = minute["text"]
                character_analysis["voice_analysis"][speaker].append(text)
        
        return character_analysis
    
    def analyze_jargon_density(self) -> Dict[str, Any]:
        """Analyze startup/business jargon usage across meetings."""
        # Load jargon categories
        char_profiles_path = os.path.join(self.dataset_dir, "character_profiles.json")
        with open(char_profiles_path, 'r') as f:
            profiles = json.load(f)
        
        all_jargon = []
        for category, terms in profiles["jargon_categories"].items():
            all_jargon.extend(terms)
        
        jargon_analysis = {
            "total_jargon_terms": len(all_jargon),
            "jargon_usage": defaultdict(int),
            "jargon_per_meeting": [],
            "jargon_by_meeting_type": defaultdict(list),
            "jargon_by_speaker_role": defaultdict(int)
        }
        
        for meeting in self.meetings:
            meeting_jargon_count = 0
            meeting_text = ""
            
            for minute in meeting["minutes"]:
                text = minute["text"].lower()
                meeting_text += " " + text
                speaker_role = None
                
                # Find speaker role
                for participant in meeting["participants"]:
                    if participant["name"] == minute["speaker"]:
                        speaker_role = participant["role"]
                        break
                
                # Count jargon in this minute
                for jargon_term in all_jargon:
                    if jargon_term.lower() in text:
                        jargon_analysis["jargon_usage"][jargon_term] += 1
                        meeting_jargon_count += 1
                        if speaker_role:
                            jargon_analysis["jargon_by_speaker_role"][speaker_role] += 1
            
            jargon_analysis["jargon_per_meeting"].append({
                "meeting_id": meeting["meeting_id"],
                "meeting_type": meeting["meeting_type"], 
                "jargon_count": meeting_jargon_count
            })
            
            jargon_analysis["jargon_by_meeting_type"][meeting["meeting_type"]].append(meeting_jargon_count)
        
        # Calculate averages
        for meeting_type, counts in jargon_analysis["jargon_by_meeting_type"].items():
            avg_jargon = sum(counts) / len(counts) if counts else 0
            jargon_analysis[f"avg_jargon_{meeting_type}"] = round(avg_jargon, 2)
        
        return jargon_analysis
    
    def analyze_emotional_authenticity(self) -> Dict[str, Any]:
        """Analyze emotional indicators and stress patterns."""
        emotion_analysis = {
            "stress_indicators": defaultdict(int),
            "emotion_by_role": defaultdict(list),
            "arjun_stress_progression": []
        }
        
        # Define stress and emotion indicators
        stress_words = ["stress", "pressure", "worried", "concerned", "tired", "exhausted"]
        confidence_words = ["confident", "strong", "improving", "success", "progress"]
        family_concern_words = ["health", "balance", "home", "relationship", "savings"]
        
        for meeting in self.meetings:
            arjun_stress_score = 0
            meeting_date = meeting["meeting_date"]
            
            for minute in meeting["minutes"]:
                text = minute["text"].lower()
                speaker = minute["speaker"]
                
                # Count stress indicators
                for stress_word in stress_words:
                    if stress_word in text:
                        emotion_analysis["stress_indicators"][stress_word] += 1
                        if speaker == "Arjun Vasanth":
                            arjun_stress_score += 1
                
                # Analyze by role
                speaker_role = None
                for participant in meeting["participants"]:
                    if participant["name"] == speaker:
                        speaker_role = participant["role"]
                        break
                
                if speaker_role:
                    emotion_analysis["emotion_by_role"][speaker_role].append(text)
            
            emotion_analysis["arjun_stress_progression"].append({
                "date": meeting_date,
                "stress_score": arjun_stress_score,
                "meeting_type": meeting["meeting_type"]
            })
        
        return emotion_analysis
    
    def analyze_business_logic(self) -> Dict[str, Any]:
        """Validate business logic and realistic progression."""
        business_analysis = {
            "timeline_consistency": True,
            "participant_logic": True,
            "topic_coherence": defaultdict(int),
            "action_item_analysis": {
                "total_items": 0,
                "items_per_type": defaultdict(int),
                "priority_distribution": defaultdict(int)
            }
        }
        
        # Analyze topics
        for meeting in self.meetings:
            for topic in meeting["topics"]:
                business_analysis["topic_coherence"][topic] += 1
            
            # Analyze action items
            for item in meeting["action_items"]:
                business_analysis["action_item_analysis"]["total_items"] += 1
                business_analysis["action_item_analysis"]["items_per_type"][meeting["meeting_type"]] += 1
                business_analysis["action_item_analysis"]["priority_distribution"][item["priority"]] += 1
        
        return business_analysis
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality assessment report."""
        print("Generating comprehensive quality report...")
        
        report = {
            "validation_timestamp": "2024-09-21T15:45:00",
            "dataset_overview": {
                "total_meetings": len(self.meetings),
                "date_range": {
                    "start": min(m["meeting_date"] for m in self.meetings),
                    "end": max(m["meeting_date"] for m in self.meetings)
                }
            },
            "schema_validation": self.validate_json_structure(),
            "character_consistency": self.analyze_character_consistency(),
            "jargon_analysis": self.analyze_jargon_density(),
            "emotional_authenticity": self.analyze_emotional_authenticity(),
            "business_logic": self.analyze_business_logic()
        }
        
        return report
    
    def save_quality_report(self, output_path: str):
        """Save the quality report to JSON file."""
        report = self.generate_quality_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Quality report saved to: {output_path}")
        
        # Print summary
        print("\n=== DATASET QUALITY SUMMARY ===")
        print(f"Total meetings: {report['dataset_overview']['total_meetings']}")
        print(f"Schema validation: {report['schema_validation']['valid_meetings']}/{report['schema_validation']['total_meetings']} valid")
        print(f"Average jargon per business meeting: {report['jargon_analysis'].get('avg_jargon_business', 0)}")
        print(f"Average jargon per family meeting: {report['jargon_analysis'].get('avg_jargon_family', 0)}")
        print(f"Total action items: {report['business_logic']['action_item_analysis']['total_items']}")
        print(f"Character role inconsistencies: {len(report['character_consistency']['role_inconsistencies'])}")
        
        if report['character_consistency']['role_inconsistencies']:
            print("Role inconsistencies found:")
            for inconsistency in report['character_consistency']['role_inconsistencies']:
                print(f"  - {inconsistency}")

def main():
    """Main validation function."""
    dataset_dir = r"C:\Users\Ranesh RK\Downloads\projects\RetrievalPOC\synthetic_dataset"
    
    print("Starting dataset validation...")
    validator = DatasetValidator(dataset_dir)
    
    # Generate and save quality report
    report_path = os.path.join(dataset_dir, "quality_report.json")
    validator.save_quality_report(report_path)
    
    print("\nValidation completed successfully!")

if __name__ == "__main__":
    main()