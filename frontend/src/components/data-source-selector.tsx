import React from "react"
import { Card, CardContent } from "./ui/card"
import { Button } from "./ui/button"
import { CheckCircle, Building2 } from "lucide-react"

interface DataSourceSelectorProps {
  activeSource?: string
  onSourceChange?: (source: string) => void
  loading?: boolean
}

export function DataSourceSelector({ activeSource = "DLD", onSourceChange, loading = false }: DataSourceSelectorProps) {
  const propertyTypes = ["All", "Apartments", "Villas", "Land", "Commercial"]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* DLD Card */}
        <Card
          className={`cursor-pointer transition-all hover:shadow-lg border-2 rounded-lg ${
            activeSource === "DLD" 
              ? "border-primary bg-blue-50 shadow-md" 
              : "border-border bg-card hover:border-accent"
          } ${loading ? "opacity-60 pointer-events-none" : ""}`}
          onClick={() => {
            if (!loading) {
              console.log('🏢 DLD source selected');
              onSourceChange?.("DLD");
            }
          }}
        >
          <CardContent className="p-8">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center space-x-4">
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                    activeSource === "DLD" 
                      ? "bg-blue-500 border-blue-500" 
                      : "border-gray-300"
                  }`}
                >
                  {activeSource === "DLD" && <CheckCircle className="h-4 w-4 text-white" />}
                </div>
                <h3 className="text-xl font-bold text-gray-900">DLD</h3>
              </div>
              <div className="flex items-center space-x-2">
                <img 
                  src="/dubai-land-department-logo.png" 
                  alt="DLD Logo" 
                  className="h-8 w-auto max-w-[80px] object-contain"
                  onError={(e) => {
                    // Fallback если логотип не загружается
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
              </div>
            </div>

            <p className="text-gray-600 mb-6 leading-relaxed">
              Analyze all real transaction data obtained from Dubai Land Department.
            </p>

            {/* Property Type Filters */}
            <div className="flex flex-wrap gap-3 mb-6">
              {propertyTypes.map((type) => (
                <Button
                  key={type}
                  variant={type === "Apartments" ? "default" : "ghost"}
                  size="sm"
                  className={`rounded-full transition-colors text-sm px-3 py-1 h-auto ${
                    type === "Apartments" 
                      ? "bg-blue-600 text-white hover:bg-blue-700" 
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  {type}
                </Button>
              ))}
            </div>

            {/* Official Data Source */}
            <div className="flex items-center space-x-3 pt-4 border-t border-border">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 font-bold text-sm">DLD</span>
              </div>
              <span className="text-sm text-muted-foreground">Official data source</span>
            </div>
          </CardContent>
        </Card>

        {/* Marketplace Card */}
        <Card
          className={`cursor-pointer transition-all hover:shadow-lg border-2 rounded-lg ${
            activeSource === "Marketplace" 
              ? "border-primary bg-blue-50 shadow-md" 
              : "border-border bg-card hover:border-accent"
          } ${loading ? "opacity-60 pointer-events-none" : ""}`}
          onClick={() => {
            if (!loading) {
              console.log('🏪 Marketplace source selected');  
              onSourceChange?.("Marketplace");
            }
          }}
        >
          <CardContent className="p-8">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center space-x-4">
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                    activeSource === "Marketplace" 
                      ? "bg-blue-500 border-blue-500" 
                      : "border-gray-300"
                  }`}
                >
                  {activeSource === "Marketplace" && <CheckCircle className="h-4 w-4 text-white" />}
                </div>
                <h3 className="text-xl font-bold text-gray-900">Marketplace</h3>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                className="rounded-full bg-transparent border-gray-300 text-gray-700 hover:text-gray-900 hover:border-gray-400"
              >
                Sign in
              </Button>
            </div>

            <p className="text-gray-600 mb-6 leading-relaxed">
              Analyze data received from real estate sales marketplaces.
            </p>

            {/* Property Type Filters */}
            <div className="flex flex-wrap gap-3 mb-6">
              {propertyTypes.map((type) => (
                <Button
                  key={type}
                  variant={type === "Apartments" ? "default" : "ghost"}
                  size="sm"
                  className={`rounded-full transition-colors text-sm px-3 py-1 h-auto ${
                    type === "Apartments" 
                      ? "bg-blue-600 text-white hover:bg-blue-700" 
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  {type}
                </Button>
              ))}
            </div>

            {/* Marketplace Logos */}
            <div className="flex items-center space-x-3 pt-4 border-t border-border">
              <div className="flex items-center space-x-3">
                <img 
                  src="/bayut-logo.png" 
                  alt="Bayut Logo" 
                  className="h-6 w-auto max-w-[60px] object-contain"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
                <img 
                  src="/property-finder-logo.png" 
                  alt="Property Finder Logo" 
                  className="h-6 w-auto max-w-[60px] object-contain"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
              </div>
              <span className="text-sm text-muted-foreground">Partner marketplaces</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}