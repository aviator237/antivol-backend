document.addEventListener('DOMContentLoaded', function () {
    // Référence au bouton de géolocalisation
    const geolocateButton = document.getElementById('geolocate-button');
    // Référence aux champs cachés pour les coordonnées
    const latitudeInput = document.querySelector('input[name="latitude"]');
    const longitudeInput = document.querySelector('input[name="longitude"]');
    // Référence à l'élément qui affiche le statut de la géolocalisation
    const geoStatus = document.getElementById('geolocation-status');

    // Vérifier si la géolocalisation est disponible dans le navigateur
    if (!navigator.geolocation) {
        if (geolocateButton) {
            geolocateButton.disabled = true;
            geolocateButton.textContent = 'Géolocalisation non disponible';
        }
        if (geoStatus) {
            geoStatus.textContent = 'La géolocalisation n\'est pas prise en charge par votre navigateur';
            geoStatus.classList.add('error');
        }
    } else {
        // Ajouter un écouteur d'événement au bouton de géolocalisation
        if (geolocateButton) {
            geolocateButton.addEventListener('click', function(e) {
                e.preventDefault(); // Empêcher le formulaire de se soumettre
                
                if (geoStatus) {
                    geoStatus.textContent = 'Récupération de votre position...';
                    geoStatus.classList.remove('error', 'success');
                    geoStatus.classList.add('loading');
                }
                
                // Demander la position de l'utilisateur
                navigator.geolocation.getCurrentPosition(
                    // Succès
                    function(position) {
                        // Mettre à jour les champs cachés avec les coordonnées
                        if (latitudeInput) {
                            latitudeInput.value = position.coords.latitude;
                        }
                        if (longitudeInput) {
                            longitudeInput.value = position.coords.longitude;
                        }
                        
                        // Mettre à jour le statut
                        if (geoStatus) {
                            geoStatus.textContent = 'Position récupérée avec succès!';
                            geoStatus.classList.remove('loading', 'error');
                            geoStatus.classList.add('success');
                        }
                        
                        // Mettre à jour le texte du bouton
                        if (geolocateButton) {
                            geolocateButton.textContent = 'Position récupérée ✓';
                            geolocateButton.classList.add('success');
                        }
                    },
                    // Erreur
                    function(error) {
                        let errorMessage = 'Erreur lors de la récupération de la position';
                        
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage = 'Vous avez refusé l\'accès à votre position';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = 'Votre position n\'est pas disponible';
                                break;
                            case error.TIMEOUT:
                                errorMessage = 'La demande de position a expiré';
                                break;
                            case error.UNKNOWN_ERROR:
                                errorMessage = 'Une erreur inconnue est survenue';
                                break;
                        }
                        
                        // Mettre à jour le statut
                        if (geoStatus) {
                            geoStatus.textContent = errorMessage;
                            geoStatus.classList.remove('loading', 'success');
                            geoStatus.classList.add('error');
                        }
                        
                        // Réinitialiser le bouton
                        if (geolocateButton) {
                            geolocateButton.textContent = 'Récupérer ma position';
                            geolocateButton.classList.remove('success');
                        }
                    },
                    // Options
                    {
                        enableHighAccuracy: true, // Haute précision
                        timeout: 10000, // 10 secondes avant timeout
                        maximumAge: 0 // Ne pas utiliser de cache
                    }
                );
            });
        }
    }
});
