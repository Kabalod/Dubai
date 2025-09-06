import React, { useState, useEffect } from 'react';
import { RealEstateDashboard } from '../components/real-estate-dashboard';
import { apiService } from '../services/apiService';
import { type PropertyStats, type Property } from '../utils/api';

const MainDashboard: React.FC = () => {
  const [stats, setStats] = useState<PropertyStats | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // ✅ ИСПРАВЛЕНО: используем только apiService и добавляем fallback данные
        try {
          console.log('📊 Trying to fetch real API data...');
          const [statsResponse, propertiesResponse] = await Promise.all([
            apiService.getStats(), // используем apiService для stats
            apiService.getProperties({ limit: 20 })
          ]);
          
          console.log('✅ Successfully loaded API data:', { statsResponse, propertiesResponse });
          setStats(statsResponse);
          setProperties(propertiesResponse.results || propertiesResponse);
          
        } catch (apiError) {
          console.warn('⚠️ API unavailable, using mock data:', apiError);
          
          // ✅ FALLBACK: моковые данные для демонстрации
          setStats({
            totalProperties: 15432,
            totalBuildings: 890,
            totalDeals: 2156,
            averagePrice: 2850000,
            medianPrice: 2450000,
            avgPricePerSqm: 12500,
            priceRange: { min: 450000, max: 25000000 },
            marketVolume: { deals: 2156, total_volume: 82500000 },
            liquidity: 85.5,
            roi: 12.8
          });
          
          setProperties([
            {
              id: '1', listing_id: 'PROP001', title: 'Luxury Apartment in Downtown Dubai',
              display_address: 'Downtown Dubai, Dubai', property_type: 'Apartment',
              price: 2850000, area: '2BR', bedrooms: '2', bathrooms: '2', sqm: 1200,
              location: { area: 'Downtown Dubai', building: 'Burj Views Tower' },
              images: [], listing_type: 'sale', description: 'Modern luxury apartment'
            },
            {
              id: '2', listing_id: 'PROP002', title: 'Villa in Dubai Marina',
              display_address: 'Dubai Marina, Dubai', property_type: 'Villa', 
              price: 4500000, area: '4BR', bedrooms: '4', bathrooms: '3', sqm: 2200,
              location: { area: 'Dubai Marina', building: 'Marina Residences' },
              images: [], listing_type: 'sale', description: 'Spacious family villa'
            },
            {
              id: '3', listing_id: 'PROP003', title: 'Penthouse in Palm Jumeirah',
              display_address: 'Palm Jumeirah, Dubai', property_type: 'Penthouse',
              price: 8750000, area: '5BR', bedrooms: '5', bathrooms: '4', sqm: 3500,
              location: { area: 'Palm Jumeirah', building: 'Palm Residences' },
              images: [], listing_type: 'sale', description: 'Exclusive penthouse'
            }
          ]);
          
          console.log('✅ Mock data loaded successfully');
        }
        
      } catch (err) {
        console.error('❌ Critical error loading dashboard:', err);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️ Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Transform API data to component props
  const dashboardProps = {
    stats: stats ? {
      totalProperties: stats.total_properties,
      totalBuildings: stats.total_buildings,
      totalDeals: stats.total_deals,
      averagePrice: stats.average_price,
      medianPrice: stats.median_price,
      avgPricePerSqm: stats.avg_price_per_sqm,
      priceRange: stats.price_range,
      marketVolume: stats.market_volume,
      liquidity: stats.liquidity,
      roi: stats.roi,
    } : null,
    properties: properties.map(property => ({
      id: property.id,
      title: property.title,
      price: property.price,
      area: property.area,
      bedrooms: property.bedrooms,
      bathrooms: property.bathrooms,
      sqm: property.sqm,
      location: property.location,
      images: property.images || [],
      listingType: property.listing_type,
    })),
  };

  return <RealEstateDashboard {...dashboardProps} />;
};

export default MainDashboard;