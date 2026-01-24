'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2, Send, Sparkles, User, Check, X } from "lucide-react";
import { useAuth } from '@/contexts/auth-context';
import { getApiUrl } from '@/utils/api-utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import TextareaAutosize from 'react-textarea-autosize';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AiCharacterCreatorProps {
  onFinalize: (data: any) => void;
  onCancel: () => void;
}

export function AiCharacterCreator({ onFinalize, onCancel }: AiCharacterCreatorProps) {
  const { getToken } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startSession();
  }, []);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const startSession = async () => {
    setIsStarting(true);
    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/characters/ai-chat/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      if (data.success) {
        setSessionId(data.session_id);
        setMessages([
          { role: 'assistant', content: "Hello! I'm your AI character assistant. Let's create something amazing together. What kind of character do you have in mind? Give me a rough idea, a name, or even just a vibe!" }
        ]);
      } else {
        setMessages([
          { role: 'assistant', content: `⚠️ Failed to initialize: ${data.error || "Unknown error"}. Please check your API configuration.` }
        ]);
      }
    } catch (error) {
      console.error("Error starting AI chat session:", error);
      setMessages([
        { role: 'assistant', content: "⚠️ Connection error: Could not start AI session. Please check if the backend is running and reachable." }
      ]);
    } finally {
      setIsStarting(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/characters/ai-chat/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId, message: userMessage })
      });
      const data = await response.json();
      if (data.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        // Handle backend error
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `⚠️ Error: ${data.error || "The AI assistant is currently unavailable."}` 
        }]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "⚠️ Connection error: Failed to reach the AI service. Please try again later." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinalize = async () => {
    if (!sessionId || isFinalizing) return;

    setIsFinalizing(true);
    try {
      const token = await getToken();
      const response = await fetch(`${getApiUrl()}/api/characters/ai-chat/finalize`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await response.json();
      if (data.success) {
        onFinalize(data.character);
      }
    } catch (error) {
      console.error("Error finalizing character:", error);
    } finally {
      setIsFinalizing(false);
    }
  };

  if (isStarting) {
    return (
      <Card className="w-full h-[600px] flex flex-col items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Initializing AI Assistant...</p>
      </Card>
    );
  }

  return (
    <Card className="w-full h-[700px] flex flex-col overflow-hidden border-2 border-primary/20 shadow-xl">
      <CardHeader className="bg-primary/5 border-b shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-full">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">AI Character Workshop</CardTitle>
              <CardDescription>Chat to refine your character's soul</CardDescription>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onCancel}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-0 relative">
        <ScrollArea ref={scrollAreaRef} className="h-full p-4">
          <div className="space-y-4 pb-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <Avatar className="h-8 w-8 shrink-0">
                    {message.role === 'user' ? (
                      <>
                        <AvatarImage src="" />
                        <AvatarFallback className="bg-primary text-primary-foreground"><User className="h-4 w-4" /></AvatarFallback>
                      </>
                    ) : (
                      <>
                        <AvatarImage src="" />
                        <AvatarFallback className="bg-secondary text-secondary-foreground"><Sparkles className="h-4 w-4" /></AvatarFallback>
                      </>
                    )}
                  </Avatar>
                  <div
                    className={`rounded-2xl px-4 py-2 text-sm ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-tr-none shadow-md'
                        : 'bg-muted rounded-tl-none border shadow-sm'
                    }`}
                  >
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                        li: ({node, ...props}) => <li className="mb-1" {...props} />,
                        strong: ({node, ...props}) => <strong className="font-bold text-amber-600 dark:text-amber-400" {...props} />,
                        code: ({node, ...props}) => <code className="bg-background/50 rounded px-1 py-0.5 text-xs font-mono" {...props} />,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[80%]">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-secondary text-secondary-foreground"><Sparkles className="h-4 w-4" /></AvatarFallback>
                  </Avatar>
                  <div className="bg-muted rounded-2xl rounded-tl-none border px-4 py-2 text-sm shadow-sm flex items-center gap-2">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="w-1.5 h-1.5 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="w-1.5 h-1.5 bg-foreground/30 rounded-full animate-bounce"></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>

      <CardFooter className="p-4 border-t bg-background shrink-0 flex flex-col gap-3">
        <div className="flex w-full gap-2 items-end">
          <TextareaAutosize
            placeholder="Describe your character..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            maxRows={8}
            className="flex-1 min-h-[40px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none overflow-y-auto"
          />
          <Button 
            size="icon" 
            onClick={handleSend} 
            disabled={isLoading || !input.trim()} 
            className="h-10 w-10 shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex justify-between items-center w-full">
          <p className="text-[10px] text-muted-foreground italic">
            AI can make mistakes. Review the final details before saving.
          </p>
          <Button 
            variant="default" 
            size="sm" 
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
            onClick={handleFinalize}
            disabled={messages.length < 3 || isFinalizing}
          >
            {isFinalizing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Check className="mr-2 h-4 w-4" />
            )}
            Finish & Extract
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
