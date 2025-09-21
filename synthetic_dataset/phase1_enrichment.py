"""
Phase 1: CPU-Optimized Data Enrichment Pipeline
Using Hugging Face models for sentiment analysis and entity extraction
Optimized for machines without GPU support
"""

import asyncio
import json
import torch
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging
import time
import re
from tqdm import tqdm
import numpy as np

# Import transformers with CPU optimization
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    pipeline, logging as transformers_logging
)

# Suppress transformers warnings for cleaner output
transformers_logging.set_verbosity_error()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    overall_sentiment: float  # -1.0 to 1.0
    sentiment_label: str      # NEGATIVE, NEUTRAL, POSITIVE
    confidence: float         # 0.0 to 1.0
    stress_indicators: List[str]  # detected stress phrases
    business_optimism: float  # business context sentiment
    emotional_intensity: float  # how intense the emotions are

@dataclass
class EntityExtraction:
    business_metrics: List[Dict]
    technical_terms: List[Dict]
    financial_terms: List[Dict]
    personal_entities: List[Dict]
    timeline_entities: List[Dict]

class CPUOptimizedSentimentAnalyzer:
    """
    CPU-optimized sentiment analysis using cardiffnlp/twitter-roberta-base-sentiment-latest
    """
    
    def __init__(self):
        logger.info("Initializing CPU-optimized sentiment analyzer...")
        
        # Force CPU for consistent performance
        self.device = "cpu"
        torch.set_num_threads(4)  # Optimize for CPU
        
        # Load models
        self._load_models()
        
        # Setup patterns for enhanced analysis
        self._setup_patterns()
        
        logger.info("Sentiment analyzer ready on CPU!")
    
    def _load_models(self):
        """Load sentiment analysis models optimized for CPU"""
        try:
            # Primary sentiment model - cardiffnlp/twitter-roberta-base-sentiment-latest
            self.sentiment_model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            
            logger.info(f"Loading {self.sentiment_model_name}...")
            
            # Load with CPU optimization
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                tokenizer=self.sentiment_model_name,
                device=-1,  # Force CPU
                framework="pt",
                batch_size=1,  # Process one at a time for memory efficiency
                truncation=True,
                max_length=512,
                padding=True
            )
            
            logger.info("Sentiment model loaded successfully!")
            
            # Test the model with a sample
            test_result = self.sentiment_pipeline("This is a test message.")
            logger.info(f"Model test successful: {test_result}")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise
    
    def _setup_patterns(self):
        """Setup keyword patterns for context analysis"""
        
        # Stress and pressure indicators
        self.stress_keywords = [
            "stressed", "overwhelmed", "pressure", "worried", "anxious",
            "burning out", "exhausted", "struggling", "difficult", "challenging",
            "concerned", "nervous", "tense", "frustrated", "tired", "strain",
            "burden", "overwhelming", "crisis", "panic"
        ]
        
        # Business positive indicators
        self.business_positive = [
            "growth", "success", "opportunity", "optimistic", "confident",
            "excited", "promising", "strong", "positive", "breakthrough",
            "scaling", "traction", "revenue", "profitable", "winning",
            "advantage", "competitive", "innovative", "revolutionary"
        ]
        
        # Business negative indicators
        self.business_negative = [
            "rejection", "failed", "declining", "issues", "problems",
            "concerned", "skeptical", "risky", "challenging", "burning",
            "runway", "cash flow", "competitors", "threats", "losses",
            "struggling", "setbacks", "obstacles", "barriers"
        ]
        
        # Family/personal stress indicators
        self.personal_stress = [
            "family sacrifice", "work-life", "relationship strain", "missing",
            "neglecting", "guilt", "balance", "personal cost", "marriage",
            "family time", "health", "exhaustion", "sacrifice"
        ]
    
    def analyze_speaker_sentiment(self, text: str, speaker: str, role: str) -> SentimentResult:
        """
        Analyze sentiment for individual speaker with business context
        """
        try:
            start_time = time.time()
            
            # Primary sentiment analysis
            sentiment_results = self.sentiment_pipeline(text)
            
            # Handle different output formats
            if isinstance(sentiment_results, list) and len(sentiment_results) > 0:
                primary_result = sentiment_results[0]
            else:
                primary_result = sentiment_results
            
            # Convert to standardized score
            sentiment_score = self._convert_sentiment_score(primary_result)
            
            # Detect stress indicators
            stress_indicators = self._detect_stress_patterns(text)
            
            # Analyze business context
            business_sentiment = self._analyze_business_context(text, role)
            
            # Calculate emotional intensity
            emotional_intensity = self._calculate_emotional_intensity(text, stress_indicators)
            
            processing_time = time.time() - start_time
            logger.debug(f"Processed {speaker} in {processing_time:.2f}s")
            
            return SentimentResult(
                overall_sentiment=sentiment_score,
                sentiment_label=primary_result['label'],
                confidence=primary_result['score'],
                stress_indicators=stress_indicators,
                business_optimism=business_sentiment,
                emotional_intensity=emotional_intensity
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {speaker}: {e}")
            return self._create_fallback_sentiment()
    
    def _convert_sentiment_score(self, sentiment_result: Dict) -> float:
        """Convert sentiment labels to numerical scores"""
        
        # Handle different label formats from the model
        label = sentiment_result['label'].upper()
        confidence = sentiment_result['score']
        
        # Map labels to scores
        if 'NEGATIVE' in label or 'LABEL_0' in label:
            base_score = -1.0
        elif 'POSITIVE' in label or 'LABEL_2' in label:
            base_score = 1.0
        else:  # NEUTRAL or LABEL_1
            base_score = 0.0
        
        # Adjust score based on confidence
        return base_score * confidence
    
    def _detect_stress_patterns(self, text: str) -> List[str]:
        """Detect stress-related phrases with context"""
        text_lower = text.lower()
        stress_phrases = []
        
        # Check for stress keywords
        for keyword in self.stress_keywords:
            if keyword in text_lower:
                # Find the sentence containing the keyword
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword.lower() in sentence.lower():
                        stress_phrases.append(sentence.strip())
                        break
        
        # Check for personal stress patterns
        for pattern in self.personal_stress:
            if pattern.lower() in text_lower:
                # Find context around the pattern
                idx = text_lower.find(pattern.lower())
                if idx != -1:
                    start = max(0, idx - 30)
                    end = min(len(text), idx + len(pattern) + 30)
                    context = text[start:end].strip()
                    stress_phrases.append(context)
        
        return list(set(stress_phrases))  # Remove duplicates
    
    def _analyze_business_context(self, text: str, role: str) -> float:
        """Analyze business-specific sentiment based on speaker role"""
        text_lower = text.lower()
        
        # Count positive and negative business indicators
        positive_count = sum(1 for word in self.business_positive if word in text_lower)
        negative_count = sum(1 for word in self.business_negative if word in text_lower)
        
        # Role-based multipliers
        role_adjustments = {
            'founder': 1.0,     # Balanced perspective
            'investor': 1.3,    # More critical/skeptical
            'family': 0.7,      # Less business-focused
            'mentor': 1.1,      # Slightly more analytical
            'peer': 1.0         # Balanced
        }
        
        multiplier = role_adjustments.get(role, 1.0)
        
        # Calculate business sentiment
        total_indicators = positive_count + negative_count
        if total_indicators == 0:
            return 0.0
        
        # Apply role-based weighting
        weighted_negative = negative_count * multiplier
        business_score = (positive_count - weighted_negative) / total_indicators
        
        # Normalize to -1.0 to 1.0 range
        return max(-1.0, min(1.0, business_score))
    
    def _calculate_emotional_intensity(self, text: str, stress_indicators: List[str]) -> float:
        """Calculate how emotionally intense the speech is"""
        
        # Factors that increase emotional intensity
        intensity_factors = []
        
        # Length of stress indicators
        if stress_indicators:
            intensity_factors.append(len(stress_indicators) * 0.2)
        
        # Presence of strong emotional words
        strong_emotions = [
            "extremely", "absolutely", "completely", "totally", "incredibly",
            "overwhelming", "devastating", "amazing", "terrible", "fantastic"
        ]
        
        text_lower = text.lower()
        emotion_count = sum(1 for word in strong_emotions if word in text_lower)
        intensity_factors.append(emotion_count * 0.15)
        
        # Repetition and emphasis patterns
        if "!" in text:
            intensity_factors.append(text.count("!") * 0.1)
        
        # Calculate overall intensity
        total_intensity = sum(intensity_factors)
        return min(1.0, total_intensity)  # Cap at 1.0
    
    def _create_fallback_sentiment(self) -> SentimentResult:
        """Create fallback result for errors"""
        return SentimentResult(
            overall_sentiment=0.0,
            sentiment_label="NEUTRAL",
            confidence=0.5,
            stress_indicators=[],
            business_optimism=0.0,
            emotional_intensity=0.0
        )

class BusinessEntityExtractor:
    """
    Extract business entities using regex patterns - CPU efficient
    """
    
    def __init__(self):
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup regex patterns for entity extraction"""
        
        # Monetary values (₹, INR, USD, $)
        self.money_pattern = re.compile(
            r'(?:₹|INR|USD|\$)\s*[\d,]+(?:\.\d{2})?(?:\s*(?:crore|lakh|million|billion|K|M|B))?|'
            r'[\d,]+(?:\.\d{2})?\s*(?:rupees|dollars|crores|lakhs|millions|billions)',
            re.IGNORECASE
        )
        
        # Percentages
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        
        # Business metrics and KPIs
        self.business_metrics_pattern = re.compile(
            r'\b(?:CAC|LTV|TAM|SAM|ARR|MRR|burn\s+rate|runway|churn|ROI|EBITDA|'
            r'revenue|valuation|customer\s+acquisition\s+cost|lifetime\s+value|'
            r'monthly\s+recurring\s+revenue|annual\s+recurring\s+revenue)\b',
            re.IGNORECASE
        )
        
        # Technical terms
        self.tech_pattern = re.compile(
            r'\b(?:API|ML|AI|model|algorithm|pipeline|integration|latency|accuracy|'
            r'POC|MVP|NLP|computer\s+vision|machine\s+learning|deep\s+learning|'
            r'neural\s+network|transformer|BERT|RoBERTa|GPT)\b',
            re.IGNORECASE
        )
        
        # Funding and investment terms
        self.funding_pattern = re.compile(
            r'\b(?:seed\s+round|Series\s+[ABC]|valuation|equity|due\s+diligence|'
            r'runway|investor|funding|venture\s+capital|angel\s+investor|'
            r'term\s+sheet|cap\s+table|dilution|liquidation\s+preference)\b',
            re.IGNORECASE
        )
        
        # Timeline and date expressions
        self.timeline_pattern = re.compile(
            r'\b(?:next\s+week|this\s+month|by\s+Friday|in\s+\d+\s+(?:days|weeks|months)|'
            r'within\s+\d+\s+months|Q[1-4]|quarter|fiscal\s+year|deadline|milestone)\b',
            re.IGNORECASE
        )
        
        # Personal/family terms (for context)
        self.personal_pattern = re.compile(
            r'\b(?:family|wife|husband|marriage|work-life\s+balance|personal\s+time|'
            r'relationship|health|stress|exhaustion|sacrifice|guilt)\b',
            re.IGNORECASE
        )
    
    def extract_entities(self, meeting_data: Dict) -> EntityExtraction:
        """Extract all entities from meeting data"""
        
        # Combine all speaker text
        full_text = " ".join([minute.get("text", "") for minute in meeting_data.get("minutes", [])])
        
        # Extract different types of entities
        business_metrics = self._extract_with_context(full_text, self.business_metrics_pattern, "business_metric")
        technical_terms = self._extract_with_context(full_text, self.tech_pattern, "technical_term")
        financial_terms = self._extract_with_context(full_text, self.funding_pattern, "financial_term")
        personal_entities = self._extract_with_context(full_text, self.personal_pattern, "personal_entity")
        timeline_entities = self._extract_with_context(full_text, self.timeline_pattern, "timeline_entity")
        
        # Add monetary values and percentages to business metrics
        monetary_entities = self._extract_with_context(full_text, self.money_pattern, "monetary_value")
        percentage_entities = self._extract_with_context(full_text, self.percentage_pattern, "percentage")
        
        business_metrics.extend(monetary_entities)
        business_metrics.extend(percentage_entities)
        
        return EntityExtraction(
            business_metrics=business_metrics,
            technical_terms=technical_terms,
            financial_terms=financial_terms,
            personal_entities=personal_entities,
            timeline_entities=timeline_entities
        )
    
    def _extract_with_context(self, text: str, pattern: re.Pattern, entity_type: str) -> List[Dict]:
        """Extract entities with surrounding context"""
        entities = []
        
        for match in pattern.finditer(text):
            entity_text = match.group().strip()
            start, end = match.span()
            
            # Get context (40 characters before and after)
            context_start = max(0, start - 40)
            context_end = min(len(text), end + 40)
            context = text[context_start:context_end].strip()
            
            entities.append({
                "entity": entity_text,
                "type": entity_type,
                "context": context,
                "position": [start, end],
                "confidence": 1.0  # High confidence for regex matches
            })
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity["entity"].lower(), entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities

class Phase1EnrichmentPipeline:
    """
    Main Phase 1 enrichment pipeline orchestrator
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Phase 1 Enrichment Pipeline...")
        
        # Initialize components
        self.sentiment_analyzer = CPUOptimizedSentimentAnalyzer()
        self.entity_extractor = BusinessEntityExtractor()
        
        # Track processing statistics
        self.stats = {
            "total_meetings": 0,
            "processed_meetings": 0,
            "total_speakers": 0,
            "total_processing_time": 0,
            "errors": []
        }
        
        logger.info("Pipeline initialization complete!")
    
    async def process_dataset(self, input_dir: str, output_dir: str):
        """
        Process entire enhanced dataset through enrichment pipeline
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Find all enhanced meeting files
        meeting_files = list(input_path.glob("enhanced_meeting_*.json"))
        self.stats["total_meetings"] = len(meeting_files)
        
        logger.info(f"Found {len(meeting_files)} meetings to process")
        logger.info(f"Output directory: {output_path}")
        
        # Process meetings with progress tracking
        start_time = time.time()
        
        with tqdm(total=len(meeting_files), desc="Processing meetings") as pbar:
            for meeting_file in meeting_files:
                try:
                    success = await self._process_single_meeting(meeting_file, output_path)
                    if success:
                        self.stats["processed_meetings"] += 1
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Success': f"{self.stats['processed_meetings']}/{self.stats['total_meetings']}",
                        'Errors': len(self.stats['errors'])
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to process {meeting_file.name}: {e}"
                    logger.error(error_msg)
                    self.stats["errors"].append(error_msg)
                    pbar.update(1)
        
        self.stats["total_processing_time"] = time.time() - start_time
        
        # Generate summary report
        await self._generate_summary_report(output_path)
        
        logger.info(f"Phase 1 enrichment complete!")
        logger.info(f"Successfully processed: {self.stats['processed_meetings']}/{self.stats['total_meetings']} meetings")
        logger.info(f"Total processing time: {self.stats['total_processing_time']:.2f} seconds")
        logger.info(f"Average time per meeting: {self.stats['total_processing_time']/max(1, self.stats['processed_meetings']):.2f} seconds")
    
    async def _process_single_meeting(self, meeting_file: Path, output_path: Path) -> bool:
        """Process a single meeting file"""
        try:
            # Load meeting data
            with open(meeting_file, 'r', encoding='utf-8') as f:
                meeting_data = json.load(f)
            
            meeting_id = meeting_data.get('meeting_id', meeting_file.name)
            logger.debug(f"Processing {meeting_id}")
            
            # Analyze sentiment for each speaker
            speaker_analyses = []
            
            for minute in meeting_data.get('minutes', []):
                speaker = minute.get('speaker', '')
                text = minute.get('text', '')
                timestamp = minute.get('timestamp', '')
                
                if not text.strip():  # Skip empty text
                    continue
                
                # Get speaker role
                role = self._get_speaker_role(speaker, meeting_data.get('participants', []))
                
                # Analyze sentiment
                sentiment_result = self.sentiment_analyzer.analyze_speaker_sentiment(text, speaker, role)
                
                speaker_analyses.append({
                    "timestamp": timestamp,
                    "speaker": speaker,
                    "role": role,
                    "text_length": len(text),
                    "word_count": len(text.split()),
                    "sentiment_analysis": asdict(sentiment_result)
                })
                
                self.stats["total_speakers"] += 1
            
            # Extract entities from entire meeting
            entity_extraction = self.entity_extractor.extract_entities(meeting_data)
            
            # Calculate meeting-level metrics
            meeting_metrics = self._calculate_meeting_metrics(speaker_analyses, meeting_data)
            
            # Create enriched meeting data
            enriched_data = {
                **meeting_data,  # Original meeting data
                "enrichment_metadata": {
                    "processing_timestamp": datetime.now().isoformat(),
                    "enrichment_version": "1.0_cpu_optimized",
                    "processing_time_seconds": time.time(),  # Will be updated later
                    "models_used": {
                        "sentiment_analysis": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                        "entity_extraction": "regex_based_patterns"
                    },
                    "analysis_results": {
                        "overall_meeting_sentiment": meeting_metrics["overall_sentiment"],
                        "stress_level": meeting_metrics["stress_level"],
                        "business_optimism": meeting_metrics["business_optimism"],
                        "emotional_intensity": meeting_metrics["emotional_intensity"],
                        "speaker_analyses": speaker_analyses,
                        "key_insights": meeting_metrics["key_insights"]
                    },
                    "entity_extraction": asdict(entity_extraction),
                    "meeting_statistics": {
                        "total_speakers": len(set(s["speaker"] for s in speaker_analyses)),
                        "total_exchanges": len(speaker_analyses),
                        "total_word_count": sum(s["word_count"] for s in speaker_analyses),
                        "average_sentiment_confidence": meeting_metrics["avg_confidence"],
                        "stress_indicators_count": len(meeting_metrics["all_stress_indicators"]),
                        "business_entities_count": len(entity_extraction.business_metrics),
                        "technical_terms_count": len(entity_extraction.technical_terms)
                    }
                }
            }
            
            # Save enriched data
            output_file = output_path / f"enriched_{meeting_file.name}"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"✅ Completed {meeting_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process {meeting_file.name}: {e}")
            return False
    
    def _get_speaker_role(self, speaker_name: str, participants: List[Dict]) -> str:
        """Get speaker role from participants list"""
        for participant in participants:
            if participant.get('name') == speaker_name:
                return participant.get('role', 'unknown')
        return 'unknown'
    
    def _calculate_meeting_metrics(self, speaker_analyses: List[Dict], meeting_data: Dict) -> Dict:
        """Calculate overall meeting-level metrics"""
        
        if not speaker_analyses:
            return self._create_empty_metrics()
        
        # Extract sentiment scores
        sentiment_scores = [s["sentiment_analysis"]["overall_sentiment"] for s in speaker_analyses]
        confidence_scores = [s["sentiment_analysis"]["confidence"] for s in speaker_analyses]
        business_scores = [s["sentiment_analysis"]["business_optimism"] for s in speaker_analyses]
        intensity_scores = [s["sentiment_analysis"]["emotional_intensity"] for s in speaker_analyses]
        
        # Collect all stress indicators
        all_stress_indicators = []
        for analysis in speaker_analyses:
            all_stress_indicators.extend(analysis["sentiment_analysis"]["stress_indicators"])
        
        # Determine overall stress level
        stress_level = "low"
        stress_count = len(all_stress_indicators)
        if stress_count > 3:
            stress_level = "high"
        elif stress_count > 1:
            stress_level = "medium"
        
        # Generate key insights
        key_insights = self._generate_meeting_insights(speaker_analyses, meeting_data, all_stress_indicators)
        
        return {
            "overall_sentiment": float(np.mean(sentiment_scores)),
            "business_optimism": float(np.mean(business_scores)),
            "emotional_intensity": float(np.mean(intensity_scores)),
            "avg_confidence": float(np.mean(confidence_scores)),
            "stress_level": stress_level,
            "all_stress_indicators": all_stress_indicators,
            "key_insights": key_insights
        }
    
    def _generate_meeting_insights(self, speaker_analyses: List[Dict], meeting_data: Dict, stress_indicators: List[str]) -> List[str]:
        """Generate key insights about the meeting"""
        insights = []
        
        # Sentiment-based insights
        sentiment_scores = [s["sentiment_analysis"]["overall_sentiment"] for s in speaker_analyses]
        avg_sentiment = np.mean(sentiment_scores)
        
        if avg_sentiment > 0.3:
            insights.append("Overall positive sentiment in the meeting")
        elif avg_sentiment < -0.3:
            insights.append("Overall negative sentiment detected")
        else:
            insights.append("Neutral to mixed sentiment throughout")
        
        # Stress-based insights
        if len(stress_indicators) > 2:
            insights.append("High stress levels detected in conversation")
        elif len(stress_indicators) > 0:
            insights.append("Some stress indicators present")
        
        # Role-based insights
        roles = [s["role"] for s in speaker_analyses]
        if "investor" in roles and "founder" in roles:
            # Find investor sentiment
            investor_sentiments = [s["sentiment_analysis"]["business_optimism"] 
                                 for s in speaker_analyses if s["role"] == "investor"]
            if investor_sentiments and np.mean(investor_sentiments) < 0:
                insights.append("Investor expressing concerns or skepticism")
            elif investor_sentiments and np.mean(investor_sentiments) > 0.3:
                insights.append("Positive investor engagement detected")
        
        # Meeting type insights
        meeting_type = meeting_data.get('meeting_type', '')
        if meeting_type == 'family' and stress_indicators:
            insights.append("Family discussion involving work-related stress")
        elif meeting_type == 'business' and stress_indicators:
            insights.append("Business pressure affecting emotional state")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _create_empty_metrics(self) -> Dict:
        """Create empty metrics for meetings with no valid analyses"""
        return {
            "overall_sentiment": 0.0,
            "business_optimism": 0.0,
            "emotional_intensity": 0.0,
            "avg_confidence": 0.0,
            "stress_level": "unknown",
            "all_stress_indicators": [],
            "key_insights": ["No valid speaker analyses found"]
        }
    
    async def _generate_summary_report(self, output_path: Path):
        """Generate comprehensive summary report"""
        
        summary_data = {
            "phase1_enrichment_summary": {
                "processing_completed": datetime.now().isoformat(),
                "statistics": {
                    "total_meetings_found": self.stats["total_meetings"],
                    "meetings_successfully_processed": self.stats["processed_meetings"],
                    "total_speakers_analyzed": self.stats["total_speakers"],
                    "success_rate_percentage": round((self.stats["processed_meetings"] / max(1, self.stats["total_meetings"])) * 100, 2),
                    "total_processing_time_seconds": round(self.stats["total_processing_time"], 2),
                    "average_time_per_meeting_seconds": round(self.stats["total_processing_time"] / max(1, self.stats["processed_meetings"]), 2)
                },
                "models_used": {
                    "sentiment_analysis": {
                        "model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                        "framework": "transformers/pytorch",
                        "device": "cpu",
                        "optimization": "cpu_optimized_pipeline"
                    },
                    "entity_extraction": {
                        "method": "regex_pattern_matching",
                        "patterns": ["business_metrics", "technical_terms", "financial_terms", "personal_entities", "timeline_entities"]
                    }
                },
                "enrichment_features": [
                    "Speaker-level sentiment analysis",
                    "Business context sentiment scoring",
                    "Stress indicator detection",
                    "Emotional intensity measurement",
                    "Business entity extraction",
                    "Technical term identification",
                    "Financial term detection",
                    "Personal entity recognition",
                    "Timeline entity extraction",
                    "Meeting-level aggregated metrics",
                    "Key insight generation"
                ],
                "errors": self.stats["errors"]
            }
        }
        
        # Save summary report
        summary_file = output_path / "phase1_enrichment_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Summary report saved to: {summary_file}")

# Main execution function
async def main():
    """Main execution function for Phase 1 enrichment"""
    
    print("Starting Phase 1: Data Enrichment Pipeline")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Device: CPU (Optimized)")
    print(f"Model: cardiffnlp/twitter-roberta-base-sentiment-latest")
    print("=" * 50)
    
    # Configuration
    INPUT_DIR = "enhanced_meetings"
    OUTPUT_DIR = "enriched_meetings"
    
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    try:
        # Initialize and run pipeline
        pipeline = Phase1EnrichmentPipeline()
        await pipeline.process_dataset(INPUT_DIR, OUTPUT_DIR)
        
        print("=" * 50)
        print("Phase 1 Enrichment Complete!")
        print(f"Check the summary report in {OUTPUT_DIR}/phase1_enrichment_summary.json")
        print("Ready to proceed to Phase 2: Vector Embedding & Storage")
        
    except Exception as e:
        print(f"Error during enrichment: {e}")
        logger.error(f"Phase 1 enrichment failed: {e}")
        raise

if __name__ == "__main__":
    # Run the enrichment pipeline
    asyncio.run(main())