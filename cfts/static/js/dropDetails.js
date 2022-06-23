if (authStatus == "prompt") {
    codeSubmit = document.getElementById("codeSubmit")
    codeInput = document.getElementById("codeInput")

    function submitCode() {
        window.location = window.location + "/" + codeInput.value
    }

    codeSubmit.addEventListener('click', function() {
        submitCode()
    }, false);

    codeInput.addEventListener('keypress', function(e) {
        if (e.keyCode == 13) {
            submitCode()
        }
    }, false);

} else {
    history.pushState(null, "", location.href.split("/").slice(0, 5).join('/'))
    if (authStatus == "not authorized") {
        alert("Request Code entered is not correct")
        window.location = window.location
    } else if (authStatus == "authorized") {
        passphraseSubmit = document.getElementById("passphraseSubmit")
        passphraseInput = document.getElementById("passphraseInput")

        function submitPassphrase() {
            window.location = "/download-drop/" + dropID + "/" + passphraseInput.value
        }

        passphraseSubmit.addEventListener('click', function() {
            submitPassphrase()
        }, false);

        passphraseInput.addEventListener('keypress', function(e) {
            if (e.keyCode == 13) {
                submitPassphrase()
            }
        }, false);
    }
}