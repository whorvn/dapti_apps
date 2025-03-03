/**
 * Theme management for the Quiz Application
 */
document.addEventListener('DOMContentLoaded', function() {
    // Dark mode functionality
    const toggleSwitch = document.querySelector('#checkbox');
    if (!toggleSwitch) return;
    
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme from localStorage
    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        if (currentTheme === 'dark') {
            toggleSwitch.checked = true;
        }
    }
    
    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }
    
    toggleSwitch.addEventListener('change', switchTheme, false);
    
    // Check system preference
    if (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
        toggleSwitch.checked = true;
        localStorage.setItem('theme', 'dark');
    }
});
