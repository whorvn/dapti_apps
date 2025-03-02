/**
 * Chart.js utility functions for interactive charts
 */

// Function to generate a random color with specific opacity
function getRandomColor(opacity=0.7) {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Function to generate a color palette with n colors
function generateColorPalette(n, opacity=0.7) {
    const colors = [];
    for (let i = 0; i < n; i++) {
        colors.push(getRandomColor(opacity));
    }
    return colors;
}

// Generate a horizontal bar chart
function createHorizontalBarChart(canvasId, labels, datasets, title, xAxisLabel) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: xAxisLabel
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Generate a line chart
function createLineChart(canvasId, labels, datasets, title, yAxisLabel, xAxisLabel) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: yAxisLabel
                    },
                    beginAtZero: true
                },
                x: {
                    title: {
                        display: true,
                        text: xAxisLabel
                    }
                }
            }
        }
    });
}

// Generate a bar chart
function createBarChart(canvasId, labels, datasets, title, yAxisLabel, xAxisLabel) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: yAxisLabel
                    },
                    beginAtZero: true
                },
                x: {
                    title: {
                        display: true,
                        text: xAxisLabel
                    }
                }
            }
        }
    });
}

// Generate a grouped bar chart for subject comparison
function createSubjectComparisonChart(canvasId, labels, datasets, title) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Generate a multi-student comparison chart
function createStudentComparisonChart(canvasId, labels, data, title, metricLabel) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generate background colors
    const backgroundColors = generateColorPalette(labels.length);
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metricLabel,
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: metricLabel
                    },
                    beginAtZero: true
                }
            }
        }
    });
}
