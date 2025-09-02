import React, { useState } from "react";
import { Card, Collapse, Segmented, DatePicker, Progress, Row, Col, Tag, Space, Divider } from "antd";
import type { Dayjs } from 'dayjs';
import CustomButton from "@/components/CustomButton/CustomButton";
import CustomSelect from "@/components/CustomSelect/CustomSelect";
import CustomTabs from "@/components/CustomTabs/CustomTabs";
import SegmentedGroup from "@/components/Segmented/SegmentedGroup";
import FiltersBar from "@/components/Analytics/FiltersBar";
import OverviewCard from "@/components/Analytics/OverviewCard";
import ChartCard from "@/components/Analytics/ChartCard";
// CollapseCard оставлен на будущее (Liquidity/ROI)
import KpiBadge from "@/components/KPI/KpiBadge";
import TransactionsTable from "@/components/Transactions/TransactionsTable";
import CustomInput from "@/components/CustomInput/CustomInput";
import { SearchOutlined, FilterOutlined, DownloadOutlined, BarChartOutlined, LineChartOutlined, PieChartOutlined } from "@ant-design/icons";
import styles from "./Analytics.module.scss";

// Chart components
import LineChart from "@/components/Charts/LineChart";
import PieChart from "@/components/Charts/PieChart";
import BarChart from "@/components/Charts/BarChart";
import { 
  pricesTrendData, 
  buildingsByDistrictsData, 
  apartmentTypesData, 
  constructionStatusData,
  avgPricePerSqmData,
  roiData
} from "@/utils/mockChartData";

// replaced Select with CustomSelect; Option not used
const { Panel } = Collapse;
const { RangePicker } = DatePicker;

// ✅ ИСПРАВЛЕНО: Перенесено определение типа выше для использования в состоянии
type TableRow = {
    key: string;
    area: string;
    project: string;
    building: string;
    price: string;
    deals: number;
    volume: string;
    status: string;
    trend: string;
};

const Analytics: React.FC = () => {
    const [selectedArea, setSelectedArea] = useState<string>("all");
    const [selectedProject, setSelectedProject] = useState<string>("all");
    const [selectedBuilding, setSelectedBuilding] = useState<string>("all");
    const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
    const [searchText, setSearchText] = useState<string>("");
    const [activeTab, setActiveTab] = useState<string>("overview");
    const [catalogMode, setCatalogMode] = useState<string>("developer");
    const [salesMode, setSalesMode] = useState<string>("sales");
    
    // ✅ ИСПРАВЛЕНО: Сначала объявляем tableData, затем используем в useState
    // Моковые данные для таблицы
    const tableData: TableRow[] = [
        {
            key: "1",
            area: "Downtown Dubai",
            project: "Burj Khalifa",
            building: "Tower A",
            price: "$2,500/m²",
            deals: 45,
            volume: "$12.5M",
            status: "active",
            trend: "up",
        },
        {
            key: "2",
            area: "Palm Jumeirah",
            project: "Palm Tower",
            building: "Tower B",
            price: "$3,200/m²",
            deals: 32,
            volume: "$8.9M",
            status: "pending",
            trend: "stable",
        },
        {
            key: "3",
            area: "Dubai Marina",
            project: "Marina Heights",
            building: "Tower C",
            price: "$2,800/m²",
            deals: 67,
            volume: "$18.7M",
            status: "active",
            trend: "up",
        },
    ];

    // ✅ ДОБАВЛЕНО: состояния для обновления графиков при применении фильтров (после объявления tableData)
    const [filteredData, setFilteredData] = useState<TableRow[]>(tableData);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [appliedFilters, setAppliedFilters] = useState<string[]>([]);
    const [chartData, setChartData] = useState({
        buildingsData: buildingsByDistrictsData,
        apartmentData: apartmentTypesData,
        constructionData: constructionStatusData,
        priceData: avgPricePerSqmData,
        trendsData: pricesTrendData,
        roiData: roiData
    });

    // columns оставлены для будущего использования с Ant Table, сейчас не используются
    // Колонки AntTable больше не нужны (используем свой компонент таблицы)

    const handleFilterApply = async () => {
        console.log("🔄 Filters applied:", { selectedArea, selectedProject, selectedBuilding, dateRange, searchText });
        setIsLoading(true);
        
        try {
            // ✅ ИСПРАВЛЕНО: Теперь реально применяем фильтры к данным
            const newFilteredData = tableData.filter(item => {
                let matches = true;
                
                if (selectedArea !== "all" && item.area !== selectedArea) matches = false;
                if (selectedProject !== "all" && item.project !== selectedProject) matches = false;  
                if (selectedBuilding !== "all" && item.building !== selectedBuilding) matches = false;
                if (searchText && !item.project.toLowerCase().includes(searchText.toLowerCase())) matches = false;
                
                return matches;
            });
            
            console.log(`✅ Found ${newFilteredData.length} items after filtering`);
            
            // ✅ ДОБАВЛЕНО: обновляем состояние с фильтрованными данными
            setFilteredData(newFilteredData);
            
            // ✅ ДОБАВЛЕНО: создаем список активных фильтров для визуального отображения
            const activeFilters = [];
            if (selectedArea !== "all") activeFilters.push(`Area: ${selectedArea}`);
            if (selectedProject !== "all") activeFilters.push(`Project: ${selectedProject}`);
            if (selectedBuilding !== "all") activeFilters.push(`Building: ${selectedBuilding}`);
            if (searchText) activeFilters.push(`Search: "${searchText}"`);
            if (dateRange && dateRange[0] && dateRange[1]) {
                activeFilters.push(`Date: ${dateRange[0].format('DD/MM')} - ${dateRange[1].format('DD/MM')}`);
            }
            
            setAppliedFilters(activeFilters);
            
            // ✅ ДОБАВЛЕНО: Перерисовка графиков с новыми данными на базе фильтров
            console.log("📊 Updating charts with filtered data...");
            
            // Имитируем загрузку данных (в реальности будет API вызов)
            await new Promise(resolve => setTimeout(resolve, 800));
            
            // Обновляем данные графиков на основе фильтров
            const updatedChartData = updateChartsBasedOnFilters(newFilteredData);
            
            setChartData(updatedChartData);
            console.log("✅ Charts updated with filtered data!");
            
        } catch (error) {
            console.error('❌ Error applying filters:', error);
        } finally {
            setIsLoading(false);
        }
    };
    
    // ✅ ДОБАВЛЕНО: Функция для обновления данных графиков на основе фильтров
    const updateChartsBasedOnFilters = (filteredData: TableRow[]) => {
        // В реальном приложении здесь будут настоящие вычисления на основе отфильтрованных данных
        // Сейчас имитируем изменение данных для демонстрации функциональности
        
        const dataMultiplier = filteredData.length / tableData.length; // коэффициент для масштабирования данных
        
        return {
            buildingsData: {
                ...buildingsByDistrictsData,
                data: buildingsByDistrictsData.data.map(val => Math.round(val * dataMultiplier))
            },
            apartmentData: {
                ...apartmentTypesData,
                data: apartmentTypesData.data.map(val => Math.round(val * dataMultiplier))
            },
            constructionData: {
                ...constructionStatusData,
                data: constructionStatusData.data.map(val => Math.round(val * dataMultiplier))
            },
            priceData: {
                ...avgPricePerSqmData,
                data: avgPricePerSqmData.data.map(val => Math.round(val * (0.8 + dataMultiplier * 0.4))) // цены меняются по-другому
            },
            trendsData: {
                ...pricesTrendData,
                data: pricesTrendData.data.map(val => Math.round(val * (0.9 + dataMultiplier * 0.2)))
            },
            roiData: {
                ...roiData,
                data: roiData.data.map(val => Math.round(val * (0.7 + dataMultiplier * 0.6)))
            }
        };
    };

    const handleExportData = () => {
        console.log("Exporting data...");
    };

    return (
        <div className={styles.analyticsContainer}>
            <div className={styles.headerBar}>
                <div>
                    <h1>📊 Analytics Dashboard</h1>
                    <p>Comprehensive real estate market analysis for Dubai</p>
                </div>
                <Space>
                    <CustomButton icon={<DownloadOutlined />} onClick={handleExportData}>
                        Export Data
                    </CustomButton>
                    <CustomButton type="primary" icon={<BarChartOutlined />}>
                        Generate Report
                    </CustomButton>
                </Space>
            </div>

            {/* Top search line: Building / Districts / Developer / Naming + select + Search */}
            <FiltersBar
                mode={catalogMode}
                onModeChange={(v)=>setCatalogMode(v)}
                selectSlot={
                    <CustomSelect
                        className={styles.select}
                        placeholder="Select value"
                        value={selectedProject}
                        onChange={setSelectedProject}
                        options={[{ value: "all", label: "All" }, { value: "option1", label: "Option 1" }, { value: "option2", label: "Option 2" }]}
                    />
                }
                onSearch={handleFilterApply}
            />

            {/* Applied Filters Indicators */}
            {appliedFilters.length > 0 && (
                <Card className={styles.appliedFiltersCard} size="small">
                    <Space wrap>
                        <span>🔍 Active Filters:</span>
                        {appliedFilters.map((filter, index) => (
                            <Tag key={index} color="blue" closable onClose={() => {
                                // TODO: Remove specific filter
                            }}>
                                {filter}
                            </Tag>
                        ))}
                        <CustomButton size="small" onClick={() => {
                            setSelectedArea("all");
                            setSelectedProject("all");
                            setSelectedBuilding("all");
                            setDateRange(null);
                            setSearchText("");
                            setAppliedFilters([]);
                            setFilteredData(tableData);
                        }}>
                            Clear All
                        </CustomButton>
                    </Space>
                </Card>
            )}

            {/* Advanced Filters Section */}
            <Card title={<><FilterOutlined /> Advanced Filters {isLoading && <span>⏳</span>}</>} className={styles.filtersCard}>
                <Row gutter={[16, 16]} align="middle">
                    <Col span={6}>
                        <Segmented
                            className={styles.segmented}
                            options={[
                                { label: "All Areas", value: "all" },
                                { label: "Downtown", value: "downtown" },
                                { label: "Marina", value: "marina" },
                                { label: "Palm", value: "palm" },
                            ]}
                            value={selectedArea}
                            onChange={(value) => setSelectedArea(value as string)}
                        />
                    </Col>
                    <Col span={6}>
                        <CustomSelect
                            className={styles.select}
                            placeholder="Select Project"
                            value={selectedProject}
                            onChange={setSelectedProject}
                            showSearch
                            options={[
                                { value: "all", label: "All Projects" },
                                { value: "burj", label: "Burj Khalifa" },
                                { value: "palm", label: "Palm Tower" },
                                { value: "marina", label: "Marina Heights" },
                            ]}
                        />
                    </Col>
                    <Col span={6}>
                        <CustomSelect
                            className={styles.select}
                            placeholder="Select Building"
                            value={selectedBuilding}
                            onChange={setSelectedBuilding}
                            showSearch
                            options={[
                                { value: "all", label: "All Buildings" },
                                { value: "tower-a", label: "Tower A" },
                                { value: "tower-b", label: "Tower B" },
                                { value: "tower-c", label: "Tower C" },
                            ]}
                        />
                    </Col>
                    <Col span={6}>
                        <RangePicker
                            value={dateRange}
                            onChange={setDateRange}
                            className={styles.rangePicker}
                            placeholder={["Start Date", "End Date"]}
                        />
                    </Col>
                </Row>
                <Row gutter={[16, 16]} className={styles.filtersFooter}>
                    <Col span={12}>
                        <CustomInput
                            placeholder="Search properties, projects, or areas..."
                            prefix={<SearchOutlined />}
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            allowClear
                        />
                    </Col>
                    <Col span={12}>
                        <Space>
                            <CustomButton 
                                type="primary" 
                                onClick={handleFilterApply}
                                loading={isLoading}
                            >
                                {isLoading ? 'Applying...' : 'Apply Filters'}
                            </CustomButton>
                            <CustomButton onClick={() => {
                                setSelectedArea("all");
                                setSelectedProject("all");
                                setSelectedBuilding("all");
                                setDateRange(null);
                                setSearchText("");
                                setAppliedFilters([]);
                                setFilteredData(tableData);
                                setChartData({
                                    buildingsData: buildingsByDistrictsData,
                                    apartmentData: apartmentTypesData,
                                    constructionData: constructionStatusData,
                                    priceData: avgPricePerSqmData,
                                    trendsData: pricesTrendData,
                                    roiData: roiData
                                });
                            }}>
                                Clear All
                            </CustomButton>
                        </Space>
                    </Col>
                </Row>
            </Card>

            {/* Developer Analytics section */}
            <Divider />
            <h2>Developer Analytics</h2>
            <Row gutter={[16, 16]} className={styles.cardsRow}>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Distribution of buildings by districts" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <BarChart 
                            data={chartData.buildingsData.data} 
                            labels={chartData.buildingsData.labels}
                            color="#3B82F6"
                        />
                    </ChartCard>
                </Col>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Lots by apartment type" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <BarChart 
                            data={chartData.apartmentData.data} 
                            labels={chartData.apartmentData.labels}
                            color="#10B981"
                        />
                    </ChartCard>
                </Col>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Buildings commissioned/under construction" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <PieChart 
                            data={chartData.constructionData.data} 
                            labels={chartData.constructionData.labels}
                            colors={chartData.constructionData.colors}
                        />
                    </ChartCard>
                </Col>
            </Row>

            {/* More Analytics */}
            <Divider />
            <div className={styles.headerBar}>
                <h2>More Analytics</h2>
                <SegmentedGroup
                    options={[{label: 'Sales', value: 'sales'}, {label: 'Rental', value: 'rental'}]}
                    value={salesMode}
                    onChange={(v) => setSalesMode(v)}
                />
            </div>
            <Row gutter={[16, 16]} className={styles.cardsRow}>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Average price AED per sqm" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <LineChart 
                            data={chartData.priceData.data} 
                            labels={chartData.priceData.labels}
                            color="#F59E0B"
                            gradient={true}
                        />
                    </ChartCard>
                </Col>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Price Trends (Last 6 months)" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <LineChart 
                            data={chartData.trendsData.data} 
                            labels={chartData.trendsData.labels}
                            color="#8B5CF6"
                            gradient={true}
                        />
                    </ChartCard>
                </Col>
                <Col xs={24} lg={8}>
                    <ChartCard 
                        title="Average ROI %" 
                        extra={
                            <Space>
                                <Tag>DLD</Tag>
                                {appliedFilters.length > 0 && <Tag color="orange">Filtered</Tag>}
                            </Space>
                        }
                    >
                        <BarChart 
                            data={chartData.roiData.data} 
                            labels={chartData.roiData.labels}
                            color="#EF4444"
                        />
                    </ChartCard>
                </Col>
            </Row>

            {/* Tabs for different views */}
            <CustomTabs 
                activeKey={activeTab} 
                onChange={setActiveTab} 
                className={styles.tabs}
                items={[
                    {
                        key: "overview",
                        label: <span><BarChartOutlined />Overview</span>,
                        children: (
                            <Row gutter={[16, 16]} className={styles.cardsRow}>
                                <Col span={6}><OverviewCard title="Total Properties" value={15432} kpi={<KpiBadge value={12.5} />} /></Col>
                                <Col span={6}><OverviewCard title="Average Price" value={<><span>$</span>2850<span className={styles.valueBlue}>/m²</span></>} kpi={<KpiBadge value={8.3} />} /></Col>
                                <Col span={6}><OverviewCard title="Total Deals" value={2156} kpi={<KpiBadge value={18.5} />} /></Col>
                                <Col span={6}><OverviewCard title="Market Volume" value={<><span>$</span>82.5<span className={styles.valueBlue}>M</span></>} kpi={<KpiBadge value={20.7} />} /></Col>
                            </Row>
                        )
                    },
                    {
                        key: "transactions",
                        label: <span><LineChartOutlined />Transactions</span>,
                        children: (
                            /* Detailed Analysis */
                            <Collapse className={styles.expandable}>
                                <Panel header={
                                    <Space>
                                        Property Transactions Analysis
                                        {appliedFilters.length > 0 && <Tag color="blue">Showing {filteredData.length} of {tableData.length} records</Tag>}
                                    </Space>
                                } key="1">
                                    <div className={styles.tableContainer}>
                                        <TransactionsTable rows={filteredData.map(r => ({
                                            key: r.key,
                                            date: '18 Dec, 2024',
                                            location: `${r.project}, ${r.area}`,
                                            rooms: '4 Rooms',
                                            sqm: 125,
                                            price: '2,374,238',
                                        }))} />
                                    </div>
                                </Panel>
                            </Collapse>
                        )
                    },
                    {
                        key: "insights",
                        label: <span><PieChartOutlined />Insights</span>,
                        children: (
                            <Collapse className={styles.expandable}>
                                <Panel header="Market Trends & Insights" key="2">
                                    <Row gutter={[16, 16]}>
                                        <Col span={12}>
                                            <Card title="Market Performance by Area">
                                                <div className={styles.p16}>
                                                    <h4>Key Market Insights:</h4>
                                                    <ul>
                                                        <li>Downtown Dubai continues to lead in property values</li>
                                                        <li>Marina area shows highest transaction volume</li>
                                                        <li>Palm Jumeirah maintains premium positioning</li>
                                                        <li>Overall market shows strong recovery post-pandemic</li>
                                                    </ul>
                                                </div>
                                            </Card>
                                        </Col>
                                        <Col span={12}>
                                            <Card title="Growth Metrics">
                                                <div className={styles.p16}>
                                                    <Space direction="vertical" className={styles.w100}>
                                                        <div>
                                                            <span>Price Growth: </span>
                                                            <Progress percent={75} status="active" />
                                                        </div>
                                                        <div>
                                                            <span>Transaction Volume: </span>
                                                            <Progress percent={85} status="active" />
                                                        </div>
                                                        <div>
                                                            <span>Market Liquidity: </span>
                                                            <Progress percent={60} status="active" />
            </div>
                                                    </Space>
        </div>
                                            </Card>
                                        </Col>
                                    </Row>
                                </Panel>
                            </Collapse>
                        )
                    }
                ]}
            />
        </div>
    );
};

export default Analytics;
