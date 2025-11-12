/**
 * ROP Dashboard Widget - Displays urgent reorder suggestions
 * 
 * Fetches and displays pending ROP suggestions from the plugin API
 * Provides quick access to parts requiring immediate procurement action
 */

function renderROPDashboard(target, context) {
    const apiUrl = context.api_url;
    
    // Create container
    const container = document.createElement('div');
    container.className = 'rop-dashboard-widget';
    container.style.cssText = 'padding: 15px; height: 100%; overflow-y: auto;';
    
    // Add loading indicator
    container.innerHTML = `
        <div class="loading-indicator" style="text-align: center; padding: 20px;">
            <i class="fas fa-spinner fa-spin fa-2x"></i>
            <p>Loading ROP suggestions...</p>
        </div>
    `;
    
    target.appendChild(container);
    
    // Fetch suggestions from API
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
        renderSuggestions(container, data.results);
    })
    .catch(error => {
        console.error('Error fetching ROP suggestions:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load ROP suggestions: ${error.message}
            </div>
        `;
    });
}

function renderSuggestions(container, suggestions) {
    container.innerHTML = '';
    
    if (!suggestions || suggestions.length === 0) {
        container.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i>
                <strong>All Clear!</strong>
                <p>No urgent reorder suggestions at this time.</p>
            </div>
        `;
        return;
    }
    
    // Create header
    const header = document.createElement('div');
    header.style.cssText = 'margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;';
    header.innerHTML = `
        <h4 style="margin: 0; color: #d9534f;">
            <i class="fas fa-exclamation-triangle"></i>
            ${suggestions.length} Part${suggestions.length > 1 ? 's' : ''} Requiring Attention
        </h4>
        <small style="color: #666;">Click any part to view details and take action</small>
    `;
    container.appendChild(header);
    
    // Create table
    const table = document.createElement('table');
    table.className = 'table table-striped table-condensed';
    table.style.cssText = 'margin-bottom: 0; font-size: 0.9em;';
    
    // Table header
    table.innerHTML = `
        <thead>
            <tr>
                <th style="width: 50px;">Urgency</th>
                <th>Part</th>
                <th style="width: 100px; text-align: right;">Order Qty</th>
                <th style="width: 100px; text-align: right;">Current</th>
                <th style="width: 120px;">Stockout</th>
                <th style="width: 140px;">Supplier</th>
                <th style="width: 80px;">Action</th>
            </tr>
        </thead>
        <tbody id="rop-suggestions-body"></tbody>
    `;
    
    container.appendChild(table);
    
    const tbody = table.querySelector('#rop-suggestions-body');
    
    // Render each suggestion
    suggestions.forEach(suggestion => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        
        // Urgency badge
        const urgencyColor = getUrgencyColor(suggestion.urgency_score);
        const urgencyBadge = `<span class="badge" style="background-color: ${urgencyColor}; color: white; font-weight: bold;">${Math.round(suggestion.urgency_score)}</span>`;
        
        // Stockout timing
        let stockoutText = 'Unknown';
        if (suggestion.days_until_stockout !== null) {
            if (suggestion.days_until_stockout <= 0) {
                stockoutText = '<strong style="color: #d9534f;">NOW</strong>';
            } else if (suggestion.days_until_stockout <= 7) {
                stockoutText = `<strong style="color: #f0ad4e;">${suggestion.days_until_stockout} days</strong>`;
            } else {
                stockoutText = `${suggestion.days_until_stockout} days`;
            }
        }
        
        row.innerHTML = `
            <td style="text-align: center;">${urgencyBadge}</td>
            <td>
                <strong>${suggestion.part_name}</strong><br>
                <small style="color: #666;">${suggestion.part_IPN || 'No IPN'}</small>
            </td>
            <td style="text-align: right; font-weight: bold; color: #5cb85c;">
                ${formatNumber(suggestion.suggested_order_qty)}
            </td>
            <td style="text-align: right;">
                ${formatNumber(suggestion.current_stock)}
            </td>
            <td>${stockoutText}</td>
            <td>
                <small>${suggestion.supplier_name || 'No supplier'}</small><br>
                <small style="color: #666;">Lead: ${suggestion.lead_time_days || '?'} days</small>
            </td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="generatePO(${suggestion.id})">
                    <i class="fas fa-shopping-cart"></i> Order
                </button>
            </td>
        `;
        
        // Make row clickable to view part details
        row.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                window.location.href = suggestion.part_url;
            }
        });
        
        tbody.appendChild(row);
    });
}

function getUrgencyColor(score) {
    if (score >= 80) return '#d9534f';  // Red - Critical
    if (score >= 60) return '#f0ad4e';  // Orange - High
    if (score >= 40) return '#f7dc6f';  // Yellow - Medium
    return '#5cb85c';                   // Green - Low
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return Math.round(num).toLocaleString();
}

function generatePO(suggestionId) {
    if (!confirm('Generate a Purchase Order for this part?')) {
        return;
    }
    
    // Get the generate-po API URL (adjust based on your plugin URL structure)
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

// Export as renderDashboardItem for InvenTree compatibility
function renderDashboardItem(target, context) {
    return renderROPDashboard(target, context);
}
