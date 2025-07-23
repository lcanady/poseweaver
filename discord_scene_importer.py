#!/usr/bin/env python3
"""
Discord Scene Importer

This script extracts poses from a Discord chat dump and imports them 
into the scene memory system. It converts Discord format to Pose model entries.
"""

import argparse
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

# Import the Discord Pose Extractor
from discord_pose_extractor import DiscordPoseExtractor

# Import the scene models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.models.scene_memory import SceneMemory, Pose, PoseType


class DiscordSceneImporter:
    """Import poses from Discord into scene memory system."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the importer."""
        self.extractor = DiscordPoseExtractor()
        self.logger = logging.getLogger(__name__)
        
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def import_discord_to_scene(
        self, 
        discord_content: str, 
        scene_id: str,
        is_ooc: bool = False
    ) -> List[Pose]:
        """
        Import Discord content into a scene.
        
        Args:
            discord_content: The Discord chat log content
            scene_id: ID of the scene to import into
            default_pose_type: Default pose type for imported poses
            is_ooc: Whether poses should be marked as OOC (out of character)
            
        Returns:
            List of created Pose objects
        """
        # Check if scene exists
        scene = SceneMemory.find_by_id(scene_id)
        if not scene:
            self.logger.error(f"Scene with ID {scene_id} not found")
            return []
            
        # Extract poses from Discord
        discord_poses = self.extractor.extract_poses(discord_content)
        discord_poses = self.extractor.clean_pose_content(discord_poses)
        
        self.logger.info(f"Extracted {len(discord_poses)} poses from Discord content")
        
        # Convert and save poses
        created_poses = []
        for discord_pose in discord_poses:
            # Convert Discord timestamp to datetime
            try:
                # Parse timestamp like "7/21/24, 3:46 PM"
                ts_string = discord_pose['timestamp']
                # Convert to datetime format
                dt = datetime.strptime(ts_string, "%m/%d/%y, %I:%M %p")
            except Exception as e:
                self.logger.warning(f"Could not parse timestamp: {discord_pose['timestamp']}, using current time")
                dt = datetime.utcnow()
            
            # Determine the pose type based on content heuristics
            pose_type = self._determine_pose_type(discord_pose['content'])
            
            # Create pose
            pose = Pose(
                scene_id=scene_id,
                character_name=discord_pose['poser'],
                content=discord_pose['content'],
                pose_type=pose_type,
                timestamp=dt,
                is_ooc=is_ooc,
                word_count=len(discord_pose['content'].split())
            )
            
            # Save the pose to database
            pose.save()
            created_poses.append(pose)
            
            self.logger.debug(f"Created pose for {pose.character_name} of type {pose.pose_type}")
        
        # Update scene metadata
        if created_poses:
            scene.pose_count += len(created_poses)
            scene.update_activity()
            scene.save()
            self.logger.info(f"Updated scene {scene_id} with {len(created_poses)} new poses")
        
        return created_poses
    
    def _determine_pose_type(self, content: str) -> PoseType:
        """
        Determine pose type based on content heuristics.
        
        Args:
            content: Pose content text
            
        Returns:
            PoseType enum value
        """
        # Count quotation marks to detect dialogue
        quote_count = content.count('"')
        
        # Check for first-person narrative 
        first_person = any(pronoun in content.lower() for pronoun in ["i ", "i'm", "i'd", "i'll", "i've"])
        
        # Look for dialogue indicators (quotes and dialogue verbs)
        has_dialogue = quote_count >= 2 or any(verb in content.lower() for verb in [" says", " said", " asks", " exclaims"])
        
        # Check for action descriptions (asterisks, physical verbs, movement indicators)
        action_verbs = [" moves", " walks", " runs", " grabs", " takes", " holds", " reaches"]
        action_indicators = ["*", "-", "_", "!", " she ", " he ", " they "]
        has_action = any(indicator in content for indicator in action_indicators) or any(verb in content.lower() for verb in action_verbs)
        
        # Check for emotional or internal thought indicators
        internal_indicators = [" feels", " thinks", " remembers", " wonders", "thought", "feel", "desire"]
        has_internal = any(indicator in content.lower() for indicator in internal_indicators)
        
        # Sophisticated detection logic with priorities
        if has_dialogue and has_action and has_internal:
            return PoseType.MIXED
        elif has_dialogue and has_action:
            return PoseType.MIXED
        elif has_dialogue:
            return PoseType.DIALOGUE
        elif has_internal and first_person:
            return PoseType.INTERNAL
        elif has_action:
            return PoseType.ACTION
        else:
            return PoseType.NARRATIVE
    
    def import_from_file(
        self, 
        discord_file: str, 
        scene_id: str,
        is_ooc: bool = False
    ) -> List[Pose]:
        """
        Import Discord content from a file into a scene.
        
        Args:
            discord_file: Path to Discord chat log file
            scene_id: ID of the scene to import into
            default_pose_type: Default pose type for imported poses
            is_ooc: Whether poses should be marked as OOC (out of character)
            
        Returns:
            List of created Pose objects
        """
        try:
            with open(discord_file, 'r') as f:
                content = f.read()
            
            return self.import_discord_to_scene(
                content, 
                scene_id, 
                is_ooc
            )
        except Exception as e:
            self.logger.error(f"Error importing from file: {e}")
            return []


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Import Discord chat into a scene.')
    parser.add_argument('discord_file', help='Path to Discord chat dump file')
    parser.add_argument('scene_id', help='ID of the scene to import into')
    parser.add_argument('--ooc', action='store_true', help='Mark poses as out-of-character')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    importer = DiscordSceneImporter(verbose=args.verbose)
    
    poses = importer.import_from_file(
        args.discord_file,
        args.scene_id,
        args.ooc
    )
    
    print(f"Imported {len(poses)} poses into scene {args.scene_id}")


if __name__ == "__main__":
    main()
