import React from "react";
import { Card } from "../ui/card";

export default function OverviewCardStory() {
  return (
    <div className="grid grid-cols-3 gap-4">
      {["Price","Market volume","Deals"].map(title => (
        <Card key={title} className="p-4">
          <div className="text-sm text-muted-foreground">{title}</div>
          <div className="mt-3 text-2xl font-semibold">3,000 <span className="text-green-600 text-sm align-top">+12.5%</span></div>
          <div className="text-xs text-muted-foreground mt-1">vs 12/2023 in Dubai</div>
        </Card>
      ))}
    </div>
  );
}
