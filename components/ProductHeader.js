import Link from 'next/link';

export default function ProductHeader({ title, subtitle, breadcrumbs = [], actions = [] }) {
  return (
    <div className="glass-panel p-3 p-md-4 mb-3 rounded-4">
      <div className="d-flex flex-wrap justify-content-between gap-3 align-items-start">
        <div className="d-flex flex-column gap-2">
          <div className="d-flex align-items-center gap-2 flex-wrap text-white-50 small">
            <Link href="/" className="text-decoration-none text-white-50 d-flex align-items-center gap-1">
              <i className="bi bi-arrow-left-short"></i> Back to Hub
            </Link>
            {breadcrumbs.length > 0 && <span className="text-white-50">/</span>}
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.label} className="d-flex align-items-center gap-1">
                {index > 0 && <span>/</span>}
                {crumb.href ? (
                  <Link href={crumb.href} className="text-decoration-none text-white">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-white">{crumb.label}</span>
                )}
              </span>
            ))}
          </div>
          <div>
            <p className="section-title mb-1">{title}</p>
            <h2 className="mb-0 text-white">{subtitle}</h2>
          </div>
        </div>

        {actions.length > 0 && (
          <div className="d-flex gap-2 flex-wrap">
            {actions.map((action) => (
              action.href ? (
                <Link
                  key={action.label}
                  href={action.href}
                  className={`btn btn-${action.variant || 'outline-light'} btn-sm rounded-pill d-flex align-items-center gap-2`}
                >
                  {action.icon && <i className={`bi bi-${action.icon}`}></i>}
                  {action.label}
                </Link>
              ) : (
                <button
                  key={action.label}
                  className={`btn btn-${action.variant || 'outline-light'} btn-sm rounded-pill d-flex align-items-center gap-2`}
                  onClick={action.onClick}
                  type="button"
                >
                  {action.icon && <i className={`bi bi-${action.icon}`}></i>}
                  {action.label}
                </button>
              )
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
