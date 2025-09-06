import React from "react";
import { Table } from "../ui/table";
import { Button } from "../ui/button";

export default function TransactionsTableStory() {
  const data = Array.from({length:8}).map((_,i)=>({
    key: i,
    date: '18 Dec, 2024',
    location: 'Downtown, Dubai',
    rooms: '4 Rooms',
    sqm: 125,
    price: '2,374,238 AED'
  }));
  const columns = [
    { title: 'Date', dataIndex: 'date', key: 'date' },
    { title: 'Location', dataIndex: 'location', key: 'location' },
    { title: 'Rooms', dataIndex: 'rooms', key: 'rooms' },
    { title: 'M²', dataIndex: 'sqm', key: 'sqm' },
    { title: 'Price, AED', dataIndex: 'price', key: 'price' },
    { title: '', key: 'action', render: ()=> <Button variant="outline" size="sm">Details</Button> },
  ];
  return (
    <div className="space-y-3">
      <Table columns={columns as any} dataSource={data as any} pagination={false} />
      <div className="text-center">
        <Button variant="outline">Show more</Button>
      </div>
    </div>
  );
}
