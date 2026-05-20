import { Suspense } from "react";

import { HomePage } from "@/components/home-page";

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-stone-950 p-8 text-stone-300">Loading...</div>}>
      <HomePage />
    </Suspense>
  );
}
