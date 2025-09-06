import { AggregationResultType } from "@/api/dto";

interface DashboardProps {
    data: AggregationResultType | null;
    isLoading: boolean;
}

interface DashboardState {
    data: AggregationResultType;
}
