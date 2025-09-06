// Моковые данные для графиков
export const pricesTrendData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  data: [2200, 2350, 2150, 2400, 2550, 2650],
};

export const marketDistributionData = {
  labels: ['Apartments', 'Villas', 'Townhouses', 'Land', 'Commercial'],
  data: [45, 25, 15, 10, 5],
  colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
};

export const buildingsByDistrictsData = {
  labels: ['Downtown', 'Marina', 'JBR', 'Palm Jumeirah', 'Business Bay', 'DIFC'],
  data: [120, 98, 75, 45, 89, 67],
};

export const apartmentTypesData = {
  labels: ['Studio', '1 BR', '2 BR', '3 BR', '4+ BR'],
  data: [35, 180, 145, 95, 45],
};

export const constructionStatusData = {
  labels: ['Completed', 'Under Construction', 'Off-Plan'],
  data: [60, 25, 15],
  colors: ['#10B981', '#F59E0B', '#3B82F6'],
};

export const avgPricePerSqmData = {
  labels: ['Q1 2023', 'Q2 2023', 'Q3 2023', 'Q4 2023', 'Q1 2024', 'Q2 2024'],
  data: [1850, 1920, 1980, 2050, 2120, 2180],
};

export const roiData = {
  labels: ['Downtown', 'Marina', 'JBR', 'Business Bay', 'DIFC'],
  data: [6.2, 7.8, 5.5, 8.1, 6.9],
};

export const generateRandomData = (length: number, min: number = 1000, max: number = 3000): number[] => {
  return Array.from({ length }, () => Math.floor(Math.random() * (max - min + 1)) + min);
};

export const generateRandomLabels = (length: number, prefix: string = 'Item'): string[] => {
  return Array.from({ length }, (_, i) => `${prefix} ${i + 1}`);
};
