
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Layout({ children }) {
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll effect for navbar
  useEffect(() => {
    const handleScroll = () => {
      const offset = window.scrollY;
      if (offset > 50) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <div className="d-flex flex-column min-vh-100">
      <header>
        <nav className={`navbar navbar-expand-lg navbar-dark bg-dark ${scrolled ? 'shadow-sm' : ''}`} 
             style={{ transition: 'all 0.3s ease' }}>
          <div className="container">
            <Link href="/" className="navbar-brand d-flex align-items-center">
              <i className="bi bi-diagram-3 me-2"></i>
              <span className="d-none d-sm-inline">Universal Knowledge Graph</span>
              <span className="d-inline d-sm-none">UKG</span>
            </Link>
            <button 
              className="navbar-toggler" 
              type="button" 
              data-bs-toggle="collapse" 
              data-bs-target="#navbarNav" 
              aria-controls="navbarNav" 
              aria-expanded="false" 
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav ms-auto">
                <li className="nav-item">
                  <Link href="/" className="nav-link px-3">
                    <i className="bi bi-house-door me-1 d-inline d-lg-none"></i> Home
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/chat" className="nav-link px-3">
                    <i className="bi bi-chat-dots me-1 d-inline d-lg-none"></i> Chat
                  </Link>
                </li>
                <li className="nav-item">
                  <a className="nav-link px-3" href="#about">
                    <i className="bi bi-info-circle me-1 d-inline d-lg-none"></i> About
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </header>
      
      <main className="flex-grow-1">
        <div className="container py-4">
          {children}
        </div>
      </main>
      
      <footer className="bg-dark text-light py-3 mt-4">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-md-6 text-center text-md-start mb-2 mb-md-0">
              <p className="mb-0">Universal Knowledge Graph System &copy; {new Date().getFullYear()}</p>
            </div>
            <div className="col-md-6">
              <ul className="list-inline mb-0 text-center text-md-end">
                <li className="list-inline-item">
                  <a href="#" className="text-light">
                    <i className="bi bi-github"></i>
                  </a>
                </li>
                <li className="list-inline-item ms-3">
                  <a href="#" className="text-light">
                    <i className="bi bi-twitter"></i>
                  </a>
                </li>
                <li className="list-inline-item ms-3">
                  <a href="#" className="text-light">
                    <i className="bi bi-linkedin"></i>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
