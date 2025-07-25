import { Card, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import type { Scene } from "../lib/types"

interface SceneCardProps {
  scene: Scene
}

export function SceneCard({ scene }: SceneCardProps) {
  return (
    <Card className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <div className="flex-1 p-6">
        <div className="flex items-center gap-4 mb-2">
          <CardTitle className="text-lg">{scene.title}</CardTitle>
          <Badge variant={scene.status === "Ongoing" ? "default" : "outline"}>{scene.status}</Badge>
        </div>
        <CardDescription>
          {scene.characters.length > 0 && (
            <span className="mr-4">
              Characters: {scene.characters.join(", ")}
            </span>
          )}
          Last updated: {scene.lastUpdated}
        </CardDescription>
        <CardContent className="p-0 pt-4">
          <p className="text-sm text-muted-foreground line-clamp-2">{scene.lastPose}</p>
        </CardContent>
      </div>
      <CardFooter className="p-6 pt-0 sm:pt-6 sm:pl-0">
        <Button asChild>
          <Link href={`/dashboard/scene-weaver?scene=${scene.id}`}>Continue Scene</Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
