"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu, Wand2, Users, Settings, Feather, LayoutGrid, BookOpen, CreditCard } from "lucide-react"
import { UserNav } from "./user-nav"
import { NotificationCenter } from "@/components/notifications"
import { cn } from "@/lib/utils"
import { useState } from "react"

export function DashboardHeader() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutGrid },
    { href: "/dashboard/scene-weaver", label: "Scene Weaver", icon: Wand2 },
    { href: "/dashboard/scenes", label: "Scenes", icon: BookOpen },
    { href: "/dashboard/characters", label: "Characters", icon: Users },
  ]

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b bg-background px-4 lg:hidden">
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button size="icon" variant="outline">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle Menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="sm:max-w-xs">
          <SheetHeader>
            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          </SheetHeader>
          <nav className="grid gap-6 text-lg font-medium">
            <Link
              href="/"
              className="group flex h-10 w-10 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground"
              onClick={() => setIsOpen(false)}
            >
              <Feather className="h-5 w-5 transition-all group-hover:scale-110" />
              <span className="sr-only">PoseWeaver</span>
            </Link>
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-4 px-2.5 hover:text-foreground",
                  (pathname.startsWith(item.href) && item.href !== "/dashboard") || pathname === item.href
                    ? "text-foreground"
                    : "text-muted-foreground",
                )}
                onClick={() => setIsOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </Link>
            ))}
          </nav>
        </SheetContent>
      </Sheet>

      <div className="flex items-center gap-2">
        <NotificationCenter />
        <UserNav />
      </div>
    </header>
  )
}
