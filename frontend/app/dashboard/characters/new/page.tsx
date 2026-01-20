"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function NewCharacterPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/characters/create");
  }, [router]);

  return (
    <div className="flex h-[80vh] items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Redirecting to character creation...</p>
      </div>
    </div>
  );
}
