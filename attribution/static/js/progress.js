// Fonction pour mettre à jour la barre de progression
function updateProgressBar(progress, text) {
    $('#progressBar').css('width', progress + '%')
        .attr('aria-valuenow', progress)
        .text(progress.toFixed(1) + '%');
    if (text) {
        $('#progressText').text(text);
    }
}

// Fonction pour gérer la migration avec progression
function startMigration(csrftoken) {
    var modal = new bootstrap.Modal(document.getElementById('progressModal'));
    $('#progressModalTitle').text('Migration des cours en cours...');
    updateProgressBar(0, 'Préparation de la migration...');
    modal.show();

    function performMigration() {
        $.ajax({
            url: '/attribution/migrate-courses/',
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.progress !== undefined) {
                    updateProgressBar(
                        response.progress,
                        `Migration en cours... (${response.migrated}/${response.total} cours)`
                    );
                    if (response.progress < 100) {
                        setTimeout(performMigration, 100);
                    } else {
                        setTimeout(function() {
                            modal.hide();
                            location.reload();
                        }, 500);
                    }
                } else if (response.status === 'success') {
                    modal.hide();
                    location.reload();
                }
            },
            error: function() {
                $('#progressText').text('Erreur lors de la migration');
                setTimeout(function() {
                    modal.hide();
                }, 2000);
            }
        });
    }

    performMigration();
}

// Fonction pour gérer l'import Excel avec progression
function startExcelImport(url, csrftoken, formData) {
    var modal = new bootstrap.Modal(document.getElementById('progressModal'));
    $('#progressModalTitle').text('Import Excel en cours...');
    updateProgressBar(0, 'Préparation de l\'import...');
    modal.show();

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    var percent = (e.loaded / e.total) * 100;
                    updateProgressBar(
                        percent,
                        `Import en cours... ${Math.round(percent)}%`
                    );
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            updateProgressBar(100, 'Import terminé avec succès!');
            setTimeout(function() {
                modal.hide();
                location.reload();
            }, 500);
        },
        error: function() {
            $('#progressText').text('Erreur lors de l\'import');
            setTimeout(function() {
                modal.hide();
            }, 2000);
        }
    });
}
