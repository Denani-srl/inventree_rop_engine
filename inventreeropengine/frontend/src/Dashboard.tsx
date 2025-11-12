
import { Alert, Badge, Button, Group, LoadingOverlay, Stack, Table, Text } from '@mantine/core';
import { useEffect, useState } from 'react';
import { IconAlertTriangle, IconShoppingCart } from '@tabler/icons-react';

// Import for type checking
import { checkPluginVersion, type InvenTreePluginContext } from '@inventreedb/ui';

interface ROPSuggestion {
    id: number;
    part_name: string;
    part_IPN: string;
    part_url: string;
    urgency_score: number;
    current_stock: number;
    suggested_order_qty: number;
    days_until_stockout: number | null;
    supplier_name: string;
    lead_time_days: number;
}

/**
 * Render ROP Dashboard Widget showing urgent reorder suggestions
 */
function ROPDashboardWidget({
    context
}: {
    context: InvenTreePluginContext;
}) {
    const [suggestions, setSuggestions] = useState<ROPSuggestion[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const apiUrl = context.context?.api_url;

    useEffect(() => {
        if (!apiUrl) {
            setError('API URL not configured');
            setLoading(false);
            return;
        }

        // Fetch ROP suggestions from the backend
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
                setSuggestions(data.results || []);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching ROP suggestions:', err);
                setError(`Failed to load suggestions: ${err.message}`);
                setLoading(false);
            });
    }, [apiUrl]);

    const getUrgencyColor = (score: number): string => {
        if (score >= 80) return 'red';
        if (score >= 60) return 'orange';
        if (score >= 40) return 'yellow';
        return 'green';
    };

    const formatStockoutDays = (days: number | null) => {
        if (days === null) return 'Unknown';
        if (days <= 0) return <Text c="red" fw={700}>NOW</Text>;
        if (days <= 7) return <Text c="orange" fw={700}>{days} days</Text>;
        return `${days} days`;
    };

    if (loading) {
        return (
            <div style={{ position: 'relative', minHeight: 200 }}>
                <LoadingOverlay visible={true} />
                <Text ta="center" mt="xl">Loading ROP suggestions...</Text>
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

    if (suggestions.length === 0) {
        return (
            <Alert icon={<IconAlertTriangle size="1rem" />} title="All Clear!" color="green">
                <Text>No urgent reorder suggestions at this time.</Text>
            </Alert>
        );
    }

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Text size="lg" fw={700}>
                    <IconAlertTriangle size="1.2rem" style={{ marginRight: 8, verticalAlign: 'middle' }} />
                    {suggestions.length} Part{suggestions.length > 1 ? 's' : ''} Requiring Attention
                </Text>
            </Group>

            <Table striped highlightOnHover>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>Urgency</Table.Th>
                        <Table.Th>Part</Table.Th>
                        <Table.Th ta="right">Order Qty</Table.Th>
                        <Table.Th ta="right">Current</Table.Th>
                        <Table.Th>Stockout</Table.Th>
                        <Table.Th>Supplier</Table.Th>
                        <Table.Th>Action</Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {suggestions.map((suggestion) => (
                        <Table.Tr
                            key={suggestion.id}
                            style={{ cursor: 'pointer' }}
                            onClick={() => window.location.href = suggestion.part_url}
                        >
                            <Table.Td>
                                <Badge color={getUrgencyColor(suggestion.urgency_score)}>
                                    {Math.round(suggestion.urgency_score)}
                                </Badge>
                            </Table.Td>
                            <Table.Td>
                                <div>
                                    <Text fw={600}>{suggestion.part_name}</Text>
                                    <Text size="xs" c="dimmed">{suggestion.part_IPN || 'No IPN'}</Text>
                                </div>
                            </Table.Td>
                            <Table.Td ta="right">
                                <Text fw={700} c="green">{Math.round(suggestion.suggested_order_qty)}</Text>
                            </Table.Td>
                            <Table.Td ta="right">
                                {Math.round(suggestion.current_stock)}
                            </Table.Td>
                            <Table.Td>
                                {formatStockoutDays(suggestion.days_until_stockout)}
                            </Table.Td>
                            <Table.Td>
                                <div>
                                    <Text size="sm">{suggestion.supplier_name || 'No supplier'}</Text>
                                    <Text size="xs" c="dimmed">Lead: {suggestion.lead_time_days || '?'} days</Text>
                                </div>
                            </Table.Td>
                            <Table.Td onClick={(e) => e.stopPropagation()}>
                                <Button
                                    size="xs"
                                    leftSection={<IconShoppingCart size="1rem" />}
                                    onClick={() => alert('Generate PO functionality coming soon')}
                                >
                                    Order
                                </Button>
                            </Table.Td>
                        </Table.Tr>
                    ))}
                </Table.Tbody>
            </Table>
        </Stack>
    );
}


// This is the function which is called by InvenTree to render the actual dashboard component
export function renderROPDashboardItem(context: InvenTreePluginContext) {
    checkPluginVersion(context);
    return <ROPDashboardWidget context={context} />;
}
