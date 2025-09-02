import React, { useState } from "react";
import { Button } from "../ui/button";

export default function SegmentedGroupStory() {
  const [value, setValue] = useState('sales');
  const items = [
    {label: 'Sales', value: 'sales'},
    {label: 'Rental', value: 'rental'},
  ];
  return (
    <div className="inline-flex rounded-full bg-slate-100 p-1">
      {items.map(i => (
        <Button key={i.value} variant={value===i.value? 'default':'ghost'} className="rounded-full" onClick={()=>setValue(i.value)}>
          {i.label}
        </Button>
      ))}
    </div>
  );
}
