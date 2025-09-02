import React from "react";

export default function KpiBadgeStory() {
  return (
    <div className="flex gap-4">
      <div className="px-2 py-1 rounded-full bg-green-50 text-green-700 text-xs">+12.5%</div>
      <div className="px-2 py-1 rounded-full bg-red-50 text-red-700 text-xs">-3.2%</div>
      <div className="px-2 py-1 rounded-full bg-slate-100 text-slate-700 text-xs">0.0%</div>
    </div>
  );
}
