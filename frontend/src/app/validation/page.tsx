"use client";

import React from "react";
import { ValidationDashboard } from "../../components/validation_pipeline/ValidationDashboard";

export default function ValidationPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <ValidationDashboard />
    </div>
  );
}
