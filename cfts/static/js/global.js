// PREVENT DEFAULT ACTIONS FROM OCCURRING ON EVENTS 
const preventDefaults = (e) => {
    e.preventDefault();
    e.stopPropagation();
};

// WORK WITH COOKIES
function getCookie(name) {
    let cookie = {};
    document.cookie.split(';').forEach(function(el) {
        let [k, v] = el.split('=');
        cookie[k.trim()] = v;
    })
    return cookie[name];
}