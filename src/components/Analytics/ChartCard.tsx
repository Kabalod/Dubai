import React from 'react';

interface ChartCardProps {
    title: string;
    extra?: React.ReactNode;
    children?: React.ReactNode;
}

const ChartCard: React.FC<ChartCardProps> = ({ title, extra, children }) => {
    return (
        <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center justify-between text-sm text-[#6b7280]">
                <div>{title}</div>
                {extra}
            </div>
            <div className="h-[180px] mt-3 flex items-center justify-center text-[#9ca3af]">
                {children || 'Chart placeholder'}
            </div>
        </div>
    );
};

export default ChartCard;


