import React from 'react';
import SegmentedGroup from '@/components/Segmented/SegmentedGroup';

interface FiltersBarProps {
    mode: string;
    onModeChange: (v: string) => void;
    selectSlot?: React.ReactNode;
    onSearch?: () => void;
}

const FiltersBar: React.FC<FiltersBarProps> = ({ mode, onModeChange, selectSlot, onSearch }) => {
    return (
        <div className="flex gap-3 items-center p-4 bg-white rounded-xl shadow">
            <div className="flex-1">
                <SegmentedGroup
                    options={[
                        { label: 'Building', value: 'building' },
                        { label: 'Districts', value: 'districts' },
                        { label: 'Developer', value: 'developer' },
                        { label: 'Naming', value: 'naming' },
                    ]}
                    value={mode}
                    onChange={onModeChange}
                />
            </div>
            <div className="w-[300px]">{selectSlot}</div>
            <button type="button" className="px-4 py-2 rounded-md bg-black text-white" onClick={onSearch}>Search</button>
        </div>
    );
};

export default FiltersBar;


