import React from "react";
import { Card } from "../ui/card";

export default function ChartCardStory() {
  return (
    <Card className="w-[420px] h-[220px] p-4">
      <div className="text-sm text-muted-foreground">Average price AED per sqm</div>
      <div className="h-[150px] mt-3 flex items-center justify-center text-muted-foreground">Line chart placeholder</div>
    </Card>
  );
}
