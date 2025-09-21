import React from 'react';
import {
  Card as FluentCard,
  CardHeader,
  CardPreview,
  CardFooter,
  makeStyles,
  shorthands,
  mergeClasses,
} from '@fluentui/react-components';
import Text from './Text';

const useStyles = makeStyles({
  root: {
    backgroundColor: 'var(--colorNeutralBackground2)',
    borderRadius: '20px',
    boxShadow: '0 18px 45px rgba(9, 17, 32, 0.35)',
    border: '1px solid rgba(255,255,255,0.04)',
    backdropFilter: 'blur(16px)',
  },
  header: {
    ...shorthands.padding('4px', '4px', '12px', '4px'),
  },
  body: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    ...shorthands.padding('8px', '4px', '4px', '4px'),
  },
  footer: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(255,255,255,0.04)',
  },
});

const Card = ({ children, className, appearance = 'filled', orientation = 'vertical', size = 'medium', ...props }) => {
  const styles = useStyles();

  return (
    <FluentCard
      appearance={appearance}
      orientation={orientation}
      size={size}
      className={mergeClasses(styles.root, className)}
      {...props}
    >
      {children}
    </FluentCard>
  );
};

const CardHeaderSection = ({ title, description, action, className }) => {
  const styles = useStyles();
  const headerContent =
    typeof title === 'string' ? (
      <Text fontSize="lg" fontWeight="semibold">
        {title}
      </Text>
    ) : (
      title
    );

  return (
    <CardHeader
      className={mergeClasses(styles.header, className)}
      header={headerContent}
      description={description}
      action={action}
    />
  );
};

const CardBodySection = ({ children, className }) => {
  const styles = useStyles();
  return <div className={mergeClasses(styles.body, className)}>{children}</div>;
};

const CardFooterSection = ({ children, className }) => {
  const styles = useStyles();
  return <CardFooter className={mergeClasses(styles.footer, className)}>{children}</CardFooter>;
};

Card.Header = CardHeaderSection;
Card.Body = CardBodySection;
Card.Footer = CardFooterSection;
Card.Preview = CardPreview;

export default Card;
