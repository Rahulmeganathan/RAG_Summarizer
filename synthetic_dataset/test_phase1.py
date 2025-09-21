#!/usr/bin/env python3
"""
Test Phase 1 enrichment on a single meeting file
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from phase1_enrichment import Phase1EnrichmentPipeline

async def test_single_meeting():
    """Test enrichment on enhanced_meeting_052.json"""
    
    print("Testing Phase 1 Enrichment on Single Meeting")
    print("=" * 50)
    
    # Test with meeting 052 (the one you have open)
    test_meeting = Path("enhanced_meetings/enhanced_meeting_052.json")
    
    if not test_meeting.exists():
        print(f"Test meeting not found: {test_meeting}")
        return False
    
    # Create test output directory
    test_output = Path("test_enrichment")
    test_output.mkdir(exist_ok=True)
    
    print(f"Input: {test_meeting}")
    print(f"Output: {test_output}")
    
    try:
        # Initialize pipeline
        print("\nInitializing pipeline...")
        pipeline = Phase1EnrichmentPipeline()
        
        # Process single meeting
        print("Processing meeting...")
        start_time = time.time()
        
        success = await pipeline._process_single_meeting(test_meeting, test_output)
        
        processing_time = time.time() - start_time
        
        if success:
            print(f"Processing completed in {processing_time:.2f} seconds")
            
            # Check output
            output_file = test_output / f"enriched_{test_meeting.name}"
            if output_file.exists():
                print(f"Output file created: {output_file}")
                
                # Load and show sample of enriched data
                with open(output_file, 'r', encoding='utf-8') as f:
                    enriched_data = json.load(f)
                
                print("\nSample Enrichment Results:")
                print("-" * 30)
                
                # Show meeting-level metrics
                if 'enrichment_metadata' in enriched_data:
                    metadata = enriched_data['enrichment_metadata']
                    
                    if 'analysis_results' in metadata:
                        analysis = metadata['analysis_results']
                        print(f"Overall Sentiment: {analysis.get('overall_meeting_sentiment', 'N/A'):.3f}")
                        print(f"Stress Level: {analysis.get('stress_level', 'N/A')}")
                        print(f"Business Optimism: {analysis.get('business_optimism', 'N/A'):.3f}")
                        print(f"Emotional Intensity: {analysis.get('emotional_intensity', 'N/A'):.3f}")
                    
                    if 'meeting_statistics' in metadata:
                        stats = metadata['meeting_statistics']
                        print(f"Total Speakers: {stats.get('total_speakers', 'N/A')}")
                        print(f"Total Exchanges: {stats.get('total_exchanges', 'N/A')}")
                        print(f"Word Count: {stats.get('total_word_count', 'N/A')}")
                        print(f"Business Entities: {stats.get('business_entities_count', 'N/A')}")
                        print(f"Technical Terms: {stats.get('technical_terms_count', 'N/A')}")
                
                # Show sample speaker analysis
                if 'enrichment_metadata' in enriched_data and 'analysis_results' in enriched_data['enrichment_metadata']:
                    speaker_analyses = enriched_data['enrichment_metadata']['analysis_results'].get('speaker_analyses', [])
                    
                    if speaker_analyses:
                        print(f"\nSample Speaker Analysis (First Speaker):")
                        print("-" * 30)
                        first_speaker = speaker_analyses[0]
                        sentiment = first_speaker.get('sentiment_analysis', {})
                        
                        print(f"Speaker: {first_speaker.get('speaker', 'N/A')}")
                        print(f"Role: {first_speaker.get('role', 'N/A')}")
                        print(f"Sentiment: {sentiment.get('overall_sentiment', 'N/A'):.3f}")
                        print(f"Confidence: {sentiment.get('confidence', 'N/A'):.3f}")
                        print(f"Business Optimism: {sentiment.get('business_optimism', 'N/A'):.3f}")
                        
                        stress_indicators = sentiment.get('stress_indicators', [])
                        if stress_indicators:
                            print(f"Stress Indicators: {len(stress_indicators)} found")
                            for i, indicator in enumerate(stress_indicators[:2]):  # Show first 2
                                print(f"  {i+1}. {indicator[:60]}...")
                        else:
                            print("Stress Indicators: None detected")
                
                print("\nTest completed successfully!")
                return True
            else:
                print(f"Output file not created: {output_file}")
                return False
        else:
            print(f"Processing failed")
            return False
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_single_meeting()
    
    if success:
        print("\nPhase 1 test passed! Ready for full dataset processing.")
        print("Run: python run_phase1.py to process all meetings")
    else:
        print("\nPhase 1 test failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())