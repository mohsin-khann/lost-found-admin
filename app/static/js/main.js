// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Tooltips
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Live stats update (example)
    const updateStats = () => {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.querySelector('.stat-card.card-users .card-text').textContent = data.total_users;
                document.querySelector('.stat-card.card-lost .card-text').textContent = data.lost_items;
                document.querySelector('.stat-card.card-found .card-text').textContent = data.found_items;
                document.querySelector('.stat-card.card-matches .card-text').textContent = data.successful_matches;
            });
    };
    
    // Update stats every 60 seconds
    setInterval(updateStats, 60000);
});