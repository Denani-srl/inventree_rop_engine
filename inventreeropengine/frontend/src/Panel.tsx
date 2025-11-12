import { useEffect, useState } from 'react';
import { Alert, Badge, Card, Group, LoadingOverlay, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { IconAlertTriangle, IconChartLine, IconTrendingUp } from '@tabler/icons-react';

// Import for type checking
import { checkPluginVersion, type InvenTreePluginContext } from '@inventreedb/ui';

interface ROPDetails {
    part_id: number;
    part_name: string;
    current_stock: number;
    reorder_point: number;
    safety_stock: number;
    max_stock: number;
    demand_rate: number;
    lead_time_days: number;
    suggested_order_qty: number;
    days_until_stockout: number | null;
    urgency_score: number;
    status: string;
    last_calculated: string;
}

/**
 * Render ROP Analysis Panel on Part Detail Page
 */
function ROPAnalysisPanel({
    context
}: {
    context: InvenTreePluginContext;
}) {
    const [ropData, setRopData] = useState<ROPDetails | null>(null);
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

    const getStatusColor = (status: string): string => {
        switch (status.toLowerCase()) {
            case 'critical': return 'red';
            case 'low': return 'orange';
            case 'adequate': return 'green';
            case 'excess': return 'blue';
            default: return 'gray';
        }
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

    if (!ropData) {
        return (
            <Alert icon={<IconAlertTriangle size="1rem" />} title="No Data" color="yellow">
                <Text>No ROP analysis available for this part. Ensure sufficient stock history exists.</Text>
            </Alert>
        );
    }

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Title order={3}>
                    <IconChartLine size="1.5rem" style={{ marginRight: 8, verticalAlign: 'middle' }} />
                    Reorder Point Analysis
                </Title>
                <Badge size="lg" color={getStatusColor(ropData.status)}>
                    {ropData.status}
                </Badge>
            </Group>

            <SimpleGrid cols={2} spacing="md">
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Current Stock</Text>
                    <Text size="xl" fw={700}>{Math.round(ropData.current_stock)}</Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Reorder Point</Text>
                    <Text size="xl" fw={700} c="blue">{Math.round(ropData.reorder_point)}</Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Safety Stock</Text>
                    <Text size="xl" fw={700}>{Math.round(ropData.safety_stock)}</Text>
                </Card>

                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Text size="sm" c="dimmed">Max Stock Level</Text>
                    <Text size="xl" fw={700}>{Math.round(ropData.max_stock)}</Text>
                </Card>
            </SimpleGrid>

            <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Stack gap="sm">
                    <Group justify="space-between">
                        <Text fw={600}>Demand Analysis</Text>
                        <IconTrendingUp size="1.2rem" />
                    </Group>

                    <Group justify="space-between">
                        <Text size="sm">Daily Demand Rate:</Text>
                        <Text fw={600}>{ropData.demand_rate.toFixed(2)} units/day</Text>
                    </Group>

                    <Group justify="space-between">
                        <Text size="sm">Lead Time:</Text>
                        <Text fw={600}>{ropData.lead_time_days} days</Text>
                    </Group>

                    {ropData.days_until_stockout !== null && (
                        <Group justify="space-between">
                            <Text size="sm">Days Until Stockout:</Text>
                            <Text
                                fw={700}
                                c={ropData.days_until_stockout <= 7 ? 'red' : ropData.days_until_stockout <= 14 ? 'orange' : 'green'}
                            >
                                {ropData.days_until_stockout <= 0 ? 'NOW' : `${Math.round(ropData.days_until_stockout)} days`}
                            </Text>
                        </Group>
                    )}

                    <Group justify="space-between">
                        <Text size="sm">Urgency Score:</Text>
                        <Badge color={ropData.urgency_score >= 80 ? 'red' : ropData.urgency_score >= 60 ? 'orange' : 'green'}>
                            {Math.round(ropData.urgency_score)}
                        </Badge>
                    </Group>
                </Stack>
            </Card>

            {ropData.suggested_order_qty > 0 && (
                <Alert icon={<IconAlertTriangle size="1rem" />} title="Reorder Recommended" color="orange">
                    <Text>
                        Suggested Order Quantity: <Text component="span" fw={700} c="green">{Math.round(ropData.suggested_order_qty)}</Text> units
                    </Text>
                    <Text size="sm" c="dimmed" mt="xs">
                        Last calculated: {new Date(ropData.last_calculated).toLocaleString()}
                    </Text>
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
