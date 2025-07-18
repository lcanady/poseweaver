import type React from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { DashboardSidebar } from "@/components/dashboard-sidebar"
import { DashboardHeader } from "@/components/dashboard-header"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen w-full bg-muted/40">
        <DashboardSidebar />
        <div className="flex flex-col lg:pl-14">
          <DashboardHeader />
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
