import "bootstrap/dist/css/bootstrap.min.css"; // Import bootstrap CSS
import '@styles/globals.css'
import { useEffect } from "react";
import $ from "jquery"



function Application({ Component, pageProps }) {
  useEffect(() => {
    var bootstrap = require("bootstrap/dist/js/bootstrap.bundle.min.js");
    document.querySelectorAll('[data-bs-toggle="popover"]')
      .forEach(popover => {
        new bootstrap.Popover(popover)
      })
  }, []);

  return <Component {...pageProps} />
}

export default Application
