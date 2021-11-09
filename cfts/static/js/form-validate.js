var password1 = document.getElementById('id_password1')
var password2 = document.getElementById('id_password2')

function validatePass(){
    if(password1.value != password2.value){
        password1.setCustomValidity("Passwords do not match.")
        password2.setCustomValidity("Passwords do not match.")
    }
    else if(password1.value == password2.value){
        console.log("passwords match")
        password1.setCustomValidity('')
        password2.setCustomValidity('')
    }
}

password1.addEventListener('change', validatePass);
password2.addEventListener('change', validatePass);

(function () {
    'use strict'
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')
    
    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
    .forEach(function (form) {
        form.addEventListener('submit', function (event) {
            validatePass()
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })
})()


