import React, { useState } from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import GoogleButtonStory from "./google-button";

export default function AuthLayoutStory() {
  const [tab, setTab] = useState<'login' | 'signup'>('login');
  return (
    <div className="grid grid-cols-2 gap-8 p-6">
      <div className="rounded-2xl bg-slate-200 h-[520px]"></div>
      <div className="flex items-center">
        <Card className="w-[420px] p-6 space-y-4">
          <div className="flex rounded-full bg-slate-100 p-1">
            <Button variant={tab==='login'?'default':'ghost'} className="flex-1" onClick={()=>setTab('login')}>Sign In</Button>
            <Button variant={tab==='signup'?'default':'ghost'} className="flex-1" onClick={()=>setTab('signup')}>Sign Up</Button>
          </div>
          <GoogleButtonStory />
          <div className="text-center text-xs text-muted-foreground">or</div>
          <div className="h-40 flex items-center justify-center text-sm text-muted-foreground">Form placeholder ({tab})</div>
        </Card>
      </div>
    </div>
  );
}


