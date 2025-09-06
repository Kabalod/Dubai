import React from 'react';

interface OverviewCardProps {
    title: string;
    value: React.ReactNode;
    hint?: string;
    kpi?: React.ReactNode;
}

const OverviewCard: React.FC<OverviewCardProps> = ({ title, value, hint, kpi }) => {
    return (
        <div className="p-4 bg-white rounded-xl shadow">
            <div className="text-sm text-[#6b7280]">{title}</div>
            <div className="mt-3 text-2xl font-semibold flex items-center gap-2">
                {value}
                {kpi}
            </div>
            {hint && <div className="text-xs text-[#9ca3af] mt-1">{hint}</div>}
        </div>
    );
};

export default OverviewCard;


