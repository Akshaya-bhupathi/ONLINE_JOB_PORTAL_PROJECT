// Any custom JavaScript can go here
document.addEventListener('DOMContentLoaded', function() {
    // Example: Confirm before deleting
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to delete this?')) {
                e.preventDefault();
            }
        });
    });
});