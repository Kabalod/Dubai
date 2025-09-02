import React from 'react';
import classNames from 'classnames';
import { Card, Tag, Space, Statistic, Row, Col, Avatar, Tooltip } from 'antd';
import { EnvironmentOutlined, DollarOutlined, EyeOutlined, HeartOutlined, ShareAltOutlined, PhoneOutlined } from '@ant-design/icons';
import CustomButton from "@/components/CustomButton/CustomButton";
import styles from "./PropertyCard.module.scss";

export interface PropertyData {
    id: string | number;
    title: string;
    price: number;
    location: string;
    type: 'Villa' | 'Apartment' | 'Office' | 'Land';
    status: 'Active' | 'Sold' | 'Pending' | 'Rented';
    bedrooms?: number;
    bathrooms?: number;
    area: number;
    areaUnit: 'sqm' | 'sqft';
    images: string[];
    views: number;
    inquiries: number;
    featured?: boolean;
    description?: string;
    amenities?: string[];
    agent?: {
        name: string;
        avatar: string;
        phone: string;
        rating: number;
    };
}

interface PropertyCardProps {
    data: PropertyData;
    onView?: (id: string | number) => void;
    onEdit?: (id: string | number) => void;
    onFavorite?: (id: string | number) => void;
    onShare?: (id: string | number) => void;
    onContact?: (id: string | number) => void;
    size?: 'small' | 'default' | 'large';
    showActions?: boolean;
    showStats?: boolean;
    showAgent?: boolean;
}

const PropertyCard: React.FC<PropertyCardProps> = ({
    data,
    onView,
    onEdit,
    onFavorite,
    onShare,
    onContact,
    size = 'default',
    showActions = true,
    showStats = true,
    showAgent = true,
}) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Active': return 'green';
            case 'Sold': return 'red';
            case 'Pending': return 'orange';
            case 'Rented': return 'blue';
            default: return 'default';
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'Villa': return 'purple';
            case 'Apartment': return 'blue';
            case 'Office': return 'orange';
            case 'Land': return 'green';
            default: return 'default';
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'Villa': return '🏠';
            case 'Apartment': return '🏢';
            case 'Office': return '🏢';
            case 'Land': return '🌍';
            default: return '🏠';
        }
    };

    const formatPrice = (price: number) => {
        if (price >= 1000000) {
            return `${(price / 1000000).toFixed(1)}M AED`;
        } else if (price >= 1000) {
            return `${(price / 1000).toFixed(0)}K AED`;
        }
        return `${price.toLocaleString()} AED`;
    };

    const formatArea = (area: number, unit: string) => {
        return `${area.toLocaleString()} ${unit}`;
    };

    const handleView = () => {
        onView?.(data.id);
    };

    const handleEdit = () => {
        onEdit?.(data.id);
    };

    const handleFavorite = () => {
        onFavorite?.(data.id);
    };

    const handleShare = () => {
        onShare?.(data.id);
    };

    const handleContact = () => {
        onContact?.(data.id);
    };

    const cardWidthClass = size === 'small' ? styles.card_small : size === 'large' ? styles.card_large : styles.card_default;
    const imgHeightClass = size === 'small' ? styles.img_small : size === 'large' ? styles.img_large : styles.img_default;

    return (
        <Card
            hoverable
            className={classNames(styles.card, cardWidthClass)}
            cover={
                <div className={styles.cover}>
                    <img
                        alt={data.title}
                        src={data.images[0] || 'https://via.placeholder.com/400x250?text=Property+Image'}
                        className={classNames(styles.img, imgHeightClass)}
                    />
                    {data.featured && (
                        <Tag color="gold" className={styles.featuredTag}>⭐ Featured</Tag>
                    )}
                    <Tag color={getStatusColor(data.status)} className={styles.statusTag}>
                        {data.status}
                    </Tag>
                </div>
            }
            actions={
                showActions ? [
                    <Tooltip title="View Details">
                        <CustomButton variant="link" icon={<EyeOutlined />} onClick={handleView} />
                    </Tooltip>,
                    <Tooltip title="Add to Favorites">
                        <CustomButton variant="link" icon={<HeartOutlined />} onClick={handleFavorite} />
                    </Tooltip>,
                    <Tooltip title="Share">
                        <CustomButton variant="link" icon={<ShareAltOutlined />} onClick={handleShare} />
                    </Tooltip>,
                    <Tooltip title="Contact Agent">
                        <CustomButton variant="link" icon={<PhoneOutlined />} onClick={handleContact} />
                    </Tooltip>,
                ] : undefined
            }
        >
            <div className={styles.body}>
                <div className={styles.topRow}>
                    <div className={styles.topMeta}>
                        <Tag color={getTypeColor(data.type)} icon={<span>{getTypeIcon(data.type)}</span>}>
                            {data.type}
                        </Tag>
                        <span className={styles.id}>ID: {data.id}</span>
                    </div>
                    <h3 className={styles.title}>{data.title}</h3>
                </div>

                <div className={styles.location}>
                    <Space>
                        <EnvironmentOutlined className={styles.locationIcon} />
                        <span className={styles.locationText}>{data.location}</span>
                    </Space>
                </div>

                <div className={styles.price}>
                    <Statistic
                        value={data.price}
                        prefix={<DollarOutlined />}
                        suffix="AED"
                        className={styles.statPrimary}
                    />
                </div>

                <Row gutter={16} className={styles.features}>
                    {data.bedrooms && (
                        <Col span={8}>
                            <div className={styles.featureBox}>
                                <div className={styles.featureValue}>{data.bedrooms}</div>
                                <div className={styles.featureLabel}>Bedrooms</div>
                            </div>
                        </Col>
                    )}
                    {data.bathrooms && (
                        <Col span={8}>
                            <div className={styles.featureBox}>
                                <div className={classNames(styles.featureValue, styles.featureValueAlt)}>{data.bathrooms}</div>
                                <div className={styles.featureLabel}>Bathrooms</div>
                            </div>
                        </Col>
                    )}
                    <Col span={data.bedrooms ? 8 : 12}>
                        <div className={styles.featureBox}>
                            <div className={styles.featureValue}>{formatArea(data.area, data.areaUnit)}</div>
                            <div className={styles.featureLabel}>Area</div>
                        </div>
                    </Col>
                </Row>

                {showStats && (
                    <Row gutter={16} className={styles.stats}>
                        <Col span={12}>
                            <div className={styles.statBlock}>
                                <div className={styles.statNumber}>{data.views}</div>
                                <div className={styles.statLabel}>Views</div>
                            </div>
                        </Col>
                        <Col span={12}>
                            <div className={styles.statBlock}>
                                <div className={classNames(styles.statNumber, styles.statNumberAlt)}>{data.inquiries}</div>
                                <div className={styles.statLabel}>Inquiries</div>
                            </div>
                        </Col>
                    </Row>
                )}

                {showAgent && data.agent && (
                    <div className={styles.agent}>
                        <div className={styles.agentInfo}>
                            <Avatar src={data.agent.avatar} size={32} className={styles.agentAvatar} />
                            <div>
                                <div className={styles.agentName}>{data.agent.name}</div>
                                <div className={styles.agentRating}>⭐ {data.agent.rating}/5</div>
                            </div>
                        </div>
                        <CustomButton size="small" onClick={handleContact}>Contact</CustomButton>
                    </div>
                )}

                {showActions && (
                    <div className={styles.actions}>
                        <CustomButton type="primary" block onClick={handleView}>
                            View Details
                        </CustomButton>
                        {onEdit && (
                            <CustomButton onClick={handleEdit}>Edit</CustomButton>
                        )}
                    </div>
                )}
            </div>
        </Card>
    );
};

export default PropertyCard;
