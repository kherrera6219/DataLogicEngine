import React from 'react';

const baseClass = 'card shadow-sm border-0 glass-panel';

const Card = ({ children, className = '', ...props }) => (
  <div className={`${baseClass} ${className}`.trim()} {...props}>
    {children}
  </div>
);

Card.Header = function CardHeader({ children, className = '' }) {
  return (
    <div className={`card-header bg-transparent border-0 pb-0 d-flex align-items-center ${className}`.trim()}>
      {children}
    </div>
  );
};

Card.Body = function CardBody({ children, className = '' }) {
  return (
    <div className={`card-body ${className}`.trim()}>
      {children}
    </div>
  );
};

Card.Title = function CardTitle({ children, className = '' }) {
  return <h5 className={`card-title mb-0 ${className}`.trim()}>{children}</h5>;
};

Card.Footer = function CardFooter({ children, className = '' }) {
  return (
    <div className={`card-footer bg-transparent border-0 pt-0 ${className}`.trim()}>
      {children}
    </div>
  );
};

export default Card;
