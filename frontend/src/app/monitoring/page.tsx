"use client";

import React from "react";
import { MonitoringDashboard } from "../../components/monitoring/MonitoringDashboard";

export default function MonitoringPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <MonitoringDashboard />
    </div>
  );
}
