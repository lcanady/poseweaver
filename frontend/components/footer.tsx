import { Feather } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t border-border/40">
      <div className="container py-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Feather className="h-5 w-5 text-primary" />
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} PoseWeaver. All rights reserved.
          </p>
        </div>
        <nav className="flex items-center gap-4 text-sm text-muted-foreground">
          <a href="/terms" className="hover:text-foreground">
            Terms of Service
          </a>
          <a href="/privacy" className="hover:text-foreground">
            Privacy Policy
          </a>
          <a href="mailto:support@poseweaver.com" className="hover:text-foreground">
            Contact
          </a>
        </nav>
      </div>
    </footer>
  )
}
