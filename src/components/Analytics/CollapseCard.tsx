import React, { useState } from 'react';

interface CollapseCardProps {
    title: string;
    children?: React.ReactNode;
}

const CollapseCard: React.FC<CollapseCardProps> = ({ title, children }) => {
    const [open, setOpen] = useState(true);
    return (
        <div className="bg-white rounded-xl shadow overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b">
                <div className="text-sm font-medium">{title}</div>
                <button type="button" className="text-sm text-[#6b7280]" onClick={() => setOpen((v) => !v)}>
                    {open ? 'Hide' : 'Show'}
                </button>
            </div>
            {open && <div className="p-4">{children}</div>}
        </div>
    );
};

export default CollapseCard;


