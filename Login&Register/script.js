const container = document.querySelector('.container');
const registerbtn = document.querySelector('.register-btn');
const loginbtn = document.querySelector('.login-btn');

if (registerbtn) {
    registerbtn.addEventListener('click', () => {
        container?.classList.add('active');
    });
}

if (loginbtn) {
    loginbtn.addEventListener('click', () => {
        container?.classList.remove('active');
    });
}
