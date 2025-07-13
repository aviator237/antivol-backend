document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const addressSearchInput = document.getElementById('address-search');
    const addressField = document.getElementById('address-field');
    const postalCodeField = document.getElementById('postal-code-field');
    const cityField = document.getElementById('city-field');
    const latitudeField = document.querySelector('input[name="latitude"]');
    const longitudeField = document.querySelector('input[name="longitude"]');
    const mapContainer = document.getElementById('map-container');
    
    // Variables pour l'autocomplétion
    let autocompleteResults = null;
    let autocompleteTimeout = null;
    let selectedIndex = -1;
    
    // Créer le conteneur de résultats d'autocomplétion s'il n'existe pas
    if (addressSearchInput && !document.getElementById('autocomplete-results')) {
        autocompleteResults = document.createElement('div');
        autocompleteResults.id = 'autocomplete-results';
        autocompleteResults.className = 'autocomplete-results';
        addressSearchInput.parentNode.appendChild(autocompleteResults);
    } else if (document.getElementById('autocomplete-results')) {
        autocompleteResults = document.getElementById('autocomplete-results');
    }
    
    // Initialiser la carte si l'élément existe
    let map = null;
    let marker = null;
    
    if (mapContainer) {
        // Coordonnées par défaut (centre de la France)
        let defaultLat = 46.603354;
        let defaultLng = 1.888334;
        let defaultZoom = 5;
        
        // Utiliser les coordonnées existantes si disponibles
        if (latitudeField && longitudeField && 
            latitudeField.value && longitudeField.value) {
            defaultLat = parseFloat(latitudeField.value);
            defaultLng = parseFloat(longitudeField.value);
            defaultZoom = 13;
        }
        
        // Initialiser la carte Leaflet
        map = L.map(mapContainer).setView([defaultLat, defaultLng], defaultZoom);
        
        // Ajouter la couche de tuiles OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Ajouter un marqueur si des coordonnées existent
        if (latitudeField && longitudeField && 
            latitudeField.value && longitudeField.value) {
            marker = L.marker([defaultLat, defaultLng]).addTo(map);
        }
        
        // Gérer les clics sur la carte
        map.on('click', function(e) {
            setLocation(e.latlng.lat, e.latlng.lng);
            
            // Faire une recherche inverse pour obtenir l'adresse
            reverseGeocode(e.latlng.lat, e.latlng.lng);
        });
    }
    
    // Fonction pour définir l'emplacement
    function setLocation(lat, lng) {
        if (latitudeField && longitudeField) {
            latitudeField.value = lat;
            longitudeField.value = lng;
        }
        
        if (map) {
            // Supprimer le marqueur existant s'il y en a un
            if (marker) {
                map.removeLayer(marker);
            }
            
            // Ajouter un nouveau marqueur
            marker = L.marker([lat, lng]).addTo(map);
            
            // Centrer la carte sur le marqueur
            map.setView([lat, lng], 13);
        }
    }
    
    // Fonction pour effectuer une recherche d'adresse
    function searchAddress(query) {
        if (!query || query.length < 3) {
            hideAutocompleteResults();
            return;
        }
        
        // Utiliser l'API d'autocomplétion de l'adresse française
        const url = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=5`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                displayAutocompleteResults(data.features);
            })
            .catch(error => {
                console.error('Erreur lors de la recherche d\'adresse:', error);
            });
    }
    
    // Fonction pour effectuer une recherche inverse (coordonnées -> adresse)
    function reverseGeocode(lat, lng) {
        const url = `https://api-adresse.data.gouv.fr/reverse/?lon=${lng}&lat=${lat}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.features && data.features.length > 0) {
                    const result = data.features[0].properties;
                    
                    if (addressField) {
                        addressField.value = result.name;
                    }
                    
                    if (postalCodeField) {
                        postalCodeField.value = result.postcode;
                    }
                    
                    if (cityField) {
                        cityField.value = result.city;
                    }
                    
                    if (addressSearchInput) {
                        addressSearchInput.value = `${result.name}, ${result.postcode} ${result.city}`;
                    }
                }
            })
            .catch(error => {
                console.error('Erreur lors de la recherche inverse:', error);
            });
    }
    
    // Fonction pour afficher les résultats d'autocomplétion
    function displayAutocompleteResults(features) {
        if (!autocompleteResults) return;
        
        // Vider les résultats précédents
        autocompleteResults.innerHTML = '';
        
        if (!features || features.length === 0) {
            hideAutocompleteResults();
            return;
        }
        
        // Ajouter chaque résultat
        features.forEach((feature, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = feature.properties.label;
            
            // Gérer le clic sur un résultat
            item.addEventListener('click', function() {
                selectAddress(feature);
            });
            
            // Gérer le survol
            item.addEventListener('mouseover', function() {
                selectedIndex = index;
                highlightSelectedItem();
            });
            
            autocompleteResults.appendChild(item);
        });
        
        // Afficher les résultats
        autocompleteResults.style.display = 'block';
    }
    
    // Fonction pour masquer les résultats d'autocomplétion
    function hideAutocompleteResults() {
        if (autocompleteResults) {
            autocompleteResults.style.display = 'none';
            autocompleteResults.innerHTML = '';
        }
        selectedIndex = -1;
    }
    
    // Fonction pour mettre en surbrillance l'élément sélectionné
    function highlightSelectedItem() {
        if (!autocompleteResults) return;
        
        // Supprimer la classe active de tous les éléments
        const items = autocompleteResults.querySelectorAll('.autocomplete-item');
        items.forEach(item => item.classList.remove('active'));
        
        // Ajouter la classe active à l'élément sélectionné
        if (selectedIndex >= 0 && selectedIndex < items.length) {
            items[selectedIndex].classList.add('active');
        }
    }
    
    // Fonction pour sélectionner une adresse
    function selectAddress(feature) {
        const properties = feature.properties;
        const coordinates = feature.geometry.coordinates;
        
        // Mettre à jour les champs d'adresse
        if (addressField) {
            addressField.value = properties.name;
        }
        
        if (postalCodeField) {
            postalCodeField.value = properties.postcode;
        }
        
        if (cityField) {
            cityField.value = properties.city;
        }
        
        // Mettre à jour le champ de recherche
        if (addressSearchInput) {
            addressSearchInput.value = properties.label;
        }
        
        // Mettre à jour les coordonnées
        setLocation(coordinates[1], coordinates[0]);
        
        // Masquer les résultats
        hideAutocompleteResults();
    }
    
    // Ajouter les écouteurs d'événements pour l'autocomplétion
    if (addressSearchInput) {
        // Recherche lors de la saisie
        addressSearchInput.addEventListener('input', function() {
            // Annuler la recherche précédente
            if (autocompleteTimeout) {
                clearTimeout(autocompleteTimeout);
            }
            
            // Définir un délai avant de lancer la recherche
            autocompleteTimeout = setTimeout(function() {
                searchAddress(addressSearchInput.value);
            }, 300);
        });
        
        // Gérer les touches spéciales (flèches, entrée, échap)
        addressSearchInput.addEventListener('keydown', function(e) {
            const items = autocompleteResults ? autocompleteResults.querySelectorAll('.autocomplete-item') : [];
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                    highlightSelectedItem();
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, 0);
                    highlightSelectedItem();
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    if (selectedIndex >= 0 && selectedIndex < items.length) {
                        items[selectedIndex].click();
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    hideAutocompleteResults();
                    break;
            }
        });
        
        // Masquer les résultats lorsque le champ perd le focus
        addressSearchInput.addEventListener('blur', function() {
            // Délai pour permettre le clic sur un résultat
            setTimeout(hideAutocompleteResults, 200);
        });
    }
    
    // Mettre à jour la carte lorsque les champs d'adresse sont modifiés
    if (addressField && postalCodeField && cityField) {
        const updateMapFromAddress = function() {
            const address = `${addressField.value}, ${postalCodeField.value} ${cityField.value}, France`;
            
            if (!addressField.value || !postalCodeField.value || !cityField.value) {
                return;
            }
            
            // Rechercher les coordonnées de l'adresse
            const url = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(address)}&limit=1`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.features && data.features.length > 0) {
                        const coordinates = data.features[0].geometry.coordinates;
                        setLocation(coordinates[1], coordinates[0]);
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la recherche d\'adresse:', error);
                });
        };
        
        // Mettre à jour la carte lorsque les champs d'adresse perdent le focus
        addressField.addEventListener('blur', updateMapFromAddress);
        postalCodeField.addEventListener('blur', updateMapFromAddress);
        cityField.addEventListener('blur', updateMapFromAddress);
    }
});
