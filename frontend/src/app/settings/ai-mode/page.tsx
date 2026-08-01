import React from "react";
import AIModeSettings from "@/components/ai/AIModeSettings";

export const metadata = {
  title: "AI Mode Manager Settings | CodeForge AI",
  description: "Platform-wide AI Provider Gateway configuration page.",
};

export default function AIModeSettingsPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6 md:p-12">
      <AIModeSettings />
    </main>
  );
}
