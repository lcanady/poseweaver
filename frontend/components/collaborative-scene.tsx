'use client';

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Send, Users, Dice6 } from 'lucide-react';
import { websocketService } from '@/utils/websocket-service';

interface Pose {
  id: string;
  character_id?: string;
  character_name: string;
  character_avatar?: string;
  pose_text: string;
  user_id: string;
  timestamp: string;
  type?: 'pose' | 'system';
}

interface CollaborativeSceneProps {
  sceneId: string;
  characterId: string;  // Changed from characterName
}

export function CollaborativeScene({ sceneId, characterId }: CollaborativeSceneProps) {
  const [poses, setPoses] = useState<Pose[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const [characterName, setCharacterName] = useState<string>('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new poses arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [poses]);

  // WebSocket connection and event handlers
  useEffect(() => {
    const connectAndJoin = async () => {
      try {
        // Connect to WebSocket (will use token from local storage if available)
        const token = localStorage.getItem('auth_token') || 'guest';
        await websocketService.connect(token);
        setIsConnected(true);

        // Join the scene room
        websocketService.emit('join_scene', {
          scene_id: sceneId,
          character_id: characterId
        });

        // Listen for scene joined confirmation
        websocketService.on('scene_joined', (data: any) => {
          console.log('Joined scene:', data);
          if (data.character) {
            setCharacterName(data.character.name);
          }
        });

        // Listen for new poses
        websocketService.on('new_pose', (data: any) => {
          const newPose: Pose = {
            id: `${Date.now()}-${Math.random()}`,
            character_id: data.character_id,
            character_name: data.character_name,
            character_avatar: data.character_avatar,
            pose_text: data.pose_text,
            user_id: data.user_id,
            timestamp: data.timestamp,
            type: 'pose'
          };
          setPoses(prev => [...prev, newPose]);
        });

        // Listen for system messages (commands)
        websocketService.on('system_message', (data: any) => {
          const systemPose: Pose = {
            id: `${Date.now()}-${Math.random()}`,
            character_name: 'System',
            pose_text: data.message,
            user_id: 'system',
            timestamp: data.timestamp,
            type: 'system'
          };
          setPoses(prev => [...prev, systemPose]);
        });

        // Listen for user joined
        websocketService.on('user_joined', (data: any) => {
          setActiveUsers(prev => [...new Set([...prev, data.character_name])]);
          const joinPose: Pose = {
            id: `${Date.now()}-${Math.random()}`,
            character_name: 'System',
            pose_text: `${data.character_name} joined the scene`,
            user_id: 'system',
            timestamp: data.timestamp,
            type: 'system'
          };
          setPoses(prev => [...prev, joinPose]);
        });

        // Listen for user left
        websocketService.on('user_left', (data: any) => {
          setActiveUsers(prev => prev.filter(u => u !== data.character_name));
          const leavePose: Pose = {
            id: `${Date.now()}-${Math.random()}`,
            character_name: 'System',
            pose_text: `${data.character_name} left the scene`,
            user_id: 'system',
            timestamp: data.timestamp,
            type: 'system'
          };
          setPoses(prev => [...prev, leavePose]);
        });

        // Listen for errors
        websocketService.on('error', (data: any) => {
          console.error('WebSocket error:', data);
        });

      } catch (error) {
        console.error('Failed to connect:', error);
        setIsConnected(false);
      }
    };

    connectAndJoin();

    // Cleanup on unmount
    return () => {
      websocketService.emit('leave_scene', {
        scene_id: sceneId,
        character_id: characterId
      });
      websocketService.off('scene_joined');
      websocketService.off('new_pose');
      websocketService.off('system_message');
      websocketService.off('user_joined');
      websocketService.off('user_left');
      websocketService.off('error');
    };
  }, [sceneId, characterId]);

  const handleSendPose = () => {
    if (!inputText.trim() || !isConnected) return;

    // Send via WebSocket
    websocketService.emit('send_pose', {
      scene_id: sceneId,
      character_id: characterId,
      pose_text: inputText.trim()
    });

    setInputText('');
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendPose();
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const isCommand = (text: string) => text.trim().startsWith('/');

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Collaborative Scene</h2>
          <p className="text-sm text-muted-foreground">
            Playing as {characterName}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? '● Connected' : '○ Disconnected'}
          </Badge>
          <div className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            <span className="text-sm">{activeUsers.length + 1}</span>
          </div>
        </div>
      </div>

      {/* Poses Display */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {poses.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p>No poses yet. Start the scene!</p>
              <p className="text-sm mt-2">Try typing <code className="bg-muted px-2 py-1 rounded">/roll 1d20</code> to roll dice</p>
            </div>
          )}
          {poses.map((pose) => (
            <div
              key={pose.id}
              className={`flex gap-3 ${
                pose.type === 'system' ? 'opacity-75' : ''
              }`}
            >
              {pose.type !== 'system' && (
                <Avatar className="h-10 w-10 flex-shrink-0">
                  {pose.character_avatar ? (
                    <img src={pose.character_avatar} alt={pose.character_name} className="h-full w-full object-cover" />
                  ) : (
                    <AvatarFallback className="text-xs">
                      {getInitials(pose.character_name)}
                    </AvatarFallback>
                  )}
                </Avatar>
              )}
              <div className={`flex-1 ${pose.type === 'system' ? 'ml-0' : ''}`}>
                {pose.type !== 'system' && (
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="font-semibold text-sm">
                      {pose.character_name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(pose.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                )}
                <Card
                  className={`p-3 ${
                    pose.type === 'system'
                      ? 'bg-muted border-dashed text-muted-foreground font-bold italic'
                      : ''
                  }`}
                >
                  <p className="whitespace-pre-wrap" dangerouslySetInnerHTML={{ 
                    __html: pose.pose_text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  }} />
                </Card>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isCommand(inputText)
                ? 'Command detected - press Enter to execute'
                : 'Type your pose or /command...'
            }
            className={isCommand(inputText) ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : ''}
            disabled={!isConnected}
          />
          <Button
            onClick={handleSendPose}
            disabled={!isConnected || !inputText.trim()}
            className="flex-shrink-0"
          >
            {isCommand(inputText) ? (
              <Dice6 className="h-4 w-4" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send • Commands start with /
        </p>
      </div>
    </div>
  );
}
