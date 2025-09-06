"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./card"
import { Badge } from "./badge"
import { Button } from "./button"
import { ChevronDown, ChevronUp, Info, TrendingUp } from "lucide-react"

interface MetricCardProps {
  title: string
  value: string
  currency?: string
  trend?: string
  comparison?: string
  description?: string
  isCollapsible?: boolean
  defaultOpen?: boolean
  children?: React.ReactNode
}

export function MetricCard({
  title,
  value,
  currency = "AED",
  trend,
  comparison,
  description,
  isCollapsible = false,
  defaultOpen = false,
  children,
}: MetricCardProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
            <Info className="h-4 w-4 text-gray-400" />
          </div>
          {isCollapsible && (
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(!isOpen)} className="h-6 w-6 p-0">
              {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-2xl font-bold">{value}</span>
          <span className="text-sm text-gray-500">{currency}</span>
          {trend && (
            <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-100">
              {trend} <TrendingUp className="ml-1 h-3 w-3" />
            </Badge>
          )}
        </div>
        {comparison && description && (
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{comparison}</span>
            <span>{description}</span>
          </div>
        )}
        {isCollapsible && isOpen && children && <div className="mt-4 pt-4 border-t">{children}</div>}
      </CardContent>
    </Card>
  )
}

export function CardsShowcase() {
  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-4">
          <Badge variant="success" className="bg-green-100 text-green-700">
            12.5% <TrendingUp className="ml-1 h-3 w-3" />
          </Badge>
          <Badge variant="destructive" className="bg-red-100 text-red-700">
            12.5% <TrendingUp className="ml-1 h-3 w-3" />
          </Badge>
        </div>

        <div className="space-y-4">
          <MetricCard
            title="Deals"
            value="2,740,000"
            trend="12.5%"
            comparison="vs 2,740 in Dubai"
            description="worse by 30%"
          />
          <MetricCard title="Deals" value="2,740,000" comparison="vs 2,740 in Dubai" description="worse by 30%" />
        </div>
      </div>

      <div className="space-y-4">
        <MetricCard title="Price" value="" isCollapsible={true} defaultOpen={true}>
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              title="Average price"
              value="2,740,000"
              trend="12.5%"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
            <MetricCard
              title="Median price"
              value="2,740,000"
              trend="12.5%"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <MetricCard
              title="Average price per sqm"
              value="2,740,000"
              trend="12.5%"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
            <MetricCard
              title="Price range"
              value="2,740,000 - 2,740,000"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
          </div>
        </MetricCard>

        <MetricCard title="Price" value="" isCollapsible={true} defaultOpen={false} />

        <MetricCard title="Price" value="" isCollapsible={true} defaultOpen={true}>
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              title="Average price"
              value="2,740,000"
              trend="12.5%"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
            <MetricCard
              title="Median price"
              value="2,740,000"
              trend="12.5%"
              comparison="vs 2,740 in Dubai"
              description="worse by 30%"
            />
          </div>
        </MetricCard>
      </div>
    </div>
  )
}
