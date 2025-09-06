import React, { useState } from "react";
import { Segmented } from "../ui/segmented"; // if absent, fallback to simple divs
import { Input } from "../ui/input";
import { Button } from "../ui/button";

export default function FiltersBarStory() {
  const [mode, setMode] = useState<'building'|'districts'|'developer'|'naming'>('developer');
  return (
    <div className="flex gap-3 items-center p-4 bg-white rounded-xl shadow">
      <div className="flex-1">
        <div className="inline-flex rounded-full bg-slate-100 p-1">
          {(['building','districts','developer','naming'] as const).map(m => (
            <Button key={m} variant={mode===m? 'default':'ghost'} className="capitalize" onClick={()=>setMode(m)}>
              {m}
            </Button>
          ))}
        </div>
      </div>
      <Input placeholder="Select value" className="w-72" />
      <Button>Search</Button>
    </div>
  );
}
