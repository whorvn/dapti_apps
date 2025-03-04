/**
 * Search functionality for the student results table
 */

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('studentSearch');
    const searchButton = document.getElementById('searchButton');
    const resultsTable = document.getElementById('resultsTable');
    
    if (!searchInput || !searchButton || !resultsTable) return;
    
    // Function to perform search
    function performSearch() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const rows = resultsTable.querySelectorAll('tbody tr');
        
        let matchCount = 0;
        
        rows.forEach(row => {
            const name = row.cells[0].textContent.toLowerCase();
            const grade = row.cells[1].textContent.toLowerCase();
            const subjects = row.cells[7] ? row.cells[7].textContent.toLowerCase() : '';
            
            // Show row if search term is found in name, grade, or subjects
            if (name.includes(searchTerm) || grade.includes(searchTerm) || subjects.includes(searchTerm)) {
                row.style.display = '';
                matchCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Add a "no results" message if no matches were found
        let noResultsRow = resultsTable.querySelector('.no-results-row');
        if (matchCount === 0) {
            if (!noResultsRow) {
                const tbody = resultsTable.querySelector('tbody');
                noResultsRow = document.createElement('tr');
                noResultsRow.className = 'no-results-row';
                const td = document.createElement('td');
                td.setAttribute('colspan', '8');
                td.className = 'text-center py-3';
                td.textContent = `No students match your search for "${searchTerm}". Try a different search term.`;
                noResultsRow.appendChild(td);
                tbody.appendChild(noResultsRow);
            }
        } else if (noResultsRow) {
            noResultsRow.remove();
        }
    }
    
    // Search when button is clicked
    searchButton.addEventListener('click', performSearch);
    
    // Search when Enter key is pressed in search box
    searchInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Clear search when the search box is emptied
    searchInput.addEventListener('input', function() {
        if (this.value === '') {
            resultsTable.querySelectorAll('tbody tr').forEach(row => {
                row.style.display = '';
            });
            
            // Remove any "no results" row
            const noResultsRow = resultsTable.querySelector('.no-results-row');
            if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    });
});
