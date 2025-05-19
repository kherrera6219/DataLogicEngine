
import Link from 'next/link';

export default function Layout({ children }) {
  return (
    <>
      <header>
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
          <div className="container-fluid">
            <Link href="/" className="navbar-brand">
              Universal Knowledge Graph
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
              <ul className="navbar-nav">
                <li className="nav-item">
                  <Link href="/" className="nav-link">
                    Home
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/chat" className="nav-link">
                    Chat
                  </Link>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="#about">About</a>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </header>
      <main className="container py-4">
        {children}
      </main>
      <footer className="bg-dark text-light py-3 mt-5">
        <div className="container text-center">
          <p>Universal Knowledge Graph System &copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </>
  );
}
