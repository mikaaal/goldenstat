// GoldenStat JavaScript Application

class GoldenStat {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        console.log('🎯 GoldenStat Application Initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Global error handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showNotification('Ett fel uppstod', 'error');
        });
    }

    // Notification system
    showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };

        const notification = document.createElement('div');
        notification.className = `alert ${alertClass[type]} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Format date for Swedish locale
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('sv-SE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Format number with commas
    formatNumber(num) {
        return new Intl.NumberFormat('sv-SE').format(num);
    }

    // Create a chart
    createChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas with id ${canvasId} not found`);
            return null;
        }

        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, config);
        return this.charts[canvasId];
    }

    // Create line chart for player progress
    createProgressChart(canvasId, matches) {
        if (!matches || matches.length === 0) return;

        // First filter for singles matches with valid data
        const singlesMatches = matches.filter(match => 
            match.player_avg && 
            match.match_date && 
            match.match_type === 'Singles'
        );

        // Sort in chronological order (oldest first) for proper time series
        const sortedMatches = singlesMatches
            .sort((a, b) => new Date(a.match_date) - new Date(b.match_date))
            .slice(-20); // Last 20 chronological matches

        // Return early if no valid matches
        if (sortedMatches.length === 0) {
            console.warn('No singles matches with valid averages found for progress chart');
            return;
        }

        const labels = sortedMatches.map(match => this.formatDate(match.match_date));
        const averages = sortedMatches.map(match => match.player_avg);
        
        // Beräkna glidande medel (3 matcher för bättre responsivitet)
        const movingAvg = [];
        for (let i = 0; i < averages.length; i++) {
            const start = Math.max(0, i - 2); // 3-matchers glidande medel
            const slice = averages.slice(start, i + 1);
            const avg = slice.reduce((sum, val) => sum + val, 0) / slice.length;
            movingAvg.push(Math.round(avg * 100) / 100); // Round to 2 decimals
        }

        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Snitt per singelmatch',
                    data: averages,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }, {
                    label: '3-matchers glidande medel',
                    data: movingAvg,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Singlar - Average utveckling över tid'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Snittpoäng'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Matchdatum'
                        }
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Create match type breakdown chart
    createMatchTypeChart(canvasId, matchTypeStats) {
        if (!matchTypeStats || matchTypeStats.length === 0) return;

        const labels = matchTypeStats.map(stat => stat.match_type);
        const matches = matchTypeStats.map(stat => stat.total_matches);
        const wins = matchTypeStats.map(stat => stat.wins);
        const averages = matchTypeStats.map(stat => parseFloat(stat.avg_score || 0).toFixed(1));

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Totala matcher',
                    data: matches,
                    backgroundColor: 'rgba(0, 123, 255, 0.7)',
                    borderColor: '#007bff',
                    borderWidth: 1
                }, {
                    label: 'Vinster',
                    data: wins,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: '#28a745',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Prestanda per matchtyp'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Antal matcher'
                        }
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Create win/loss pie chart
    createWinLossChart(canvasId, wins, losses) {
        const total = wins + losses;
        if (total === 0) return;

        const config = {
            type: 'doughnut',
            data: {
                labels: ['Vinster', 'Förluster'],
                datasets: [{
                    data: [wins, losses],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)'
                    ],
                    borderColor: [
                        '#28a745',
                        '#dc3545'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Vinst/Förlust-fördelning'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Create throw score distribution chart
    createThrowDistributionChart(canvasId, scoreRanges) {
        if (!scoreRanges || Object.keys(scoreRanges).length === 0) return;

        const labels = Object.keys(scoreRanges);
        const data = Object.values(scoreRanges);

        // Modern gradient colors from low to high scores
        const colors = [
            '#EF4444',  // Red - 0-20
            '#F97316',  // Orange - 21-40  
            '#F59E0B',  // Amber - 41-60
            '#84CC16',  // Lime - 61-80
            '#10B981',  // Emerald - 81-99
            '#059669'   // Dark emerald - 100+
        ];

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Antal kast',
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Kastpoängfördelning',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: 'Antal kast'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Poängintervall'
                        }
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Create checkout analysis chart
    createCheckoutChart(canvasId, checkouts) {
        if (!checkouts || checkouts.length === 0) return;

        // Group checkouts by range
        const ranges = {
            '2-20': checkouts.filter(c => c >= 2 && c <= 20).length,
            '21-40': checkouts.filter(c => c >= 21 && c <= 40).length,
            '41-80': checkouts.filter(c => c >= 41 && c <= 80).length,
            '81-100': checkouts.filter(c => c >= 81 && c <= 100).length,
            '100+': checkouts.filter(c => c > 100).length
        };

        const config = {
            type: 'doughnut',
            data: {
                labels: Object.keys(ranges),
                datasets: [{
                    data: Object.values(ranges),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Utcheckning-fördelning'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Calculate match positions from match data
    calculateMatchPositions(matches) {
        const positionCounts = {};
        
        matches.forEach(match => {
            let position = 'Unknown';
            
            // Extract position from match_name (e.g., "...Division 1FA Singles1" -> "S1")
            if (match.match_name) {
                const matchName = match.match_name;
                
                // Check for specific patterns and convert to short format
                if (matchName.includes(' AD')) {
                    position = 'AD';
                } else if (matchName.includes(' Singles1')) {
                    position = 'S1';
                } else if (matchName.includes(' Singles2')) {
                    position = 'S2';
                } else if (matchName.includes(' Singles3')) {
                    position = 'S3';
                } else if (matchName.includes(' Singles4')) {
                    position = 'S4';
                } else if (matchName.includes(' Singles5')) {
                    position = 'S5';
                } else if (matchName.includes(' Singles6')) {
                    position = 'S6';
                } else if (matchName.includes(' Doubles1')) {
                    position = 'D1';
                } else if (matchName.includes(' Doubles2')) {
                    position = 'D2';
                } else if (matchName.includes(' Doubles3')) {
                    position = 'D3';
                } else {
                    // Fallback to match type if no specific position found
                    position = match.match_type === 'Singles' ? 'S' : 
                              match.match_type === 'Doubles' ? 'D' : 'Unknown';
                }
            } else if (match.match_type) {
                // Fallback to just match type with short format
                position = match.match_type === 'Singles' ? 'S' : 
                          match.match_type === 'Doubles' ? 'D' : 'Unknown';
            }
            
            positionCounts[position] = (positionCounts[position] || 0) + 1;
        });
        
        return positionCounts;
    }

    // Create match position distribution chart
    createMatchPositionChart(canvasId, positionStats) {
        if (!positionStats || Object.keys(positionStats).length === 0) return;

        const labels = Object.keys(positionStats);
        const data = Object.values(positionStats);

        // Modern, clean color scheme - sorted to match typical positions
        const getPositionColor = (position) => {
            const colorMap = {
                'S1': '#3B82F6',  // Blue
                'S2': '#06B6D4',  // Cyan
                'S3': '#10B981',  // Emerald
                'S4': '#84CC16',  // Lime
                'S5': '#F59E0B',  // Amber
                'S6': '#F97316',  // Orange
                'D1': '#8B5CF6',  // Violet
                'D2': '#A855F7',  // Purple
                'D3': '#EC4899',  // Pink
                'AD': '#EF4444',  // Red
                'S': '#64748B',   // Slate (fallback)
                'D': '#64748B'    // Slate (fallback)
            };
            return colorMap[position] || '#64748B';
        };

        const backgroundColor = labels.map(label => getPositionColor(label));
        const borderColor = backgroundColor.map(color => color.replace('1)', '0.8)'));

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Antal matcher',
                    data: data,
                    backgroundColor: backgroundColor,
                    borderColor: borderColor,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Spelade positioner',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed.y * 100) / total).toFixed(1);
                                return `${context.parsed.y} matcher (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: 'Antal matcher'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Matchposition'
                        }
                    }
                }
            }
        };

        return this.createChart(canvasId, config);
    }

    // Fetch and display detailed throw analysis
    async fetchThrowAnalysis(playerName, filters = {}) {
        try {
            // Build query parameters with filters
            const params = new URLSearchParams();
            if (filters.season) params.append('season', filters.season);
            
            const queryString = params.toString();
            const url = `/api/player/${encodeURIComponent(playerName)}/throws${queryString ? '?' + queryString : ''}`;
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Kunde inte hämta kastdata');
            }
            
            const data = await response.json();
            console.log('Throw analysis data:', data); // Debug log
            return data;
        } catch (error) {
            console.error('Fel vid hämtning av kastanalys:', error);
            this.showNotification('Kunde inte ladda kast-analys', 'error');
            return null;
        }
    }

    // Utility function to calculate win percentage
    calculateWinPercentage(wins, total) {
        if (total === 0) return 0;
        return ((wins / total) * 100).toFixed(1);
    }

    // SPA navigation for player searches
    navigateToPlayer(playerName, showModal = true) {
        if (showModal) {
            // Update search field and trigger search with modal
            document.getElementById('playerSearch').value = playerName;
            // Trigger the existing search function which shows modal
            window.searchPlayer();
        } else {
            // Direct navigation without modal (for future SPA routes)
            const url = new URL(window.location);
            url.searchParams.set('player', playerName);
            window.history.pushState({player: playerName}, `${playerName} - GoldenStat`, url);
        }
    }

    // Make player name clickable
    makePlayerNameClickable(playerName, isDoubles = false) {
        const escapedName = playerName.replace(/'/g, "\\'");
        if (isDoubles && (playerName.includes(' + ') || playerName.includes(' / '))) {
            // Handle doubles - make each player clickable
            const separator = playerName.includes(' + ') ? ' + ' : ' / ';
            const players = playerName.split(separator);
            const newSeparator = ' / ';
            return players.map(player => 
                `<span class="player-link" onclick="goldenStat.navigateToPlayer('${player.trim().replace(/'/g, "\\'")}'); event.stopPropagation();" title="Klicka för att se ${player.trim()}">${player.trim()}</span>`
            ).join(newSeparator);
        } else {
            return `<span class="player-link" onclick="goldenStat.navigateToPlayer('${escapedName}'); event.stopPropagation();" title="Klicka för att se ${playerName}">${playerName}</span>`;
        }
    }

    // Cleanup charts
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }

    // Destroy all charts
    destroyAllCharts() {
        Object.keys(this.charts).forEach(canvasId => {
            this.destroyChart(canvasId);
        });
    }
}

// Initialize the application
const goldenStat = new GoldenStat();

// Global functions for template use
function showOverview() {
    // Scroll to overview section
    document.querySelector('.container').scrollIntoView({ behavior: 'smooth' });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GoldenStat;
}