#!/usr/bin/env python3
"""
Discord Pose Extractor

This script extracts poses and posers from a Discord chat dump.
It handles multi-paragraph poses and outputs structured data.
"""

import re
import json
import sys
import argparse
from typing import List, Dict, Tuple


class DiscordPoseExtractor:
    """Extract poses and posers from Discord chat logs."""

    def __init__(self):
        # Pattern to match Discord username and timestamp
        # Example: "FaeWitch — 7/21/24, 3:46 PM"
        self.user_pattern = re.compile(r'^([^—]+)\s+—\s+(\d+/\d+/\d+,\s+\d+:\d+\s+[AP]M)')
        
    def extract_poses(self, content: str) -> List[Dict]:
        """
        Extract poses and posers from Discord content.
        
        Args:
            content: String containing Discord chat log
            
        Returns:
            List of dicts containing poser name, timestamp, and pose content
        """
        lines = content.split('\n')
        poses = []
        current_pose = None
        
        for line in lines:
            # Check if line starts with a username and timestamp
            match = self.user_pattern.match(line)
            
            if match:
                # If we have a previous pose stored, add it to results
                if current_pose:
                    poses.append(current_pose)
                
                # Start a new pose
                username = match.group(1).strip()
                timestamp = match.group(2).strip()
                
                # Get the content part (everything after the timestamp)
                pose_start_idx = line.find(timestamp) + len(timestamp)
                pose_content = line[pose_start_idx:].strip()
                
                # Remove any quotes at the beginning
                if pose_content.startswith('"'):
                    pose_content = pose_content[1:]
                
                current_pose = {
                    'poser': username,
                    'timestamp': timestamp,
                    'content': pose_content
                }
            elif current_pose:
                # Continue previous pose (multi-paragraph)
                current_pose['content'] += '\n\n' + line.strip()
        
        # Add the last pose
        if current_pose:
            poses.append(current_pose)
            
        return poses
    
    def clean_pose_content(self, poses: List[Dict]) -> List[Dict]:
        """Clean up pose content by handling formatting and quotes."""
        for pose in poses:
            # Clean up the content
            content = pose['content']
            
            # Trim leading/trailing whitespace
            content = content.strip()
            
            # Remove any unnecessary quotes
            if content.endswith('"') and '"' not in content[:-1]:
                content = content[:-1]
                
            pose['content'] = content
            
        return poses
        
    def save_json(self, poses: List[Dict], output_file: str):
        """Save extracted poses to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(poses, f, indent=2)
            
    def save_text(self, poses: List[Dict], output_file: str):
        """Save extracted poses to a formatted text file."""
        with open(output_file, 'w') as f:
            for pose in poses:
                f.write(f"Poser: {pose['poser']}\n")
                f.write(f"Time: {pose['timestamp']}\n")
                f.write(f"Content:\n{pose['content']}\n\n")
                f.write("-" * 50 + "\n\n")
                
    def process_file(self, input_file: str, output_file: str, format: str = 'json'):
        """Process a Discord dump file and save extracted poses."""
        try:
            with open(input_file, 'r') as f:
                content = f.read()
                
            poses = self.extract_poses(content)
            poses = self.clean_pose_content(poses)
            
            if format.lower() == 'json':
                self.save_json(poses, output_file)
            else:
                self.save_text(poses, output_file)
                
            return len(poses)
        except Exception as e:
            print(f"Error processing file: {e}")
            return 0


def main():
    parser = argparse.ArgumentParser(description='Extract poses and posers from Discord chat dumps.')
    parser.add_argument('input_file', help='Path to Discord chat dump file')
    parser.add_argument('-o', '--output', default='poses.json', help='Output file path')
    parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                       help='Output format (json or text)')
    
    args = parser.parse_args()
    
    extractor = DiscordPoseExtractor()
    pose_count = extractor.process_file(args.input_file, args.output, args.format)
    
    print(f"Extracted {pose_count} poses and saved to {args.output}")


if __name__ == "__main__":
    main()
