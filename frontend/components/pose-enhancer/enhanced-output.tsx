import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Copy, CheckCircle, Save } from "lucide-react";
import { useState } from "react";

interface EnhancedOutputProps {
  enhancedPose: string | null;
  originalPose?: string;
  selectedCharacterId?: string;
  enhancementSettings?: any;
  copyFormat: string;
  onCopyFormatChange: (format: string) => void;
  onCopy: () => void;
  onSave?: () => void;
}

export const EnhancedOutput = ({
  enhancedPose,
  originalPose,
  selectedCharacterId,
  enhancementSettings,
  copyFormat,
  onCopyFormatChange,
  onCopy,
  onSave
}: EnhancedOutputProps) => {
  const [justCopied, setJustCopied] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

  const handleCopy = () => {
    onCopy();
    setJustCopied(true);
    setTimeout(() => setJustCopied(false), 2000);
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 2000);
    }
  };

  const canSave = enhancedPose && originalPose && selectedCharacterId && onSave;

  if (!enhancedPose) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Enhanced Pose</CardTitle>
          <CardDescription>Your enhanced pose will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            <p>No enhanced pose yet. Enter a pose above and click "Enhance Pose".</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Enhanced Pose</CardTitle>
            <CardDescription>Your enhanced pose is ready</CardDescription>
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
                  <SelectItem value="mush">MUSH (%r)</SelectItem>
                  <SelectItem value="mux">MUX (%r)</SelectItem>
                  <SelectItem value="moo">MOO (%n)</SelectItem>
                  <SelectItem value="html">HTML (&lt;br&gt;)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              {canSave && (
                <Button
                  onClick={handleSave}
                  size="sm"
                  variant="outline"
                  className="mt-5"
                >
                  {justSaved ? (
                    <>
                      <CheckCircle className="mr-1 h-3 w-3 text-green-500" />
                      Saved!
                    </>
                  ) : (
                    <>
                      <Save className="mr-1 h-3 w-3" />
                      Save for Training
                    </>
                  )}
                </Button>
              )}
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
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-muted/30 rounded-lg p-4 border border-border/50">
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {enhancedPose}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
