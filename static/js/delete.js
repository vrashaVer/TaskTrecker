// Отримуємо елементи модального вікна
var modal = document.getElementById("deleteModal");
var confirmBtn = document.getElementById("confirmDeleteBtn");
var cancelBtn = document.getElementById("cancelDeleteBtn");
var closeBtn = document.getElementsByClassName("close")[0];

// Функція відкриття модального вікна при натисканні "Delete"
function confirmDelete() {
    modal.style.display = "block";  // Відкриваємо модальне вікно
}

// Закриваємо модальне вікно при натисканні на "x" або "Cancel"
closeBtn.onclick = function() {
    modal.style.display = "none";
}

cancelBtn.onclick = function() {
    modal.style.display = "none";
}

// Закриваємо модальне вікно при натисканні за межами вікна
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
