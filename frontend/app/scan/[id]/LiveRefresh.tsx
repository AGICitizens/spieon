"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LiveRefresh({ intervalMs = 3000 }: { intervalMs?: number }) {
  const router = useRouter();
  useEffect(() => {
    const handle = window.setInterval(() => {
      router.refresh();
    }, intervalMs);
    return () => window.clearInterval(handle);
  }, [router, intervalMs]);
  return null;
}
