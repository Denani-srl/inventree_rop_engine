import { useEffect, useState } from 'react';
import { Alert, Badge, Card, Group, LoadingOverlay, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { IconAlertTriangle, IconChartLine, IconTrendingUp } from '@tabler/icons-react';

// Import for type checking
import { checkPluginVersion, type InvenTreePluginContext } from '@inventreedb/ui';

interface ROPApiResponse {
    part_id: number;
    part_name?: string;
    has_policy: boolean;
    message?: string;
    current_stock?: number;
    on_order?: number;
    policy?: {
        enabled: boolean;
        safety_stock: number;
        use_calculated_safety_stock: boolean;
        service_level: number;
        target_stock_multiplier: number;
        last_calculated_rop: number | null;
        last_calculated_demand_rate: number | null;
        last_calculation_date: string | null;
    };
    demand_statistics?: {
        mean_daily_demand: number;
        std_dev_daily_demand: number;
        total_removals: number;
        analysis_period_days: number;
        calculated_safety_stock: number | null;
        calculation_date: string;
    };
    suggestion?: {
        id: number;
        suggested_order_qty: number;
        projected_stock: number;
        calculated_rop: number;
        urgency_score: number;
        days_until_stockout: number | null;
        stockout_date: string | null;
        created_date: string;
    };
}

/**
 * Render ROP Analysis Panel on Part Detail Page
 */
function ROPAnalysisPanel({
    context
}: {
    context: InvenTreePluginContext;
}) {
    const [ropData, setRopData] = useState<ROPApiResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const apiUrl = context.context?.api_url;
    const partId = context.context?.part_id;

    useEffect(() => {
        if (!apiUrl || !partId) {
            setError('Configuration error: Missing API URL or Part ID');
            setLoading(false);
            return;
        }

        // Fetch ROP details for this part
        fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                setRopData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching ROP details:', err);
                setError(`Failed to load ROP data: ${err.message}`);
                setLoading(false);
            });
    }, [apiUrl, partId]);

    const getUrgencyColor = (score: number): string => {
        if (score >= 80) return 'red';
        if (score >= 60) return 'orange';
        if (score >= 40) return 'yellow';
        return 'green';
    };

    if (loading) {
        return (
            <div style={{ position: 'relative', minHeight: 200 }}>
                <LoadingOverlay visible={true} />
                <Text ta="center" mt="xl">Loading ROP analysis...</Text>
            </div>
        );
    }

    if (error) {
        return (
            <Alert icon={<IconAlertTriangle size="1rem" />} title="Error" color="red">
                {error}
            </Alert>
        );
    }

    if (!ropData || !ropData.has_policy) {
        return (
            <Alert icon={<IconAlertTriangle size="1rem" />} title="No ROP Policy" color="yellow">
                <Text>{ropData?.message || 'No ROP policy configured for this part.'}</Text>
            </Alert>
        );
    }

    const policy = ropData.policy;
    const stats = ropData.demand_statistics;
    const suggestion = ropData.suggestion;

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Title order={3}>
                    <IconChartLine size="1.5rem" style={{ marginRight: 8, verticalAlign: 'middle' }} />
                    Reorder Point Analysis
                </Title>
                {suggestion && (
                    <Badge size="lg" color={getUrgencyColor(suggestion.urgency_score)}>
                        Urgency: {Math.round(suggestion.urgency_score)}
                    </Badge>
                )}
            </Group>

            <SimpleGrid cols={2} spacing="md">
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Current Stock</Text>
                    <Text size="xl" fw={700}>{Math.round(ropData.current_stock || 0)}</Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Reorder Point (ROP)</Text>
                    <Text size="xl" fw={700} c="blue">
                        {policy?.last_calculated_rop != null ? Math.round(policy.last_calculated_rop) : 'Not calculated'}
                    </Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Safety Stock</Text>
                    <Text size="xl" fw={700}>
                        {policy?.use_calculated_safety_stock && stats?.calculated_safety_stock != null
                            ? Math.round(stats.calculated_safety_stock)
                            : Math.round(policy?.safety_stock || 0)}
                    </Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">On Order</Text>
                    <Text size="xl" fw={700}>{Math.round(ropData.on_order || 0)}</Text>
                </Card>
            </SimpleGrid>

            {stats && (
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="sm">
                        <Group justify="space-between">
                            <Text fw={600}>Demand Analysis</Text>
                            <IconTrendingUp size="1.2rem" />
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Daily Demand Rate:</Text>
                            <Text fw={600}>{stats.mean_daily_demand.toFixed(2)} units/day</Text>
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Demand Std Dev:</Text>
                            <Text fw={600}>{stats.std_dev_daily_demand.toFixed(2)}</Text>
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Analysis Period:</Text>
                            <Text fw={600}>{stats.analysis_period_days} days ({stats.total_removals} events)</Text>
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Service Level:</Text>
                            <Text fw={600}>{policy?.service_level}%</Text>
                        </Group>
                    </Stack>
                </Card>
            )}

            {suggestion && (
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="sm">
                        <Group justify="space-between">
                            <Text fw={600}>Active Suggestion</Text>
                            <Badge color={getUrgencyColor(suggestion.urgency_score)}>
                                Score: {Math.round(suggestion.urgency_score)}
                            </Badge>
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Suggested Order Qty:</Text>
                            <Text fw={700} c="green">{Math.round(suggestion.suggested_order_qty)}</Text>
                        </Group>

                        <Group justify="space-between">
                            <Text size="sm">Projected Stock:</Text>
                            <Text fw={600}>{Math.round(suggestion.projected_stock)}</Text>
                        </Group>

                        {suggestion.days_until_stockout != null && (
                            <Group justify="space-between">
                                <Text size="sm">Days Until Stockout:</Text>
                                <Text
                                    fw={700}
                                    c={suggestion.days_until_stockout <= 7 ? 'red' : suggestion.days_until_stockout <= 14 ? 'orange' : 'green'}
                                >
                                    {suggestion.days_until_stockout <= 0 ? 'NOW' : `${Math.round(suggestion.days_until_stockout)} days`}
                                </Text>
                            </Group>
                        )}

                        {suggestion.stockout_date && (
                            <Group justify="space-between">
                                <Text size="sm">Stockout Date:</Text>
                                <Text fw={600}>{new Date(suggestion.stockout_date).toLocaleDateString()}</Text>
                            </Group>
                        )}
                    </Stack>
                </Card>
            )}

            {!suggestion && policy?.last_calculated_rop != null && (
                <Alert icon={<IconChartLine size="1rem" />} title="Stock Status" color="green">
                    <Text>Stock level is adequate. No reorder needed at this time.</Text>
                    {policy.last_calculation_date && (
                        <Text size="sm" c="dimmed" mt="xs">
                            Last calculated: {new Date(policy.last_calculation_date).toLocaleString()}
                        </Text>
                    )}
                </Alert>
            )}

            {!stats && !suggestion && (
                <Alert icon={<IconAlertTriangle size="1rem" />} title="No Data" color="gray">
                    <Text>No demand statistics yet. ROP calculations require stock movement history.</Text>
                </Alert>
            )}
        </Stack>
    );
}

// This is the function which is called by InvenTree to render the actual panel
export function renderROPAnalysisPanel(context: InvenTreePluginContext) {
    checkPluginVersion(context);
    return <ROPAnalysisPanel context={context} />;
}
