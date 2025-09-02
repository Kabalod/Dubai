import React, { useState } from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";

export default function CollapseCardStory() {
  const [open, setOpen] = useState(true);
  return (
    <Card className="p-0 overflow-hidden w-[420px]">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="text-sm font-medium">Liquidity</div>
        <Button size="sm" variant="ghost" onClick={()=>setOpen(v=>!v)}>{open? 'Hide':'Show'}</Button>
      </div>
      {open && (
        <div className="p-4 text-sm text-muted-foreground h-32 flex items-center justify-center">
          Chart placeholder
        </div>
      )}
    </Card>
  );
}
