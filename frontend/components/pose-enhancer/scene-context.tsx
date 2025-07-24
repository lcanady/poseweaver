import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface SceneContextProps {
  sceneDump: string;
  onSceneDumpChange: (value: string) => void;
}

export const SceneContext = ({
  sceneDump,
  onSceneDumpChange
}: SceneContextProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scene Context</CardTitle>
        <CardDescription>Provide context to enhance pose accuracy</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Label>Scene Description</Label>
          <Textarea 
            placeholder="Paste scene dump or describe the current situation..."
            value={sceneDump}
            onChange={(e) => onSceneDumpChange(e.target.value)}
            className="min-h-[120px] resize-none"
          />
        </div>
      </CardContent>
    </Card>
  );
};
