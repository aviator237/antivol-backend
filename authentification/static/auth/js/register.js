document.addEventListener('DOMContentLoaded', function () {
    const passwordInput = document.querySelector('input[name="password"]');
    const passwordConfirmInput = document.querySelector('input[name="password1"]');
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');
    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone_number"]');
    const submitButton = document.querySelector('.submit');
    const passwordConditions = document.getElementById('password-conditions');
    const conditions = {
        length: document.querySelector('#length'),
        uppercase: document.querySelector('#uppercase'),
        lowercase: document.querySelector('#lowercase'),
        number: document.querySelector('#number'),
        special: document.querySelector('#special')
    };

    // Variables pour suivre l'état de validation
    let recaptchaValidated = false;
    let passwordValid = false;

    // Fonction pour vérifier si tous les champs sont remplis
    function areAllFieldsFilled() {
        // Vérifier les champs utilisateur
        const userFieldsFilled =
            firstNameInput.value.trim() !== '' &&
            lastNameInput.value.trim() !== '' &&
            emailInput.value.trim() !== '' &&
            phoneInput.value.trim() !== '' &&
            passwordInput.value.trim() !== '' &&
            passwordConfirmInput.value.trim() !== '';

        // Vérifier les champs entreprise
        const companyNameInput = document.querySelector('input[name="company_name"]');
        const companySiretInput = document.querySelector('input[name="company_siret"]');
        const companyCategoryInput = document.querySelector('select[name="company_category"]');
        const companyAddressInput = document.querySelector('input[name="company_address"]');
        const companyPostalCodeInput = document.querySelector('input[name="company_postal_code"]');
        const companyCityInput = document.querySelector('input[name="company_city"]');
        const companyLatitudeInput = document.querySelector('input[name="company_latitude"]');
        const companyLongitudeInput = document.querySelector('input[name="company_longitude"]');

        // Si nous sommes sur une page qui n'a pas les champs d'entreprise
        if (!companyNameInput || !companySiretInput || !companyCategoryInput ||
            !companyAddressInput || !companyPostalCodeInput || !companyCityInput ||
            !companyLatitudeInput || !companyLongitudeInput) {
            return userFieldsFilled;
        }

        // Afficher les valeurs des champs pour le débogage
        console.log("Valeurs des champs entreprise:", {
            companyName: companyNameInput.value,
            companySiret: companySiretInput.value,
            companyCategory: companyCategoryInput.value,
            companyAddress: companyAddressInput.value,
            companyPostalCode: companyPostalCodeInput.value,
            companyCity: companyCityInput.value,
            companyLatitude: companyLatitudeInput.value,
            companyLongitude: companyLongitudeInput.value
        });

        // Pour le champ de catégorie, nous devons vérifier s'il a une valeur sélectionnée
        let categoryValue = companyCategoryInput.value;
        if (companyCategoryInput.selectedIndex === 0 && companyCategoryInput.options[0].text.includes("Sélectionnez")) {
            categoryValue = '';
        }

        const companyFieldsFilled =
            companyNameInput.value.trim() !== '' &&
            companySiretInput.value.trim() !== '' &&
            categoryValue.trim() !== '' &&
            companyAddressInput.value.trim() !== '' &&
            companyPostalCodeInput.value.trim() !== '' &&
            companyCityInput.value.trim() !== '';

        // Les coordonnées sont optionnelles si l'adresse est remplie
        const hasCoordinates =
            companyLatitudeInput.value.trim() !== '' &&
            companyLongitudeInput.value.trim() !== '';

        // Si les coordonnées ne sont pas remplies, essayons de les obtenir à partir de l'adresse
        if (!hasCoordinates && companyAddressInput.value.trim() !== '' &&
            companyPostalCodeInput.value.trim() !== '' && companyCityInput.value.trim() !== '') {
            // Construire l'adresse complète
            const fullAddress = `${companyAddressInput.value}, ${companyPostalCodeInput.value} ${companyCityInput.value}, France`;

            // Utiliser l'API de géocodage pour obtenir les coordonnées
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(fullAddress)}&limit=1`)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        companyLatitudeInput.value = data[0].lat;
                        companyLongitudeInput.value = data[0].lon;

                        // Mettre à jour la carte si elle existe
                        if (window.centerMapOnAddress) {
                            window.centerMapOnAddress(data[0].lat, data[0].lon, fullAddress);
                        }

                        // Mettre à jour l'état du bouton
                        updateSubmitButton(passwordValid);
                    }
                })
                .catch(error => console.error("Erreur lors du géocodage:", error));
        }

        return userFieldsFilled && companyFieldsFilled && (hasCoordinates || companyFieldsFilled);
    }

    passwordInput.addEventListener('focus', function () {
        passwordConditions.style.display = 'block';
    });

    passwordInput.addEventListener('blur', function () {
        if (passwordInput.value === '') {
            passwordConditions.style.display = 'none';
        }
    });

    // Ajouter des écouteurs d'événements pour tous les champs
    const allInputs = [firstNameInput, lastNameInput, emailInput, phoneInput, passwordInput, passwordConfirmInput];

    // Ajouter les champs d'entreprise s'ils existent
    const companyInputs = [
        document.querySelector('input[name="company_name"]'),
        document.querySelector('input[name="company_siret"]'),
        document.querySelector('select[name="company_category"]'),
        document.querySelector('input[name="company_address"]'),
        document.querySelector('input[name="company_postal_code"]'),
        document.querySelector('input[name="company_city"]'),
        document.querySelector('input[name="company_latitude"]'),
        document.querySelector('input[name="company_longitude"]')
    ].filter(input => input !== null);

    // Combiner tous les champs
    const allFormInputs = [...allInputs, ...companyInputs];

    allFormInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Vérifier si le mot de passe est valide
            const password = passwordInput.value;
            let passwordValid =
                password.length >= 8 &&
                /[A-Z]/.test(password) &&
                /[a-z]/.test(password) &&
                /[0-9]/.test(password) &&
                /[!@#$%^&*(),.?":{}|<>]/.test(password);

            // Mettre à jour l'état du bouton
            updateSubmitButton(passwordValid);
        });
    });

    passwordInput.addEventListener('input', function () {
        const password = passwordInput.value;
        let valid = true;

        // Check length
        if (password.length >= 8) {
            conditions.length.classList.add('valid');
            conditions.length.classList.remove('invalid');
        } else {
            conditions.length.classList.add('invalid');
            conditions.length.classList.remove('valid');
            valid = false;
        }

        // Check uppercase
        if (/[A-Z]/.test(password)) {
            conditions.uppercase.classList.add('valid');
            conditions.uppercase.classList.remove('invalid');
        } else {
            conditions.uppercase.classList.add('invalid');
            conditions.uppercase.classList.remove('valid');
            valid = false;
        }

        // Check lowercase
        if (/[a-z]/.test(password)) {
            conditions.lowercase.classList.add('valid');
            conditions.lowercase.classList.remove('invalid');
        } else {
            conditions.lowercase.classList.add('invalid');
            conditions.lowercase.classList.remove('valid');
            valid = false;
        }

        // Check number
        if (/[0-9]/.test(password)) {
            conditions.number.classList.add('valid');
            conditions.number.classList.remove('invalid');
        } else {
            conditions.number.classList.add('invalid');
            conditions.number.classList.remove('valid');
            valid = false;
        }

        // Check special character
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            conditions.special.classList.add('valid');
            conditions.special.classList.remove('invalid');
        } else {
            conditions.special.classList.add('invalid');
            conditions.special.classList.remove('valid');
            valid = false;
        }

        // Vérifier si le mot de passe est valide et si le reCAPTCHA est validé
        updateSubmitButton(valid);
    });

    // Fonction pour mettre à jour l'état du bouton de soumission
    function updateSubmitButton(isPasswordValid) {
        passwordValid = isPasswordValid;
        const allFieldsFilled = areAllFieldsFilled();
        const passwordsMatch = passwordInput.value === passwordConfirmInput.value;

        // Activer le bouton si toutes les conditions sont remplies
        submitButton.disabled = !(passwordValid && recaptchaValidated && allFieldsFilled && passwordsMatch);

        // Mettre à jour le message de statut
        const formStatus = document.getElementById('form-status');
        if (formStatus) {
            if (!allFieldsFilled) {
                formStatus.textContent = "Veuillez remplir tous les champs obligatoires.";
                formStatus.style.color = "#ff6b6b";
            } else if (!passwordValid) {
                formStatus.textContent = "Le mot de passe ne respecte pas les critères de sécurité.";
                formStatus.style.color = "#ff6b6b";
            } else if (!passwordsMatch) {
                formStatus.textContent = "Les mots de passe ne correspondent pas.";
                formStatus.style.color = "#ff6b6b";
            } else if (!recaptchaValidated) {
                formStatus.textContent = "Veuillez valider le captcha.";
                formStatus.style.color = "#ff6b6b";
            } else {
                formStatus.textContent = "Formulaire valide ! Vous pouvez continuer.";
                formStatus.style.color = "#37b24d";
            }
        }

        // Afficher l'état de validation dans la console pour le débogage
        console.log({
            passwordValid,
            recaptchaValidated,
            allFieldsFilled,
            passwordsMatch,
            buttonDisabled: submitButton.disabled
        });
    }

    // Fonction générique pour intercepter tous les callbacks de reCAPTCHA
    function handleRecaptchaSuccess(token) {
        console.log("reCAPTCHA validé avec succès, token:", token ? "reçu" : "non reçu");
        recaptchaValidated = true;

        // Vérifier si le mot de passe est valide
        const password = passwordInput.value;
        const isPasswordValid =
            password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /[a-z]/.test(password) &&
            /[0-9]/.test(password) &&
            /[!@#$%^&*(),.?":{}|<>]/.test(password);

        updateSubmitButton(isPasswordValid);

        // Mettre à jour le message de statut
        const formStatus = document.getElementById('form-status');
        if (formStatus) {
            formStatus.textContent = "reCAPTCHA validé ! Vérification des autres champs...";
            formStatus.style.color = "#37b24d";
        }
    }

    // Fonction de callback pour reCAPTCHA
    window.onRecaptchaSuccess = handleRecaptchaSuccess;

    // Intercepter tous les callbacks possibles générés par reCAPTCHA
    // Le format est généralement onSubmit_UUID
    window.addEventListener('load', function() {
        // Observer les changements dans l'objet window pour détecter les nouveaux callbacks
        const windowProps = Object.getOwnPropertyNames(window);
        for (const prop of windowProps) {
            if (prop.startsWith('onSubmit_')) {
                console.log("Callback reCAPTCHA détecté:", prop);
                // Sauvegarder le callback original s'il existe
                const originalCallback = window[prop];
                // Remplacer par notre fonction qui appelle à la fois le callback original et notre handler
                window[prop] = function(token) {
                    console.log("reCAPTCHA validated for '" + prop + "'");
                    if (typeof originalCallback === 'function') {
                        originalCallback(token);
                    }
                    handleRecaptchaSuccess(token);
                };
            }
        }
    });

    // Vérifier périodiquement les nouveaux callbacks
    const checkInterval = setInterval(function() {
        const windowProps = Object.getOwnPropertyNames(window);
        for (const prop of windowProps) {
            if (prop.startsWith('onSubmit_') && typeof window[prop] === 'function' && window[prop].toString().indexOf('handleRecaptchaSuccess') === -1) {
                console.log("Nouveau callback reCAPTCHA détecté:", prop);
                const originalCallback = window[prop];
                window[prop] = function(token) {
                    console.log("reCAPTCHA validated for '" + prop + "'");
                    if (typeof originalCallback === 'function') {
                        originalCallback(token);
                    }
                    handleRecaptchaSuccess(token);
                };
            }
        }
    }, 1000); // Vérifier toutes les secondes

    window.onRecaptchaExpired = function() {
        console.log("reCAPTCHA expiré");
        recaptchaValidated = false;
        updateSubmitButton(passwordValid);

        // Mettre à jour le message de statut
        const formStatus = document.getElementById('form-status');
        if (formStatus) {
            formStatus.textContent = "Le reCAPTCHA a expiré. Veuillez le valider à nouveau.";
            formStatus.style.color = "#ff6b6b";
        }
    };

    window.onRecaptchaError = function() {
        console.log("Erreur reCAPTCHA");
        recaptchaValidated = false;
        updateSubmitButton(passwordValid);

        // Mettre à jour le message de statut
        const formStatus = document.getElementById('form-status');
        if (formStatus) {
            formStatus.textContent = "Une erreur s'est produite avec le reCAPTCHA. Veuillez réessayer.";
            formStatus.style.color = "#ff6b6b";
        }

        // Afficher un message d'erreur sous le captcha
        const captchaField = document.querySelector('.captcha-field');
        if (captchaField && !document.querySelector('.captcha-error')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'captcha-error';
            errorDiv.textContent = 'Une erreur s\'est produite avec le captcha. Veuillez réessayer.';
            captchaField.appendChild(errorDiv);
        }
    };

    // Ne pas initialiser le reCAPTCHA ici, cela sera fait par le callback onRecaptchaLoad
    console.log("En attente de l'initialisation du reCAPTCHA par le callback onRecaptchaLoad...");
});
