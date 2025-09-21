#!/usr/bin/env python3
"""
Phase 1 Execution Script
Run this script to perform data enrichment on your enhanced meetings dataset
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'torch', 'transformers', 'numpy', 'tqdm', 'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package}")
        except ImportError:
            print(f"{package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements_phase1.txt")
        return False
    
    print("All dependencies satisfied!")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    try:
        # Install from requirements file
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements_phase1.txt"
        ])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def validate_input_directory():
    """Validate that input directory exists and has meetings"""
    input_dir = Path("enhanced_meetings")
    
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        print("Make sure you're running this from the synthetic_dataset directory")
        return False
    
    meeting_files = list(input_dir.glob("enhanced_meeting_*.json"))
    
    if not meeting_files:
        print(f"No enhanced meeting files found in {input_dir}")
        return False
    
    print(f"Found {len(meeting_files)} meeting files to process")
    return True

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = Path("enriched_meetings")
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory ready: {output_dir}")

async def run_enrichment():
    """Run the main enrichment process"""
    print("\n" + "="*50)
    print("Starting Phase 1 Data Enrichment")
    print("="*50)
    
    try:
        # Import and run the enrichment pipeline
        from phase1_enrichment import main as enrichment_main
        await enrichment_main()
        
        print("\n" + "="*50)
        print("Phase 1 Enrichment Completed Successfully!")
        print("="*50)
        print("Check the enriched_meetings/ directory for results")
        print("Review the summary report: enriched_meetings/phase1_enrichment_summary.json")
        
        return True
        
    except Exception as e:
        print(f"\nEnrichment failed: {e}")
        return False

def main():
    """Main execution function"""
    print("Phase 1 Data Enrichment Setup & Execution")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        install_choice = input("\nInstall missing dependencies? (y/N): ").lower().strip()
        if install_choice in ['y', 'yes']:
            if not install_dependencies():
                print("Setup failed. Please install dependencies manually.")
                return
        else:
            print("Cannot proceed without required dependencies.")
            return
    
    # Step 2: Validate input
    if not validate_input_directory():
        print("Setup failed. Please check input directory.")
        return
    
    # Step 3: Setup output
    setup_output_directory()
    
    # Step 4: Run enrichment
    print("\nReady to start enrichment!")
    start_choice = input("▶Start Phase 1 enrichment now? (Y/n): ").lower().strip()
    
    if start_choice in ['', 'y', 'yes']:
        try:
            asyncio.run(run_enrichment())
        except KeyboardInterrupt:
            print("\nEnrichment stopped by user")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
    else:
        print("Enrichment postponed. Run this script again when ready.")

if __name__ == "__main__":
    main()