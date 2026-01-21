"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Users, Settings, Feather, LayoutGrid, CreditCard, Sparkles, Eye, Shield, BookOpen, GitGraph, Search } from "lucide-react"
import { UserNav } from "./user-nav"
import { NotificationCenter } from "@/components/notifications"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/auth-context"

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

export function DashboardSidebar() {
  const pathname = usePathname()
  const { isAuthenticated, user } = useAuth()

  const navItems: NavItem[] = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutGrid },
    { href: "/dashboard/stories", label: "Stories", icon: BookOpen },
    { href: "/dashboard/characters", label: "Characters", icon: Users },
    { href: "/dashboard/pose-enhancer", label: "Pose Enhancer", icon: Sparkles },
    { href: "/dashboard/description-writer", label: "Description Writer", icon: Eye },
    { href: "/dashboard/plot-tracker", label: "Plot Tracker", icon: GitGraph },
    { href: "/dashboard/search", label: "Search & Summary", icon: Search },
  ]

  // Add admin navigation for admin users
  // TODO: Implement admin check with Firebase Custom Claims or Firestore User Profile
  if (user?.is_admin) {
    navItems.push({ href: "/dashboard/admin", label: "Admin Panel", icon: Shield });
  }

  const bottomNavItems: NavItem[] = [
    // Settings and Billing moved to user dropdown menu
  ]

  return (
    <aside className="hidden fixed left-0 top-0 z-40 w-14 h-screen flex-col border-r bg-background lg:flex">
      <TooltipProvider>
        <nav className="flex flex-col items-center gap-4 px-2 sm:py-5">
          <Link
            href={isAuthenticated ? "/dashboard" : "/"}
            className="group flex h-9 w-9 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:h-8 md:w-8 md:text-base"
          >
            <Feather className="h-4 w-4 transition-all group-hover:scale-110" />
            <span className="sr-only">PoseWeaver</span>
          </Link>
          {navItems.map((item) => (
            <Tooltip key={item.href}>
              <TooltipTrigger asChild>
                <Link
                  href={item.href}
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:text-foreground md:h-8 md:w-8",
                    (pathname.startsWith(item.href) && item.href !== "/dashboard") || pathname === item.href
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <span className="sr-only">{item.label}</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right">{item.label}</TooltipContent>
            </Tooltip>
          ))}
        </nav>
        <nav className="mt-auto flex flex-col items-center gap-4 px-2 sm:py-5">
          <div className="flex items-center justify-center">
            <NotificationCenter />
          </div>
          {bottomNavItems.map((item) => (
            <Tooltip key={item.href}>
              <TooltipTrigger asChild>
                <Link
                  href={item.href}
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:text-foreground md:h-8 md:w-8",
                    pathname.startsWith(item.href) ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <span className="sr-only">{item.label}</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right">{item.label}</TooltipContent>
            </Tooltip>
          ))}
          <UserNav />
        </nav>
      </TooltipProvider>
    </aside>
  )
}
