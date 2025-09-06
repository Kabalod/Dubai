import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';

interface Transaction {
    key: React.Key;
    date: string;
    location: string;
    rooms: string;
    sqm: number | string;
    price: string;
}

interface TransactionsTableProps {
    rows?: Transaction[];
    onLoadMore?: () => void;
}

const TransactionsTable: React.FC<TransactionsTableProps> = ({ rows: propRows, onLoadMore }) => {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [displayCount, setDisplayCount] = useState(5);
    const [loadingMore, setLoadingMore] = useState(false);

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                setLoading(true);
                console.log('📊 Fetching transactions from API...');
                
                const response = await apiService.getProperties({ limit: 20 });
                const properties = response.results || response;
                
                // Конвертируем properties в transactions format
                const transactionsData: Transaction[] = properties.map((prop: any, index: number) => ({
                    key: prop.id || index,
                    date: new Date(prop.added_on || Date.now()).toISOString().split('T')[0],
                    location: prop.display_address || 'Unknown Location',
                    rooms: prop.bedrooms || 'N/A',
                    sqm: prop.numeric_area || 'N/A',
                    price: prop.price?.toLocaleString() || 'N/A'
                }));
                
                setTransactions(transactionsData);
                console.log('✅ Transactions loaded:', transactionsData.length);
                
            } catch (error) {
                console.warn('⚠️ API unavailable, using empty state:', error);
                setTransactions([]); // Empty state instead of mock data
            } finally {
                setLoading(false);
            }
        };

        // Use prop rows if provided, otherwise fetch from API
        if (propRows) {
            setTransactions(propRows);
            setLoading(false);
        } else {
            fetchTransactions();
        }
    }, [propRows]);

    const handleShowMore = async () => {
        setLoadingMore(true);
        console.log('🔄 Loading more transactions...');
        
        // Симуляция загрузки
        setTimeout(() => {
            setDisplayCount(prev => prev + 5);
            setLoadingMore(false);
            console.log('✅ Loaded more transactions');
            
            // Вызываем callback если есть
            if (onLoadMore) {
                onLoadMore();
            }
        }, 500);
    };
    
    if (loading) {
        return (
            <div className="text-center py-8">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-gray-600">Loading transactions...</p>
            </div>
        );
    }

    const displayedRows = transactions.slice(0, displayCount);
    const hasMore = displayCount < transactions.length;

    return (
        <div className="space-y-3">
            <table className="w-full">
                <thead>
                    <tr className="text-left text-sm text-[#6b7280]">
                        <th className="py-2">Date</th>
                        <th className="py-2">Location</th>
                        <th className="py-2">Rooms</th>
                        <th className="py-2">M²</th>
                        <th className="py-2">Price, AED</th>
                        <th className="py-2"></th>
                    </tr>
                </thead>
                <tbody>
                    {displayedRows.map((r) => (
                        <tr key={r.key} className="border-t">
                            <td className="py-3">{r.date}</td>
                            <td className="py-3">{r.location}</td>
                            <td className="py-3">{r.rooms}</td>
                            <td className="py-3">{r.sqm}</td>
                            <td className="py-3 font-medium">{r.price}</td>
                            <td className="py-3 text-right">
                                <button 
                                    className="px-3 py-1 border rounded-md hover:bg-gray-50 transition-colors"
                                    onClick={() => console.log('Details clicked for:', r.key)}
                                >
                                    Details
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            {/* Show more button with loading state */}
            {hasMore && (
                <div className="text-center">
                    <button 
                        className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={handleShowMore}
                        disabled={loadingMore}
                    >
                        {loadingMore ? (
                            <span className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                Loading...
                            </span>
                        ) : (
                            `Show more (${transactions.length - displayCount} remaining)`
                        )}
                    </button>
                </div>
            )}
            
            {/* Show count info */}
            <div className="text-center text-sm text-gray-500">
                Showing {displayedRows.length} of {transactions.length} transactions
            </div>

            {/* Empty state */}
            {transactions.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    <p>No transactions available</p>
                    <p className="text-sm">Connect to backend API to load real data</p>
                </div>
            )}
        </div>
    );
};

export default TransactionsTable;