'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Share2, 
  Copy, 
  Link, 
  QrCode, 
  Download, 
  Mail, 
  MessageSquare,
  Twitter,
  Facebook,
  CheckCircle,
  ExternalLink
} from "lucide-react";
import { Character } from "@/hooks/useCharacter";

interface CharacterShareModalProps {
  character: Character;
  children?: React.ReactNode;
}

export function CharacterShareModal({ character, children }: CharacterShareModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customMessage, setCustomMessage] = useState('');
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});

  // Generate the public profile URL
  const publicProfileUrl = `${window.location.origin}/character/${character.id}`;
  
  // Generate share text
  const defaultShareText = `Check out ${character.name} - ${character.description || 'A character in the world of roleplay'}`;
  const shareText = customMessage.trim() || defaultShareText;

  const handleCopy = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates(prev => ({ ...prev, [type]: true }));
      toast.success(`${type} copied to clipboard!`);
      
      // Reset copied state after 2 seconds
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [type]: false }));
      }, 2000);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const shareOptions = [
    {
      name: 'Direct Link',
      description: 'Copy the public profile link',
      icon: Link,
      action: () => handleCopy(publicProfileUrl, 'Link'),
      copied: copiedStates['Link']
    },
    {
      name: 'With Message',
      description: 'Copy link with custom message',
      icon: MessageSquare,
      action: () => handleCopy(`${shareText}\n\n${publicProfileUrl}`, 'Message'),
      copied: copiedStates['Message']
    },
    {
      name: 'Email',
      description: 'Share via email',
      icon: Mail,
      action: () => {
        const subject = encodeURIComponent(`Character Profile: ${character.name}`);
        const body = encodeURIComponent(`${shareText}\n\nView the full profile: ${publicProfileUrl}`);
        window.open(`mailto:?subject=${subject}&body=${body}`);
      }
    },
    {
      name: 'Twitter',
      description: 'Share on Twitter/X',
      icon: Twitter,
      action: () => {
        const text = encodeURIComponent(`${shareText} ${publicProfileUrl}`);
        window.open(`https://twitter.com/intent/tweet?text=${text}`);
      }
    }
  ];

  const downloadOptions = [
    {
      name: 'Character Summary',
      description: 'Download a text summary',
      icon: Download,
      action: () => {
        const summary = generateCharacterSummary();
        downloadTextFile(summary, `${character.name}_summary.txt`);
      }
    },
    {
      name: 'Profile Card',
      description: 'Download as formatted card',
      icon: Download,
      action: () => {
        const card = generateProfileCard();
        downloadTextFile(card, `${character.name}_profile.txt`);
      }
    }
  ];

  const generateCharacterSummary = () => {
    const { metadata } = character;
    return `CHARACTER PROFILE: ${character.name}

Description: ${character.description || 'No description provided'}

Background: ${metadata?.background || 'No background provided'}

Personality Traits:
${metadata?.personality?.map(trait => `• ${trait}`).join('\n') || '• None listed'}

Skills:
${metadata?.skills?.map(skill => `• ${skill}`).join('\n') || '• None listed'}

Goals:
${metadata?.goals?.map(goal => `• ${goal}`).join('\n') || '• None listed'}

Created: ${character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}

Public Profile: ${publicProfileUrl}

Generated from PoseWeaver - ${new Date().toLocaleDateString()}`;
  };

  const generateProfileCard = () => {
    return `╔══════════════════════════════════════════════════════════════╗
║                        CHARACTER PROFILE                        ║
╠══════════════════════════════════════════════════════════════╣
║ Name: ${character.name.padEnd(54)} ║
║ Description: ${(character.description || 'No description').substring(0, 45).padEnd(45)} ║
╠══════════════════════════════════════════════════════════════╣
║ Personality: ${(character.metadata?.personality?.[0] || 'Not specified').substring(0, 45).padEnd(45)} ║
║ Primary Skill: ${(character.metadata?.skills?.[0] || 'Not specified').substring(0, 43).padEnd(43)} ║
║ Main Goal: ${(character.metadata?.goals?.[0] || 'Not specified').substring(0, 47).padEnd(47)} ║
╠══════════════════════════════════════════════════════════════╣
║ View Full Profile: ${publicProfileUrl.substring(0, 38).padEnd(38)} ║
╚══════════════════════════════════════════════════════════════╝

Generated from PoseWeaver - ${new Date().toLocaleDateString()}`;
  };

  const downloadTextFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${filename}`);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Share Character Profile
          </DialogTitle>
          <DialogDescription>
            Share {character.name}'s public profile with others
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Character Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Preview</CardTitle>
              <CardDescription>How your character will appear when shared</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-4 p-4 bg-muted/30 rounded-lg border">
                <div className="w-12 h-12 bg-secondary rounded-full flex items-center justify-center overflow-hidden flex-shrink-0">
                  {character.profile_image ? (
                    <img 
                      src={character.profile_image} 
                      alt={character.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-secondary-foreground font-medium">
                      {character.name.charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold">{character.name}</h3>
                    <Badge variant="outline" className="text-xs">Public Profile</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {character.description || 'A character in the world of roleplay'}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {publicProfileUrl}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Custom Message */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Custom Message (Optional)</CardTitle>
              <CardDescription>Add a personal message when sharing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                placeholder={defaultShareText}
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to use the default message
              </p>
            </CardContent>
          </Card>

          {/* Share Options */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Share Options</CardTitle>
              <CardDescription>Choose how you'd like to share this character</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {shareOptions.map((option) => (
                  <Button
                    key={option.name}
                    variant="outline"
                    className="h-auto p-4 justify-start"
                    onClick={option.action}
                  >
                    <div className="flex items-center gap-3 w-full">
                      {option.copied ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <option.icon className="h-5 w-5" />
                      )}
                      <div className="text-left">
                        <div className="font-medium">{option.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {option.description}
                        </div>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Download Options */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Download Options</CardTitle>
              <CardDescription>Download character information for offline sharing</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {downloadOptions.map((option) => (
                  <Button
                    key={option.name}
                    variant="outline"
                    className="h-auto p-4 justify-start"
                    onClick={option.action}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <option.icon className="h-5 w-5" />
                      <div className="text-left">
                        <div className="font-medium">{option.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {option.description}
                        </div>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Copy Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Copy</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label>Public Profile URL</Label>
                <div className="flex gap-2">
                  <Input 
                    value={publicProfileUrl} 
                    readOnly 
                    className="font-mono text-sm"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleCopy(publicProfileUrl, 'QuickURL')}
                  >
                    {copiedStates['QuickURL'] ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
