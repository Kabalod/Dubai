import React, { useState } from "react";
import { Button } from "../ui/button";
import { Icons } from "lucide-react";

export default function GoogleButtonStory() {
  const [loading, setLoading] = useState(false);
  const handleClick = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1500);
  };

  return (
    <div className="w-[360px] space-y-3">
      <Button variant="outline" className="w-full" onClick={handleClick} disabled={loading}>
        {/* Simple placeholder icon */}
        <span className="mr-2">G</span>
        {loading ? "Connecting…" : "Continue with Google"}
      </Button>
      <p className="text-sm text-muted-foreground">Отображение состояния загрузки и disabled.</p>
    </div>
  );
}


