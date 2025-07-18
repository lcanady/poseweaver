"use client"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu, Feather } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/contexts/auth-context"

export function Header() {
  const { isAuthenticated } = useAuth()
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <div className="mr-4 hidden md:flex">
          <a href={isAuthenticated ? "/dashboard" : "/"} className="mr-6 flex items-center space-x-2">
            <Feather className="h-6 w-6 text-primary" />
            <span className="hidden font-bold sm:inline-block">SceneForge</span>
          </a>
          <nav className="flex items-center gap-6 text-sm">
            <a href="/#features" className="transition-colors hover:text-foreground/80 text-foreground/60">
              Features
            </a>
            <a href="/#pricing" className="transition-colors hover:text-foreground/80 text-foreground/60">
              Pricing
            </a>
            <a href="/#faq" className="transition-colors hover:text-foreground/80 text-foreground/60">
              FAQ
            </a>
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">{/* You can add a search bar here if needed */}</div>
          <nav className="hidden md:flex items-center gap-2">
            <Button asChild variant="ghost">
              <Link href={isAuthenticated ? "/dashboard" : "/login"}>Log In</Link>
            </Button>
            <Button asChild>
              <Link href={isAuthenticated ? "/dashboard" : "/signup"}>Try It Free</Link>
            </Button>
          </nav>
        </div>
        <div className="md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right">
              <a href={isAuthenticated ? "/dashboard" : "/"} className="mr-6 flex items-center space-x-2 mb-6">
                <Feather className="h-6 w-6 text-primary" />
                <span className="font-bold">SceneForge</span>
              </a>
              <nav className="flex flex-col gap-4 text-lg">
                <a href="/#features" className="hover:text-primary">
                  Features
                </a>
                <a href="/#pricing" className="hover:text-primary">
                  Pricing
                </a>
                <a href="/#faq" className="hover:text-primary">
                  FAQ
                </a>
                <Button asChild variant="ghost" className="justify-start">
                  <Link href={isAuthenticated ? "/dashboard" : "/login"}>Log In</Link>
                </Button>
                <Button asChild>
                  <Link href={isAuthenticated ? "/dashboard" : "/signup"}>Try It Free</Link>
                </Button>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
