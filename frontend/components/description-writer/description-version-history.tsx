import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Clock, FileText, Check, History, Sparkles } from "lucide-react";

interface DescriptionVersion {
  id: string;
  description: string;
  timestamp: Date;
  refinementSuggestion?: string;
  metadata?: {
    style: string;
    word_count: number;
    processing_time_ms: number;
    model_used: string;
    timestamp: string;
  };
}

interface DescriptionVersionHistoryProps {
  versions: DescriptionVersion[];
  currentVersionIndex: number;
  onVersionSelect: (index: number) => void;
}

export const DescriptionVersionHistory = ({
  versions,
  currentVersionIndex,
  onVersionSelect
}: DescriptionVersionHistoryProps) => {
  const [selectedVersionIndex, setSelectedVersionIndex] = useState<number>(currentVersionIndex)
  
  if (versions.length === 0) {
    return null;
  }

  const handleApplyVersion = () => {
    if (selectedVersionIndex !== currentVersionIndex) {
      onVersionSelect(selectedVersionIndex)
    }
  }

  const selectedVersion = versions[selectedVersionIndex]
  const isSelectionDifferent = selectedVersionIndex !== currentVersionIndex

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-primary/10">
            <History className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold">Version History</CardTitle>
            <CardDescription className="text-xs mt-0.5">
              {versions.length} version{versions.length !== 1 ? 's' : ''} generated
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-5 pt-0">
        {/* Version Selector */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="h-3 w-3 text-muted-foreground" />
            <label className="text-xs font-medium text-foreground">Select Version</label>
          </div>
          <Select 
            value={selectedVersionIndex.toString()} 
            onValueChange={(value) => setSelectedVersionIndex(parseInt(value))}
          >
            <SelectTrigger className="h-9 bg-background/50 border-border/60 hover:bg-background/80 transition-colors">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="min-w-[200px]">
              {versions.map((version, index) => {
                const versionNumber = versions.length - index
                const isCurrentVersion = index === currentVersionIndex
                
                return (
                  <SelectItem key={version.id} value={index.toString()} className="py-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                      <span className="text-sm font-medium">
                        Version {versionNumber}
                      </span>
                      {isCurrentVersion && (
                        <Badge variant="default" className="text-xs px-2 py-0.5 h-5 bg-primary/15 text-primary border-primary/20">
                          Current
                        </Badge>
                      )}
                      {version.refinementSuggestion && (
                        <Badge variant="outline" className="text-xs px-1.5 py-0.5 h-5 border-amber-200 text-amber-700 bg-amber-50">
                          <Sparkles className="h-2.5 w-2.5 mr-1" />
                          Refined
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>
        </div>

        {/* Preview of Selected Version */}
        {selectedVersion && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-muted-foreground/20 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60" />
              </div>
              <label className="text-xs font-medium text-foreground">Preview</label>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-muted/40 to-muted/60 rounded-xl p-4 border border-border/40 shadow-sm">
                <div className="space-y-3">
                  <p className="text-sm text-foreground/90 leading-relaxed line-clamp-4 font-medium">
                    {selectedVersion.description}
                  </p>
                  <div className="flex items-center justify-between pt-2 border-t border-border/30">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3 w-3 text-muted-foreground/70" />
                      <span className="text-xs text-muted-foreground font-medium">
                        {selectedVersion.timestamp.toLocaleDateString([], { 
                          month: 'short', 
                          day: 'numeric',
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {selectedVersion.metadata && (
                        <Badge variant="secondary" className="text-xs px-2 py-0.5 h-5 bg-background/60">
                          {selectedVersion.metadata.word_count}w
                        </Badge>
                      )}
                      {selectedVersion.refinementSuggestion && (
                        <Badge variant="outline" className="text-xs px-2 py-0.5 h-5 border-amber-200 text-amber-700 bg-amber-50">
                          <Sparkles className="h-2.5 w-2.5 mr-1" />
                          Refined
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Apply Button */}
        <div className="pt-1">
          <Button 
            onClick={handleApplyVersion}
            disabled={!isSelectionDifferent}
            size="sm"
            className={`w-full h-9 font-medium transition-all duration-200 ${
              isSelectionDifferent 
                ? 'bg-primary hover:bg-primary/90 shadow-sm hover:shadow-md' 
                : 'bg-muted/60 text-muted-foreground cursor-not-allowed'
            }`}
          >
            <Check className={`mr-2 h-3.5 w-3.5 transition-transform duration-200 ${
              isSelectionDifferent ? 'scale-100' : 'scale-90'
            }`} />
            {isSelectionDifferent ? 'Apply Selected Version' : 'Current Version Selected'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
