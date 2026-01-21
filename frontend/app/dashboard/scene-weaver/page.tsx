'use client';

import { PostEditor } from "@/components/post-editor"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { Loader2 } from "lucide-react"

function SceneWeaverContent() {
  const searchParams = useSearchParams()
  const sceneId = searchParams.get('scene')

  return (
    <div className="flex-1 w-full h-full overflow-hidden">
      <PostEditor autoLoadSceneId={sceneId} />
    </div>
  )
}

export default function SceneWeaverPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex justify-center items-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <SceneWeaverContent />
    </Suspense>
  )
}
