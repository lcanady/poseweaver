import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Scroll, Home, LayoutDashboard } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <div className="container max-w-2xl">
        <Card className="bg-card/50">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-6">
              <Scroll className="h-16 w-16 text-muted-foreground" />
            </div>
            <CardTitle className="text-4xl font-bold mb-2">Story Not Found</CardTitle>
            <p className="text-xl text-muted-foreground">
              The page you're seeking has vanished into the narrative void.
            </p>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="text-center">
              <p className="text-muted-foreground mb-6">
                It seems this chapter of your journey doesn't exist yet. Perhaps it's time to write a new one?
              </p>
            </div>
            
            <div className="grid gap-3 sm:grid-cols-2">
              <Link href="/dashboard" className="w-full">
                <Button className="w-full" size="lg">
                  <LayoutDashboard className="mr-2 h-4 w-4" />
                  Return to Dashboard
                </Button>
              </Link>
              
              <Link href="/" className="w-full">
                <Button variant="outline" className="w-full" size="lg">
                  <Home className="mr-2 h-4 w-4" />
                  Back to Home
                </Button>
              </Link>
            </div>
            
            <div className="text-center pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Lost in the story? Our AI co-writer is here to help guide your narrative.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
