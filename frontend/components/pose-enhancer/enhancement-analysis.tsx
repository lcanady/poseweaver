import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Target, Lightbulb, AlertCircle } from "lucide-react";

interface EnhancementAnalysisProps {
  enhancedPose: string | null;
  originalPose: string;
  enhancementSettings: {
    detailLevel: number;
    creativityLevel: number;
    sensoryFocus: number;
    emotionalDepth: number;
    enhancementStyle: string;
    narrativeTone: string;
  };
}

export const EnhancementAnalysis = ({
  enhancedPose,
  originalPose,
  enhancementSettings
}: EnhancementAnalysisProps) => {
  if (!enhancedPose) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <BarChart3 className="mr-2 h-4 w-4" />
              Enhancement Analysis
            </CardTitle>
            <CardDescription className="text-xs">
              Analysis will appear after enhancement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground text-center py-8">
              Enhance a pose to see detailed analysis
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Calculate basic metrics
  const originalWordCount = originalPose.split(/\s+/).length;
  const enhancedWordCount = enhancedPose.split(/\s+/).length;
  const expansionRatio = enhancedWordCount / originalWordCount;
  
  // Generate analysis based on settings
  const getStyleDescription = (style: string) => {
    switch (style) {
      case 'subtle': return 'Light enhancement preserving original style';
      case 'balanced': return 'Moderate enhancement with good detail balance';
      case 'dramatic': return 'Heavy enhancement with rich descriptive language';
      default: return 'Custom enhancement settings';
    }
  };

  const getMetricColor = (value: number) => {
    if (value >= 70) return 'bg-green-500';
    if (value >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Enhancement Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <BarChart3 className="mr-2 h-4 w-4" />
            Enhancement Analysis
          </CardTitle>
          <CardDescription className="text-xs">
            Detailed breakdown of your enhancement
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Word Count Comparison */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Original</span>
              <span>{originalWordCount} words</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Enhanced</span>
              <span>{enhancedWordCount} words</span>
            </div>
            <div className="flex justify-between text-xs font-medium">
              <span>Expansion</span>
              <span>{expansionRatio.toFixed(1)}x</span>
            </div>
          </div>

          {/* Enhancement Metrics */}
          <div className="space-y-3">
            <div className="text-xs font-medium">Enhancement Levels</div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span>Detail Level</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getMetricColor(enhancementSettings.detailLevel)} transition-all`}
                      style={{ width: `${enhancementSettings.detailLevel}%` }}
                    />
                  </div>
                  <span className="text-muted-foreground">{enhancementSettings.detailLevel}%</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span>Creativity</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getMetricColor(enhancementSettings.creativityLevel)} transition-all`}
                      style={{ width: `${enhancementSettings.creativityLevel}%` }}
                    />
                  </div>
                  <span className="text-muted-foreground">{enhancementSettings.creativityLevel}%</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span>Sensory Focus</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getMetricColor(enhancementSettings.sensoryFocus)} transition-all`}
                      style={{ width: `${enhancementSettings.sensoryFocus}%` }}
                    />
                  </div>
                  <span className="text-muted-foreground">{enhancementSettings.sensoryFocus}%</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span>Emotional Depth</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getMetricColor(enhancementSettings.emotionalDepth)} transition-all`}
                      style={{ width: `${enhancementSettings.emotionalDepth}%` }}
                    />
                  </div>
                  <span className="text-muted-foreground">{enhancementSettings.emotionalDepth}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Style Information */}
          <div className="space-y-2 pt-2 border-t border-border/50">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Style</span>
              <Badge variant="secondary" className="text-xs capitalize">
                {enhancementSettings.enhancementStyle}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Tone</span>
              <Badge variant="outline" className="text-xs capitalize">
                {enhancementSettings.narrativeTone}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Enhancement Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <Lightbulb className="mr-2 h-4 w-4" />
            Enhancement Tips
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <Target className="h-3 w-3 text-muted-foreground mt-0.5 flex-shrink-0" />
              <p className="text-xs text-muted-foreground">
                {getStyleDescription(enhancementSettings.enhancementStyle)}
              </p>
            </div>
            
            {expansionRatio > 3 && (
              <div className="flex items-start gap-2">
                <AlertCircle className="h-3 w-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">
                  High expansion ratio - consider reducing detail level for more concise output
                </p>
              </div>
            )}
            
            {enhancementSettings.creativityLevel > 80 && (
              <div className="flex items-start gap-2">
                <Lightbulb className="h-3 w-3 text-blue-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">
                  High creativity setting may produce more experimental language
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
