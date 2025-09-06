import React, { useState } from 'react';
import { Table, Tag, Tooltip, Button, Space } from 'antd';
import { SortAscendingOutlined, SortDescendingOutlined, FilterOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface ReportTableData {
  key: string;
  property: string;
  location: string;
  type: string;
  price: number;
  pricePerSqm: number;
  area: number;
  bedrooms: string;
  status: 'active' | 'pending' | 'sold';
  roi: number;
  lastUpdate: string;
}

interface ReportsTableProps {
  data: ReportTableData[];
  loading?: boolean;
  onRowSelect?: (keys: React.Key[]) => void;
}

const ReportsTable: React.FC<ReportsTableProps> = ({ data, loading = false, onRowSelect }) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [sortedInfo, setSortedInfo] = useState<any>({});

  const handleChange = (pagination: any, filters: any, sorter: any) => {
    setSortedInfo(sorter);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'pending': return 'orange';
      case 'sold': return 'blue';
      default: return 'default';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value).replace('AED', 'AED ');
  };

  const columns: ColumnsType<ReportTableData> = [
    {
      title: 'Property',
      dataIndex: 'property',
      key: 'property',
      width: 200,
      sorter: (a, b) => a.property.localeCompare(b.property),
      sortOrder: sortedInfo.columnKey === 'property' ? sortedInfo.order : null,
      render: (text: string) => (
        <Tooltip title={text}>
          <div className="font-medium text-gray-900 truncate">{text}</div>
        </Tooltip>
      ),
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      width: 180,
      sorter: (a, b) => a.location.localeCompare(b.location),
      sortOrder: sortedInfo.columnKey === 'location' ? sortedInfo.order : null,
      render: (text: string) => (
        <span className="text-sm text-gray-600">{text}</span>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      filters: [
        { text: 'Apartment', value: 'apartment' },
        { text: 'Villa', value: 'villa' },
        { text: 'Townhouse', value: 'townhouse' },
        { text: 'Office', value: 'office' },
      ],
      onFilter: (value, record) => record.type.toLowerCase().includes(value as string),
      render: (text: string) => (
        <Tag color="blue" className="capitalize">{text}</Tag>
      ),
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      sorter: (a, b) => a.price - b.price,
      sortOrder: sortedInfo.columnKey === 'price' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className="font-semibold text-green-600">
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      title: 'Price/m²',
      dataIndex: 'pricePerSqm',
      key: 'pricePerSqm',
      width: 110,
      sorter: (a, b) => a.pricePerSqm - b.pricePerSqm,
      sortOrder: sortedInfo.columnKey === 'pricePerSqm' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className="text-sm text-gray-700">
          {formatCurrency(value)}/m²
        </span>
      ),
    },
    {
      title: 'Area',
      dataIndex: 'area',
      key: 'area',
      width: 90,
      sorter: (a, b) => a.area - b.area,
      sortOrder: sortedInfo.columnKey === 'area' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className="text-sm">{value.toLocaleString()} m²</span>
      ),
    },
    {
      title: 'Bedrooms',
      dataIndex: 'bedrooms',
      key: 'bedrooms',
      width: 100,
      sorter: (a, b) => a.bedrooms.localeCompare(b.bedrooms),
      sortOrder: sortedInfo.columnKey === 'bedrooms' ? sortedInfo.order : null,
      render: (text: string) => (
        <Tag className="bg-gray-100 text-gray-700 border-gray-300">{text}</Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      filters: [
        { text: 'Active', value: 'active' },
        { text: 'Pending', value: 'pending' },
        { text: 'Sold', value: 'sold' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status: string) => (
        <Tag color={getStatusColor(status)} className="capitalize">
          {status}
        </Tag>
      ),
    },
    {
      title: 'ROI',
      dataIndex: 'roi',
      key: 'roi',
      width: 90,
      sorter: (a, b) => a.roi - b.roi,
      sortOrder: sortedInfo.columnKey === 'roi' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className={`font-medium ${value >= 7 ? 'text-green-600' : value >= 5 ? 'text-yellow-600' : 'text-red-500'}`}>
          {value.toFixed(1)}%
        </span>
      ),
    },
    {
      title: 'Last Update',
      dataIndex: 'lastUpdate',
      key: 'lastUpdate',
      width: 120,
      sorter: (a, b) => new Date(a.lastUpdate).getTime() - new Date(b.lastUpdate).getTime(),
      sortOrder: sortedInfo.columnKey === 'lastUpdate' ? sortedInfo.order : null,
      render: (date: string) => (
        <span className="text-xs text-gray-500">
          {new Date(date).toLocaleDateString('en-GB', { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric' 
          })}
        </span>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => {
      setSelectedRowKeys(keys);
      onRowSelect?.(keys);
    },
    getCheckboxProps: (record: ReportTableData) => ({
      disabled: record.status === 'sold',
      name: record.property,
    }),
  };

  return (
    <div className="w-full">
      {selectedRowKeys.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <Space>
            <span className="text-sm text-blue-700">
              {selectedRowKeys.length} item{selectedRowKeys.length !== 1 ? 's' : ''} selected
            </span>
            <Button size="small" type="primary" ghost>
              Export Selected
            </Button>
            <Button size="small" onClick={() => setSelectedRowKeys([])}>
              Clear Selection
            </Button>
          </Space>
        </div>
      )}
      
      <Table<ReportTableData>
        columns={columns}
        dataSource={data}
        loading={loading}
        rowSelection={onRowSelect ? rowSelection : undefined}
        onChange={handleChange}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} properties`,
          pageSizeOptions: ['10', '25', '50', '100'],
          defaultPageSize: 25,
        }}
        scroll={{ x: 1200 }}
        className="w-full"
        rowClassName={(record, index) => 
          index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
        }
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}
      />
    </div>
  );
};

export default ReportsTable;
