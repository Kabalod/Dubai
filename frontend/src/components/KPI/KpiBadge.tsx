import React from 'react';

interface KpiBadgeProps {
    value: number; // percentage (e.g., 12.5 => +12.5%)
}

const KpiBadge: React.FC<KpiBadgeProps> = ({ value }) => {
    const positive = value > 0;
    const zero = value === 0;
    const bg = zero ? 'bg-slate-100 text-slate-700' : positive ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700';
    const sign = zero ? '' : positive ? '+' : '';
    return (
        <span className={`px-2 py-1 rounded-full text-xs ${bg}`}>{`${sign}${value}%`}</span>
    );
};

export default KpiBadge;


