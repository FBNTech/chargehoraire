function startExcelImport(url, csrftoken, formData) {
    var modal = new bootstrap.Modal(document.getElementById('progressModal'));
    modal.show();
    
    var progressBar = document.querySelector('.progress-bar');
    var progressText = document.getElementById('progressText');
    
    function updateProgress() {
        $.ajax({
            url: url,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            success: function(data) {
                if (data.progress) {
                    var progress = Math.round(data.progress);
                    progressBar.style.width = progress + '%';
                    progressBar.setAttribute('aria-valuenow', progress);
                    progressBar.textContent = progress + '%';
                    progressText.textContent = `Traitement : ${data.processed}/${data.total}`;
                    
                    if (progress < 100) {
                        setTimeout(updateProgress, 500);
                    } else {
                        window.location.reload();
                    }
                }
            },
            error: function(xhr, status, error) {
                alert('Erreur lors de l\'importation : ' + error);
                modal.hide();
            }
        });
    }
    
    updateProgress();
}
