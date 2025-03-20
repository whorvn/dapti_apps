/**
 * Form validation to prevent empty values being submitted for numeric fields
 */
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    
    if (filterForm) {
        // Add logging to see what happens during form submission
        console.log('Filter form found, adding validation');
        
        filterForm.addEventListener('submit', function(e) {
            // Log the submission event
            console.log('Form submitted');
            
            // Check all number inputs
            const numberInputs = filterForm.querySelectorAll('input[type="number"]');
            
            numberInputs.forEach(input => {
                console.log(`Processing input ${input.name} with value "${input.value}"`);
                
                // If value is empty string, set to 0
                if (input.value === '') {
                    console.log(`Setting empty ${input.name} to 0`);
                    input.value = '0';
                }
                
                // Additional validation if needed
                if (isNaN(parseFloat(input.value))) {
                    console.log(`Invalid number ${input.name}, setting to 0`);
                    input.value = '0';
                }
                
                // Log the final value
                console.log(`Final ${input.name} value: ${input.value}`);
            });
            
            // Save a copy of the form data to localStorage for debugging
            const formData = new FormData(filterForm);
            const formValues = {};
            for (const [key, value] of formData.entries()) {
                formValues[key] = value;
            }
            localStorage.setItem('lastFormSubmission', JSON.stringify(formValues));
            console.log('Saved form values to localStorage:', formValues);
            
            // Form can continue submission
            return true;
        });
        
        // Add hidden field to store the source of the submission
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = 'form_source';
        hiddenField.value = 'analyze_page';
        filterForm.appendChild(hiddenField);
    }
});
