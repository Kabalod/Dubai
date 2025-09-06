// API client for Dubai MVP
// Единый источник базового URL бекенда
import { API_BASE_URL } from '../config';

// Префикс API для всех запросов
const API_PREFIX = `${API_BASE_URL}/api`;

// Types
export interface Property {
  id: string;
  listing_id: string;
  title: string;
  description?: string;
  display_address: string;
  property_type: string;
  price: number;
  price_currency?: string;
  price_duration?: string;
  area: string;
  bedrooms: string | null; // Backend возвращает CharField - может быть строкой
  bathrooms: string | null;
  sqm: number;
  numeric_area?: number;
  location: {
    area: string;
    building: string;
    floor?: string;
  };
  images?: string[];
  listing_type: 'sale' | 'rent';
  created_at?: string;
  added_on?: string;
  area_name?: string;
  building_name?: string;
  furnishing?: string;
  broker?: string;
  agent?: string;
  agent_phone?: string;
  verified?: boolean;
  latitude?: number;
  longitude?: number;
  url?: string;
}

export interface Area {
  id: number;
  name: string;
  name_en: string;
  properties_count: number;
}

export interface PropertyStats {
  total_properties: number;
  total_buildings: number;
  total_deals: number;
  average_price: number;
  median_price: number;
  avg_price_per_sqm: number;
  price_range: {
    min: number;
    max: number;
  };
  market_volume: {
    deals: number;
    total_volume: number;
  };
  liquidity: number;
  roi: number;
}

export interface PropertyFilters {
  search?: string;
  property_type?: string;
  bedrooms?: string; // Backend ожидает строку
  area?: string;
  min_price?: number;
  max_price?: number;
  listing_type?: 'sale' | 'rent';
  limit?: number;
  offset?: number;
}

// API functions
export const api = {
  // Properties API
  async getProperties(filters: PropertyFilters = {}): Promise<{ results: Property[], count: number }> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${API_PREFIX}/properties/?${params}`);
    if (!response.ok) throw new Error('Failed to fetch properties');
    return response.json();
  },

  async getPropertyDetail(listingId: string): Promise<Property> {
    const response = await fetch(`${API_PREFIX}/properties/${listingId}/`);
    if (!response.ok) throw new Error('Failed to fetch property detail');
    return response.json();
  },

  // Areas API
  async getAreas(): Promise<Area[]> {
    const response = await fetch(`${API_PREFIX}/areas/`);
    if (!response.ok) throw new Error('Failed to fetch areas');
    return response.json();
  },

  // Stats API
  async getStats(): Promise<PropertyStats> {
    const response = await fetch(`${API_PREFIX}/stats/`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_PREFIX}/health/`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },

  // User Profile API
  async getUserProfile(token: string): Promise<any> {
    const response = await fetch(`${API_PREFIX}/profile/me/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) throw new Error('Failed to fetch user profile');
    return response.json();
  },

  // Payment API (mock)
  async createPayment(paymentData: any, token: string): Promise<{ success: boolean, message: string }> {
    const response = await fetch(`${API_PREFIX}/payments/create/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(paymentData)
    });
    
    if (!response.ok) {
      // Mock success response for demo
      return { success: true, message: 'Demo payment processed successfully!' };
    }
    return response.json();
  }
};
