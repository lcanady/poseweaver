'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Copy, Download, CheckCircle, FileText, Clock, Hash, Sparkles } from "lucide-react";
import { toast } from 'sonner'

interface DescriptionOutputProps {
  description: string | null;
  copyFormat: string;
  onCopyFormatChange: (format: string) => void;
  onCopy: () => void;
  onDownload: () => void;
  metadata?: {
    style: string;
    word_count: number;
    processing_time_ms: number;
    model_used: string;
    timestamp: string;
  };
}

export function DescriptionOutput({
  description,
  copyFormat,
  onCopyFormatChange,
  onCopy,
  onDownload,
  metadata
}: DescriptionOutputProps) {
  const [justCopied, setJustCopied] = useState(false);

  const handleCopy = () => {
    onCopy();
    setJustCopied(true);
    setTimeout(() => setJustCopied(false), 2000);
  };
  if (!description) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Generated Description
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Upload an image and generate a description to see results here
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Generated Description</CardTitle>
            <CardDescription>Your generated description is ready</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="space-y-1">
              <Label className="text-xs">Copy Format</Label>
              <Select value={copyFormat} onValueChange={onCopyFormatChange}>
                <SelectTrigger className="w-24 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="plain">Plain</SelectItem>
                  <SelectItem value="quoted">Quoted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={handleCopy}
              size="sm"
              variant="outline"
              className="mt-5"
            >
              {justCopied ? (
                <>
                  <CheckCircle className="mr-1 h-3 w-3 text-green-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="mr-1 h-3 w-3" />
                  Copy
                </>
              )}
            </Button>
            <Button
              onClick={onDownload}
              size="sm"
              variant="outline"
              className="mt-5"
            >
              <Download className="mr-1 h-3 w-3" />
              Download
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-muted/30 rounded-lg p-4 border border-border/50">
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {description}
          </div>
        </div>
        {metadata && (
          <div className="mt-4 pt-4 border-t border-border/50">
            <div className="text-xs text-muted-foreground">
              Generated on {new Date(metadata.timestamp).toLocaleString()} • {metadata.style} style • {metadata.word_count} words
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
