/**
 * Filter state persistence functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get filter form and elements
    const filterForm = document.querySelector('form[action*="analyze"]');
    if (!filterForm) return;
    
    // Save form state on submission
    filterForm.addEventListener('submit', function() {
        const formData = new FormData(filterForm);
        const filterState = {};
        
        for (const [key, value] of formData.entries()) {
            filterState[key] = value;
        }
        
        // Save filter state to sessionStorage as backup
        sessionStorage.setItem('filterState', JSON.stringify(filterState));
    });
    
    // On page load, check if we need to restore values
    function restoreFiltersIfNeeded() {
        // Only restore from sessionStorage if server-side session is missing values
        const startDateInput = filterForm.querySelector('[name="start_date"]');
        const endDateInput = filterForm.querySelector('[name="end_date"]');
        
        // If form has empty values, try to restore from sessionStorage
        if (!startDateInput.value || !endDateInput.value) {
            const savedState = sessionStorage.getItem('filterState');
            if (savedState) {
                const filterState = JSON.parse(savedState);
                
                // Apply saved values to form
                for (const key in filterState) {
                    const input = filterForm.querySelector(`[name="${key}"]`);
                    if (input && !input.value) {
                        input.value = filterState[key];
                    }
                }
            }
        }
    }
    
    // Try to restore filters
    restoreFiltersIfNeeded();
});
