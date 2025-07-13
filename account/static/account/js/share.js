const phoneNumberInput = document.getElementById("phoneNumberInput");
const addPhoneNumberBtn = document.getElementById("addPhoneNumberBtn");
const contactList = document.getElementById("contactList");
const loadingIndicator = document.getElementById("loadingIndicator");
let contactsArray = [];

submitBtn.addEventListener("click", (event) => {
  const checkedContacts = document.querySelectorAll('input[name="my_contacts"]:checked');
  if (contactsArray.length === 0 && checkedContacts.length === 0) {
    alert("Veuillez ajouter au moins un numéro de téléphone.");
    event.preventDefault();
  } else {
    event.preventDefault();
    my_form = document.getElementById("uploadForm");
    const phoneNumbersInput = document.getElementById("phoneNumbersInput");
    console.log(contactsArray.map((contact) => contact.number));
    phoneNumbersInput.value = contactsArray.map((contact) => contact.number);
    my_form.submit();
  }
});

addPhoneNumberBtn.addEventListener("click", () => {
  const phoneNumber = phoneNumberInput.value.trim();
  if (phoneNumber) {
    loadingIndicator.style.display = "block";
    fetch(`/api-box/check_phone_number/${phoneNumber}/`)
      .then((response) => response.json())
      .then((data) => {
        loadingIndicator.style.display = "none";
        if (data.exists === true) {
          addContactToList({ name: "", number: phoneNumber });
          phoneNumberInput.value = "";
        } else {
          alert("Numéro de téléphone non reconu.");
        }
      })
      .catch((error) => {
        loadingIndicator.style.display = "none";
        alert(
          "Une erreur s'est produite lors de la vérification du numéro de téléphone."
        );
      });
  }
});

function addContactToList(contact) {
  contactsArray.push(contact);
  updateContactList();
}

function updateContactList() {
  contactList.innerHTML = "";
  contactsArray.forEach((contact, index) => {
    const li = document.createElement("span");
    li.textContent = contact.name
      ? `${contact.name} (${contact.number})`
      : contact.number;
    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Supprimer";
    removeBtn.addEventListener("click", () => removeContact(index));
    li.appendChild(removeBtn);
    contactList.appendChild(li);
  });
}

function removeContact(index) {
  contactsArray.splice(index, 1);
  updateContactList();
}
