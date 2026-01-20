import 'dotenv/config';
import { poseService } from './lib/services/pose-service';
import { contextService } from './lib/services/context-service';
import { characterService } from './lib/services/character-service';
import { sceneService } from './lib/services/scene-service';
import { summaryService } from './lib/services/summary-service';

console.log('Services imported successfully.');

if (poseService && contextService && characterService && sceneService && summaryService) {
    console.log('All Service instances created successfully.');
}
