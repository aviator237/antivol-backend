const fileInput = document.getElementById('fileInput');
const previewGrid = document.getElementById('previewGrid');
const addMoreBtn = document.getElementById('addMoreBtn');
const submitBtn = document.getElementById('submitBtn');
const deleteBtn = document.getElementById('deleteBtn');
const dropZone = document.getElementById('dropZone');
const selectedCount = document.getElementById('selectedCount');
const totalCount = document.getElementById('totalCount');
const progressBar = document.querySelector('.progress .bar');
const progressContainer = document.querySelector('.progress');
const progressPercentage = document.getElementById('progress-percentage');
const progressCount = document.getElementById('progress-count');
let filesArray = [];
let selectedFiles = new Set();

fileInput.addEventListener('change', (event) => {
    const files = Array.from(event.target.files);
    if (filesArray.length + files.length > 30) {
        UIkit.notification({ message: 'Vous pouvez télécharger jusqu\'à 30 photos.', status: 'danger' });
        return;
    }
    filesArray = filesArray.concat(files);
    updatePreviewGrid();
});

addMoreBtn.addEventListener('click', () => {
    fileInput.click();
});

dropZone.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropZone.classList.remove('dragover');
    const files = Array.from(event.dataTransfer.files);
    const dataTransfer = new DataTransfer();
    files.forEach(file => {
        dataTransfer.items.add(file);
    });
    const currentFiles = Array.from(fileInput.files);
    const newFiles = currentFiles.concat(files);
    const newDataTransfer = new DataTransfer();
    newFiles.forEach(file => newDataTransfer.items.add(file));
    fileInput.files = newDataTransfer.files;
    
    if (filesArray.length + files.length > 30) {
        UIkit.notification({ message: 'Vous pouvez télécharger jusqu\'à 30 photos.', status: 'danger' });
        return;
    }
    
    filesArray = filesArray.concat(files);
    updatePreviewGrid();
});

function updatePreviewGrid() {
    previewGrid.innerHTML = '';
    filesArray.forEach((file, index) => {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.classList.add('grid-item');
        img.addEventListener('click', () => toggleSelect(img, index));
        previewGrid.appendChild(img);
    });
    updateDeleteButton();
    updateSelectedCount();
    updateTotalCount();
}

function toggleSelect(img, index) {
    if (selectedFiles.has(index)) {
        selectedFiles.delete(index);
        img.classList.remove('selected');
    } else {
        selectedFiles.add(index);
        img.classList.add('selected');
    }
    updateDeleteButton();
    updateSelectedCount();
}

function updateDeleteButton() {
    if (selectedFiles.size > 0) {
        deleteBtn.style.display = 'block';
    } else {
        deleteBtn.style.display = 'none';
    }
}

function updateSelectedCount() {
    selectedCount.textContent = `${selectedFiles.size} images sélectionnées`;
}

function updateTotalCount() {
    totalCount.textContent = `${filesArray.length} images au total`;
}

deleteBtn.addEventListener('click', () => {
    filesArray = filesArray.filter((_, index) => !selectedFiles.has(index));
    selectedFiles.clear();
    updatePreviewGrid();
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

submitBtn.addEventListener('click', (event) => {
    if (filesArray.length === 0) {
        UIkit.notification({ message: 'Veuillez sélectionner des photos avant d\'envoyer.', status: 'danger' });
        event.preventDefault();
        return;
    }

    const formData = new FormData();
    filesArray.forEach(file => {
        formData.append('photos', file);
    });

    const xhr = new XMLHttpRequest();
    xhr.open('POST', document.getElementById('uploadForm').action, true);

    // Include CSRF token in the request headers
    const csrftoken = getCookie('csrftoken');
    xhr.setRequestHeader('X-CSRFToken', csrftoken);

    xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100;
            progressBar.style.width = `${percentComplete}%`;
            progressPercentage.textContent = `${Math.round(percentComplete)}%`;
            progressCount.textContent = `${event.loaded} / ${event.total}`;
        }
    });

    xhr.addEventListener('load', () => {
        progressContainer.style.display = 'none';
        const response = JSON.parse(xhr.responseText);
        if (xhr.status === 200) {
            UIkit.notification({ message: response.message, status: 'success' });
            if (response.redirect_url) {
                window.location.href = response.redirect_url;
            }
        } else {
            UIkit.notification({ message: response.message, status: 'danger' });
        }
    });

    progressContainer.style.display = 'flex';
    xhr.send(formData);
    event.preventDefault();
});

