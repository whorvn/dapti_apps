/**
 * Student search and table filtering functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Student search functionality
    const searchInput = document.getElementById('studentSearch');
    const searchFeedback = document.getElementById('searchFeedback');
    const clearSearchBtn = document.getElementById('clearSearch');
    const studentTable = document.getElementById('studentsTable');
    
    if (!searchInput || !studentTable) return;
    
    const tableRows = Array.from(studentTable.querySelectorAll('tbody tr'));
    
    function filterTable() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        let matchCount = 0;
        
        tableRows.forEach(row => {
            const name = (row.cells[0].textContent || '').toLowerCase();
            const phone = (row.cells[1].textContent || '').toLowerCase();
            const matchesSearch = name.includes(searchTerm) || phone.includes(searchTerm);
            
            row.style.display = matchesSearch ? '' : 'none';
            if (matchesSearch) matchCount++;
        });
        
        // Update search feedback
        if (searchFeedback) {
            if (searchTerm) {
                searchFeedback.textContent = `Found ${matchCount} matching students`;
            } else {
                searchFeedback.textContent = '';
            }
        }
    }
    
    // Search input event
    searchInput.addEventListener('input', filterTable);
    
    // Clear search button
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            filterTable();
        });
    }
    
    // Initialize table filters
    filterTable();
});
