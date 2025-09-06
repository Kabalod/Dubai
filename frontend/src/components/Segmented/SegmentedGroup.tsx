import React, { useState } from 'react';

export interface SegmentedOption {
    label: string;
    value: string;
}

interface SegmentedGroupProps {
    options: SegmentedOption[];
    value?: string;
    onChange?: (value: string) => void;
    className?: string;
}

const SegmentedGroup: React.FC<SegmentedGroupProps> = ({ options, value, onChange, className }) => {
    const [internal, setInternal] = useState<string>(value ?? options?.[0]?.value ?? '');

    const current = value ?? internal;

    const handleClick = (val: string) => {
        if (!value) setInternal(val);
        onChange?.(val);
    };

    return (
        <div className={`inline-flex rounded-full bg-[#f5f5f5] p-1 ${className || ''}`}>
            {options.map((opt) => (
                <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleClick(opt.value)}
                    className={`px-4 py-2 rounded-full text-sm transition-colors ${
                        current === opt.value ? 'bg-white shadow text-black' : 'text-[#666]'
                    }`}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    );
};

export default SegmentedGroup;


