import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Clock, RotateCcw } from "lucide-react";

interface PoseVersion {
  id: string;
  pose: string;
  timestamp: Date;
  editSuggestion?: string;
}

interface VersionHistoryProps {
  poseVersions: PoseVersion[];
  currentVersionIndex: number;
  onVersionSelect: (index: number) => void;
}

export const VersionHistory = ({
  poseVersions,
  currentVersionIndex,
  onVersionSelect
}: VersionHistoryProps) => {
  if (poseVersions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Version History</CardTitle>
          <CardDescription className="text-xs">Previous versions will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-muted-foreground text-center py-4">
            No versions yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Version History</CardTitle>
        <CardDescription className="text-xs">
          {poseVersions.length} version{poseVersions.length !== 1 ? 's' : ''}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {poseVersions.map((version, index) => (
          <div
            key={version.id}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              index === currentVersionIndex
                ? 'border-primary bg-primary/5'
                : 'border-border/50 hover:border-border hover:bg-muted/30'
            }`}
            onClick={() => onVersionSelect(index)}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {version.timestamp.toLocaleTimeString()}
                </span>
              </div>
              {index === currentVersionIndex && (
                <Badge variant="secondary" className="text-xs px-2 py-0">
                  Current
                </Badge>
              )}
            </div>
            
            {version.editSuggestion && (
              <div className="mb-2">
                <Badge variant="outline" className="text-xs px-2 py-0 mb-1">
                  Refined
                </Badge>
                <p className="text-xs text-muted-foreground italic">
                  "{version.editSuggestion}"
                </p>
              </div>
            )}
            
            <p className="text-xs line-clamp-3">
              {version.pose.substring(0, 120)}
              {version.pose.length > 120 ? '...' : ''}
            </p>
            
            {index !== currentVersionIndex && (
              <Button
                size="sm"
                variant="ghost"
                className="mt-2 h-6 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onVersionSelect(index);
                }}
              >
                <RotateCcw className="mr-1 h-3 w-3" />
                Restore
              </Button>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
