import { ParsedPose, ParsedScene, PoseType } from '@/lib/types/mush-parser';

export class MushParserService {
  private patterns: Record<string, RegExp>;

  constructor() {
    this.patterns = {
      // Discord format: "Username — Date, Time"
      discord_header: /^([A-Za-z0-9_\-']+)\s+[—\u2014]\s+(\d{1,2}\/\d{1,2}\/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[AP]M)/i,
      
      // Character name separator: "======> Name <======"
      name_separator: /^=+>\s*(.+?)\s*<=+$/,

      // Standard pose: "CharacterName does something"
      pose: /^([A-Za-z][A-Za-z0-9_\-']*)\s+(.+)$/,

      // Say pattern: 'CharacterName says, "dialogue"'
      say: /^([A-Za-z][A-Za-z0-9_\-']*)\s+says?,?\s*["'](.+?)["']\.?$/,

      // OOC pattern: '<OOC> CharacterName says, "comment"'
      ooc_say: /^<OOC>\s*([A-Za-z][A-Za-z0-9_\-']*)\s+says?,?\s*["'](.+?)["']\.?$/,

      // OOC pose: "<OOC> CharacterName does something"
      ooc_pose: /^<OOC>\s*([A-Za-z][A-Za-z0-9_\-']*)\s+(.+)$/,

      // Room description: "---- Room Name ----"
      room_header: /^-+\s*(.+?)\s*-+$/,

      // Contents/Who list: "Contents:" or "Players:"
      contents_header: /^(Contents|Players?):\s*$/,

      // Character list line
      character_list: /^([A-Za-z][A-Za-z0-9_\-']*(?:\s+[A-Za-z][A-Za-z0-9_\-']*)*)\s*$/,

      // Exits: "<N> North" or "[N] North"
      exits: /^[<\[]([A-Za-z0-9]+)[>\]]\s*(.+)$/,

      // Timestamp patterns (various formats)
      timestamp: /^\[?(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]?\s*(.*)$/i,

      // You say/pose patterns
      you_say: /^You\s+say,?\s*["'](.+?)["']\.?$/,
      you_pose: /^You\s+(.+)$/,
    };
  }

  public parseMushOutput(output: string, yourCharacterHint?: string | null): ParsedScene {
    const lines = output.trim().split('\n');
    const poses: ParsedPose[] = [];
    let roomDescription: string | null = null;
    const charactersPresent = new Set<string>();
    let yourCharacter = yourCharacterHint;

    // State tracking
    let inRoomDesc = false;
    let inContents = false;
    const roomDescLines: string[] = [];
    let currentCharacter: string | null = null;
    let currentPoseLines: string[] = [];
    let currentTimestamp: string | null = null;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) {
            // Empty lines can be paragraph breaks in poses
            if (currentCharacter && currentPoseLines.length > 0) {
                currentPoseLines.push('');
            }
            continue;
        }

        // Check for Discord format
        const discordMatch = line.match(this.patterns.discord_header);
        if (discordMatch) {
            // Save previous pose
            if (currentCharacter && currentPoseLines.length > 0) {
                this.finalizePose(poses, charactersPresent, currentCharacter, currentPoseLines, currentTimestamp);
            }

            // Start new character section
            const discordUsername = discordMatch[1].trim();
            currentCharacter = discordUsername;
            currentTimestamp = `${discordMatch[2]} ${discordMatch[3]}`;
            currentPoseLines = [];
            continue;
        }

        // Check for character name separator
        const nameMatch = line.match(this.patterns.name_separator);
        if (nameMatch) {
            if (currentCharacter && currentPoseLines.length > 0) {
                 this.finalizePose(poses, charactersPresent, currentCharacter, currentPoseLines, currentTimestamp);
            }
            currentCharacter = nameMatch[1].trim();
            currentPoseLines = [];
            currentTimestamp = null; // Reset timestamp for new separator section
            continue;
        }

        // Check for timestamp
        const timestampMatch = line.match(this.patterns.timestamp);
        let timestamp = currentTimestamp; 
        if (timestampMatch) {
            // If line is ONLY timestamp or starts with it
            // The regex captures [Time] Rest of Line
            const extractedTime = timestampMatch[1];
            const restOfLine = timestampMatch[2].trim();
            
            // If we are INSIDE a discord block, we might update timestamp or just treat it as text?
            // MUSH timestamps usually prefix every line or start a line.
            // If we found a timestamp, update the 'line' to be the rest
            timestamp = extractedTime;
            line = restOfLine;
            if (!line) continue;
        }

        // If currently capturing a multi-line pose
        if (currentCharacter) {
            currentPoseLines.push(line);
            continue;
        }

        // Legacy/Standard MUSH Parsing
        const roomMatch = line.match(this.patterns.room_header);
        if (roomMatch) {
            inRoomDesc = true;
            inContents = false;
            roomDescLines.push(roomMatch[1]);
            continue;
        }

        const contentsMatch = line.match(this.patterns.contents_header);
        if (contentsMatch) {
            inRoomDesc = false;
            inContents = true;
            continue;
        }

        const exitMatch = line.match(this.patterns.exits);
        if (exitMatch) {
            inRoomDesc = false;
            inContents = false;
            continue;
        }

        if (inRoomDesc) {
            roomDescLines.push(line);
            continue;
        }

        if (inContents) {
            const charMatch = line.match(this.patterns.character_list);
            if (charMatch) {
                const chars = charMatch[1].split(/\s+/).filter(n => n.trim());
                chars.forEach(c => charactersPresent.add(c));
                continue;
            }
            // If it doesn't match a character list, we assume the Contents section is done
            inContents = false;
        }

        // Parse individual pose lines
        const parsedPose = this.parsePoseLine(line, timestamp);
        if (parsedPose) {
            poses.push(parsedPose);
            if (parsedPose.character_name && parsedPose.character_name.trim()) {
                charactersPresent.add(parsedPose.character_name.trim());
            }

            if (!yourCharacter && this.isLikelyYourCharacter(line)) {
                yourCharacter = 'You';
            }
        }
    }

    // Finalize last pose
    if (currentCharacter && currentPoseLines.length > 0) {
        this.finalizePose(poses, charactersPresent, currentCharacter, currentPoseLines, currentTimestamp);
    }

    if (roomDescLines.length > 0) {
        roomDescription = roomDescLines.join('\n');
    }

    if (!yourCharacter) {
        yourCharacter = this.inferYourCharacter(poses, Array.from(charactersPresent));
    }

    // Fallback if hint provided but no poses found
    if (yourCharacterHint && output.trim() && poses.length === 0) {
         const singlePose: ParsedPose = {
            character_name: yourCharacterHint,
            content: output.trim(),
            pose_type: this.determinePoseType(output.trim()),
            is_ooc: false
         };
         poses.push(singlePose);
         charactersPresent.add(yourCharacterHint);
         yourCharacter = yourCharacterHint;
    }

    return {
        poses: poses,
        room_description: roomDescription,
        characters_present: charactersPresent.size > 0 ? Array.from(charactersPresent).sort() : null,
        your_character: yourCharacter || null
    };
  }

  private finalizePose(poses: ParsedPose[], charactersPresent: Set<string>, currentCharacter: string, lines: string[], timestamp: string | null) {
      const poseText = lines.join('\n').trim();
      if (!poseText) return;

      let actualName = currentCharacter;
      // Try extracting name from content
      const extractedName = this.extractCharacterNameFromContent(poseText);
      if (extractedName) {
          actualName = extractedName;
      }

      let finalContent = poseText;
      // Strip name from content if it starts with it (to match MUSH parser behavior)
      if (actualName && poseText.startsWith(actualName)) {
          // Check if there's text after the name
          const restOfText = poseText.substring(actualName.length);
          // If it starts with space or punctuation that implies separation
          if (restOfText.startsWith(' ') || restOfText.startsWith("'") || restOfText.startsWith(',')) {
               finalContent = restOfText.trim();
          }
      }

      const pose: ParsedPose = {
          character_name: actualName,
          content: finalContent,
          pose_type: this.determinePoseType(finalContent),
          is_ooc: false,
          timestamp: timestamp
      };

      poses.push(pose);
      if (actualName && actualName.trim()) {
          charactersPresent.add(actualName.trim());
      }
  }

  private parsePoseLine(line: string, timestamp: string | null = null): ParsedPose | null {
      // You say
      const youSayMatch = line.match(this.patterns.you_say);
      if (youSayMatch) {
          return {
              character_name: 'You',
              content: `says, "${youSayMatch[1]}"`,
              pose_type: PoseType.DIALOGUE,
              is_ooc: false,
              timestamp
          };
      }

      // You pose
      const youPoseMatch = line.match(this.patterns.you_pose);
      if (youPoseMatch) {
          const content = youPoseMatch[1];
          return {
              character_name: 'You',
              content,
              pose_type: this.determinePoseType(content),
              is_ooc: false,
              timestamp
          }
      }

      // OOC Say
      const oocSayMatch = line.match(this.patterns.ooc_say);
      if (oocSayMatch) {
          return {
              character_name: oocSayMatch[1],
              content: `says, "${oocSayMatch[2]}"`,
              pose_type: PoseType.DIALOGUE,
              is_ooc: true,
              timestamp
          };
      }

      // OOC Pose
      const oocPoseMatch = line.match(this.patterns.ooc_pose);
      if (oocPoseMatch) {
          return {
               character_name: oocPoseMatch[1],
               content: oocPoseMatch[2],
               pose_type: this.determinePoseType(oocPoseMatch[2]),
               is_ooc: true,
               timestamp
          };
      }

      // Regular Say
      const sayMatch = line.match(this.patterns.say);
      if (sayMatch) {
          return {
              character_name: sayMatch[1],
              content: `says, "${sayMatch[2]}"`,
              pose_type: PoseType.DIALOGUE,
              is_ooc: false,
              timestamp
          };
      }

      // Regular Pose
      const poseMatch = line.match(this.patterns.pose);
      if (poseMatch) {
           const characterName = poseMatch[1];
           const content = poseMatch[2];

           if (this.isSystemMessage(characterName, content)) {
               return null;
           }

           return {
               character_name: characterName,
               content,
               pose_type: this.determinePoseType(content),
               is_ooc: false,
               timestamp
           };
      }

      return null;
  }

  private isSystemMessage(characterName: string, content: string): boolean {
      const systemIndicators = [
        'connects', 'disconnects', 'has connected', 'has disconnected',
        'goes home', 'has left', 'arrives', 'enters', 'exits',
        'is now known as', 'changes', 'sets'
      ];
      const lowerContent = content.toLowerCase();
      return systemIndicators.some(ind => lowerContent.includes(ind));
  }

  private isLikelyYourCharacter(line: string): boolean {
      return line.startsWith('You ') || line.toLowerCase().includes('you say');
  }

  private inferYourCharacter(poses: ParsedPose[], charactersPresent: string[]): string | null {
      const youPoses = poses.filter(p => p.character_name === 'You');
      if (youPoses.length > 0 && charactersPresent.length > 0) {
          return charactersPresent[0];
      }
      return null;
  }

  private determinePoseType(content: string): PoseType {
      const lower = content.toLowerCase();
      
      const dialogueWords = ['says', 'asks', 'whispers', 'shouts', 'calls', 'replies'];
      if (dialogueWords.some(w => lower.includes(w))) return PoseType.DIALOGUE;

      const internalWords = ['thinks', 'wonders', 'realizes', 'remembers', 'considers'];
      if (internalWords.some(w => lower.includes(w))) return PoseType.INTERNAL;

      if (content.includes('"') || content.includes("'")) return PoseType.MIXED;

      return PoseType.ACTION;
  }

  private extractCharacterNameFromContent(content: string): string | null {
      if (!content) return null;
      
      // Pattern 1: Starters
      // Matches "Name is/was/has..."
      const firstSentenceMatch = content.match(/^([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:is|was|has|had|seems|looks|moves|walks|sits|stands|takes)/);
      if (firstSentenceMatch) return firstSentenceMatch[1];

      // Pattern 2: Possessive
      // Matches "Name's eyes..."
      // (?:^|\.\s+) looks for start of string or start of sentence
      const possessiveMatch = content.match(/(?:^|\.\s+)([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?'s\s+(?:eyes|face|body|hand|hair|voice|gaze)/);
      if (possessiveMatch) return possessiveMatch[1];

      // Pattern 3: Action
      const actionMatch = content.match(/(?:^|\.\s+)([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\s+(?:takes|moves|walks|runs|jumps|looks|glances|stares|smiles|frowns|nods|shakes)/);
      if (actionMatch) return actionMatch[1];

      return null;
  }

  public buildSceneContextFromParsed(parsedScene: ParsedScene, maxPoses: number = 20): {
      setting: string;
      activeCharacters: string[];
      rawContext: string;
      poses: any[]; // refined structure
  } {
      const contextParts: string[] = [];
      
      if (parsedScene.room_description) {
          contextParts.push(`Location: ${parsedScene.room_description}`);
      }

      const activeChars = parsedScene.characters_present || [];
      if (activeChars.length > 0) {
          const uniqueChars = Array.from(new Set(activeChars)).sort();
          contextParts.push(`Characters present (${uniqueChars.length}): ${uniqueChars.join(', ')}`);
      }

      const structuredPoses: any[] = [];

      if (parsedScene.poses && parsedScene.poses.length > 0) {
          // Sort poses by timestamp string (lexicographical sort usually works for standard formats, but ideally parse time)
          // For now, simple sort if timestamp exists
          const sortedPoses = [...parsedScene.poses].sort((a, b) => {
              if (!a.timestamp) return 1;
              if (!b.timestamp) return -1;
               return a.timestamp.localeCompare(b.timestamp);
          });

          // Unique poses
          const uniquePoseMap = new Map<string, ParsedPose>();
          sortedPoses.forEach(p => {
              const id = `${p.character_name}:${p.content.substring(0, 50)}`;
              if (!uniquePoseMap.has(id)) {
                  uniquePoseMap.set(id, p);
              }
          });
          
          contextParts.push(`\nRecent scene activity (${uniquePoseMap.size} poses):`);

          // Recent poses
          const recentPoses = Array.from(uniquePoseMap.values()).slice(-maxPoses);

          recentPoses.forEach(pose => {
              const oocMarker = pose.is_ooc ? '<OOC> ' : '';
              const timestampMarker = pose.timestamp ? `[${pose.timestamp}] ` : '';
              contextParts.push(`${timestampMarker}${oocMarker}${pose.character_name} ${pose.content}`);

              const preview = pose.content.length > 80 ? pose.content.substring(0, 80) + '...' : pose.content;
              structuredPoses.push({
                  character_name: pose.character_name,
                  content: pose.content,
                  preview,
                  is_ooc: pose.is_ooc,
                  timestamp: pose.timestamp
              });
          });
      }

      return {
          setting: parsedScene.room_description || '',
          activeCharacters: parsedScene.characters_present || [],
          rawContext: contextParts.join('\n'),
          poses: structuredPoses
      };
  }
}
