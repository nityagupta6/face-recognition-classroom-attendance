document.addEventListener('DOMContentLoaded', function () {
    // Role-based file upload visibility
    const roleSelect = document.querySelector('select[name="role"]');
    const studentUpload = document.getElementById('student-upload');

    if (roleSelect) {
        roleSelect.addEventListener('change', function () {
            if (roleSelect.value === 'student') {
                studentUpload.style.display = 'block';
            } else {
                studentUpload.style.display = 'none';
            }
        });
    }

    // Loop through each attendance record and create a pie chart for it
    if (typeof attendanceData !== 'undefined') {
        attendanceData.forEach(record => {
            var ctx = document.getElementById('attendance-chart-' + record.course.id).getContext('2d');
            var attendanceChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Attended', 'Missed'],
                    datasets: [{
                        data: [record.attended, record.missed],  // Use dynamic data from attendanceData
                        backgroundColor: ['#4caf50', '#f44336'],  // Colors for 'Attended' and 'Missed'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                        }
                    }
                }
            });
        });
    }

    // Initialize Select2 with options for auto-opening search
    const selectElements = document.querySelectorAll('.select2');
    selectElements.forEach(function (element) {
        $(element).select2({
            placeholder: 'Search or select an option',   // Set a default placeholder
            allowClear: true,  // Add the "clear" button to reset selection
            minimumResultsForSearch: 0,  // Always show the search box
            width: '100%',  // Make sure the width fits nicely
        });

        // Force the dropdown to open and search box to focus on single click
        $(element).on('select2:open', function () {
            setTimeout(function () {
                // Focus the search field when the dropdown opens
                $('.select2-search__field').focus();
            }, 100);  // Add a small delay to ensure the dropdown is fully open before focusing
        });
    });
});
