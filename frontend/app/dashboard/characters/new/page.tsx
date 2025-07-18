import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import Link from "next/link"
import { Upload } from "lucide-react"

export default function NewCharacterPage() {
  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create New Character</h1>
          <p className="text-muted-foreground mt-1">
            Breathe life into a new persona. The more detail you provide, the better the AI can embody them.
          </p>
        </div>
        <Card>
          <CardContent className="p-6 grid gap-8">
            <div className="grid md:grid-cols-3 gap-6 items-start">
              <div className="md:col-span-1 flex flex-col items-center gap-4">
                <Label>Character Avatar</Label>
                <Avatar className="h-32 w-32">
                  <AvatarImage src="/placeholder.svg?width=128&height=128" alt="Avatar" />
                  <AvatarFallback>AV</AvatarFallback>
                </Avatar>
                <Button variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Image
                </Button>
              </div>
              <div className="md:col-span-2 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Character Name</Label>
                  <Input id="name" placeholder="e.g., Jax, the Cyber-Noir Detective" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tagline">Short Description / Tagline</Label>
                  <Input id="tagline" placeholder="A cynical ex-cop with a cybernetic eye..." />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="brain-dump">Character Brain Dump</Label>
              <p className="text-sm text-muted-foreground">
                This is the most important part. Describe their personality, history, goals, fears, mannerisms, speaking
                style, and anything else that defines them.
              </p>
              <Textarea
                id="brain-dump"
                placeholder="Jax is world-weary and cynical on the surface, but underneath lies a strong, albeit tarnished, sense of justice. He speaks in short, clipped sentences and often uses noir-style metaphors. He has a prosthetic left eye that glows faintly in the dark..."
                className="min-h-[300px]"
              />
            </div>
          </CardContent>
        </Card>
        <div className="flex justify-end gap-2">
          <Button variant="outline" asChild>
            <Link href="/dashboard/characters">Cancel</Link>
          </Button>
          <Button>Save Character</Button>
        </div>
      </div>
    </div>
  )
}
