/**
 * ROP Part Panel - Detailed ROP analysis for individual parts
 * 
 * Displays:
 * - Current ROP calculation breakdown
 * - Demand statistics and trends
 * - Safety stock configuration
 * - Visual chart of stock projection vs ROP threshold
 */

function renderROPPartPanel(target, context) {
    const apiUrl = context.api_url;
    const partId = context.part_id;
    
    // Create container
    const container = document.createElement('div');
    container.className = 'rop-part-panel';
    container.style.cssText = 'padding: 15px;';
    
    // Add loading indicator
    container.innerHTML = `
        <div class="loading-indicator" style="text-align: center; padding: 20px;">
            <i class="fas fa-spinner fa-spin fa-2x"></i>
            <p>Loading ROP analysis...</p>
        </div>
    `;
    
    target.appendChild(container);
    
    // Fetch ROP details from API
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
        renderROPDetails(container, data, partId);
    })
    .catch(error => {
        console.error('Error fetching ROP details:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load ROP analysis: ${error.message}
            </div>
        `;
    });
}

function renderROPDetails(container, data, partId) {
    container.innerHTML = '';
    
    if (!data.has_policy) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                <strong>No ROP Policy Configured</strong>
                <p>This part does not have a Reorder Point policy configured yet.</p>
                <button class="btn btn-primary" onclick="createROPPolicy(${partId})">
                    <i class="fas fa-plus"></i> Create ROP Policy
                </button>
            </div>
        `;
        return;
    }
    
    // Create layout with two columns
    const layout = document.createElement('div');
    layout.style.cssText = 'display: flex; gap: 20px;';
    
    // Left column - Policy and statistics
    const leftColumn = document.createElement('div');
    leftColumn.style.cssText = 'flex: 1;';
    
    // Right column - Current suggestion and actions
    const rightColumn = document.createElement('div');
    rightColumn.style.cssText = 'flex: 1;';
    
    // Policy Status Card
    const policyCard = createPolicyCard(data);
    leftColumn.appendChild(policyCard);
    
    // Demand Statistics Card
    if (data.demand_statistics) {
        const statsCard = createStatsCard(data);
        leftColumn.appendChild(statsCard);
    }
    
    // Current Stock Status Card
    const stockCard = createStockCard(data);
    rightColumn.appendChild(stockCard);
    
    // Current Suggestion Card
    if (data.suggestion) {
        const suggestionCard = createSuggestionCard(data.suggestion, partId);
        rightColumn.appendChild(suggestionCard);
    } else {
        const noSuggestionCard = document.createElement('div');
        noSuggestionCard.className = 'panel panel-success';
        noSuggestionCard.style.cssText = 'margin-bottom: 15px;';
        noSuggestionCard.innerHTML = `
            <div class="panel-heading">
                <h4 class="panel-title">
                    <i class="fas fa-check-circle"></i> Stock Status: OK
                </h4>
            </div>
            <div class="panel-body">
                <p><strong>No reorder needed at this time.</strong></p>
                <p>Current stock levels are sufficient based on ROP analysis.</p>
            </div>
        `;
        rightColumn.appendChild(noSuggestionCard);
    }
    
    // Actions Card
    const actionsCard = createActionsCard(partId, data);
    rightColumn.appendChild(actionsCard);
    
    layout.appendChild(leftColumn);
    layout.appendChild(rightColumn);
    container.appendChild(layout);
    
    // Add chart if historical data available
    if (data.historical_demand && data.historical_demand.length > 0) {
        const chartCard = createDemandChart(data.historical_demand);
        container.appendChild(chartCard);
    }
}

function createPolicyCard(data) {
    const card = document.createElement('div');
    card.className = 'panel panel-default';
    card.style.cssText = 'margin-bottom: 15px;';
    
    const policy = data.policy;
    const statusBadge = policy.enabled 
        ? '<span class="badge badge-success">Enabled</span>'
        : '<span class="badge badge-danger">Disabled</span>';
    
    card.innerHTML = `
        <div class="panel-heading">
            <h4 class="panel-title">
                <i class="fas fa-cog"></i> ROP Policy Configuration ${statusBadge}
            </h4>
        </div>
        <div class="panel-body">
            <table class="table table-condensed" style="margin-bottom: 0;">
                <tr>
                    <td><strong>Safety Stock:</strong></td>
                    <td>${formatNumber(policy.safety_stock)} ${policy.use_calculated_safety_stock ? '(Auto-calculated)' : '(Manual)'}</td>
                </tr>
                <tr>
                    <td><strong>Service Level:</strong></td>
                    <td>${policy.service_level}%</td>
                </tr>
                <tr>
                    <td><strong>Target Stock Multiplier:</strong></td>
                    <td>${policy.target_stock_multiplier}x</td>
                </tr>
                ${policy.last_calculated_rop ? `
                <tr style="border-top: 2px solid #ddd;">
                    <td><strong>Calculated ROP:</strong></td>
                    <td><strong style="color: #5cb85c; font-size: 1.2em;">${formatNumber(policy.last_calculated_rop)}</strong></td>
                </tr>
                <tr>
                    <td><strong>Demand Rate:</strong></td>
                    <td>${policy.last_calculated_demand_rate.toFixed(2)} units/day</td>
                </tr>
                <tr>
                    <td><small>Last Calculated:</small></td>
                    <td><small>${formatDate(policy.last_calculation_date)}</small></td>
                </tr>
                ` : '<tr><td colspan="2"><em>Not yet calculated</em></td></tr>'}
            </table>
        </div>
    `;
    
    return card;
}

function createStatsCard(data) {
    const card = document.createElement('div');
    card.className = 'panel panel-info';
    card.style.cssText = 'margin-bottom: 15px;';
    
    const stats = data.demand_statistics;
    
    card.innerHTML = `
        <div class="panel-heading">
            <h4 class="panel-title">
                <i class="fas fa-chart-line"></i> Demand Statistics
            </h4>
        </div>
        <div class="panel-body">
            <table class="table table-condensed" style="margin-bottom: 0;">
                <tr>
                    <td><strong>Mean Daily Demand:</strong></td>
                    <td>${stats.mean_daily_demand.toFixed(2)} units/day</td>
                </tr>
                <tr>
                    <td><strong>Std Deviation:</strong></td>
                    <td>±${stats.std_dev_daily_demand.toFixed(2)} units/day</td>
                </tr>
                <tr>
                    <td><strong>Analysis Period:</strong></td>
                    <td>${stats.analysis_period_days} days</td>
                </tr>
                <tr>
                    <td><strong>Removal Events:</strong></td>
                    <td>${stats.total_removals} transactions</td>
                </tr>
                ${stats.calculated_safety_stock ? `
                <tr>
                    <td><strong>Calculated Safety Stock:</strong></td>
                    <td>${formatNumber(stats.calculated_safety_stock)}</td>
                </tr>
                ` : ''}
                <tr>
                    <td><small>Analyzed:</small></td>
                    <td><small>${formatDate(stats.calculation_date)}</small></td>
                </tr>
            </table>
        </div>
    `;
    
    return card;
}

function createStockCard(data) {
    const card = document.createElement('div');
    card.className = 'panel panel-default';
    card.style.cssText = 'margin-bottom: 15px;';
    
    const currentStock = data.current_stock;
    const rop = data.policy.last_calculated_rop || 0;
    const stockStatus = currentStock >= rop ? 'Sufficient' : 'Below ROP';
    const statusColor = currentStock >= rop ? '#5cb85c' : '#d9534f';
    
    card.innerHTML = `
        <div class="panel-heading">
            <h4 class="panel-title">
                <i class="fas fa-boxes"></i> Current Stock Status
            </h4>
        </div>
        <div class="panel-body">
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 3em; font-weight: bold; color: ${statusColor};">
                    ${formatNumber(currentStock)}
                </div>
                <div style="font-size: 1.2em; color: #666;">
                    units in stock
                </div>
                <div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
                    <strong>Status:</strong> <span style="color: ${statusColor};">${stockStatus}</span><br>
                    ${rop > 0 ? `<small>ROP Threshold: ${formatNumber(rop)}</small>` : ''}
                </div>
            </div>
            ${data.on_order > 0 ? `
            <div class="alert alert-info" style="margin-bottom: 0;">
                <i class="fas fa-truck"></i> <strong>${formatNumber(data.on_order)}</strong> units on order
            </div>
            ` : ''}
        </div>
    `;
    
    return card;
}

function createSuggestionCard(suggestion, partId) {
    const card = document.createElement('div');
    card.className = 'panel panel-warning';
    card.style.cssText = 'margin-bottom: 15px;';
    
    const urgencyColor = getUrgencyColor(suggestion.urgency_score);
    
    card.innerHTML = `
        <div class="panel-heading" style="background-color: ${urgencyColor}; color: white;">
            <h4 class="panel-title">
                <i class="fas fa-exclamation-triangle"></i> Reorder Recommended
            </h4>
        </div>
        <div class="panel-body">
            <div style="text-align: center; padding: 15px;">
                <div style="font-size: 2.5em; font-weight: bold; color: #5cb85c;">
                    ${formatNumber(suggestion.suggested_order_qty)}
                </div>
                <div style="font-size: 1.1em; color: #666;">
                    suggested order quantity
                </div>
            </div>
            <table class="table table-condensed">
                <tr>
                    <td><strong>Urgency:</strong></td>
                    <td><span class="badge" style="background-color: ${urgencyColor};">${Math.round(suggestion.urgency_score)}</span></td>
                </tr>
                <tr>
                    <td><strong>Projected Stock:</strong></td>
                    <td>${formatNumber(suggestion.projected_stock)}</td>
                </tr>
                <tr>
                    <td><strong>Days Until Stockout:</strong></td>
                    <td><strong>${suggestion.days_until_stockout !== null ? suggestion.days_until_stockout + ' days' : 'Unknown'}</strong></td>
                </tr>
                ${suggestion.stockout_date ? `
                <tr>
                    <td><strong>Stockout Date:</strong></td>
                    <td>${formatDate(suggestion.stockout_date)}</td>
                </tr>
                ` : ''}
            </table>
            <div style="text-align: center; margin-top: 15px;">
                <button class="btn btn-primary btn-lg" onclick="generatePOFromPanel(${suggestion.id})">
                    <i class="fas fa-shopping-cart"></i> Generate Purchase Order
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function createActionsCard(partId, data) {
    const card = document.createElement('div');
    card.className = 'panel panel-default';
    
    card.innerHTML = `
        <div class="panel-heading">
            <h4 class="panel-title">
                <i class="fas fa-tools"></i> Actions
            </h4>
        </div>
        <div class="panel-body">
            <button class="btn btn-info btn-block" onclick="recalculateROP(${partId})">
                <i class="fas fa-sync"></i> Recalculate ROP
            </button>
            <button class="btn btn-default btn-block" onclick="editROPPolicy(${partId})" style="margin-top: 10px;">
                <i class="fas fa-edit"></i> Edit Policy Settings
            </button>
        </div>
    `;
    
    return card;
}

function createDemandChart(historicalData) {
    const card = document.createElement('div');
    card.className = 'panel panel-default';
    card.style.cssText = 'margin-top: 20px;';
    
    card.innerHTML = `
        <div class="panel-heading">
            <h4 class="panel-title">
                <i class="fas fa-chart-area"></i> Historical Demand Trend
            </h4>
        </div>
        <div class="panel-body">
            <canvas id="demand-chart" style="max-height: 300px;"></canvas>
        </div>
    `;
    
    // Note: Charting would require Chart.js or similar library
    // This is a placeholder for the chart implementation
    
    return card;
}

// Utility functions
function getUrgencyColor(score) {
    if (score >= 80) return '#d9534f';
    if (score >= 60) return '#f0ad4e';
    if (score >= 40) return '#f7dc6f';
    return '#5cb85c';
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return Math.round(num).toLocaleString();
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Action functions
function recalculateROP(partId) {
    if (!confirm('Recalculate ROP for this part? This may take a moment.')) {
        return;
    }
    
    const calculateUrl = `/api/plugin/rop-suggestion/part/${partId}/calculate/`;
    
    fetch(calculateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('ROP recalculated successfully!');
            location.reload();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error recalculating ROP:', error);
        alert('Failed to recalculate ROP. Please try again.');
    });
}

function generatePOFromPanel(suggestionId) {
    if (!confirm('Generate a Purchase Order for this suggestion?')) {
        return;
    }
    
    const generatePoUrl = `/api/plugin/rop-suggestion/generate-po/`;
    
    fetch(generatePoUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            suggestion_id: suggestionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Purchase Order ${data.po_reference} created successfully!`);
            window.location.href = data.po_url;
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error generating PO:', error);
        alert('Failed to generate Purchase Order. Please try again.');
    });
}

function editROPPolicy(partId) {
    alert('ROP Policy editing interface would be implemented here.\nFor now, please use the admin interface.');
}

function createROPPolicy(partId) {
    alert('ROP Policy creation interface would be implemented here.\nFor now, please use the admin interface.');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Export as renderPanel for InvenTree compatibility
function renderPanel(target, context) {
    return renderROPPartPanel(target, context);
}
