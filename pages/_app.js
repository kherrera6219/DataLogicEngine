
import 'bootstrap/dist/css/bootstrap.min.css';
import '../styles/globals.css';
import { useEffect } from 'react';

function MyApp({ Component, pageProps }) {
  // Load Bootstrap JS on client side only
  useEffect(() => {
    import('bootstrap/dist/js/bootstrap.bundle.min.js');
  }, []);

  return <Component {...pageProps} />;
}

export default MyApp;
